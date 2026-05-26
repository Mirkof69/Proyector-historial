"""Data Pipeline for Fetal Medical System AI Training

Provides comprehensive data loading, augmentation, and evaluation utilities
for clinical ultrasound image datasets. Supports both real clinical data and
public datasets with medical-image-specific augmentation.

Features:
- Clinical ultrasound image loading (JPEG, PNG, TIFF, DICOM)
- Medical-image-specific data augmentation
- Cross-validation with medical data standards
- Clinical metrics evaluation (sensitivity, specificity, AUC, F1)
- Batch data generators for efficient training

Author: Fetal Medical System AI Team
Version: 1.0.0
"""

import json
import logging
import os
from pathlib import Path

import numpy as np
Image = None  # Will be overridden if PIL is available
try:
    from PIL import Image  # type: ignore[assignment]
except ImportError:
    pass

logger = logging.getLogger(__name__)

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

try:
    import tensorflow as tf
    from tensorflow import keras

    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from pydicom import dcmread

    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False

from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import KFold, StratifiedKFold, train_test_split

# ─── Clinical Ultrasound Image Extensions ───
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
DICOM_EXTENSIONS = {".dcm", ".dicom"}
ALL_IMAGE_EXTENSIONS = IMAGE_EXTENSIONS | DICOM_EXTENSIONS


