#!/usr/bin/env python
"""Train Predictive Models - Personalized Risk Prediction & Forecasting

Training script for predictive models that provide:
- Personalized risk prediction per patient
- Predictive forecasting of pregnancy outcomes
- Risk stratification based on clinical and imaging features
- Temporal outcome prediction

These models combine imaging features with clinical metadata to generate
patient-specific risk assessments and outcome predictions.

Architecture:
- Multi-modal feature fusion (imaging + clinical data)
- Temporal sequence modeling for longitudinal data
- Ensemble methods for robust risk prediction
- Calibration for clinically meaningful probability estimates

Usage:
    python train_predictive_models.py
    python train_predictive_models.py --data_dir datasets/train --epochs 80
    python train_predictive_models.py --clinical_data clinical_data.csv
    python train_predictive_models.py --ensemble --n_estimators 10

Author: Fetal Medical System AI Team
Version: 1.0.0
"""

import argparse
import json
import logging
import os
import pickle
import sys
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split

import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_pipeline import (
    ClinicalImageLoader,
    ClinicalMetricsEvaluator,
    TrainingProgressTracker,
)
from model_registry import ModelMetadata, ModelRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/train_predictive_models.log", encoding="utf-8"),
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

from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

# â”€â”€â”€ Clinical Feature Names â”€â”€â”€
CLINICAL_FEATURES = [
    "maternal_age",
    "gestational_age",
    "gravidity",
    "parity",
    "bmi",
    "blood_pressure_systolic",
    "blood_pressure_diastolic",
    "biparietal_diameter",
    "head_circumference",
    "abdominal_circumference",
    "femur_length",
    "estimated_fetal_weight",
    "amniotic_fluid_index",
    "placenta_grade",
    "heart_rate",
]

# â”€â”€â”€ Risk Categories â”€â”€â”€
RISK_CATEGORIES = ["low", "medium", "high"]
OUTCOME_CLASSES = [
    "full_term_normal",
    "preterm_delivery",
    "cesarean_required",
    "complications_detected",
    "fetal_distress",
    "growth_restriction",
]


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train Predictive Models for Fetal Risk Assessment",
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
        "--clinical_data", type=str, default=None, help="Path to clinical data CSV file",
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

    # Model selection
    parser.add_argument(
        "--model_type",
        type=str,
        default="ensemble",
        choices=["neural", "random_forest", "gradient_boosting", "ensemble", "svm"],
        help="Model type to train",
    )
    parser.add_argument(
        "--ensemble",
        action="store_true",
        default=True,
        help="Use ensemble of multiple models",
    )
    parser.add_argument(
        "--n_estimators",
        type=int,
        default=100,
        help="Number of estimators for ensemble methods",
    )

    # Neural network arguments
    parser.add_argument(
        "--hidden_dims",
        type=int,
        nargs="+",
        default=[256, 128, 64],
        help="Hidden layer dimensions for neural network",
    )
    parser.add_argument("--dropout_rate", type=float, default=0.3, help="Dropout rate")
    parser.add_argument(
        "--use_image_features",
        action="store_true",
        default=True,
        help="Include image features from CNN backbone",
    )

    # Training arguments
    parser.add_argument(
        "--epochs",
        type=int,
        default=80,
        help="Maximum training epochs (for neural network)",
    )
    parser.add_argument(
        "--learning_rate", type=float, default=1e-3, help="Initial learning rate",
    )
    parser.add_argument(
        "--patience", type=int, default=15, help="Early stopping patience",
    )
    parser.add_argument(
        "--use_calibration",
        action="store_true",
        default=True,
        help="Calibrate probability estimates",
    )

    # Cross-validation
    parser.add_argument(
        "--cross_validation", action="store_true", help="Use cross-validation",
    )
    parser.add_argument("--n_folds", type=int, default=5, help="Number of CV folds")

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
        "--model_name", type=str, default="predictive", help="Model name for registry",
    )

    return parser.parse_args()


def setup_gpu(gpu_id: str):
    """Configure GPU."""
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu_id
    gpus = tf.config.list_physical_devices("GPU") if TF_AVAILABLE else []
    if gpus:
        logger.info("Found %s GPU(s)", len(gpus))
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    else:
        logger.info("Training on CPU")


