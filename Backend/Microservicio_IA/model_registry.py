"""Model Registry for Fetal Medical System AI Training

Provides model serialization, version control, and metadata tracking
for trained clinical AI models.

Features:
- Automatic version management (v1, v2, v3, ...)
- Metadata tracking (training date, accuracy, dataset size)
- Model comparison and selection
- Backup and rollback capabilities
- Export for production deployment

Author: Fetal Medical System AI Team
Version: 1.0.0
"""

import json
import logging
import os
import pickle
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Silence TensorFlow warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

try:
    import tensorflow.keras as keras
    TF_AVAILABLE = True
except ImportError:
    keras = None
    TF_AVAILABLE = False


# ─── Model Types ───
MODEL_TYPES = {
    "graphmdl": "Graph-based Medical Deep Learning",
    "predictive": "Predictive Risk Model",
    "screening": "Early Screening Model",
    "image_predictor": "Image Prediction/Segmentation Model",
    "classifier": "Ultrasound Type Classifier",
    "pathology": "Pathology Detector",
    "segmenter": "Fetal Segmenter",
}


class ModelMetadata:
    """Metadata container for a trained model.

    Tracks:
    - Training configuration
    - Performance metrics
    - Dataset information
    - Model architecture details
    - Deployment status
    """

    def __init__(
        self,
        model_name: str,
        model_type: str,
        version: str = "v1",
        training_date: str = None,
        architecture: dict = None,
        hyperparameters: dict = None,
        metrics: dict = None,
        dataset_info: dict = None,
        notes: str = "",
    ):
        """Initialize model metadata.

        Args:
            model_name: Human-readable model name
            model_type: Type of model (graphmdl, predictive, etc.)
            version: Version string (v1, v2, etc.)
            training_date: ISO format training date
            architecture: Architecture configuration
            hyperparameters: Training hyperparameters
            metrics: Performance metrics
            dataset_info: Dataset information
            notes: Additional notes

        """
        self.model_name = model_name
        self.model_type = model_type
        self.version = version
        self.training_date = training_date or datetime.now().isoformat()
        self.architecture = architecture or {}
        self.hyperparameters = hyperparameters or {}
        self.metrics = metrics or {}
        self.dataset_info = dataset_info or {}
        self.notes = notes
        self.deployment_status = (
            "development"  # development, staging, production, deprecated
        )

    def to_dict(self) -> dict:
        """Convert metadata to dictionary."""
        return {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "version": self.version,
            "training_date": self.training_date,
            "architecture": self.architecture,
            "hyperparameters": self.hyperparameters,
            "metrics": self.metrics,
            "dataset_info": self.dataset_info,
            "notes": self.notes,
            "deployment_status": self.deployment_status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModelMetadata":
        """Create metadata from dictionary."""
        metadata = cls(
            model_name=data.get("model_name", "unknown"),
            model_type=data.get("model_type", "unknown"),
            version=data.get("version", "v1"),
            training_date=data.get("training_date"),
            architecture=data.get("architecture", {}),
            hyperparameters=data.get("hyperparameters", {}),
            metrics=data.get("metrics", {}),
            dataset_info=data.get("dataset_info", {}),
            notes=data.get("notes", ""),
        )
        metadata.deployment_status = data.get("deployment_status", "development")
        return metadata

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "ModelMetadata":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __repr__(self):
        """Repr"""
        return (
            f"ModelMetadata(name={self.model_name!r}, type={self.model_type!r}, "
            f"version={self.version!r}, acc={self.metrics.get('accuracy', 'N/A')})"
        )


class ModelRegistry:
    """Centralized model registry for managing trained clinical AI models.

    Directory structure:
        trained_models/
            graphmdl/
                v1/
                    model.keras
                    metadata.json
                    training_history.json
                v2/
                    model.keras
                    metadata.json
                    training_history.json
            predictive/
                v1/
                    ...
            screening/
                v1/
                    ...
            image_predictor/
                v1/
                    ...
    """

    def __init__(self, base_dir: str = None):
        """Initialize model registry.

        Args:
            base_dir: Base directory for model storage (defaults to trained_models/)

        """
        if base_dir is None:
            base_dir = Path(__file__).parent / "trained_models"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for each model type
        for model_type in MODEL_TYPES:
            (self.base_dir / model_type).mkdir(exist_ok=True)

        self._index = self._build_index()

    def _build_index(self) -> dict[str, dict[str, ModelMetadata]]:
        """Build index of all registered models."""
        index = {}

        for model_type in MODEL_TYPES:
            type_dir = self.base_dir / model_type
            if not type_dir.exists():
                continue

            index[model_type] = {}

            for version_dir in sorted(type_dir.iterdir()):
                if not version_dir.is_dir():
                    continue

                metadata_path = version_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, encoding='utf-8') as f:
                            data = json.load(f)
                        metadata = ModelMetadata.from_dict(data)
                        index[model_type][metadata.version] = metadata
                    except Exception as e:
                        logger.warning(
                            "Failed to load metadata from %s: %s",
                            metadata_path,
                            e,
                        )

        return index

    def get_next_version(self, model_type: str) -> str:
        """Get the next available version for a model type.

        Args:
            model_type: Model type string

        Returns:
            Next version string (e.g., "v3")

        """
        if model_type not in self._index:
            return "v1"

        versions = self._index[model_type]
        if not versions:
            return "v1"

        # Extract version numbers
        version_nums = []
        for v in versions:
            try:
                num = int(v.lower().replace("v", ""))
                version_nums.append(num)
            except ValueError:
                continue

        next_num = max(version_nums) + 1 if version_nums else 1
        return f"v{next_num}"

    def register_model(
        self,
        model_type: str,
        model: Any,
        metadata: ModelMetadata,
        training_history: dict = None,
        model_format: str = "keras",
    ) -> str:
        """Register a trained model in the registry.

        Args:
            model_type: Model type (graphmdl, predictive, etc.)
            model: Trained model object
            metadata: Model metadata
            training_history: Optional training history dict
            model_format: Model file format (keras, h5, pkl, etc.)

        Returns:
            Path to saved model directory

        """
        # Get next version
        version = self.get_next_version(model_type)
        metadata.version = version

        # Create version directory
        version_dir = self.base_dir / model_type / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Save model
        if model_format == "keras" and TF_AVAILABLE:
            model_path = version_dir / "model.keras"
            model.save(str(model_path))
        elif model_format == "h5" and TF_AVAILABLE:
            model_path = version_dir / "model.h5"
            model.save(str(model_path))
        elif model_format == "pkl":

            model_path = version_dir / "model.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(model, f)
        else:
            model_path = version_dir / "model.keras"
            if TF_AVAILABLE:
                model.save(str(model_path))
            else:
                # Create placeholder for mock models
                model_path.touch()

        # Save metadata
        metadata_path = version_dir / "metadata.json"
        with open(metadata_path, "w", encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, indent=2, default=str)

        # Save training history if provided
        if training_history:
            history_path = version_dir / "training_history.json"
            with open(history_path, "w", encoding='utf-8') as f:
                json.dump(training_history, f, indent=2)

        # Update index
        if model_type not in self._index:
            self._index[model_type] = {}
        self._index[model_type][version] = metadata

        logger.info("Registered %s/%s at %s", model_type, version, version_dir)
        return str(version_dir)

    def load_model(self, model_type: str, version: str = None, **kwargs):
        """Load a registered model.

        Args:
            model_type: Model type string
            version: Version string (defaults to latest)
            **kwargs: Additional arguments for custom object loading

        Returns:
            Loaded model and metadata

        """
        if version is None:
            version = self.get_latest_version(model_type)

        version_dir = self.base_dir / model_type / version
        if not version_dir.exists():
            raise FileNotFoundError(f"Model not found: {model_type}/{version}")

        # Load metadata
        metadata_path = version_dir / "metadata.json"
        with open(metadata_path, encoding='utf-8') as f:
            metadata = ModelMetadata.from_dict(json.load(f))

        # Load model
        model_files = list(version_dir.glob("model.*"))
        if not model_files:
            raise FileNotFoundError(f"No model file found in {version_dir}")

        model_path = model_files[0]
        ext = model_path.suffix

        if (ext == ".keras" and TF_AVAILABLE) or (ext == ".h5" and TF_AVAILABLE):
            custom_objects = kwargs.get("custom_objects", {})
            model = keras.models.load_model(
                str(model_path), custom_objects=custom_objects,
            )
        elif ext == ".pkl":

            with open(model_path, "rb") as f:
                model = pickle.load(f)
        else:
            raise ValueError(f"Unsupported model format: {ext}")

        logger.info("Loaded %s/%s from %s", model_type, version, model_path)
        return model, metadata

    def get_latest_version(self, model_type: str) -> str:
        """Get the latest version string for a model type."""
        if model_type not in self._index or not self._index[model_type]:
            raise ValueError(f"No models registered for type: {model_type}")

        versions = self._index[model_type].keys()
        version_nums = {}
        for v in versions:
            try:
                num = int(v.lower().replace("v", ""))
                version_nums[num] = v
            except ValueError:
                continue

        if not version_nums:
            return list(versions)[-1]

        return version_nums[max(version_nums.keys())]

    def get_best_model(self, model_type: str, metric: str = "val_accuracy") -> tuple:
        """Get the best model based on a specific metric.

        Args:
            model_type: Model type string
            metric: Metric name to compare

        Returns:
            Tuple of (model, metadata) for the best model

        """
        if model_type not in self._index or not self._index[model_type]:
            raise ValueError(f"No models registered for type: {model_type}")

        best_version = None
        best_score = -1

        for version, metadata in self._index[model_type].items():
            score = metadata.metrics.get(metric, 0)
            if score > best_score:
                best_score = score
                best_version = version

        if best_version is None:
            raise ValueError(f"No valid scores found for {model_type}")

        return self.load_model(model_type, best_version)

    def list_models(
        self, model_type: str = None,
    ) -> dict[str, dict[str, ModelMetadata]]:
        """List all registered models.

        Args:
            model_type: Optional filter by model type

        Returns:
            Dictionary of model types and their versions

        """
        if model_type:
            return {model_type: self._index.get(model_type, {})}
        return self._index

    def delete_model(self, model_type: str, version: str):
        """Delete a model version."""
        version_dir = self.base_dir / model_type / version
        if version_dir.exists():
            shutil.rmtree(version_dir)
            if model_type in self._index and version in self._index[model_type]:
                del self._index[model_type][version]
            logger.info("Deleted %s/%s", model_type, version)

    def compare_models(self, model_type: str) -> str:
        """Generate a comparison report for all versions of a model type.

        Args:
            model_type: Model type string

        Returns:
            Formatted comparison string

        """
        if model_type not in self._index or not self._index[model_type]:
            return f"No models registered for type: {model_type}"

        report = f"\n{'=' * 80}\n"
        report += f"MODEL COMPARISON: {model_type.upper()}\n"
        report += f"{'=' * 80}\n\n"

        # Header
        report += f"{'Version':<10} {'Accuracy':<12} {'AUC':<10} {'F1':<10} {'Dataset Size':<15} {'Date':<20}\n"
        report += "-" * 80 + "\n"

        for version, metadata in sorted(self._index[model_type].items()):
            acc = metadata.metrics.get("val_accuracy", "N/A")
            auc = metadata.metrics.get("auc_roc", "N/A")
            f1 = metadata.metrics.get("f1", "N/A")
            dataset_size = metadata.dataset_info.get("total_samples", "N/A")
            date = metadata.training_date[:10] if metadata.training_date else "N/A"

            report += f"{version:<10} {acc!s:<12} {auc!s:<10} {f1!s:<10} {dataset_size!s:<15} {date:<20}\n"

        report += "\n"
        return report

    def export_model(self, model_type: str, version: str, export_dir: str) -> str:
        """Export a model for production deployment.

        Args:
            model_type: Model type string
            version: Version string
            export_dir: Export directory

        Returns:
            Path to exported model

        """
        version_dir = self.base_dir / model_type / version
        export_path = Path(export_dir) / f"{model_type}_{version}"
        export_path.mkdir(parents=True, exist_ok=True)

        # Copy model files
        for f in version_dir.iterdir():
            shutil.copy2(f, export_path / f.name)

        # Add deployment manifest
        manifest = {
            "model_type": model_type,
            "version": version,
            "exported_at": datetime.now().isoformat(),
            "source": str(version_dir),
            "deployment_status": "ready",
        }
        with open(export_path / "deployment_manifest.json", "w", encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        logger.info("Exported %s/%s to %s", model_type, version, export_path)
        return str(export_path)


# ═══════════════════════════════════════════════════════════
# MODEL VERSION MANAGER
# ═══════════════════════════════════════════════════════════
class ModelVersionManager:
    """Higher-level model version management with rollback and comparison.
    """

    def __init__(self, registry: ModelRegistry = None):
        """Initialize version manager.

        Args:
            registry: ModelRegistry instance (creates one if not provided)

        """
        self.registry = registry or ModelRegistry()

    def rollback(self, model_type: str, target_version: str) -> bool:
        """Rollback to a previous model version.

        Args:
            model_type: Model type string
            target_version: Version to rollback to

        Returns:
            True if rollback was successful

        """
        try:
            latest = self.registry.get_latest_version(model_type)
            if target_version == latest:
                logger.info("Already on %s", target_version)
                return True

            # Load target version
            _model, _metadata = self.registry.load_model(model_type, target_version)

            # Deprecate newer versions
            versions = self.registry._index.get(model_type, {})
            for v in versions:
                try:
                    v_num = int(v.lower().replace("v", ""))
                    t_num = int(target_version.lower().replace("v", ""))
                    if v_num > t_num:
                        versions[v].deployment_status = "deprecated"
                        metadata_path = (
                            self.registry.base_dir / model_type / v / "metadata.json"
                        )
                        if metadata_path.exists():
                            with open(metadata_path, "w", encoding='utf-8') as f:
                                json.dump(versions[v].to_dict(), f, indent=2)
                except ValueError:
                    continue

            logger.info("Rolled back %s to %s", model_type, target_version)
            return True
        except Exception as e:
            logger.error("Rollback failed: %s", e)
            return False

    def promote_to_production(self, model_type: str, version: str) -> bool:
        """Promote a model to production deployment.

        Args:
            model_type: Model type string
            version: Version string

        Returns:
            True if promotion was successful

        """
        try:
            if model_type not in self.registry._index:
                return False

            metadata = self.registry._index[model_type].get(version)
            if metadata is None:
                return False

            metadata.deployment_status = "production"
            metadata_path = (
                self.registry.base_dir / model_type / version / "metadata.json"
            )
            with open(metadata_path, "w", encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2)

            # Deprecate previous production models
            for v, m in self.registry._index[model_type].items():
                if v != version and m.deployment_status == "production":
                    m.deployment_status = "staging"
                    m_path = self.registry.base_dir / model_type / v / "metadata.json"
                    if m_path.exists():
                        with open(m_path, "w", encoding='utf-8') as f:
                            json.dump(m.to_dict(), f, indent=2)

            logger.info("Promoted %s/%s to production", model_type, version)
            return True
        except Exception as e:
            logger.error("Promotion failed: %s", e)
            return False

    def get_production_model(self, model_type: str) -> tuple:
        """Get the current production model.

        Args:
            model_type: Model type string

        Returns:
            Tuple of (model, metadata) or None

        """
        if model_type not in self.registry._index:
            return None

        for version, metadata in self.registry._index[model_type].items():
            if metadata.deployment_status == "production":
                return self.registry.load_model(model_type, version)

        # Fallback to latest
        return self.registry.load_model(model_type)
