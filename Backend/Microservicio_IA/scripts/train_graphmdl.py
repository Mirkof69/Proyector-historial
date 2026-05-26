#!/usr/bin/env python
"""Train GraphMDL - Graph-based Medical Deep Learning Architecture

Main training script for the GraphMDL architecture that combines:
- Graph Neural Networks (GNN) for modeling relationships between fetal biometric measurements
- Attention mechanisms for focusing on critical anatomical regions
- Multi-task learning for simultaneous classification and segmentation

This script supports:
- Real clinical ultrasound image datasets
- Medical-image-specific data augmentation
- Cross-validation with medical data standards
- Clinical metrics evaluation (sensitivity, specificity, AUC)
- GPU-accelerated training
- Model serialization with version control

Usage:
    python train_graphmdl.py
    python train_graphmdl.py --data_dir datasets/train --epochs 100 --batch_size 32
    python train_graphmdl.py --use_transfer_learning --gpu 0
    python train_graphmdl.py --cross_validation --n_folds 5

Author: Fetal Medical System AI Team
Version: 1.0.0
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_pipeline import (
    ClinicalMetricsEvaluator,
    FetalDatasetBuilder,
    KerasProgressCallback,
    MedicalCrossValidator,
    TrainingProgressTracker,
)
from graphmdl import ANATOMICAL_ADJACENCY, PATHOLOGY_CLASSES, GraphMDL
from model_registry import ModelMetadata, ModelRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/train_graphmdl.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)

# TensorFlow setup
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

try:
    import tensorflow as tf
    from tensorflow import keras

    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.error(
        "TensorFlow is required for training GraphMDL. Install with: pip install tensorflow",
    )
    sys.exit(1)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train GraphMDL - Graph-based Medical Deep Learning for Fetal Ultrasound",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Data arguments
    parser.add_argument(
        "--data_dir",
        type=str,
        default="datasets/train",
        help="Path to training dataset directory",
    )
    parser.add_argument(
        "--target_size",
        type=int,
        nargs=2,
        default=[224, 224],
        help="Target image size (height width)",
    )
    parser.add_argument(
        "--batch_size", type=int, default=16, help="Batch size for training",
    )
    parser.add_argument(
        "--num_workers", type=int, default=4, help="Number of data loading workers",
    )

    # Model architecture arguments
    parser.add_argument(
        "--graph_hidden_dim",
        type=int,
        default=128,
        help="Hidden dimension for graph convolution layers",
    )
    parser.add_argument(
        "--num_gcn_layers", type=int, default=2, help="Number of GCN layers",
    )
    parser.add_argument(
        "--num_gat_layers", type=int, default=1, help="Number of Graph Attention layers",
    )
    parser.add_argument(
        "--num_attention_heads",
        type=int,
        default=4,
        help="Number of attention heads in GAT",
    )
    parser.add_argument(
        "--use_transfer_learning",
        action="store_true",
        default=True,
        help="Use EfficientNet pre-trained weights",
    )
    parser.add_argument(
        "--no_transfer_learning",
        action="store_true",
        help="Disable transfer learning (train from scratch)",
    )
    parser.add_argument(
        "--dropout_rate",
        type=float,
        default=0.3,
        help="Dropout rate for regularization",
    )

    # Training arguments
    parser.add_argument(
        "--epochs", type=int, default=100, help="Maximum number of training epochs",
    )
    parser.add_argument(
        "--learning_rate", type=float, default=1e-3, help="Initial learning rate",
    )
    parser.add_argument(
        "--weight_decay",
        type=float,
        default=1e-4,
        help="Weight decay for AdamW optimizer",
    )
    parser.add_argument(
        "--patience", type=int, default=15, help="Early stopping patience",
    )
    parser.add_argument(
        "--min_lr", type=float, default=1e-6, help="Minimum learning rate",
    )
    parser.add_argument(
        "--reduce_lr_patience",
        type=int,
        default=5,
        help="Patience for learning rate reduction",
    )

    # Cross-validation arguments
    parser.add_argument(
        "--cross_validation", action="store_true", help="Use cross-validation training",
    )
    parser.add_argument(
        "--n_folds", type=int, default=5, help="Number of cross-validation folds",
    )

    # Augmentation arguments
    parser.add_argument(
        "--augment", action="store_true", default=True, help="Enable data augmentation",
    )
    parser.add_argument(
        "--no_augment", action="store_true", help="Disable data augmentation",
    )
    parser.add_argument(
        "--speckle_noise", type=float, default=0.02, help="Speckle noise intensity",
    )
    parser.add_argument(
        "--mixup_alpha", type=float, default=0.2, help="MixUp augmentation alpha",
    )

    # Hardware arguments
    parser.add_argument(
        "--gpu", type=str, default="0", help="GPU device to use (e.g., '0' or '0,1')",
    )
    parser.add_argument(
        "--mixed_precision", action="store_true", help="Enable mixed precision training",
    )

    # Output arguments
    parser.add_argument(
        "--output_dir",
        type=str,
        default="trained_models",
        help="Output directory for trained models",
    )
    parser.add_argument(
        "--log_dir", type=str, default="logs", help="Directory for training logs",
    )
    parser.add_argument(
        "--model_name", type=str, default="graphmdl", help="Model name for registry",
    )
    parser.add_argument(
        "--save_history",
        action="store_true",
        default=True,
        help="Save training history",
    )

    return parser.parse_args()


def setup_gpu(gpu_id: str, mixed_precision: bool = False):
    """Configure GPU settings."""
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu_id

    # Check GPU availability
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        logger.info("Found %s GPU(s): %s", len(gpus), [g.name for g in gpus])
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logger.info("GPU memory growth enabled")
    else:
        logger.warning("No GPU found. Training on CPU (this will be slow).")

    # Enable mixed precision
    if mixed_precision:
        tf.keras.mixed_precision.set_global_policy("mixed_float16")
        logger.info("Mixed precision training enabled")


def build_data_generators(args):
    """Build training and validation data generators."""
    logger.info("Loading dataset from: %s", args.data_dir)

    builder = FetalDatasetBuilder(
        data_dir=args.data_dir,
        target_size=tuple(args.target_size),
        batch_size=args.batch_size,
        augment=args.augment and not args.no_augment,
        validation_split=0.2,
        test_split=0.1,
        seed=42,
        clahe_enhance=True,
    )

    train_data, val_data, test_data, metadata = builder.build()

    X_train, y_train, _train_gen = train_data
    X_val, y_val, _val_gen = val_data

    logger.info("Dataset statistics:")
    logger.info("  Train samples: %s", len(X_train))
    logger.info("  Val samples:   %s", len(X_val))
    logger.info("  Test samples:  %s", metadata.get('test_size', 0))
    logger.info("  Classes:       %s", metadata.get('num_classes', 0))
    logger.info("  Image shape:   %s", metadata.get('image_shape', 'N/A'))

    return X_train, y_train, X_val, y_val, test_data, metadata


def build_model(args, num_pathology_classes: int = 15):
    """Build GraphMDL model."""
    logger.info("Building GraphMDL architecture...")
    logger.info("  Graph hidden dim:   %s", args.graph_hidden_dim)
    logger.info("  GCN layers:         %s", args.num_gcn_layers)
    logger.info("  GAT layers:         %s", args.num_gat_layers)
    logger.info("  Attention heads:    %s", args.num_attention_heads)
    logger.info(
        "  Transfer learning:  %s",
        args.use_transfer_learning and not args.no_transfer_learning,
    )

    model = GraphMDL(
        num_pathology_classes=num_pathology_classes,
        num_biometric_nodes=16,
        graph_hidden_dim=args.graph_hidden_dim,
        num_gcn_layers=args.num_gcn_layers,
        num_gat_layers=args.num_gat_layers,
        num_attention_heads=args.num_attention_heads,
        use_transfer_learning=args.use_transfer_learning
        and not args.no_transfer_learning,
        dropout_rate=args.dropout_rate,
        adjacency_matrix=ANATOMICAL_ADJACENCY,
    )

    model.build(input_shape=(None, *args.target_size, 3))

    total_params = model.model.count_params()
    logger.info("Total parameters: %s", total_params)

    return model


def create_callbacks(args, tracker):
    """Create training callbacks."""
    callbacks = [
        KerasProgressCallback(tracker),
        # Model checkpoint (save best)
        keras.callbacks.ModelCheckpoint(
            filepath=str(Path(args.output_dir) / "graphmdl_best.keras"),
            save_best_only=True,
            monitor="val_pathology_output_accuracy",
            mode="max",
            verbose=1,
        ),
        # Early stopping
        keras.callbacks.EarlyStopping(
            monitor="val_pathology_output_accuracy",
            patience=args.patience,
            restore_best_weights=True,
            mode="max",
            verbose=1,
        ),
        # Reduce learning rate on plateau
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_pathology_output_loss",
            factor=0.5,
            patience=args.reduce_lr_patience,
            min_lr=args.min_lr,
            verbose=1,
        ),
        # TensorBoard logging
        keras.callbacks.TensorBoard(
            log_dir=str(Path(args.log_dir) / "graphmdl_tensorboard"),
            histogram_freq=1,
            update_freq="epoch",
        ),
    ]

    return callbacks


def prepare_multi_task_labels(y_labels, num_samples, _adjacency_matrix):
    """Prepare labels for multi-task learning.

    Creates proxy labels for each task based on pathology labels:
    - ultrasound_type: derived from image features (simulated)
    - gestational_age_group: derived from pathology severity
    - risk_level: derived from pathology classification
    - anomaly_present: binary (normal vs abnormal)
    """
    # Default: assume all classes are equally distributed for proxy tasks
    num_ultrasound_classes = 5
    num_age_groups = 4
    num_risk_levels = 3

    # Generate proxy labels (in real scenario, these come from clinical metadata)
    ultrasound_labels = np.zeros((num_samples, num_ultrasound_classes))
    age_group_labels = np.zeros((num_samples, num_age_groups))
    risk_labels = np.zeros((num_samples, num_risk_levels))

    # Anomaly present: 0=normal, 1=anomaly
    anomaly_labels = np.zeros((num_samples, 1))

    for i in range(num_samples):
        if y_labels.ndim > 1:
            pathology_idx = np.argmax(y_labels[i])
        else:
            pathology_idx = int(y_labels[i])

        # Proxy assignments based on pathology index
        ultrasound_labels[i, i % num_ultrasound_classes] = 1.0
        age_group_labels[i, min(pathology_idx // 4, num_age_groups - 1)] = 1.0
        risk_labels[i, min(pathology_idx // 5, num_risk_levels - 1)] = 1.0
        anomaly_labels[i, 0] = 0.0 if pathology_idx == 0 else 1.0

    return {
        "pathology_output": y_labels if y_labels.ndim > 1 else np.eye(15)[y_labels],
        "quality_output": np.random.uniform(0.5, 1.0, (num_samples, 1)).astype(
            np.float32,
        ),
        "segmentation_output": np.zeros((num_samples, 224, 224, 1), dtype=np.float32),
        "ultrasound_type_head": ultrasound_labels,
        "gestational_age_group_head": age_group_labels,
        "risk_level_head": risk_labels,
        "anomaly_present_head": anomaly_labels,
    }


def train_single_fold(model, X_train, y_train, X_val, y_val, args, tracker):
    """Train model on a single fold."""
    num_train = len(X_train)
    num_val = len(X_val)

    # Prepare multi-task labels
    train_labels = prepare_multi_task_labels(y_train, num_train, ANATOMICAL_ADJACENCY)
    val_labels = prepare_multi_task_labels(y_val, num_val, ANATOMICAL_ADJACENCY)

    # Prepare adjacency matrices
    train_adjacency = np.stack([ANATOMICAL_ADJACENCY] * num_train, axis=0)
    val_adjacency = np.stack([ANATOMICAL_ADJACENCY] * num_val, axis=0)

    # Compile model
    model.compile(learning_rate=args.learning_rate, weight_decay=args.weight_decay)

    # Create callbacks
    callbacks = create_callbacks(args, tracker)

    # Train
    logger.info("\nTraining for %s epochs...", args.epochs)
    history = model.model.fit(
        [X_train, train_adjacency],
        train_labels,
        validation_data=([X_val, val_adjacency], val_labels),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=1,
    )

    return history


def evaluate_model(model, X_test, y_test, class_names=None):
    """Evaluate model on test set with clinical metrics."""
    logger.info("\nEvaluating model on test set...")

    num_test = len(X_test)
    test_adjacency = np.stack([ANATOMICAL_ADJACENCY] * num_test, axis=0)

    # Get predictions
    predictions = model.model.predict([X_test, test_adjacency], verbose=1)

    # Extract pathology predictions
    y_prob = predictions["pathology_output"]
    y_pred = np.argmax(y_prob, axis=1)

    if y_test.ndim > 1:
        y_true = np.argmax(y_test, axis=1)
    else:
        y_true = y_test

    if class_names is None:
        class_names = PATHOLOGY_CLASSES

    # Compute clinical metrics
    evaluator = ClinicalMetricsEvaluator()
    metrics = evaluator.evaluate(y_true, y_pred, y_prob, class_names)

    logger.info("\n%s", '=' * 60)
    logger.info("CLINICAL METRICS REPORT")
    logger.info("%s", '=' * 60)
    logger.info("  Accuracy:    %s", metrics['accuracy'])
    logger.info("  Precision:   %s", metrics['precision'])
    logger.info("  Recall:      %s", metrics['recall'])
    logger.info("  F1 Score:    %s", metrics['f1'])
    if "auc_roc" in metrics:
        logger.info("  AUC-ROC:     %s", metrics['auc_roc'])
    if "auc_pr" in metrics:
        logger.info("  AUC-PR:      %s", metrics['auc_pr'])

    logger.info("\nPer-class metrics:")
    for name, class_metrics in metrics.get("per_class", {}).items():
        logger.info(
            "  %-25s | Sens: %.3f | Spec: %.3f | Precision: %.3f | F1: %.3f",
            name,
            class_metrics['sensitivity'],
            class_metrics['specificity'],
            class_metrics['precision'],
            class_metrics['f1'],
        )

    return metrics


def train_cross_validated(args, X, y, _metadata):
    """Train with cross-validation."""
    logger.info("\n%s", '=' * 60)
    logger.info("CROSS-VALIDATION TRAINING (%s folds)", args.n_folds)
    logger.info("%s", '=' * 60)

    cv = MedicalCrossValidator(n_splits=args.n_folds, stratified=True)

    fold_metrics = []

    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y)):
        logger.info("\n%s", '=' * 60)
        logger.info("FOLD %s/%s", fold + 1, args.n_folds)
        logger.info("%s", '=' * 60)

        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        # Build fresh model for each fold
        model = build_model(args)

        tracker = TrainingProgressTracker(
            log_dir=str(Path(args.log_dir) / f"fold_{fold + 1}"),
        )

        _history = train_single_fold(
            model, X_train, y_train, X_val, y_val, args, tracker,
        )

        # Evaluate fold
        fold_metrics.append(
            {
                "fold": fold + 1,
                "best_val_accuracy": tracker.best_val_accuracy,
                "best_epoch": tracker.best_epoch,
            },
        )

        # Save fold model
        fold_path = Path(args.output_dir) / f"graphmdl_fold_{fold + 1}"
        fold_path.mkdir(parents=True, exist_ok=True)
        model.save(str(fold_path / "model.keras"))

    # Average metrics
    avg_accuracy = np.mean([m["best_val_accuracy"] for m in fold_metrics])
    logger.info("\n%s", '=' * 60)
    logger.info("CROSS-VALIDATION RESULTS")
    logger.info("%s", '=' * 60)
    logger.info("  Average Val Accuracy: %s", avg_accuracy)
    for m in fold_metrics:
        logger.info(
            "  Fold %s: %s (epoch %s)",
            m['fold'],
            m['best_val_accuracy'],
            m['best_epoch'],
        )

    return fold_metrics


def main():
    """Main training pipeline."""
    args = parse_args()

    logger.info("\n%s", '=' * 80)
    logger.info("GraphMDL TRAINING PIPELINE")
    logger.info("%s", '=' * 80)
    logger.info("Date: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logger.info("Arguments: %s", json.dumps(vars(args), indent=2))

    # Setup GPU
    setup_gpu(args.gpu, args.mixed_precision)

    # Create output directories
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    Path(args.log_dir).mkdir(parents=True, exist_ok=True)

    # Check data directory
    if not Path(args.data_dir).exists():
        logger.error("Data directory not found: %s", args.data_dir)
        logger.error("Please provide a valid dataset directory with --data_dir")
        logger.error("Expected structure: data_dir/class_name_1/image1.jpg, ...")
        sys.exit(1)

    # Build data
    X_train, y_train, X_val, y_val, test_data, metadata = build_data_generators(args)

    # Initialize model registry
    registry = ModelRegistry(base_dir=args.output_dir)
    tracker = TrainingProgressTracker(log_dir=args.log_dir)

    if args.cross_validation:
        # Cross-validation training
        X_all = np.concatenate([X_train, X_val], axis=0)
        y_all = np.concatenate([y_train, y_val], axis=0)
        _fold_metrics = train_cross_validated(args, X_all, y_all, metadata)

        # Build final model on all data
        logger.info("\nBuilding final model on all training data...")
        model = build_model(args)
        train_single_fold(model, X_all, y_all, X_val, y_val, args, tracker)
    else:
        # Single training run
        model = build_model(args)
        _history = train_single_fold(
            model, X_train, y_train, X_val, y_val, args, tracker,
        )

    # Evaluate on test set if available
    test_metrics = None
    if test_data is not None:
        X_test, y_test, _ = test_data
        if X_test is not None and len(X_test) > 0:
            test_metrics = evaluate_model(model, X_test, y_test)

    # Save model
    logger.info("\nSaving model...")
    save_path = Path(args.output_dir) / "graphmdl_latest.keras"
    model.save(
        str(save_path),
        metadata={
            "version": registry.get_next_version("graphmdl"),
            "training_date": datetime.now().isoformat(),
            "dataset_size": len(X_train) + len(X_val),
            "final_metrics": {
                "val_accuracy": float(tracker.best_val_accuracy),
                "best_epoch": tracker.best_epoch,
                **(test_metrics or {}),
            },
        },
    )

    # Register in model registry
    model_metadata = ModelMetadata(
        model_name=args.model_name,
        model_type="graphmdl",
        training_date=datetime.now().isoformat(),
        architecture={
            "graph_hidden_dim": args.graph_hidden_dim,
            "num_gcn_layers": args.num_gcn_layers,
            "num_gat_layers": args.num_gat_layers,
            "num_attention_heads": args.num_attention_heads,
            "use_transfer_learning": args.use_transfer_learning
            and not args.no_transfer_learning,
            "dropout_rate": args.dropout_rate,
        },
        hyperparameters={
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "batch_size": args.batch_size,
            "weight_decay": args.weight_decay,
        },
        metrics={
            "val_accuracy": float(tracker.best_val_accuracy),
            "best_epoch": tracker.best_epoch,
            **(test_metrics or {}),
        },
        dataset_info={
            "train_size": len(X_train),
            "val_size": len(X_val),
            "test_size": metadata.get("test_size", 0),
            "total_samples": metadata.get("total_samples", 0),
            "num_classes": metadata.get("num_classes", 0),
            "class_names": metadata.get("class_names", []),
        },
    )

    registry.register_model(
        model_type="graphmdl",
        model=model.model,
        metadata=model_metadata,
        training_history={
            "epoch_history": tracker.epoch_history,
            "best_val_accuracy": tracker.best_val_accuracy,
            "best_epoch": tracker.best_epoch,
        },
    )

    # Save training history
    if args.save_history:
        tracker.save_history(str(Path(args.log_dir) / "graphmdl_training_history.json"))

    # Print model comparison
    logger.info(registry.compare_models("graphmdl"))

    logger.info("\n%s", '=' * 80)
    logger.info("TRAINING COMPLETED SUCCESSFULLY")
    logger.info("%s", '=' * 80)
    logger.info("Model saved to: %s", save_path)
    logger.info(
        "Best validation accuracy: %s (epoch %s)",
        tracker.best_val_accuracy,
        tracker.best_epoch,
    )
    logger.info("Model registered in registry as: graphmdl/%s", model_metadata.version)

    return model, model_metadata


if __name__ == "__main__":
    main()