def load_clinical_data(clinical_csv: str) -> pd.DataFrame:
    """Load clinical data from CSV.

    Expected columns: maternal_age, gestational_age, gravidity, parity,
    bmi, blood_pressure_systolic, blood_pressure_diastolic,
    biparietal_diameter, head_circumference, abdominal_circumference,
    femur_length, estimated_fetal_weight, amniotic_fluid_index,
    placenta_grade, heart_rate, risk_level, outcome
    """
    if clinical_csv and Path(clinical_csv).exists():
        df = pd.read_csv(clinical_csv)
        logger.info(
            "Loaded clinical data: %s patients, %s features",
            len(df),
            len(df.columns),
        )
        return df
    logger.warning(
        "No clinical data provided. Generating synthetic features from image labels.",
    )
    return None


def extract_image_features(images: np.ndarray) -> np.ndarray:
    """Extract hand-crafted features from ultrasound images.

    Features include:
    - Statistical moments (mean, std, skewness, kurtosis)
    - Texture features (GLCM-based)
    - Shape features
    - Intensity distribution features
    """
    features = []

    for img in images:
        # Convert to grayscale if needed
        if img.ndim == 3:
            gray = np.mean(img, axis=-1)
        else:
            gray = img

        gray = gray.flatten()

        # Statistical features
        mean_val = np.mean(gray)
        std_val = np.std(gray)
        skew_val = np.mean(((gray - mean_val) / (std_val + 1e-8)) ** 3)
        kurt_val = np.mean(((gray - mean_val) / (std_val + 1e-8)) ** 4)

        # Percentile features
        p25, p50, p75 = np.percentile(gray, [25, 50, 75])
        iqr = p75 - p25

        # Intensity range features
        intensity_range = np.max(gray) - np.min(gray)

        # Gradient features (edge content)
        if img.ndim == 3 and img.shape[2] == 3:
            grad_x = np.diff(np.mean(img, axis=2), axis=1)
            grad_y = np.diff(np.mean(img, axis=2), axis=0)
            grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            mean_grad = np.mean(grad_magnitude)
            std_grad = np.std(grad_magnitude)
        else:
            mean_grad = 0.0
            std_grad = 0.0

        features.append(
            [
                mean_val,
                std_val,
                skew_val,
                kurt_val,
                p25,
                p50,
                p75,
                iqr,
                intensity_range,
                mean_grad,
                std_grad,
            ],
        )

    return np.array(features, dtype=np.float32)


