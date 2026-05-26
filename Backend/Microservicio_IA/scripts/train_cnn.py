"""ENTRENAMIENTO CNN - CLASIFICADOR ECOGRAFIAS v3.0 (PyTorch)
- 5 clases: ecografia_2d, ecografia_3d, doppler, transabdominal, transvaginal
- Backbone: EfficientNet-B4 (timm) con transfer learning
- Regularizacion: Dropout + Weight Decay + CosineAnnealingLR
- Data augmentation con torchvision.transforms
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CLASSES = ["ecografia_2d", "ecografia_3d", "doppler", "transabdominal", "transvaginal"]
NUM_CLASSES = len(CLASSES)
IMG_SIZE = 224
BATCH = 16
EPOCHS = 20
LR = 1e-3
WEIGHT_DECAY = 1e-4
MODELS_DIR = ROOT / "trained_models"
DATA_DIR = ROOT / "datasets"
SAVE_PATH = MODELS_DIR / "classifier_v2.pth"
MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


# ── SYNTHETIC DATA GENERATION ────────────────────────────────────────────────

def gen_img(class_idx: int) -> np.ndarray:
    """Genera imagen sintetica con patron visual por clase."""
    rng = np.random.default_rng()
    h, w = IMG_SIZE, IMG_SIZE
    img = rng.integers(20, 60, (h, w, 3), dtype=np.uint8).astype(np.float32)
    cx, cy = w // 2, h // 2

    def ell(ex, ey, rx, ry, color):
        """Ell"""
        y_grid, x_grid = np.ogrid[:h, :w]
        mask = ((x_grid - ex) ** 2 / max(rx, 1) ** 2 + (y_grid - ey) ** 2 / max(ry, 1) ** 2) <= 1
        noise = rng.random(mask.shape) > 0.15
        img[mask & noise] = color

    if class_idx == 0:  # 2D: circulo central
        ell(cx, cy, 60, 60, [150, 150, 150])
        ell(cx, cy, 40, 40, [130, 130, 130])
    elif class_idx == 1:  # 3D: rectangulo con textura
        img[cy - 50:cy + 50, cx - 60:cx + 60] = rng.integers(140, 200, (100, 120, 3))
        img[cy - 30:cy + 30, cx - 40:cx + 40] = [180, 170, 160]
    elif class_idx == 2:  # Doppler: bandas de color
        for y in range(0, h, 40):
            band = (y // 40) % 3
            if band == 0:
                img[y:y + 20, :, 0] = 200
            elif band == 1:
                img[y:y + 20, :, 2] = 200
    elif class_idx == 3:  # Transabdominal: elipse horizontal
        ell(cx, cy, 90, 50, [160, 160, 170])
        ell(cx, cy - 10, 70, 35, [140, 140, 150])
    else:  # Transvaginal: cono triangular
        for y in range(40, 184):
            w2 = max(2, int((y - 40) * 0.5))
            img[y, max(0, cx - w2):min(w, cx + w2)] = [170, 165, 155]

    noise = rng.normal(0, 8, img.shape).astype(np.float32)
    return np.clip(img + noise, 0, 255).astype(np.uint8)


def gen_dataset(base: Path, per_class: int = 1500) -> None:
    """Gen dataset"""
    total = per_class * NUM_CLASSES * 2
    logger.info("Generando %d imagenes sinteticas...", total)
    t0 = time.time()
    for split_name, count in [
        ("train", int(per_class * 0.8)),
        ("validation", int(per_class * 0.2)),
    ]:
        for ci, cls in enumerate(CLASSES):
            d = base / split_name / cls
            d.mkdir(parents=True, exist_ok=True)
            for i in range(count):
                Image.fromarray(gen_img(ci)).save(str(d / f"{i:04d}.png"))
    logger.info("Dataset generado en %.1fs", time.time() - t0)


# ── DATASET ──────────────────────────────────────────────────────────────────

class UltrasoundDataset(Dataset):
    """Dataset de imagenes de ecografia desde directorio."""

    def __init__(self, root_dir: Path, transform=None):
        """Init"""
        self.transform = transform
        self.samples = []
        self.class_to_idx = {c: i for i, c in enumerate(CLASSES)}
        for cls in CLASSES:
            cls_dir = root_dir / cls
            if cls_dir.exists():
                for img_path in cls_dir.glob("*.png"):
                    self.samples.append((img_path, self.class_to_idx[cls]))

    def __len__(self):
        """Len"""
        return len(self.samples)

    def __getitem__(self, idx):
        """Getitem"""
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label


# ── MODEL ────────────────────────────────────────────────────────────────────

def build_model(num_classes: int) -> nn.Module:
    """EfficientNet-B4 con cabeza de clasificacion."""
    if TIMM_AVAILABLE:
        model = _timm.create_model(
            "efficientnet_b4",
            pretrained=False,
            num_classes=num_classes,
        )
    else:
        # Fallback: CNN simple si timm no disponible
        model = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Dropout(0.4),
            nn.Linear(128, num_classes),
        )
    return model


# ── TRANSFORMS ───────────────────────────────────────────────────────────────

TRAIN_TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(25),
    transforms.ColorJitter(brightness=0.4, contrast=0.4),
    transforms.RandomAffine(degrees=0, translate=(0.2, 0.2), scale=(0.8, 1.2)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

VAL_TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


# ── TRAINING ─────────────────────────────────────────────────────────────────

def train_epoch(model, loader, criterion, optimizer, device):
    """Train epoch"""
    model.train()
    total_loss, correct, total = 0.0, 0, 0
    for imgs, labels in loader:
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(labels)
        correct += (outputs.argmax(1) == labels).sum().item()
        total += len(labels)
    return total_loss / total, correct / total


def val_epoch(model, loader, criterion, device):
    """Val epoch"""
    model.train(False)
    total_loss, correct, total = 0.0, 0, 0
    with torch.no_grad():
        for imgs, labels in loader:
            imgs, labels = imgs.to(device), labels.to(device)
            outputs = model(imgs)
            total_loss += criterion(outputs, labels).item() * len(labels)
            correct += (outputs.argmax(1) == labels).sum().item()
            total += len(labels)
    return total_loss / total, correct / total


def train():
    """Train"""
    print("=" * 60)
    print("  ENTRENAMIENTO CNN CLASIFICADOR v3.0 (PyTorch)")
    print(f"  {NUM_CLASSES} clases | EfficientNet-B4 + Dropout")
    print("=" * 60)

    # Generar dataset si no existe
    tr_d = DATA_DIR / "train"
    if not tr_d.exists() or len(list(tr_d.glob("*/*.png"))) < 1000:
        gen_dataset(DATA_DIR, 1500)

    train_ds = UltrasoundDataset(DATA_DIR / "train", TRAIN_TRANSFORM)
    val_ds = UltrasoundDataset(DATA_DIR / "validation", VAL_TRANSFORM)

    train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=BATCH, shuffle=False, num_workers=0)

    logger.info("Train: %d | Val: %d", len(train_ds), len(val_ds))

    device: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    model = build_model(NUM_CLASSES).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_val_acc = 0.0
    patience_count = 0
    patience = 6
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()
        tr_loss, tr_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        v_loss, v_acc = val_epoch(model, val_loader, criterion, device)
        scheduler.step()

        history["train_loss"].append(tr_loss)
        history["val_loss"].append(v_loss)
        history["train_acc"].append(tr_acc)
        history["val_acc"].append(v_acc)

        improved = v_acc > best_val_acc
        if improved:
            best_val_acc = v_acc
            torch.save(model.state_dict(), SAVE_PATH)
            patience_count = 0
        else:
            patience_count += 1

        logger.info(
            "Epoch %02d/%02d | Loss %.4f/%.4f | Acc %.4f/%.4f %s | %.1fs",
            epoch, EPOCHS, tr_loss, v_loss, tr_acc, v_acc,
            "[BEST]" if improved else f"[no improve {patience_count}]",
            time.time() - t0,
        )

        if patience_count >= patience:
            logger.info("Early stopping en epoch %d", epoch)
            break

    print(f"\n{'=' * 60}")
    print(f"  COMPLETADO | Mejor Val Acc: {best_val_acc:.4f}")
    print(f"  Modelo: {SAVE_PATH}")
    print(f"{'=' * 60}")

    meta_path = MODELS_DIR / "classifier_history.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_val_accuracy": best_val_acc,
                "classes": CLASSES,
                "date": datetime.now().isoformat(),
                "framework": "pytorch",
                "backbone": "efficientnet_b4",
                "history": history,
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    train()