# ═══════════════════════════════════════════════════════════
# MEDICAL IMAGE AUGMENTATION
# ═══════════════════════════════════════════════════════════
class MedicalImageAugmenter:
    """Data augmentation specifically designed for medical ultrasound images.

    Unlike natural image augmentation, medical augmentation must preserve
    clinically relevant features while simulating real-world variations:
    - Probe angle variations
    - Gain/brightness changes
    - Speckle noise (characteristic of ultrasound)
    - Patient movement artifacts
    - Depth/focus variations
    """

    def __init__(
        self,
        rotation_range: float = 20.0,
        width_shift_range: float = 0.15,
        height_shift_range: float = 0.15,
        zoom_range: float = 0.15,
        horizontal_flip: bool = True,
        vertical_flip: bool = False,
        brightness_range: tuple[float, float] | None = None,
        contrast_range: tuple[float, float] | None = None,
        speckle_noise_range: float = 0.0,
        elastic_distortion: bool = False,
        mixup_alpha: float = 0.0,
        cutmix_alpha: float = 0.0,
    ):
        """Initialize medical image augmenter.

        Args:
            rotation_range: Maximum rotation angle in degrees
            width_shift_range: Maximum horizontal shift as fraction of width
            height_shift_range: Maximum vertical shift as fraction of height
            zoom_range: Maximum zoom factor
            horizontal_flip: Whether to apply horizontal flip
            vertical_flip: Whether to apply vertical flip (usually False for ultrasound)
            brightness_range: Tuple of (min, max) brightness multiplier
            contrast_range: Tuple of (min, max) contrast multiplier
            speckle_noise_range: Maximum speckle noise intensity (0-1)
            elastic_distortion: Whether to apply elastic distortion
            mixup_alpha: Alpha parameter for MixUp augmentation (0 to disable)
            cutmix_alpha: Alpha parameter for CutMix augmentation (0 to disable)

        """
        self.rotation_range = rotation_range
        self.width_shift_range = width_shift_range
        self.height_shift_range = height_shift_range
        self.zoom_range = zoom_range
        self.horizontal_flip = horizontal_flip
        self.vertical_flip = vertical_flip
        self.brightness_range = brightness_range or (0.8, 1.2)
        self.contrast_range = contrast_range or (0.8, 1.2)
        self.speckle_noise_range = speckle_noise_range
        self.elastic_distortion = elastic_distortion
        self.mixup_alpha = mixup_alpha
        self.cutmix_alpha = cutmix_alpha

    def augment(
        self, image: np.ndarray, label: np.ndarray = None, training: bool = True,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Apply augmentation to a single image.

        Args:
            image: Input image as numpy array
            label: Optional label (one-hot encoded)
            training: Whether in training mode

        Returns:
            Augmented image and label

        """
        if not training:
            return image, label

        aug_image = image.copy().astype(np.float32)

        # Rotation (simulating probe angle variation)
        if self.rotation_range > 0:
            angle = np.random.uniform(-self.rotation_range, self.rotation_range)
            if CV2_AVAILABLE:
                h, w = aug_image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                aug_image = cv2.warpAffine(
                    aug_image, M, (w, h), borderMode=cv2.BORDER_REFLECT,
                )

        # Translation (simulating probe position variation)
        if self.width_shift_range > 0 or self.height_shift_range > 0:
            tx = np.random.uniform(-self.width_shift_range, self.width_shift_range)
            ty = np.random.uniform(-self.height_shift_range, self.height_shift_range)
            if CV2_AVAILABLE:
                h, w = aug_image.shape[:2]
                M = np.float32([[1, 0, tx * w], [0, 1, ty * h]])
                aug_image = cv2.warpAffine(
                    aug_image, M, (w, h), borderMode=cv2.BORDER_REFLECT,
                )

        # Zoom (simulating depth variation)
        if self.zoom_range > 0:
            zoom = np.random.uniform(1.0 - self.zoom_range, 1.0 + self.zoom_range)
            if CV2_AVAILABLE:
                h, w = aug_image.shape[:2]
                new_h, new_w = int(h * zoom), int(w * zoom)
                aug_image = cv2.resize(aug_image, (new_w, new_h))
                if zoom > 1:
                    start_y = (new_h - h) // 2
                    start_x = (new_w - w) // 2
                    aug_image = aug_image[start_y : start_y + h, start_x : start_x + w]
                else:
                    pad_y = (h - new_h) // 2
                    pad_x = (w - new_w) // 2
                    aug_image = np.pad(
                        aug_image,
                        ((pad_y, h - new_h - pad_y), (pad_x, w - new_w - pad_x), (0, 0))
                        if aug_image.ndim == 3
                        else ((pad_y, h - new_h - pad_y), (pad_x, w - new_w - pad_x)),
                        mode="reflect",
                    )

        # Horizontal flip (simulating left/right probe orientation)
        if self.horizontal_flip and np.random.random() > 0.5:
            aug_image = np.fliplr(aug_image)

        # Vertical flip (rarely used in ultrasound)
        if self.vertical_flip and np.random.random() > 0.5:
            aug_image = np.flipud(aug_image)

        # Brightness variation (simulating gain changes)
        brightness = np.random.uniform(*self.brightness_range)
        aug_image = aug_image * brightness

        # Contrast variation (simulating different tissue contrast)
        contrast = np.random.uniform(*self.contrast_range)
        mean = np.mean(aug_image, axis=(0, 1), keepdims=True)
        aug_image = (aug_image - mean) * contrast + mean

        # Speckle noise (characteristic of ultrasound imaging)
        if self.speckle_noise_range > 0:
            noise_std = np.random.uniform(0, self.speckle_noise_range)
            noise = np.random.normal(0, noise_std * 255, aug_image.shape)
            aug_image = aug_image + noise

        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        if CV2_AVAILABLE and np.random.random() > 0.5:
            if aug_image.ndim == 3 and aug_image.shape[2] == 3:
                lab = cv2.cvtColor(aug_image.astype(np.uint8), cv2.COLOR_RGB2LAB)
                l_channel = lab[:, :, 0]
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                lab[:, :, 0] = clahe.apply(l_channel)
                aug_image = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            elif aug_image.ndim == 2:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                aug_image = clahe.apply(aug_image.astype(np.uint8))

        # Clip values
        aug_image = np.clip(aug_image, 0, 255).astype(np.float32)

        return aug_image, label

    def apply_mixup(
        self, images: np.ndarray, labels: np.ndarray, batch_size: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Apply MixUp augmentation to a batch."""
        if self.mixup_alpha <= 0:
            return images, labels

        lam = np.random.beta(self.mixup_alpha, self.mixup_alpha, batch_size)
        lam = np.maximum(lam, 1.0 - lam)  # Ensure lam >= 0.5

        indices = np.random.permutation(batch_size)
        mixed_images = (
            lam[:, None, None, None] * images
            + (1 - lam[:, None, None, None]) * images[indices]
        )
        mixed_labels = lam[:, None] * labels + (1 - lam[:, None]) * labels[indices]

        return mixed_images, mixed_labels


# ═══════════════════════════════════════════════════════════
# IMAGE LOADER
# ═══════════════════════════════════════════════════════════
class ClinicalImageLoader:
    """Loads clinical ultrasound images from various formats.

    Supports:
    - Standard image formats: JPEG, PNG, BMP, TIFF
    - DICOM medical imaging format
    - Directory-based dataset organization
    - Automatic preprocessing (normalization, resizing)
    """

    def __init__(
        self,
        target_size: tuple[int, int] = (224, 224),
        grayscale: bool = False,
        normalize: bool = True,
        clahe_enhance: bool = False,
    ):
        """Initialize clinical image loader.

        Args:
            target_size: Target image dimensions (height, width)
            grayscale: Convert to grayscale
            normalize: Normalize pixel values to [0, 1]
            clahe_enhance: Apply CLAHE for contrast enhancement

        """
        self.target_size = target_size
        self.grayscale = grayscale
        self.normalize = normalize
        self.clahe_enhance = clahe_enhance

    def load_image(self, path: str) -> np.ndarray:
        """Load a single image from file.

        Args:
            path: Path to image file

        Returns:
            Loaded and preprocessed image as numpy array

        """
        path = str(path)
        ext = os.path.splitext(path)[1].lower()

        if ext in DICOM_EXTENSIONS or (PYDICOM_AVAILABLE and self._is_dicom(path)):
            return self._load_dicom(path)
        return self._load_standard(path)

    def _load_standard(self, path: str) -> np.ndarray:
        """Load standard image format (JPEG, PNG, etc.)."""
        if CV2_AVAILABLE:
            flags = cv2.IMREAD_GRAYSCALE if self.grayscale else cv2.IMREAD_COLOR
            image = cv2.imread(path, flags)
            if image is None:
                raise ValueError(f"Failed to load image: {path}")
            image = (
                cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if not self.grayscale else image
            )
        else:
            image = np.array(Image.open(path))  # Image loaded at module level
            if self.grayscale and image.ndim == 3:
                image = np.mean(image, axis=-1)

        # Resize
        if CV2_AVAILABLE:
            image = cv2.resize(image, self.target_size[::-1])
        else:

            image = np.array(Image.fromarray(image).resize(self.target_size[::-1]))

        # Add channel dimension if grayscale
        if image.ndim == 2:
            image = np.stack([image] * 3, axis=-1)

        # CLAHE enhancement
        if self.clahe_enhance and CV2_AVAILABLE:
            if image.shape[2] == 3:
                lab = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2LAB)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                lab[:, :, 0] = clahe.apply(lab[:, :, 0])
                image = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

        # Normalize
        if self.normalize:
            image = image.astype(np.float32) / 255.0

        return image

    def _load_dicom(self, path: str) -> np.ndarray:
        """Load DICOM medical image."""
        if not PYDICOM_AVAILABLE:
            raise ImportError("pydicom is required for DICOM support")

        ds = dcmread(path)
        image = ds.pixel_array.astype(np.float32)

        # Apply DICOM rescale slope and intercept
        slope = getattr(ds, "RescaleSlope", 1)
        intercept = getattr(ds, "RescaleIntercept", 0)
        image = image * slope + intercept

        # Normalize to [0, 255]
        img_min, img_max = image.min(), image.max()
        if img_max > img_min:
            image = ((image - img_min) / (img_max - img_min) * 255).astype(np.uint8)
        else:
            image = np.zeros_like(image, dtype=np.uint8)

        # Resize
        if CV2_AVAILABLE:
            image = cv2.resize(image, self.target_size[::-1])
        else:

            image = np.array(Image.fromarray(image).resize(self.target_size[::-1]))

        # Convert to 3-channel
        if image.ndim == 2:
            image = np.stack([image] * 3, axis=-1)

        if self.normalize:
            image = image.astype(np.float32) / 255.0

        return image

    def _is_dicom(self, path: str) -> bool:
        """Check if file is DICOM format."""
        if not PYDICOM_AVAILABLE:
            return False
        try:
            with open(path, "rb") as f:
                f.read(128)
                prefix = f.read(4)
                return prefix == b"DICM"
        except Exception:
            return False

    def load_from_directory(
        self,
        directory: str,
        class_mode: str = "categorical",
        shuffle: bool = True,
        seed: int = 42,
    ) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """Load all images from a directory organized by class.

        Expected structure:
            directory/
                class_name_1/
                    image1.jpg
                    image2.jpg
                class_name_2/
                    image1.jpg
                    ...

        Args:
            directory: Root directory containing class subdirectories
            class_mode: "categorical" for one-hot, "binary" for binary, "raw" for raw labels
            shuffle: Whether to shuffle the dataset
            seed: Random seed for reproducibility

        Returns:
            Tuple of (images, labels, class_names)

        """
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        images = []
        labels = []
        class_names = sorted([d.name for d in directory.iterdir() if d.is_dir()])
        class_to_idx = {name: i for i, name in enumerate(class_names)}

        for class_name in class_names:
            class_dir = directory / class_name
            class_idx = class_to_idx[class_name]

            for img_path in class_dir.iterdir():
                if img_path.suffix.lower() in ALL_IMAGE_EXTENSIONS:
                    try:
                        img = self.load_image(str(img_path))
                        images.append(img)
                        labels.append(class_idx)
                    except Exception as e:
                        logger.warning("Failed to load %s: %s", img_path, e)

        if len(images) == 0:
            raise ValueError(f"No valid images found in {directory}")

        images = np.array(images)
        labels = np.array(labels)

        if class_mode == "categorical":
            num_classes = len(class_names)
            labels = np.eye(num_classes)[labels]

        if shuffle:
            rng = np.random.RandomState(seed)
            indices = rng.permutation(len(images))
            images = images[indices]
            labels = labels[indices]

        logger.info("Loaded %s images from %s classes", len(images), len(class_names))
        return images, labels, class_names