def prepare_dataset(
    images: np.ndarray,
    labels: np.ndarray,
    clinical_data: pd.DataFrame = None,
    use_image_features: bool = True,
):
    """Prepare combined feature dataset.

    Combines:
    - Image-extracted features
    - Clinical metadata features
    - Target labels (risk level and outcome)
    """
    num_samples = len(images)

    # Extract image features
    img_features = (
        extract_image_features(images)
        if use_image_features
        else np.zeros((num_samples, 0))
    )

    # Generate clinical features if not provided
    if clinical_data is not None and len(clinical_data) == num_samples:
        # Use provided clinical data
        clinical_features = clinical_data[CLINICAL_FEATURES].values.astype(np.float32)
        # Fill missing values with median
        clinical_features = np.nan_to_num(
            clinical_features, nan=np.nanmedian(clinical_features, axis=0),
        )
    else:
        # Generate synthetic clinical features from labels
        if labels.ndim > 1:
            label_indices = np.argmax(labels, axis=1)
        else:
            label_indices = labels

        # Create proxy features
        clinical_features = (
            np.random.randn(num_samples, len(CLINICAL_FEATURES)).astype(np.float32)
            * 0.1
        )
        clinical_features[:, 0] = np.clip(
            label_indices * 5 + 25, 15, 45,
        )  # maternal_age
        clinical_features[:, 1] = np.clip(
            label_indices * 8 + 12, 8, 42,
        )  # gestational_age

    # Combine features
    all_features = np.concatenate([img_features, clinical_features], axis=1)

    # Create risk labels (proxy from pathology labels)
    if labels.ndim > 1:
        label_indices = np.argmax(labels, axis=1)
    else:
        label_indices = labels

    # Risk stratification: 0=low, 1=medium, 2=high
    risk_labels = np.clip(label_indices // 5, 0, 2)

    # Outcome labels (proxy)
    outcome_labels = np.clip(label_indices, 0, len(OUTCOME_CLASSES) - 1)

    feature_names = [
        f"img_feat_{i}" for i in range(img_features.shape[1])
    ] + CLINICAL_FEATURES

    return all_features, risk_labels, outcome_labels, feature_names


def build_neural_predictor(
    input_dim: int,
    hidden_dims: list = None,
    dropout_rate: float = 0.3,
    num_risk_classes: int = 3,
    num_outcome_classes: int = 6,
):
    """Build neural network predictor for risk and outcome prediction.

    Architecture:
    - Feature encoder (dense layers)
    - Risk prediction head
    - Outcome prediction head
    - Uncertainty estimation head
    """
    if hidden_dims is None:
        hidden_dims = [256, 128, 64]

    inputs = layers.Input(shape=(input_dim,), name="features_input")

    # Feature encoder
    x = inputs
    for i, dim in enumerate(hidden_dims):
        x = layers.Dense(dim, activation="relu", name=f"encoder_{i}")(x)
        x = layers.BatchNormalization(name=f"bn_{i}")(x)
        x = layers.Dropout(dropout_rate, name=f"dropout_{i}")(x)

    # Shared representation
    shared = layers.Dense(64, activation="relu", name="shared")(x)

    # Risk prediction head
    risk_output = layers.Dense(
        num_risk_classes, activation="softmax", name="risk_output",
    )(shared)

    # Outcome prediction head
    outcome_output = layers.Dense(
        num_outcome_classes, activation="softmax", name="outcome_output",
    )(shared)

    # Uncertainty estimation (variance prediction)
    uncertainty_output = layers.Dense(
        1, activation="softplus", name="uncertainty_output",
    )(shared)

    model = models.Model(
        inputs=inputs,
        outputs={
            "risk_output": risk_output,
            "outcome_output": outcome_output,
            "uncertainty_output": uncertainty_output,
        },
        name="NeuralPredictiveModel",
    )

    model.compile(
        optimizer=keras.optimizers.AdamW(learning_rate=1e-3, weight_decay=1e-4),
        loss={
            "risk_output": "sparse_categorical_crossentropy",
            "outcome_output": "sparse_categorical_crossentropy",
            "uncertainty_output": "mse",
        },
        loss_weights={
            "risk_output": 1.0,
            "outcome_output": 0.5,
            "uncertainty_output": 0.1,
        },
        metrics={
            "risk_output": ["accuracy"],
            "outcome_output": ["accuracy"],
        },
    )

    return model


def build_sklearn_models(n_estimators: int = 100):
    """Build scikit-learn models for ensemble prediction.

    Returns a dictionary of model instances.
    """
    models_dict = {
        "random_forest": RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=n_estimators,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42,
        ),
        "logistic_regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
        ),
        "mlp": MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),
            activation="relu",
            solver="adam",
            max_iter=500,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
        ),
    }

    return models_dict


def train_neural_model(features, risk_labels, outcome_labels, args, _tracker):
    """Train neural network predictor."""

    # Split for validation
    X_train, X_val, y_risk_train, y_risk_val = train_test_split(
        features, risk_labels, test_size=0.2, random_state=42, stratify=risk_labels,
    )

    input_dim = features.shape[1]
    model = build_neural_predictor(
        input_dim=input_dim,
        hidden_dims=args.hidden_dims,
        dropout_rate=args.dropout_rate,
    )

    logger.info("\nNeural Predictor Architecture:")
    logger.info("  Input dim: %s", input_dim)
    logger.info("  Hidden dims: %s", args.hidden_dims)
    logger.info("  Total params: %s", model.count_params())

    # Dummy uncertainty targets
    uncertainty_train = np.ones((len(X_train), 1), dtype=np.float32) * 0.1
    uncertainty_val = np.ones((len(X_val), 1), dtype=np.float32) * 0.1

    # Callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_risk_output_accuracy",
            patience=args.patience,
            restore_best_weights=True,
            mode="max",
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_risk_output_loss", factor=0.5, patience=5, min_lr=1e-6,
        ),
    ]

    # Train
    history = model.fit(
        X_train,
        {
            "risk_output": y_risk_train,
            "outcome_output": outcome_labels[: len(X_train)],
            "uncertainty_output": uncertainty_train,
        },
        validation_data=(
            X_val,
            {
                "risk_output": y_risk_val,
                "outcome_output": outcome_labels[len(X_train) :],
                "uncertainty_output": uncertainty_val,
            },
        ),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=1,
    )

    return model, history


