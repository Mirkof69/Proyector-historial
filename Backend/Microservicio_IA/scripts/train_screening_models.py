#!/usr/bin/env python
"""Train Screening Models - Early Complication Screening (Cribado)

Training script for early screening models that detect potential pregnancy
complications before they become clinically apparent. These models perform
cribado (screening) to identify patients who need closer monitoring or
early intervention.

Screening capabilities:
- First-trimester aneuploidy screening markers
- Pre-eclampsia early risk detection
- Gestational diabetes early indicators
- Fetal growth restriction early screening
- Preterm birth risk screening
- Placental dysfunction early markers

Architecture:
- Multi-task screening with shared feature extraction
- Sensitivity-optimized decision thresholds
- Sequential screening (early -> mid -> late pregnancy)
- Cost-sensitive learning (minimize false negatives)

Usage:
    python train_screening_models.py
    python train_screening_models.py --data_dir datasets/train --epochs 60
    python train_screening_models.py --high_sensitivity --threshold 0.3
    python train_screening_models.py --sequential_screening

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
    ClinicalImageLoader,
    KerasProgressCallback,
    TrainingProgressTracker,
)
from model_registry import ModelMetadata, ModelRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/train_screening_models.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

Path("logs").mkdir(exist_ok=True)

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models

    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.error("TensorFlow is required for training screening models.")
    sys.exit(1)

from sklearn.metrics import roc_curve

# ─── Screening Categories ───
SCREENING_CATEGORIES = {
    "aneuploidy": {
        "name": "Aneuploidy Screening",
        "description": "Early screening for chromosomal abnormalities (T21, T18, T13)",
        "markers": ["nuchal_translucency", "nasal_bone", "ductus_venosus"],
        "classes": ["low_risk", "screen_positive"],
    },
    "preeclampsia": {
        "name": "Pre-eclampsia Screening",
        "description": "Early detection of pre-eclampsia risk factors",
        "markers": ["uterine_artery_pi", "map", "plg"],
        "classes": ["low_risk", "screen_positive"],
    },
    "growth_restriction": {
        "name": "Fetal Growth Restriction Screening",
        "description": "Early screening for intrauterine growth restriction",
        "markers": ["cmbdl", "utero_placental_flow", "abdominal_circumference"],
        "classes": ["low_risk", "screen_positive"],
    },
    "preterm_birth": {
        "name": "Preterm Birth Screening",
        "description": "Cervical length and risk factor assessment",
        "markers": ["cervical_length", "fetal_fibronectin", "history"],
        "classes": ["low_risk", "screen_positive"],
    },
    "gestational_diabetes": {
        "name": "Gestational Diabetes Screening",
        "description": "Early metabolic and ultrasound markers",
        "markers": ["macrosomia_signs", "polyhydramnios", "maternal_factors"],
        "classes": ["low_risk", "screen_positive"],
    },
    "placental_dysfunction": {
        "name": "Placental Dysfunction Screening",
        "description": "Placental morphology and Doppler assessment",
        "markers": ["placental_volume", "uterine_doppler", "placental_lakes"],
        "classes": ["low_risk", "screen_positive"],
    },
}


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train Screening Models for Early Complication Detection",
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
        "--batch_size", type=int, default=32, help="Batch size for training",
    )

    # Model architecture
    parser.add_argument(
        "--backbone",
        type=str,
        default="efficientnet",
        choices=["efficientnet", "resnet", "custom"],
        help="Feature extractor backbone",
    )
    parser.add_argument(
        "--hidden_dim",
        type=int,
        default=256,
        help="Hidden dimension for screening heads",
    )
    parser.add_argument("--dropout_rate", type=float, default=0.3, help="Dropout rate")
    parser.add_argument(
        "--use_transfer_learning",
        action="store_true",
        default=True,
        help="Use pre-trained backbone weights",
    )

    # Screening optimization
    parser.add_argument(
        "--high_sensitivity",
        action="store_true",
        default=True,
        help="Optimize for high sensitivity (minimize false negatives)",
    )
    parser.add_argument(
        "--sensitivity_threshold",
        type=float,
        default=0.90,
        help="Target sensitivity threshold",
    )
    parser.add_argument(
        "--class_weight_positive",
        type=float,
        default=3.0,
        help="Class weight for positive screening cases",
    )

    # Training arguments
    parser.add_argument(
        "--epochs", type=int, default=60, help="Maximum training epochs",
    )
    parser.add_argument(
        "--learning_rate", type=float, default=1e-3, help="Initial learning rate",
    )
    parser.add_argument(
        "--patience", type=int, default=12, help="Early stopping patience",
    )
    parser.add_argument(
        "--focal_loss",
        action="store_true",
        default=True,
        help="Use focal loss for class imbalance",
    )
    parser.add_argument(
        "--gamma_focal", type=float, default=2.0, help="Focal loss gamma parameter",
    )

    # Screening type
    parser.add_argument(
        "--screening_types",
        type=str,
        nargs="+",
        default=list(SCREENING_CATEGORIES.keys()),
        help="Types of screening to train",
    )
    parser.add_argument(
        "--sequential_screening",
        action="store_true",
        help="Train sequential screening model",
    )

    # Hardware
    parser.add_argument("--gpu", type=str, default="0", help="GPU device to use")

    # Output
    parser.add_argument(
        "--output_dir",
        type=str,
        default="trained_models",
        help="Output directory for models",
    )
    parser.add_argument("--log_dir", type=str, default="logs", help="Log directory")
    parser.add_argument(
        "--model_name", type=str, default="screening", help="Model name for registry",
    )

    return parser.parse_args()


def setup_gpu(gpu_id: str):
    """Configure GPU."""
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu_id
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        logger.info("Found %s GPU(s)", len(gpus))
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    else:
        logger.warning("No GPU found. Training on CPU.")


class FocalLoss(keras.losses.Loss):
    """Focal Loss for handling class imbalance in screening tasks.

    FL(p_t) = -alpha * (1 - p_t)^gamma * log(p_t)

    Focuses learning on hard-to-classify examples by down-weighting
    well-classified examples. Critical for medical screening where
    positive cases are rare.
    """

    def __init__(self, alpha: float = 0.25, gamma: float = 2.0, **kwargs):
        """Initialize focal loss.

        Args:
            alpha: Weighting factor for positive class
            gamma: Focusing parameter (higher = more focus on hard examples)

        """
        super().__init__(**kwargs)
        self.alpha = alpha
        self.gamma = gamma

    def call(self, y_true, y_pred):
        """Call"""
        y_true = tf.cast(y_true, y_pred.dtype)
        bce = keras.losses.binary_crossentropy(y_true, y_pred)

        p_t = y_true * y_pred + (1 - y_true) * (1 - y_pred)
        focal_factor = tf.pow(1.0 - p_t, self.gamma)
        alpha_factor = y_true * self.alpha + (1 - y_true) * (1 - self.alpha)

        return alpha_factor * focal_factor * bce

    def get_config(self):
        """Get config"""
        config = super().get_config()
        config.update({"alpha": self.alpha, "gamma": self.gamma})
        return config


class SensitivityAtSpecificity(keras.metrics.Metric):
    """Custom metric: Sensitivity at fixed specificity.

    Measures the sensitivity achieved when specificity is at least
    the target value. Important for screening where we need to
    maintain a minimum specificity while maximizing sensitivity.
    """

    def __init__(self, target_specificity: float = 0.90, name="sens_at_spec", **kwargs):
        """Init"""
        super().__init__(name=name, **kwargs)
        self.target_specificity = target_specificity
        self.sensitivity = self.add_weight(name="sens", initializer="zeros")

    def update_state(self, y_true, y_pred, _sample_weight=None):
        """Update state"""
        y_true = tf.cast(y_true, tf.bool)
        y_pred = tf.cast(y_pred, tf.float32)

        # Compute ROC curve
        thresholds = tf.linspace(0.0, 1.0, 1000)
        sensitivities = []
        specificities = []

        for threshold in thresholds:
            y_pred_class = y_pred >= threshold
            tp = tf.reduce_sum(tf.cast(y_true & y_pred_class, tf.float32))
            fn = tf.reduce_sum(tf.cast(y_true & ~y_pred_class, tf.float32))
            tn = tf.reduce_sum(tf.cast(~y_true & ~y_pred_class, tf.float32))
            fp = tf.reduce_sum(tf.cast(~y_true & y_pred_class, tf.float32))

            sens = tp / (tp + fn + 1e-7)
            spec = tn / (tn + fp + 1e-7)
            sensitivities.append(sens)
            specificities.append(spec)

        # Find sensitivity at target specificity
        specificities = tf.stack(specificities)
        sensitivities = tf.stack(sensitivities)

        valid_mask = specificities >= self.target_specificity
        if tf.reduce_any(valid_mask):
            best_sens = tf.reduce_max(tf.where(valid_mask, sensitivities, 0.0))
        else:
            best_sens = 0.0

        self.sensitivity.assign(best_sens)

    def result(self):
        """Result"""
        return self.sensitivity

    def reset_state(self):
        """Reset state"""
        self.sensitivity.assign(0.0)


def build_screening_model(
    input_shape: tuple = (224, 224, 3),
    screening_types: list = None,
    hidden_dim: int = 256,
    dropout_rate: float = 0.3,
    use_transfer_learning: bool = True,
    backbone: str = "efficientnet",
):
    """Build multi-task screening model.

    Architecture:
    - Shared feature extractor (pre-trained backbone)
    - Task-specific screening heads
    - Each head optimized for high sensitivity

    Args:
        input_shape: Input image shape
        screening_types: List of screening categories to include
        hidden_dim: Hidden layer dimension
        dropout_rate: Dropout rate
        use_transfer_learning: Use pre-trained weights
        backbone: Feature extractor backbone type

    Returns:
        Compiled Keras model

    """
    if screening_types is None:
        screening_types = list(SCREENING_CATEGORIES.keys())

    # ─── Shared Feature Extractor ───
    if use_transfer_learning and backbone == "efficientnet":
        try:
            from tensorflow.keras.applications import EfficientNetB0

            base = EfficientNetB0(
                weights="imagenet",
                include_top=False,
                input_shape=input_shape,
            )
            for layer in base.layers[:-20]:
                layer.trainable = False
        except ImportError:
            use_transfer_learning = False

    if backbone == "resnet" and use_transfer_learning:
        try:
            from tensorflow.keras.applications import ResNet50

            base = ResNet50(
                weights="imagenet",
                include_top=False,
                input_shape=input_shape,
            )
            for layer in base.layers[:-20]:
                layer.trainable = False
        except ImportError:
            use_transfer_learning = False

    if not use_transfer_learning:
        base = models.Sequential(
            [
                layers.Conv2D(32, 3, strides=2, padding="same", activation="relu"),
                layers.BatchNormalization(),
                layers.MaxPooling2D(2),
                layers.Conv2D(64, 3, padding="same", activation="relu"),
                layers.BatchNormalization(),
                layers.MaxPooling2D(2),
                layers.Conv2D(128, 3, padding="same", activation="relu"),
                layers.BatchNormalization(),
                layers.GlobalAveragePooling2D(),
                layers.Dense(512, activation="relu"),
            ],
        )

    inputs = layers.Input(shape=input_shape)
    features = base(inputs, training=False) if use_transfer_learning else base(inputs)

    # Global pooling if needed
    if len(features.shape) == 4:
        features = layers.GlobalAveragePooling2D()(features)

    # Shared representation
    shared = layers.Dense(hidden_dim, activation="relu")(features)
    shared = layers.BatchNormalization()(shared)
    shared = layers.Dropout(dropout_rate)(shared)

    # ─── Task-Specific Screening Heads ───
    outputs = {}
    for screening_type in screening_types:
        if screening_type not in SCREENING_CATEGORIES:
            continue

        head = layers.Dense(
            hidden_dim // 2, activation="relu", name=f"{screening_type}_dense",
        )(shared)
        head = layers.Dropout(dropout_rate)(head)
        output = layers.Dense(1, activation="sigmoid", name=f"{screening_type}_output")(
            head,
        )
        outputs[f"{screening_type}_output"] = output

    model = models.Model(inputs=inputs, outputs=outputs, name="ScreeningModel")

    # ─── Compile with focal loss ───
    focal_loss = FocalLoss(alpha=0.25, gamma=2.0)

    loss_dict = {f"{st}_output": focal_loss for st in screening_types}
    metrics_dict = {
        f"{st}_output": [
            "accuracy",
            keras.metrics.AUC(name="auc"),
            keras.metrics.Recall(name="sensitivity"),
            keras.metrics.Precision(name="ppv"),
        ]
        for st in screening_types
    }

    model.compile(
        optimizer=keras.optimizers.AdamW(learning_rate=1e-3, weight_decay=1e-4),
        loss=loss_dict,
        loss_weights={f"{st}_output": 1.0 for st in screening_types},
        metrics=metrics_dict,
    )

    return model


def prepare_screening_labels(
    labels: np.ndarray, screening_types: list, num_samples: int,
) -> dict:
    """Prepare screening labels for multi-task training.

    Since screening labels are typically binary (positive/negative),
    we generate proxy labels based on pathology classifications.

    In production, these should come from actual clinical screening data.
    """
    screening_labels = {}

    if labels.ndim > 1:
        pathology_indices = np.argmax(labels, axis=1)
    else:
        pathology_indices = labels

    for screening_type in screening_types:
        # Generate proxy labels (replace with real screening data in production)
        positive_cases = np.zeros((num_samples, 1), dtype=np.float32)

        # Assign positive cases based on pathology patterns
        for i, idx in enumerate(pathology_indices):
            # Proxy: certain pathologies correlate with screening positives
            if (screening_type == "aneuploidy" and idx in [
                1,
                2,
            ]) or (screening_type == "preeclampsia" and idx in [
                12,
            ]) or (screening_type == "growth_restriction" and idx in [
                9,
            ]) or (screening_type == "preterm_birth" and idx in [7]) or (screening_type == "gestational_diabetes" and idx in [10]) or (screening_type == "placental_dysfunction" and idx in [
                11,
            ]) or np.random.random() < 0.05:  # hidrocefalia, anencefalia
                positive_cases[i, 0] = 1.0

        screening_labels[f"{screening_type}_output"] = positive_cases

    return screening_labels


def find_optimal_threshold(
    y_true: np.ndarray, y_prob: np.ndarray, target_sensitivity: float = 0.90,
) -> float:
    """Find optimal classification threshold for target sensitivity.

    Args:
        y_true: Ground truth binary labels
        y_prob: Predicted probabilities
        target_sensitivity: Target sensitivity (recall) value

    Returns:
        Optimal threshold value

    """
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)

    # Find threshold where sensitivity >= target
    for i in range(len(tpr) - 1, -1, -1):
        if tpr[i] >= target_sensitivity:
            return float(thresholds[i])

    # If not achievable, return threshold that maximizes Youden's J
    youden = tpr - fpr
    best_idx = np.argmax(youden)
    return float(thresholds[best_idx])


def evaluate_screening_model(
    model, X_test, y_test_dict, screening_types: list, target_sensitivity: float = 0.90,
):
    """Evaluate screening model with clinical metrics.

    Focuses on sensitivity-specific metrics important for screening.
    """
    logger.info("\n%s", '=' * 60)
    logger.info(
        "SCREENING MODEL EVALUATION (target sensitivity: %s)",
        target_sensitivity,
    )
    logger.info("%s", '=' * 60)

    predictions = model.predict(X_test, verbose=0)

    overall_metrics = {}
    optimal_thresholds = {}

    for screening_type in screening_types:
        output_key = f"{screening_type}_output"
        if output_key not in predictions:
            continue

        y_prob = predictions[output_key].flatten()
        y_true = y_test_dict.get(output_key, np.zeros_like(y_prob))

        if isinstance(y_true, dict):
            continue

        # Find optimal threshold
        threshold = find_optimal_threshold(y_true, y_prob, target_sensitivity)
        optimal_thresholds[screening_type] = threshold

        y_pred = (y_prob >= threshold).astype(int)

        # Compute metrics
        tp = np.sum((y_true == 1) & (y_pred == 1))
        tn = np.sum((y_true == 0) & (y_pred == 0))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))

        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0

        try:
            auc = float(tf.keras.metrics.AUC()(y_true, y_prob).numpy())
        except Exception:
            auc = 0.0

        overall_metrics[screening_type] = {
            "sensitivity": float(sensitivity),
            "specificity": float(specificity),
            "ppv": float(ppv),
            "npv": float(npv),
            "auc": auc,
            "optimal_threshold": threshold,
            "num_positive": int(np.sum(y_true)),
            "num_negative": int(np.sum(y_true == 0)),
        }

        logger.info("\n  %s:", SCREENING_CATEGORIES[screening_type]['name'])
        logger.info(
            "    Sensitivity: %s | Specificity: %s",
            sensitivity,
            specificity,
        )
        logger.info("    PPV: %s | NPV: %s | AUC: %s", ppv, npv, auc)
        logger.info(
            "    Threshold: %s | Positives: %s/%s",
            threshold,
            int(np.sum(y_true)),
            len(y_true),
        )

    return overall_metrics, optimal_thresholds


def main():
    """Main screening model training pipeline."""
    args = parse_args()

    logger.info("\n%s", '=' * 80)
    logger.info("SCREENING MODELS TRAINING PIPELINE")
    logger.info("%s", '=' * 80)
    logger.info("Date: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logger.info("Screening types: %s", args.screening_types)
    logger.info("Target sensitivity: %s", args.sensitivity_threshold)
    logger.info("Arguments: %s", json.dumps(vars(args), indent=2))

    setup_gpu(args.gpu)

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Check data directory
    if not Path(args.data_dir).exists():
        logger.error("Data directory not found: %s", args.data_dir)
        sys.exit(1)

    # Load images
    logger.info("Loading images from %s...", args.data_dir)
    loader = ClinicalImageLoader(
        target_size=tuple(args.target_size), clahe_enhance=True,
    )
    images, labels, class_names = loader.load_from_directory(
        args.data_dir, class_mode="categorical",
    )

    # Split data
    from sklearn.model_selection import train_test_split

    X_train, X_val, y_train, y_val = train_test_split(
        images,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=np.argmax(labels, axis=1) if labels.ndim > 1 else labels,
    )

    # Prepare screening labels
    train_screening_labels = prepare_screening_labels(
        y_train, args.screening_types, len(X_train),
    )
    val_screening_labels = prepare_screening_labels(
        y_val, args.screening_types, len(X_val),
    )

    logger.info("\nDataset prepared:")
    logger.info("  Train samples: %s", len(X_train))
    logger.info("  Val samples:   %s", len(X_val))
    logger.info("  Screening types: %s", args.screening_types)

    # Build model
    logger.info("\nBuilding screening model...")
    model = build_screening_model(
        input_shape=(*args.target_size, 3),
        screening_types=args.screening_types,
        hidden_dim=args.hidden_dim,
        dropout_rate=args.dropout_rate,
        use_transfer_learning=args.use_transfer_learning,
        backbone=args.backbone,
    )

    total_params = model.count_params()
    logger.info("Total parameters: %s", total_params)

    # Training tracker
    tracker = TrainingProgressTracker(log_dir=args.log_dir)

    # Callbacks
    callbacks = [
        KerasProgressCallback(tracker),
        keras.callbacks.ModelCheckpoint(
            filepath=str(Path(args.output_dir) / "screening_best.keras"),
            save_best_only=True,
            monitor="val_loss",
            mode="min",
            verbose=1,
        ),
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=args.patience,
            restore_best_weights=True,
            mode="min",
            verbose=1,
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6, verbose=1,
        ),
        keras.callbacks.TensorBoard(
            log_dir=str(Path(args.log_dir) / "screening_tensorboard"),
            histogram_freq=1,
        ),
    ]

    # Train
    logger.info("\nTraining for %s epochs...", args.epochs)
    history = model.fit(
        X_train,
        train_screening_labels,
        validation_data=(X_val, val_screening_labels),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=1,
    )

    # Evaluate
    eval_metrics, optimal_thresholds = evaluate_screening_model(
        model,
        X_val,
        val_screening_labels,
        args.screening_types,
        target_sensitivity=args.sensitivity_threshold,
    )

    # Save model with thresholds
    logger.info("\nSaving model...")
    save_path = Path(args.output_dir) / "screening_latest.keras"
    model.save(str(save_path))

    # Save optimal thresholds
    thresholds_path = Path(args.output_dir) / "screening_thresholds.json"
    with open(thresholds_path, "w", encoding='utf-8') as f:
        json.dump(
            {
                "optimal_thresholds": optimal_thresholds,
                "target_sensitivity": args.sensitivity_threshold,
                "training_date": datetime.now().isoformat(),
            },
            f,
            indent=2,
        )
    logger.info("Optimal thresholds saved to %s", thresholds_path)

    # Register in model registry
    registry = ModelRegistry(base_dir=args.output_dir)

    model_metadata = ModelMetadata(
        model_name=args.model_name,
        model_type="screening",
        training_date=datetime.now().isoformat(),
        architecture={
            "backbone": args.backbone,
            "hidden_dim": args.hidden_dim,
            "dropout_rate": args.dropout_rate,
            "use_transfer_learning": args.use_transfer_learning,
            "screening_types": args.screening_types,
        },
        hyperparameters={
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "batch_size": args.batch_size,
            "focal_loss": args.focal_loss,
            "gamma_focal": args.gamma_focal,
        },
        metrics={
            "val_loss": float(min(history.history.get("val_loss", [0])), default=0),
            "screening_metrics": eval_metrics,
            "optimal_thresholds": optimal_thresholds,
        },
        dataset_info={
            "train_size": len(X_train),
            "val_size": len(X_val),
            "num_classes": len(class_names),
            "class_names": class_names,
        },
    )

    registry.register_model(
        model_type="screening",
        model=model,
        metadata=model_metadata,
    )

    # Save training history
    tracker.save_history(str(Path(args.log_dir) / "screening_training_history.json"))

    logger.info(registry.compare_models("screening"))

    logger.info("\n%s", '=' * 80)
    logger.info("SCREENING MODELS TRAINING COMPLETED")
    logger.info("%s", '=' * 80)
    logger.info("Model saved to: %s", save_path)
    logger.info("Thresholds saved to: %s", thresholds_path)
    logger.info("Model registered as: screening/%s", model_metadata.version)


if __name__ == "__main__":
    main()