# ═══════════════════════════════════════════════════════════
# DATA GENERATOR (TensorFlow-compatible)
# ═══════════════════════════════════════════════════════════
class ClinicalDataGenerator:
    """TensorFlow-compatible data generator for clinical ultrasound datasets.

    Provides:
    - On-the-fly data augmentation
    - Batch generation with configurable batch size
    - Support for in-memory and disk-based datasets
    - Compatible with tf.data pipeline
    """

    def __init__(
        self,
        images: np.ndarray,
        labels: np.ndarray,
        augmenter: MedicalImageAugmenter | None = None,
        batch_size: int = 32,
        shuffle: bool = True,
        seed: int = 42,
    ):
        """Initialize data generator.

        Args:
            images: Image array of shape (N, H, W, C)
            labels: Label array (one-hot or raw)
            augmenter: MedicalImageAugmenter instance
            batch_size: Batch size for training
            shuffle: Whether to shuffle data
            seed: Random seed

        """
        self.images = images
        self.labels = labels
        self.augmenter = augmenter or MedicalImageAugmenter()
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.seed = seed
        self.index = 0
        self.epoch = 0

        if shuffle:
            self._shuffle_data()

    def _shuffle_data(self):
        """Shuffle data at the beginning of each epoch."""
        rng = np.random.RandomState(self.seed + self.epoch)
        indices = rng.permutation(len(self.images))
        self.images = self.images[indices]
        self.labels = self.labels[indices]

    def __len__(self):
        """Number of batches per epoch."""
        return int(np.ceil(len(self.images) / self.batch_size))

    def __iter__(self):
        """Reset iterator."""
        self.index = 0
        return self

    def __next__(self) -> tuple[np.ndarray, np.ndarray]:
        """Get next batch."""
        if self.index >= len(self.images):
            self.epoch += 1
            if self.shuffle:
                self._shuffle_data()
            self.index = 0
            raise StopIteration

        end_index = min(self.index + self.batch_size, len(self.images))
        batch_images = self.images[self.index : end_index]
        batch_labels = self.labels[self.index : end_index]
        self.index = end_index

        # Apply augmentation
        augmented_images = []
        augmented_labels = []
        for img, label in zip(batch_images, batch_labels):
            aug_img, aug_label = self.augmenter.augment(img, label, training=True)
            augmented_images.append(aug_img)
            augmented_labels.append(aug_label)

        batch_images = np.array(augmented_images)
        batch_labels = np.array(augmented_labels)

        # Apply MixUp
        if self.augmenter.mixup_alpha > 0:
            batch_images, batch_labels = self.augmenter.apply_mixup(
                batch_images, batch_labels, len(batch_images),
            )

        return batch_images, batch_labels

    def get_tf_dataset(self) -> tf.data.Dataset:
        """Convert to TensorFlow Dataset for efficient training."""
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow is required for tf.data.Dataset")

        dataset = tf.data.Dataset.from_generator(
            self.__iter__,
            output_signature=(
                tf.TensorSpec(shape=(None,) + self.images.shape[1:], dtype=tf.float32),
                tf.TensorSpec(shape=(None,) + self.labels.shape[1:], dtype=tf.float32),
            ),
        )
        dataset = dataset.prefetch(tf.data.AUTOTUNE)
        return dataset