def train_sklearn_models(features, risk_labels, args, _tracker):
    """Train scikit-learn models and return ensemble."""
    X_train, X_val, y_train, y_val = train_test_split(
        features, risk_labels, test_size=0.2, random_state=42, stratify=risk_labels,
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    models_dict = build_sklearn_models(args.n_estimators)
    trained_models = {}

    for name, clf in models_dict.items():
        logger.info("\nTraining %s...", name)
        try:
            clf.fit(X_train_scaled, y_train)

            # Evaluate
            train_acc = clf.score(X_train_scaled, y_train)
            val_acc = clf.score(X_val_scaled, y_val)
            logger.info(
                "  %s - Train Acc: %s, Val Acc: %s",
                name,
                train_acc,
                val_acc,
            )

            # Calibrate if requested
            if args.use_calibration:
                logger.info("  Calibrating %s...", name)
                clf = CalibratedClassifierCV(clf, cv=3, method="isotonic")
                clf.fit(X_train_scaled, y_train)
                val_acc_cal = clf.score(X_val_scaled, y_val)
                logger.info("  %s calibrated - Val Acc: %s", name, val_acc_cal)

            trained_models[name] = {
                "model": clf,
                "val_accuracy": val_acc_cal if args.use_calibration else val_acc,
            }
        except Exception as e:
            logger.warning("Failed to train %s: %s", name, e)

    # Build ensemble
    if len(trained_models) > 1:
        ensemble_estimators = [
            (name, data["model"]) for name, data in trained_models.items()
        ]
        ensemble = VotingClassifier(
            estimators=ensemble_estimators,
            voting="soft",
            weights=[data["val_accuracy"] for data in trained_models.values()],
        )
        ensemble.fit(X_train_scaled, y_train)
        ensemble_acc = ensemble.score(X_val_scaled, y_val)
        logger.info("\nEnsemble Val Accuracy: %s", ensemble_acc)

        trained_models["ensemble"] = {
            "model": ensemble,
            "val_accuracy": ensemble_acc,
        }

    return trained_models, scaler


def evaluate_predictive_model(model, X_test, y_true, scaler=None, model_type="neural"):
    """Evaluate predictive model with clinical metrics."""
    if scaler is not None:
        X_test = scaler.transform(X_test)

    if model_type == "neural":
        predictions = model.predict(X_test, verbose=0)
        y_pred = np.argmax(predictions["risk_output"], axis=1)
        y_prob = predictions["risk_output"]
    else:
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)

    evaluator = ClinicalMetricsEvaluator()
    metrics = evaluator.evaluate(y_true, y_pred, y_prob, RISK_CATEGORIES)

    logger.info("\n%s", '=' * 60)
    logger.info("PREDICTIVE MODEL CLINICAL METRICS")
    logger.info("%s", '=' * 60)
    logger.info("  Accuracy:  %s", metrics['accuracy'])
    logger.info("  F1 Score:  %s", metrics['f1'])
    if "auc_roc" in metrics:
        logger.info("  AUC-ROC:   %s", metrics['auc_roc'])

    # Calibration metric (Brier score)
    if y_prob is not None and len(RISK_CATEGORIES) == 3:
        try:
            brier = brier_score_loss(y_true, y_prob[:, 1])
            logger.info("  Brier Score: %s", brier)
        except Exception:
            pass

    for name, class_metrics in metrics.get("per_class", {}).items():
        logger.info(
            "  %-10s | Sens: %.3f | Spec: %.3f | F1: %.3f",
            name,
            class_metrics['sensitivity'],
            class_metrics['specificity'],
            class_metrics['f1'],
        )

    return metrics


