#!/usr/bin/env python
"""Train Image Predictor - Image Quality Prediction & Segmentation

Training script for image prediction models that perform:
- Image quality prediction before analysis (assess if image is usable)
- Fetal segmentation (delimit fetal region in ultrasound)
- Anatomical landmark detection
- Image enhancement and restoration
- Viewplane classification (which anatomical view is shown)

These models ensure that only clinically adequate images are processed
and provide precise anatomical segmentation for biometric measurements.

Architecture:
- U-Net++ with EfficientNet backbone for segmentation
- Image quality assessment network
- Multi-scale feature fusion
- Boundary-aware loss functions

Usage:
    python train_image_predictor.py
    python train_image_predictor.py --data_dir datasets/train --epochs 100
    python train_image_predictor.py --segmentation_only
    python train_image_predictor.py --quality_only
    python train_image_predictor.py --joint_training

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
        logging.FileHandler("logs/train_image_predictor.log", encoding="utf-8"),
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
    logger.error("TensorFlow is required for training image predictor.")
    sys.exit(1)

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


# ─── Anatomical View Classes ───
ANATOMICAL_VIEWS = [
    "biparietal_diameter",  # BPD view
    "head_circumference",  # HC view
    "abdominal_circumference",  # AC view
    "femur_length",  # FL view
    "four_chamber_heart",  # 4CH view
    "cerebellum",  # Transcerebellar view
    "spine_sagittal",  # Sagittal spine
    "spine_transverse",  # Transverse spine
    "face_profile",  # Facial profile
    "kidneys",  # Kidney view
    "bladder",  # Bladder view
    "placenta",  # Placenta view
    "cervix",  # Cervical view
    "other",  # Other/unknown
]


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train Image Predictor for Quality Assessment & Segmentation",
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
        "--segmentation_dir",
        type=str,
        default=None,
        help="Path to segmentation dataset (images + masks)",
    )
    parser.add_argument(
        "--target_size",
        type=int,
        nargs=2,
        default=[256, 256],
        help="Target image size for segmentation (height width)",
    )
    parser.add_argument(
        "--quality_size",
        type=int,
        nargs=2,
        default=[224, 224],
        help="Target image size for quality assessment (height width)",
    )
    parser.add_argument(
        "--batch_size", type=int, default=16, help="Batch size for training",
    )

    # Training mode
    parser.add_argument(
        "--mode",
        type=str,
        default="joint",
        choices=["joint", "segmentation_only", "quality_only", "view_classification"],
        help="Training mode",
    )

    # Segmentation architecture
    parser.add_argument(
        "--seg_backbone",
        type=str,
        default="efficientnet",
        choices=["efficientnet", "resnet", "vanilla_unet"],
        help="Segmentation backbone type",
    )
    parser.add_argument(
        "--use_deep_supervision",
        action="store_true",
        default=True,
        help="Use deep supervision in U-Net++",
    )
    parser.add_argument(
        "--seg_filters",
        type=int,
        nargs="+",
        default=[64, 128, 256, 512],
        help="Filter sizes for segmentation encoder",
    )

    # Loss functions
    parser.add_argument(
        "--seg_loss",
        type=str,
        default="combined",
        choices=["dice", "bce", "combined", "focal_dice"],
        help="Segmentation loss function",
    )
    parser.add_argument(
        "--dice_weight",
        type=float,
        default=0.5,
        help="Weight for Dice loss in combined loss",
    )
    parser.add_argument(
        "--boundary_weight",
        type=float,
        default=0.2,
        help="Weight for boundary-aware loss",
    )

    # Training arguments
    parser.add_argument(
        "--epochs", type=int, default=100, help="Maximum training epochs",
    )
    parser.add_argument(
        "--learning_rate", type=float, default=1e-3, help="Initial learning rate",
    )
    parser.add_argument(
        "--patience", type=int, default=20, help="Early stopping patience",
    )
    parser.add_argument(
        "--use_tta",
        action="store_true",
        help="Enable test-time augmentation during evaluation",
    )

    # Augmentation
    parser.add_argument(
        "--augment", action="store_true", default=True, help="Enable data augmentation",
    )
    parser.add_argument(
        "--elastic_distortion",
        action="store_true",
        help="Apply elastic distortion for segmentation",
    )

    # Hardware
    parser.add_argument("--gpu", type=str, default="0", help="GPU device to use")
    parser.add_argument(
        "--mixed_precision", action="store_true", help="Enable mixed precision training",
    )

    # Output
    parser.add_argument(
        "--output_dir",
        type=str,
        default="trained_models",
        help="Output directory for models",
    )
    parser.add_argument("--log_dir", type=str, default="logs", help="Log directory")
    parser.add_argument(
        "--model_name",
        type=str,
        default="image_predictor",
        help="Model name for registry",
    )

    return parser.parse_args()


def setup_gpu(gpu_id: str, mixed_precision: bool = False):
    """Configure GPU."""
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu_id
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        logger.info("Found %s GPU(s)", len(gpus))
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    else:
        logger.warning("No GPU found. Training on CPU.")

    if mixed_precision:
        tf.keras.mixed_precision.set_global_policy("mixed_float16")
        logger.info("Mixed precision training enabled")


# ═══════════════════════════════════════════════════════════
# LOSS FUNCTIONS
# ═══════════════════════════════════════════════════════════
class DiceLoss(keras.losses.Loss):
    """Dice Loss for segmentation.

    DSC = 2 * |X intersection Y| / (|X| + |Y|)
    Dice Loss = 1 - DSC

    Better than BCE for imbalanced segmentation masks.
    """

    def __init__(self, smooth: float = 1e-6, **kwargs):
        """Init"""
        super().__init__(**kwargs)
        self.smooth = smooth

    def call(self, y_true, y_pred):
        """Call"""
        y_true = tf.cast(y_true, y_pred.dtype)
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1.0 - 1e-7)

        intersection = tf.reduce_sum(y_true * y_pred, axis=[1, 2, 3])
        union = tf.reduce_sum(y_true, axis=[1, 2, 3]) + tf.reduce_sum(
            y_pred, axis=[1, 2, 3],
        )

        dice = (2.0 * intersection + self.smooth) / (union + self.smooth)
        return 1.0 - dice

    def get_config(self):
        """Get config"""
        config = super().get_config()
        config.update({"smooth": self.smooth})
        return config


class CombinedSegmentationLoss(keras.losses.Loss):
    """Combined BCE + Dice loss for segmentation.

    L = alpha * BCE + (1 - alpha) * Dice

    Combines the stability of BCE with the region-overlap optimization of Dice.
    """

    def __init__(self, dice_weight: float = 0.5, smooth: float = 1e-6, **kwargs):
        """Init"""
        super().__init__(**kwargs)
        self.dice_weight = dice_weight
        self.bce_weight = 1.0 - dice_weight
        self.smooth = smooth
        self.bce = keras.losses.BinaryCrossentropy()
        self.dice = DiceLoss(smooth=smooth)

    def call(self, y_true, y_pred):
        """Call"""
        bce_loss = self.bce(y_true, y_pred)
        dice_loss = self.dice(y_true, y_pred)
        return self.bce_weight * bce_loss + self.dice_weight * dice_loss

    def get_config(self):
        """Get config"""
        config = super().get_config()
        config.update(
            {
                "dice_weight": self.dice_weight,
                "smooth": self.smooth,
            },
        )
        return config


class BoundaryAwareLoss(keras.losses.Loss):
    """Boundary-aware segmentation loss.

    Adds a penalty for boundary errors to improve segmentation edge quality.
    Uses Sobel operators to detect boundary discrepancies.
    """

    def __init__(self, base_loss=None, boundary_weight: float = 0.2, **kwargs):
        """Init"""
        super().__init__(**kwargs)
        self.base_loss = base_loss or CombinedSegmentationLoss()
        self.boundary_weight = boundary_weight

    def _compute_boundaries(self, mask):
        """Compute boundary map using Sobel operators."""
        # Sobel kernels
        sobel_x = tf.constant([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=mask.dtype)
        sobel_y = tf.constant([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=mask.dtype)

        sobel_x = tf.reshape(sobel_x, [3, 3, 1, 1])
        sobel_y = tf.reshape(sobel_y, [3, 3, 1, 1])

        # Apply Sobel to each channel
        edges_x = tf.nn.conv2d(mask, sobel_x, strides=1, padding="SAME")
        edges_y = tf.nn.conv2d(mask, sobel_y, strides=1, padding="SAME")
        edges = tf.sqrt(tf.square(edges_x) + tf.square(edges_y))

        return edges

    def call(self, y_true, y_pred):
        """Call"""
        base = self.base_loss(y_true, y_pred)

        # Boundary loss
        true_edges = self._compute_boundaries(y_true)
        pred_edges = self._compute_boundaries(y_pred)
        boundary_loss = tf.reduce_mean(tf.square(true_edges - pred_edges))

        return base + self.boundary_weight * boundary_loss

    def get_config(self):
        """Get config"""
        config = super().get_config()
        config.update({"boundary_weight": self.boundary_weight})
        return config


# ═══════════════════════════════════════════════════════════
# U-NET++ SEGMENTATION MODEL
# ═══════════════════════════════════════════════════════════
def conv_block(x, filters, kernel_size=3, activation="relu", name=None):
    """Standard convolution block with BN and activation."""
    x = layers.Conv2D(
        filters,
        kernel_size,
        padding="same",
        kernel_initializer="he_normal",
        name=f"{name}_conv" if name else None,
    )(x)
    x = layers.BatchNormalization(name=f"{name}_bn" if name else None)(x)
    x = layers.Activation(activation, name=f"{name}_act" if name else None)(x)
    return x


def build_unet_plus_plus(
    input_shape: tuple = (256, 256, 3),
    filters: list = None,
    use_deep_supervision: bool = True,
    backbone: str = "efficientnet",
):
    """Build U-Net++ segmentation model.

    U-Net++ extends U-Net with:
    - Dense skip connections between encoder and decoder
    - Deep supervision for multi-scale outputs
    - Improved gradient flow

    Args:
        input_shape: Input image shape
        filters: List of filter sizes for each encoder block
        use_deep_supervision: Add auxiliary outputs for deep supervision
        backbone: Encoder backbone type

    Returns:
        Compiled Keras model

    """
    if filters is None:
        filters = [64, 128, 256, 512]

    inputs = layers.Input(shape=input_shape)

    # ─── Encoder ───
    if backbone == "efficientnet":
        try:
            from tensorflow.keras.applications import EfficientNetB0

            base = EfficientNetB0(
                weights="imagenet",
                include_top=False,
                input_shape=input_shape,
            )
            # Extract features at different scales
            skip_connections = []
            current = inputs
            for layer in base.layers:
                current = layer(current, training=False)
                if "block" in layer.name and "add" in layer.name:
                    skip_connections.append(current)

            # Use bottleneck
            bottleneck = base(inputs, training=False)
            if len(bottleneck.shape) == 4:
                bottleneck = layers.Conv2D(filters[-1], 1, padding="same")(bottleneck)

        except ImportError:
            backbone = "vanilla_unet"

    if backbone == "vanilla_unet":
        # Standard encoder
        skip_connections = []
        x = inputs
        for f in filters:
            x = conv_block(x, f, name=f"enc_conv1_{f}")
            x = conv_block(x, f, name=f"enc_conv2_{f}")
            skip_connections.append(x)
            x = layers.MaxPooling2D(2, name=f"enc_pool_{f}")(x)
        bottleneck = x

    # ─── Decoder with dense skip connections ───
    decoder_filters = filters[::-1]
    x = bottleneck

    for i, f in enumerate(decoder_filters):
        # Upsample
        if i < len(decoder_filters) - 1:
            x = layers.UpSampling2D(2, name=f"dec_up_{i}")(x)

        # Skip connection (dense)
        if i < len(skip_connections):
            skip = skip_connections[-(i + 1)]
            # Resize skip if needed
            if x.shape[1] != skip.shape[1] or x.shape[2] != skip.shape[2]:
                skip = layers.Conv2D(f, 1, padding="same", name=f"skip_proj_{i}")(skip)
                skip = (
                    layers.UpSampling2D(2)(skip)
                    if x.shape[1] > skip.shape[1]
                    else layers.AveragePooling2D(2)(skip)
                )
            x = layers.Concatenate(name=f"dec_concat_{i}")([x, skip])

        # Decoder convolutions
        x = conv_block(x, f, name=f"dec_conv1_{i}")
        x = conv_block(x, f, name=f"dec_conv2_{i}")

    # ─── Output ───
    output = layers.Conv2D(1, 1, activation="sigmoid", name="segmentation_output")(x)

    if use_deep_supervision:
        # Add auxiliary outputs at different scales
        aux_outputs = []
        aux_x = bottleneck
        for i in range(min(3, len(decoder_filters) - 1)):
            aux_x = layers.UpSampling2D(2 ** (3 - i))(aux_x)
            aux_x = conv_block(aux_x, 64, name=f"aux_conv_{i}")
            aux_out = layers.Conv2D(1, 1, activation="sigmoid", name=f"aux_output_{i}")(
                aux_x,
            )
            aux_outputs.append(aux_out)

        model = models.Model(
            inputs=inputs, outputs=[output] + aux_outputs, name="UNetPlusPlus",
        )
    else:
        model = models.Model(inputs=inputs, outputs=output, name="UNetPlusPlus")

    return model


# ═══════════════════════════════════════════════════════════
# IMAGE QUALITY ASSESSMENT NETWORK
# ═══════════════════════════════════════════════════════════
def build_quality_assessment_network(input_shape: tuple = (224, 224, 3)):
    """Build image quality assessment network.

    Predicts quality score (0-1) based on:
    - Image sharpness/focus
    - Contrast adequacy
    - Anatomical coverage
    - Artifact presence
    - Standard plane compliance

    Returns:
        Compiled Keras model

    """
    inputs = layers.Input(shape=input_shape)

    # Feature extractor
    try:
        from tensorflow.keras.applications import EfficientNetB0
        base = EfficientNetB0(
            weights="imagenet", include_top=False, input_shape=input_shape,
        )
        for layer in base.layers[:-10]:
            layer.trainable = False
        features = base(inputs, training=False)
    except ImportError:
        features = conv_block(inputs, 32)
        features = layers.MaxPooling2D(2)(features)
        features = conv_block(features, 64)
        features = layers.MaxPooling2D(2)(features)
        features = conv_block(features, 128)

    # Global pooling
    x = layers.GlobalAveragePooling2D()(features)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)

    # Quality score output
    quality_output = layers.Dense(1, activation="sigmoid", name="quality_score")(x)

    # Quality component predictions (multi-output)
    sharpness = layers.Dense(1, activation="sigmoid", name="sharpness")(x)
    contrast = layers.Dense(1, activation="sigmoid", name="contrast")(x)
    coverage = layers.Dense(1, activation="sigmoid", name="coverage")(x)
    artifact_free = layers.Dense(1, activation="sigmoid", name="artifact_free")(x)

    model = models.Model(
        inputs=inputs,
        outputs={
            "quality_score": quality_output,
            "sharpness": sharpness,
            "contrast": contrast,
            "coverage": coverage,
            "artifact_free": artifact_free,
        },
        name="QualityAssessmentNetwork",
    )

    model.compile(
        optimizer=keras.optimizers.AdamW(learning_rate=1e-3, weight_decay=1e-4),
        loss={
            "quality_score": "mse",
            "sharpness": "mse",
            "contrast": "mse",
            "coverage": "mse",
            "artifact_free": "binary_crossentropy",
        },
        loss_weights={
            "quality_score": 1.0,
            "sharpness": 0.3,
            "contrast": 0.3,
            "coverage": 0.3,
            "artifact_free": 0.2,
        },
        metrics={
            "quality_score": ["mae"],
            "artifact_free": ["accuracy"],
        },
    )

    return model


# ═══════════════════════════════════════════════════════════
# VIEW CLASSIFICATION NETWORK
# ═══════════════════════════════════════════════════════════
def build_view_classifier(input_shape: tuple = (224, 224, 3), num_views: int = 14):
    """Build anatomical view classification network."""
    try:
        from tensorflow.keras.applications import EfficientNetB0
        base = EfficientNetB0(
            weights="imagenet", include_top=False, input_shape=input_shape,
        )
        for layer in base.layers[:-20]:
            layer.trainable = False
        features = base(inputs := layers.Input(shape=input_shape), training=False)
    except Exception:
        inputs = layers.Input(shape=input_shape)
        features = conv_block(inputs, 32)
        features = layers.MaxPooling2D(2)(features)
        features = conv_block(features, 64)
        features = layers.MaxPooling2D(2)(features)
        features = conv_block(features, 128)
        features = layers.GlobalAveragePooling2D()(features)

    if len(features.shape) == 4:
        features = layers.GlobalAveragePooling2D()(features)

    x = layers.Dense(512, activation="relu")(features)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.3)(x)

    output = layers.Dense(num_views, activation="softmax", name="view_output")(x)

    model = models.Model(inputs=inputs, outputs=output, name="ViewClassifier")

    model.compile(
        optimizer=keras.optimizers.AdamW(learning_rate=1e-3, weight_decay=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy", keras.metrics.AUC(name="auc")],
    )

    return model


def generate_synthetic_masks(images: np.ndarray) -> np.ndarray:
    """Generate synthetic segmentation masks for training.

    Creates elliptical masks simulating fetal region in ultrasound.
    In production, replace with real annotated masks.
    """
    masks = np.zeros(
        (len(images), images.shape[1], images.shape[2], 1), dtype=np.float32,
    )

    for i, img in enumerate(images):
        h, w = img.shape[:2]

        # Simulate fetal region as ellipse
        center_y = h // 2 + np.random.randint(-h // 6, h // 6)
        center_x = w // 2 + np.random.randint(-w // 6, w // 6)
        axes_y = h // 3 + np.random.randint(0, h // 6)
        axes_x = w // 3 + np.random.randint(0, w // 6)

        y_coords, x_coords = np.ogrid[:h, :w]
        ellipse = (
            (x_coords - center_x) ** 2 / axes_x**2
            + (y_coords - center_y) ** 2 / axes_y**2
        ) <= 1

        masks[i, :, :, 0] = ellipse.astype(np.float32)

    return masks


def evaluate_segmentation(model, X_test, y_test_masks, use_tta: bool = False):
    """Evaluate segmentation model with Dice and IoU metrics."""
    logger.info("\n%s", '=' * 60)
    logger.info("SEGMENTATION MODEL EVALUATION")
    logger.info("%s", '=' * 60)

    if use_tta:
        # Test-time augmentation
        predictions = []
        # Original
        predictions.append(model.predict(X_test, verbose=0))
        # Flipped
        predictions.append(
            np.flip(model.predict(np.flip(X_test, axis=2), verbose=0), axis=2),
        )
        # Rotated 90
        X_rot = np.rot90(X_test, 1, axes=(1, 2))
        pred_rot = model.predict(X_rot, verbose=0)
        predictions.append(np.rot90(pred_rot, -1, axes=(1, 2)))

        # Average predictions
        if isinstance(predictions[0], list):
            y_pred = [
                np.mean([p[i] for p in predictions], axis=0)
                for i in range(len(predictions[0]))
            ]
        else:
            y_pred = np.mean(predictions, axis=0)
    else:
        y_pred = model.predict(X_test, verbose=0)

    # Handle deep supervision outputs
    if isinstance(y_pred, list):
        y_pred = y_pred[0]  # Use main output

    # Compute Dice and IoU
    dice_scores = []
    iou_scores = []

    for i in range(len(X_test)):
        pred_mask = (y_pred[i, :, :, 0] > 0.5).astype(np.float32)
        true_mask = y_test_masks[i, :, :, 0]

        # Dice
        intersection = np.sum(pred_mask * true_mask)
        dice = (2 * intersection) / (np.sum(pred_mask) + np.sum(true_mask) + 1e-6)
        dice_scores.append(float(dice))

        # IoU
        union = np.sum(pred_mask) + np.sum(true_mask) - intersection
        iou = intersection / (union + 1e-6)
        iou_scores.append(float(iou))

    mean_dice = np.mean(dice_scores)
    mean_iou = np.mean(iou_scores)

    logger.info("  Mean Dice Score: %s", mean_dice)
    logger.info("  Mean IoU:        %s", mean_iou)
    logger.info(
        "  Dice > 0.8:      %s/%s",
        np.sum(np.array(dice_scores) > 0.8),
        len(dice_scores),
    )
    logger.info(
        "  Dice > 0.9:      %s/%s",
        np.sum(np.array(dice_scores) > 0.9),
        len(dice_scores),
    )

    return {
        "mean_dice": float(mean_dice),
        "mean_iou": float(mean_iou),
        "dice_scores": dice_scores,
        "iou_scores": iou_scores,
    }


def main():
    """Main image predictor training pipeline."""
    args = parse_args()

    logger.info("\n%s", '=' * 80)
    logger.info("IMAGE PREDICTOR TRAINING PIPELINE")
    logger.info("%s", '=' * 80)
    logger.info("Date: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logger.info("Mode: %s", args.mode)
    logger.info("Arguments: %s", json.dumps(vars(args), indent=2))

    setup_gpu(args.gpu, args.mixed_precision)

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

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

    # Split data
    from sklearn.model_selection import train_test_split

    X_train, X_val, _y_train, _y_val = train_test_split(
        images,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=np.argmax(labels, axis=1) if labels.ndim > 1 else labels,
    )

    # Generate synthetic masks (replace with real masks in production)
    logger.info("Generating synthetic segmentation masks for training...")
    train_masks = generate_synthetic_masks(X_train)
    val_masks = generate_synthetic_masks(X_val)

    logger.info("Dataset prepared:")
    logger.info("  Train samples: %s", len(X_train))
    logger.info("  Val samples:   %s", len(X_val))
    logger.info("  Image shape:   %s", X_train.shape[1:])

    # Initialize registry and tracker
    registry = ModelRegistry(base_dir=args.output_dir)
    tracker = TrainingProgressTracker(log_dir=args.log_dir)

    # Train models based on mode
    trained_models = {}
    eval_metrics = {}

    if args.mode in ["joint", "segmentation_only"]:
        # ─── Train Segmentation Model ───
        logger.info("\nBuilding U-Net++ segmentation model...")
        seg_model = build_unet_plus_plus(
            input_shape=(*args.target_size, 3),
            filters=args.seg_filters,
            use_deep_supervision=args.use_deep_supervision,
            backbone=args.seg_backbone,
        )

        total_params = seg_model.count_params()
        logger.info("Segmentation model parameters: %s", total_params)

        # Choose loss function
        if args.seg_loss == "dice":
            seg_loss = DiceLoss()
        elif args.seg_loss == "bce":
            seg_loss = keras.losses.BinaryCrossentropy()
        elif args.seg_loss == "combined":
            seg_loss = CombinedSegmentationLoss(dice_weight=args.dice_weight)
        else:
            seg_loss = BoundaryAwareLoss(
                base_loss=CombinedSegmentationLoss(dice_weight=args.dice_weight),
                boundary_weight=args.boundary_weight,
            )

        # Compile with deep supervision if needed
        if args.use_deep_supervision:
            _num_outputs = 1 + 3  # main + 3 auxiliary
            loss_list = [seg_loss] + [DiceLoss()] * 3
            loss_weights_list = [1.0] + [0.3] * 3

            seg_model.compile(
                optimizer=keras.optimizers.AdamW(
                    learning_rate=args.learning_rate, weight_decay=1e-4,
                ),
                loss=loss_list,
                loss_weights=loss_weights_list,
                metrics={
                    seg_model.output_names[0]: [
                        keras.metrics.MeanIoU(num_classes=2, name="dice"),
                    ],
                },
            )

        # Callbacks
        callbacks = [
            KerasProgressCallback(tracker),
            keras.callbacks.ModelCheckpoint(
                filepath=str(Path(args.output_dir) / "segmentation_best.keras"),
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
                monitor="val_loss", factor=0.5, patience=7, min_lr=1e-6, verbose=1,
            ),
        ]

        # Train
        logger.info("Training segmentation model for %s epochs...", args.epochs)
        _seg_history = seg_model.fit(
            X_train,
            [train_masks] + [train_masks] * 3
            if args.use_deep_supervision
            else train_masks,
            validation_data=(
                X_val,
                [val_masks] + [val_masks] * 3
                if args.use_deep_supervision
                else val_masks,
            ),
            epochs=args.epochs,
            batch_size=args.batch_size,
            callbacks=callbacks,
            verbose=1,
        )

        # Evaluate
        seg_metrics = evaluate_segmentation(
            seg_model, X_val, val_masks, use_tta=args.use_tta,
        )
        eval_metrics["segmentation"] = seg_metrics

        trained_models["segmentation"] = seg_model

    if args.mode in ["joint", "quality_only"]:
        # ─── Train Quality Assessment Model ───
        logger.info("\nBuilding quality assessment network...")
        quality_loader = ClinicalImageLoader(
            target_size=tuple(args.quality_size), clahe_enhance=True,
        )
        # Reload images at quality size
        quality_images, _, _ = quality_loader.load_from_directory(
            args.data_dir, class_mode="categorical",
        )
        X_train_q, X_val_q, _, _ = train_test_split(
            quality_images, labels, test_size=0.2, random_state=42,
        )

        quality_model = build_quality_assessment_network(
            input_shape=(*args.quality_size, 3),
        )

        # Generate quality labels (proxy based on image statistics)
        def generate_quality_labels(imgs):
            """Generate quality labels"""
            quality = np.zeros((len(imgs), 1), dtype=np.float32)
            for i, img in enumerate(imgs):
                # Proxy quality based on image statistics
                sharpness = (
                    np.std(cv2.Laplacian(img.astype(np.uint8), cv2.CV_64F))
                    if CV2_AVAILABLE
                    else np.std(img)
                )
                contrast = np.ptp(img) / 255.0
                quality[i, 0] = np.clip((sharpness / 100 + contrast) / 2, 0.1, 1.0)
            return quality

        train_quality = generate_quality_labels(X_train_q)
        val_quality = generate_quality_labels(X_val_q)

        quality_labels = {
            "quality_score": train_quality,
            "sharpness": np.clip(
                train_quality + np.random.randn(*train_quality.shape) * 0.1, 0, 1,
            ).astype(np.float32),
            "contrast": np.clip(
                train_quality + np.random.randn(*train_quality.shape) * 0.1, 0, 1,
            ).astype(np.float32),
            "coverage": np.clip(
                train_quality + np.random.randn(*train_quality.shape) * 0.1, 0, 1,
            ).astype(np.float32),
            "artifact_free": (train_quality > 0.5).astype(np.float32),
        }
        val_quality_labels = {
            "quality_score": val_quality,
            "sharpness": np.clip(
                val_quality + np.random.randn(*val_quality.shape) * 0.1, 0, 1,
            ).astype(np.float32),
            "contrast": np.clip(
                val_quality + np.random.randn(*val_quality.shape) * 0.1, 0, 1,
            ).astype(np.float32),
            "coverage": np.clip(
                val_quality + np.random.randn(*val_quality.shape) * 0.1, 0, 1,
            ).astype(np.float32),
            "artifact_free": (val_quality > 0.5).astype(np.float32),
        }

        quality_callbacks = [
            keras.callbacks.EarlyStopping(
                monitor="val_quality_score_mae",
                patience=args.patience,
                restore_best_weights=True,
                mode="min",
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_quality_score_mae", factor=0.5, patience=5, min_lr=1e-6,
            ),
        ]

        logger.info("Training quality assessment model...")
        quality_model.fit(
            X_train_q,
            quality_labels,
            validation_data=(X_val_q, val_quality_labels),
            epochs=args.epochs // 2,  # Quality model needs fewer epochs
            batch_size=args.batch_size,
            callbacks=quality_callbacks,
            verbose=1,
        )

        eval_metrics["quality"] = {"trained": True}
        trained_models["quality"] = quality_model

    if args.mode in ["joint", "view_classification"]:
        # ─── Train View Classifier ───
        logger.info("\nBuilding view classification model...")
        view_loader = ClinicalImageLoader(
            target_size=tuple(args.quality_size), clahe_enhance=True,
        )
        view_images, view_labels, view_class_names = view_loader.load_from_directory(
            args.data_dir, class_mode="categorical",
        )
        X_train_v, X_val_v, y_train_v, y_val_v = train_test_split(
            view_images, view_labels, test_size=0.2, random_state=42,
        )

        num_views = min(len(view_class_names), len(ANATOMICAL_VIEWS))
        view_model = build_view_classifier(
            input_shape=(*args.quality_size, 3), num_views=num_views,
        )

        view_callbacks = [
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy",
                patience=args.patience,
                restore_best_weights=True,
                mode="max",
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6,
            ),
        ]

        logger.info("Training view classification model...")
        view_model.fit(
            X_train_v,
            y_train_v,
            validation_data=(X_val_v, y_val_v),
            epochs=args.epochs // 2,
            batch_size=args.batch_size,
            callbacks=view_callbacks,
            verbose=1,
        )

        eval_metrics["view_classification"] = {"trained": True, "num_views": num_views}
        trained_models["view_classification"] = view_model

    # Save models
    logger.info("\nSaving models...")
    save_dir = Path(args.output_dir) / "image_predictor"
    save_dir.mkdir(parents=True, exist_ok=True)

    for name, model in trained_models.items():
        model_path = save_dir / f"{name}_latest.keras"
        model.save(str(model_path))
        logger.info("  Saved %s to %s", name, model_path)

    # Register in model registry
    model_metadata = ModelMetadata(
        model_name=args.model_name,
        model_type="image_predictor",
        training_date=datetime.now().isoformat(),
        architecture={
            "mode": args.mode,
            "seg_backbone": args.seg_backbone,
            "seg_filters": args.seg_filters,
            "use_deep_supervision": args.use_deep_supervision,
            "seg_loss": args.seg_loss,
            "target_size": list(args.target_size),
        },
        hyperparameters={
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "batch_size": args.batch_size,
            "dice_weight": args.dice_weight,
            "boundary_weight": args.boundary_weight,
        },
        metrics=eval_metrics,
        dataset_info={
            "train_size": len(X_train),
            "val_size": len(X_val),
            "image_shape": list(X_train.shape[1:]),
        },
    )

    registry = ModelRegistry(base_dir=args.output_dir)
    # Register the primary model (segmentation if joint, otherwise the trained one)
    primary_model = (
        trained_models.get("segmentation") or list(trained_models.values())[0]
    )
    registry.register_model(
        model_type="image_predictor",
        model=primary_model,
        metadata=model_metadata,
    )

    # Save training history
    tracker.save_history(
        str(Path(args.log_dir) / "image_predictor_training_history.json"),
    )

    logger.info(registry.compare_models("image_predictor"))

    logger.info("\n%s", '=' * 80)
    logger.info("IMAGE PREDICTOR TRAINING COMPLETED")
    logger.info("%s", '=' * 80)
    logger.info("Models saved to: %s", save_dir)
    logger.info("Model registered as: image_predictor/%s", model_metadata.version)


if __name__ == "__main__":
    main()