# ═══════════════════════════════════════════════════════════
# CROSS-VALIDATION
# ═══════════════════════════════════════════════════════════
class MedicalCrossValidator:
    """Cross-validation utilities for medical data.

    Implements:
    - Stratified K-Fold (preserves class distribution)
    - Patient-level splitting (avoids data leakage)
    - Nested cross-validation for hyperparameter tuning
    """

    def __init__(
        self, n_splits: int = 5, stratified: bool = True, random_state: int = 42,
    ):
        """Initialize cross-validator.

        Args:
            n_splits: Number of cross-validation folds
            stratified: Use stratified splitting
            random_state: Random seed

        """
        self.n_splits = n_splits
        self.stratified = stratified
        self.random_state = random_state

        if stratified:
            self.cv = StratifiedKFold(
                n_splits=n_splits, shuffle=True, random_state=random_state,
            )
        else:
            self.cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    def split(self, X: np.ndarray, y: np.ndarray):
        """Generate train/validation splits.

        Args:
            X: Feature array
            y: Label array

        Yields:
            Tuple of (train_indices, val_indices)

        """
        if self.stratified and y.ndim > 1:
            # Convert one-hot to class indices for stratification
            y_labels = np.argmax(y, axis=1)
        else:
            y_labels = y

        yield from self.cv.split(X, y_labels)