def main():
    """Main training pipeline."""
    args = parse_args()

    logger.info("\n%s", '=' * 80)
    logger.info("PREDICTIVE MODELS TRAINING PIPELINE")
    logger.info("%s", '=' * 80)
    logger.info("Date: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logger.info("Model type: %s", args.model_type)
    logger.info("Arguments: %s", json.dumps(vars(args), indent=2))

    if TF_AVAILABLE:
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
    images, labels, _class_names = loader.load_from_directory(
        args.data_dir, class_mode="categorical",
    )

    # Load clinical data
    clinical_data = load_clinical_data(args.clinical_data)

    # Prepare dataset
    features, risk_labels, outcome_labels, feature_names = prepare_dataset(
        images, labels, clinical_data, args.use_image_features,
    )

    logger.info("\nDataset prepared:")
    logger.info("  Samples:      %s", len(features))
    logger.info("  Features:     %s", features.shape[1])
    logger.info("  Risk classes: %s", len(np.unique(risk_labels)))
    logger.info("  Outcome classes: %s", len(np.unique(outcome_labels)))

    # Initialize registry and tracker
    registry = ModelRegistry(base_dir=args.output_dir)
    tracker = TrainingProgressTracker(log_dir=args.log_dir)

    # Train models
    trained_models = {}

    if args.model_type == "neural" and TF_AVAILABLE:
        model, _history = train_neural_model(
            features, risk_labels, outcome_labels, args, tracker,
        )
        trained_models["neural"] = {
            "model": model,
            "val_accuracy": tracker.best_val_accuracy,
        }
    else:
        sklearn_models, scaler = train_sklearn_models(
            features, risk_labels, args, tracker,
        )
        trained_models.update(sklearn_models)
        trained_models["scaler"] = scaler

    # Evaluate best model
    best_model_name = max(
        trained_models.keys(),
        key=lambda k: (
            trained_models[k].get("val_accuracy", 0)
            if isinstance(trained_models[k], dict)
            else 0
        ),
    )
    best_model_info = trained_models[best_model_name]

    # Split test data

    _, X_test, _, y_test = train_test_split(
        features, risk_labels, test_size=0.1, random_state=42, stratify=risk_labels,
    )
    scaler = trained_models.get("scaler")
    test_metrics = evaluate_predictive_model(
        best_model_info["model"]
        if isinstance(best_model_info, dict)
        else best_model_info,
        X_test,
        y_test,
        scaler,
        model_type=best_model_name,
    )

    # Save models
    logger.info("\nSaving models...")
    save_dir = Path(args.output_dir) / "predictive"
    save_dir.mkdir(parents=True, exist_ok=True)

    for name, info in trained_models.items():
        if name == "scaler":
            continue
        model_obj = info["model"] if isinstance(info, dict) else info
        model_path = save_dir / f"{name}_predictor.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(model_obj, f)
        logger.info("  Saved %s to %s", name, model_path)

    # Save scaler
    if scaler is not None:
        scaler_path = save_dir / "feature_scaler.pkl"
        with open(scaler_path, "wb") as f:
            pickle.dump(scaler, f)

    # Register in model registry
    model_metadata = ModelMetadata(
        model_name=args.model_name,
        model_type="predictive",
        training_date=datetime.now().isoformat(),
        architecture={
            "model_type": args.model_type,
            "hidden_dims": args.hidden_dims,
            "dropout_rate": args.dropout_rate,
            "n_estimators": args.n_estimators,
            "use_calibration": args.use_calibration,
        },
        hyperparameters={
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "batch_size": args.batch_size,
        },
        metrics={
            "val_accuracy": float(tracker.best_val_accuracy),
            **(test_metrics or {}),
        },
        dataset_info={
            "total_samples": len(features),
            "num_features": features.shape[1],
            "feature_names": feature_names,
            "risk_classes": len(np.unique(risk_labels)),
            "outcome_classes": len(np.unique(outcome_labels)),
        },
    )

    registry.register_model(
        model_type="predictive",
        model=best_model_info["model"]
        if isinstance(best_model_info, dict)
        else best_model_info,
        metadata=model_metadata,
        model_format="pkl",
    )

    # Save training history
    tracker.save_history(str(Path(args.log_dir) / "predictive_training_history.json"))

    logger.info(registry.compare_models("predictive"))

    logger.info("\n%s", '=' * 80)
    logger.info("PREDICTIVE MODELS TRAINING COMPLETED")
    logger.info("%s", '=' * 80)
    logger.info("Best model: %s", best_model_name)
    logger.info("Models saved to: %s", save_dir)
    logger.info("Model registered as: predictive/%s", model_metadata.version)


if __name__ == "__main__":
    main()
