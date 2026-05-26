"""Script maestro de entrenamiento - Microservicio IA Fetal Medical (PyTorch)
Entrena EfficientNetB4CNN: clasificacion de patologias + regresion biometria fetal
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

try:
    import timm as _timm  # type: ignore[import-untyped]
    TIMM_AVAILABLE = True
except ImportError:
    _timm = None  # type: ignore[assignment]
    TIMM_AVAILABLE = False

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import DATASETS_DIR, MODEL_PATHS  # type: ignore[import]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PATHOLOGY_CLASSES = [
    "normal", "hidrocefalia", "anencefalia", "espina_bifida", "labio_leporino",
    "atresia_duodenal", "cardiopatia_congenita", "oligohidramnios", "polihidramnios",
    "restriccion_crecimiento", "macrosomia_fetal", "placenta_previa",
    "preeclampsia_signos", "muerte_fetal", "embarazo_multiple",
]
BIOMETRY_FIELDS = ["BPD_mm", "HC_mm", "AC_mm", "FL_mm", "peso_estimado_g"]
NUM_PATHOLOGIES = len(PATHOLOGY_CLASSES)
NUM_BIOMETRY = len(BIOMETRY_FIELDS)
IMG_SIZE = 384
BATCH = 16
EPOCHS = 30


class FetalDataset(Dataset):
    """Dataset con imagenes de ecografia y labels de patologia + biometria."""

    def __init__(self, root_dir: Path, transform=None):
        """Init"""
        self.transform = transform
        self.samples = []
        cls_to_idx = {c: i for i, c in enumerate(PATHOLOGY_CLASSES)}
        for cls in PATHOLOGY_CLASSES:
            cls_dir = root_dir / cls
            if cls_dir.exists():
                for p in cls_dir.glob("*.png"):
                    self.samples.append((p, cls_to_idx[cls]))

    def __len__(self):
        """Len"""
        return len(self.samples)

    def __getitem__(self, idx):
        """Getitem"""
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        # Biometria sintetica (placeholder hasta tener dataset real)
        biometry = torch.zeros(NUM_BIOMETRY, dtype=torch.float32)
        return img, label, biometry


TRAIN_TF = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(20),
    transforms.ColorJitter(brightness=0.3, contrast=0.3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

VAL_TF = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def build_efficientnet_b4() -> nn.Module:
    """Construye EfficientNet-B4 con dos cabezas: clasificacion + biometria."""
    if not TIMM_AVAILABLE:
        raise ImportError("timm es requerido: pip install timm")

    backbone = _timm.create_model("efficientnet_b4", pretrained=False, num_classes=0, global_pool="avg")
    feat_dim = backbone.num_features  # 1792

    class EfficientNetB4Dual(nn.Module):
        """Efficientnetb4dual"""
        def __init__(self):
            """Init"""
            super().__init__()
            self.backbone = backbone
            self.classification_head = nn.Sequential(
                nn.Dropout(0.3),
                nn.Linear(feat_dim, 512),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(512, NUM_PATHOLOGIES),
                nn.Sigmoid(),
            )
            self.biometry_head = nn.Sequential(
                nn.Dropout(0.3),
                nn.Linear(feat_dim, 256),
                nn.ReLU(),
                nn.Linear(256, NUM_BIOMETRY),
                nn.ReLU(),
            )

        def forward(self, x):
            """Forward"""
            features = self.backbone(x)
            return self.classification_head(features), self.biometry_head(features)

    return EfficientNetB4Dual()


def train_classifier():
    """Entrena EfficientNet-B4 dual-head para patologias + biometria fetal."""
    print("=" * 60)
    print("  ENTRENANDO EfficientNet-B4 (Clasificacion + Biometria)")
    print("=" * 60)

    train_dir = DATASETS_DIR / "train"
    val_dir = DATASETS_DIR / "validation"

    if not train_dir.exists():
        logger.error("No existe el directorio: %s", train_dir)
        logger.info("Crea la estructura: datasets/train/<clase>/*.png")
        return False

    train_ds = FetalDataset(train_dir, TRAIN_TF)
    val_ds = FetalDataset(val_dir, VAL_TF)
    train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=BATCH, shuffle=False, num_workers=0)

    logger.info("Train: %d | Val: %d", len(train_ds), len(val_ds))
    logger.info("Clases: %s", list(PATHOLOGY_CLASSES))

    device: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    model = build_efficientnet_b4().to(device)

    cls_criterion = nn.BCELoss()
    bio_criterion = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_val_loss = float("in")
    patience, patience_count = 10, 0
    save_path = MODEL_PATHS.get("efficientnet_b4", str(ROOT / "trained_models" / "efficientnet_b4.pth"))

    history = {"train_loss": [], "val_loss": []}

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()

        # Entrenamiento
        model.train()
        tr_loss = 0.0
        for imgs, labels, bio_labels in train_loader:
            imgs = imgs.to(device)
            labels_onehot = torch.zeros(len(labels), NUM_PATHOLOGIES, device=device)
            labels_onehot.scatter_(1, labels.to(device).unsqueeze(1), 1.0)
            bio_labels = bio_labels.to(device)

            optimizer.zero_grad()
            cls_out, bio_out = model(imgs)
            loss = cls_criterion(cls_out, labels_onehot) + 0.1 * bio_criterion(bio_out, bio_labels)
            loss.backward()
            optimizer.step()
            tr_loss += loss.item()

        # Validacion
        model.train(False)
        v_loss = 0.0
        with torch.no_grad():
            for imgs, labels, bio_labels in val_loader:
                imgs = imgs.to(device)
                labels_onehot = torch.zeros(len(labels), NUM_PATHOLOGIES, device=device)
                labels_onehot.scatter_(1, labels.to(device).unsqueeze(1), 1.0)
                bio_labels = bio_labels.to(device)
                cls_out, bio_out = model(imgs)
                v_loss += (cls_criterion(cls_out, labels_onehot) + 0.1 * bio_criterion(bio_out, bio_labels)).item()

        scheduler.step()
        tr_loss /= max(len(train_loader), 1)
        v_loss /= max(len(val_loader), 1)
        history["train_loss"].append(tr_loss)
        history["val_loss"].append(v_loss)

        improved = v_loss < best_val_loss
        if improved:
            best_val_loss = v_loss
            torch.save(model.state_dict(), save_path)
            patience_count = 0
        else:
            patience_count += 1

        logger.info(
            "Epoch %02d/%02d | Loss %.4f/%.4f %s | %.1fs",
            epoch, EPOCHS, tr_loss, v_loss,
            "[BEST]" if improved else f"[patience {patience_count}/{patience}]",
            time.time() - t0,
        )

        if patience_count >= patience:
            logger.info("Early stopping en epoch %d", epoch)
            break

    logger.info("Modelo guardado en: %s", save_path)

    meta = {
        "best_val_loss": best_val_loss,
        "classes": list(PATHOLOGY_CLASSES),
        "biometry_fields": BIOMETRY_FIELDS,
        "date": datetime.now().isoformat(),
        "framework": "pytorch",
        "backbone": "efficientnet_b4",
        "history": history,
    }
    meta_path = Path(save_path).parent / "efficientnet_b4_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return True


def main():
    """Main"""
    print("\n" + "=" * 60)
    print("  ENTRENAMIENTO REDES NEURONALES - Fetal Medical IA")
    print("=" * 60)
    print("\n1. EfficientNet-B4 (Clasificacion Patologias + Biometria)")
    print("0. Salir")

    choice = input("\nSelecciona: ").strip()
    if choice == "1":
        train_classifier()
    elif choice != "0":
        print("Opcion invalida")


if __name__ == "__main__":
    main()