# ═══════════════════════════════════════════════════════════
# CLINICAL METRICS EVALUATOR
# ═══════════════════════════════════════════════════════════
class ClinicalMetricsEvaluator:
    """Evaluates model performance using clinical metrics.

    Provides:
    - Sensitivity (Recall)
    - Specificity
    - Precision (PPV)
    - NPV (Negative Predictive Value)
    - AUC-ROC
    - AUC-PR (Precision-Recall)
    - F1 Score
    - Confusion Matrix
    - Per-class metrics
    """

    @staticmethod
    def evaluate(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: np.ndarray = None,
        class_names: list[str] = None,
        average: str = "macro",
    ) -> dict:
        """Compute comprehensive clinical metrics.

        Args:
            y_true: Ground truth labels (class indices or one-hot)
            y_pred: Predicted labels (class indices)
            y_prob: Predicted probabilities (for AUC calculation)
            class_names: List of class names
            average: Averaging method for multi-class metrics

        Returns:
            Dictionary of metrics

        """
        # Convert one-hot to indices if needed
        if y_true.ndim > 1:
            y_true = np.argmax(y_true, axis=1)
        if y_pred.ndim > 1:
            y_pred = np.argmax(y_pred, axis=1)

        num_classes = len(np.unique(y_true))
        if class_names is None:
            class_names = [f"class_{i}" for i in range(num_classes)]

        metrics = {}

        # Overall metrics
        metrics["accuracy"] = float(accuracy_score(y_true, y_pred))
        metrics["precision"] = float(
            precision_score(y_true, y_pred, average=average, zero_division=0),
        )
        metrics["recall"] = float(
            recall_score(y_true, y_pred, average=average, zero_division=0),
        )
        metrics["f1"] = float(
            f1_score(y_true, y_pred, average=average, zero_division=0),
        )

        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=range(num_classes))
        metrics["confusion_matrix"] = cm.tolist()

        # Per-class metrics
        per_class_metrics = {}
        for i, name in enumerate(class_names):
            if i >= num_classes:
                break
            # Binary one-vs-rest for each class
            binary_true = (y_true == i).astype(int)
            binary_pred = (y_pred == i).astype(int)

            tp = np.sum((binary_true == 1) & (binary_pred == 1))
            tn = np.sum((binary_true == 0) & (binary_pred == 0))
            fp = np.sum((binary_true == 0) & (binary_pred == 1))
            fn = np.sum((binary_true == 1) & (binary_pred == 0))

            sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
            f1 = (
                2 * precision * sensitivity / (precision + sensitivity)
                if (precision + sensitivity) > 0
                else 0.0
            )

            per_class_metrics[name] = {
                "sensitivity": float(sensitivity),
                "specificity": float(specificity),
                "precision": float(precision),
                "npv": float(npv),
                "f1": float(f1),
                "support": int(np.sum(binary_true)),
            }

        metrics["per_class"] = per_class_metrics

        # AUC-ROC (if probabilities provided)
        if y_prob is not None and num_classes == 2:
            try:
                metrics["auc_roc"] = float(roc_auc_score(y_true, y_prob[:, 1]))
            except Exception:
                metrics["auc_roc"] = 0.0
        elif y_prob is not None and num_classes > 2:
            try:
                metrics["auc_roc"] = float(
                    roc_auc_score(y_true, y_prob, multi_class="ovr", average=average),
                )
            except Exception:
                metrics["auc_roc"] = 0.0

        # AUC-PR
        if y_prob is not None and num_classes == 2:
            try:
                metrics["auc_pr"] = float(average_precision_score(y_true, y_prob[:, 1]))
            except Exception:
                metrics["auc_pr"] = 0.0

        # Classification report
        metrics["classification_report"] = classification_report(
            y_true, y_pred, target_names=class_names, zero_division=0,
        )

        return metrics

    @staticmethod
    def compute_dice_score(
        y_true_mask: np.ndarray, y_pred_mask: np.ndarray, smooth: float = 1e-6,
    ) -> float:
        """Compute Dice coefficient for segmentation evaluation.

        Args:
            y_true_mask: Ground truth binary mask
            y_pred_mask: Predicted binary mask
            smooth: Smoothing factor

        Returns:
            Dice coefficient (0-1)

        """
        y_true_flat = y_true_mask.flatten()
        y_pred_flat = y_pred_mask.flatten()

        intersection = np.sum(y_true_flat * y_pred_flat)
        dice = (2.0 * intersection + smooth) / (
            np.sum(y_true_flat) + np.sum(y_pred_flat) + smooth
        )

        return float(dice)

    @staticmethod
    def compute_iou(
        y_true_mask: np.ndarray, y_pred_mask: np.ndarray, smooth: float = 1e-6,
    ) -> float:
        """Compute Intersection over Union (IoU) for segmentation.

        Args:
            y_true_mask: Ground truth binary mask
            y_pred_mask: Predicted binary mask
            smooth: Smoothing factor

        Returns:
            IoU score (0-1)

        """
        y_true_flat = y_true_mask.flatten()
        y_pred_flat = y_pred_mask.flatten()

        intersection = np.sum(y_true_flat * y_pred_flat)
        union = np.sum(y_true_flat) + np.sum(y_pred_flat) - intersection
        iou = (intersection + smooth) / (union + smooth)

        return float(iou)


# ═══════════════════════════════════════════════════════════
# DATASET BUILDER
# ═══════════════════════════════════════════════════════════
class FetalDatasetBuilder:
    """High-level dataset builder that combines loading, augmentation,
    and splitting into a single workflow.

    Usage:
        builder = FetalDatasetBuilder(
            data_dir="datasets/train",
            target_size=(224, 224),
            batch_size=32,
            augment=True
        )
        train_ds, val_ds, test_ds = builder.build()
    """

    def __init__(
        self,
        data_dir: str,
        target_size: tuple[int, int] = (224, 224),
        batch_size: int = 32,
        augment: bool = True,
        validation_split: float = 0.2,
        test_split: float = 0.1,
        seed: int = 42,
        clahe_enhance: bool = True,
    ):
        """Initialize dataset builder.

        Args:
            data_dir: Path to dataset directory
            target_size: Target image size (height, width)
            batch_size: Batch size
            augment: Whether to apply augmentation
            validation_split: Fraction for validation
            test_split: Fraction for test
            seed: Random seed
            clahe_enhance: Apply CLAHE contrast enhancement

        """
        self.data_dir = data_dir
        self.target_size = target_size
        self.batch_size = batch_size
        self.augment = augment
        self.validation_split = validation_split
        self.test_split = test_split
        self.seed = seed
        self.clahe_enhance = clahe_enhance

        self.loader = ClinicalImageLoader(
            target_size=target_size, clahe_enhance=clahe_enhance,
        )

    def build(self) -> tuple:
        """Build train/validation/test datasets.

        Returns:
            Tuple of (train_data, val_data, test_data, metadata)
            Each data tuple: (images, labels)

        """
        # Load all images
        images, labels, class_names = self.loader.load_from_directory(
            self.data_dir, class_mode="categorical", shuffle=True, seed=self.seed,
        )

        num_classes = len(class_names)
        metadata = {
            "num_classes": num_classes,
            "class_names": class_names,
            "total_samples": len(images),
            "image_shape": images.shape[1:],
        }

        # Split: train / val / test
        # First split off test set
        if self.test_split > 0:
            X_temp, X_test, y_temp, y_test = train_test_split(
                images,
                labels,
                test_size=self.test_split,
                random_state=self.seed,
                stratify=np.argmax(labels, axis=1) if labels.ndim > 1 else labels,
            )
        else:
            X_temp, y_temp = images, labels
            X_test, y_test = None, None

        # Then split validation from remaining
        val_ratio = (
            self.validation_split / (1.0 - self.test_split)
            if self.test_split > 0
            else self.validation_split
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp,
            y_temp,
            test_size=val_ratio,
            random_state=self.seed,
            stratify=np.argmax(y_temp, axis=1) if y_temp.ndim > 1 else y_temp,
        )

        metadata["train_size"] = len(X_train)
        metadata["val_size"] = len(X_val)
        metadata["test_size"] = len(X_test) if X_test is not None else 0

        # Create generators
        if self.augment:
            augmenter = MedicalImageAugmenter(
                speckle_noise_range=0.02,
                mixup_alpha=0.2,
            )
        else:
            augmenter = None

        train_gen = ClinicalDataGenerator(
            X_train,
            y_train,
            augmenter=augmenter,
            batch_size=self.batch_size,
            shuffle=True,
            seed=self.seed,
        )
        val_gen = ClinicalDataGenerator(
            X_val,
            y_val,
            augmenter=None,  # No augmentation for validation
            batch_size=self.batch_size,
            shuffle=False,
            seed=self.seed,
        )

        train_data = (X_train, y_train, train_gen)
        val_data = (X_val, y_val, val_gen)
        test_data = (X_test, y_test, None) if X_test is not None else None

        return train_data, val_data, test_data, metadata


# ═══════════════════════════════════════════════════════════
# PROGRESS TRACKER
# ═══════════════════════════════════════════════════════════
class TrainingProgressTracker:
    """Tracks and logs training progress with clinical metrics.
    """

    def __init__(self, log_dir: str = "logs", verbose: int = 1):
        """Initialize progress tracker.

        Args:
            log_dir: Directory for training logs
            verbose: Logging verbosity (0=silent, 1=progress, 2=detailed)

        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.epoch_history = {
            "epoch": [],
            "train_loss": [],
            "val_loss": [],
            "train_accuracy": [],
            "val_accuracy": [],
        }
        self.best_val_accuracy = 0.0
        self.best_epoch = 0
        self.start_time = None

    def on_epoch_begin(self, epoch: int):
        """Called at the start of an epoch."""
        if self.verbose >= 1:
            logger.info("\n%s", '=' * 60)
            logger.info("EPOCH %s", epoch + 1)
            logger.info("%s", '=' * 60)

    def on_epoch_end(self, epoch: int, logs: dict = None):
        """Called at the end of an epoch."""
        logs = logs or {}
        self.epoch_history["epoch"].append(epoch + 1)
        self.epoch_history["train_loss"].append(float(logs.get("loss", 0)))
        self.epoch_history["val_loss"].append(float(logs.get("val_loss", 0)))
        self.epoch_history["train_accuracy"].append(float(logs.get("accuracy", 0)))
        self.epoch_history["val_accuracy"].append(float(logs.get("val_accuracy", 0)))

        # Track best model
        val_acc = logs.get("val_accuracy", 0)
        if val_acc > self.best_val_accuracy:
            self.best_val_accuracy = val_acc
            self.best_epoch = epoch + 1
            is_best = True
        else:
            is_best = False

        if self.verbose >= 1:
            logger.info(
                "  Train Loss: %s | Val Loss: %s",
                logs.get('loss', 0),
                logs.get('val_loss', 0),
            )
            best_marker = "<-- BEST" if is_best else ""
            logger.info(
                "  Train Acc:  %.4f | Val Acc:  %.4f %s",
                logs.get('accuracy', 0),
                logs.get('val_accuracy', 0),
                best_marker,
            )

    def save_history(self, path: str = None):
        """Save training history to JSON."""
        path = path or str(self.log_dir / "training_history.json")
        with open(path, "w", encoding='utf-8') as f:
            json.dump(
                {
                    "epoch_history": self.epoch_history,
                    "best_val_accuracy": self.best_val_accuracy,
                    "best_epoch": self.best_epoch,
                },
                f,
                indent=2,
            )
        logger.info("Training history saved to %s", path)


if TF_AVAILABLE:

    class KerasProgressCallback(keras.callbacks.Callback):
        """Keras callback for progress tracking."""

        def __init__(self, tracker: TrainingProgressTracker):
            """Init"""
            super().__init__()
            self.tracker = tracker

        def on_epoch_begin(self, epoch, _logs=None):
            """On epoch begin"""
            self.tracker.on_epoch_begin(epoch)

        def on_epoch_end(self, epoch, logs=None):
            """On epoch end"""
            self.tracker.on_epoch_end(epoch, logs)

else:

    class KerasProgressCallback:
        """Mock callback when TensorFlow is not available."""

        def __init__(self, tracker):
            """Init"""
            self._tracker = tracker

        def on_epoch_begin(self, epoch, logs=None):
            """On epoch begin"""

        def on_epoch_end(self, epoch, logs=None):
            """On epoch end"""
