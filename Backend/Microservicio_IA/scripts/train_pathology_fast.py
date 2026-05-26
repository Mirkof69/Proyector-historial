"""ENTRENAMIENTO RAPIDO - DETECTOR DE PATOLOGIAS FETALES (PyTorch)
EfficientNet-B4 + Transfer Learning | 15 clases
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

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CLASSES = [
    "normal", "hidrocefalia", "anencefalia", "espina_bifida", "labio_leporino",
    "atresia_duodenal", "cardiopatia_congenita", "oligohidramnios", "polihidramnios",
    "restriccion_crecimiento", "macrosomia_fetal", "placenta_previa",
    "preeclampsia_signos", "muerte_fetal", "embarazo_multiple",
]
NUM_CLASSES = len(CLASSES)
IMG_SIZE = 224
BATCH = 32
EPOCHS_PHASE1 = 5
EPOCHS_PHASE2 = 8
MODELS_DIR = ROOT_DIR / "trained_models"
DATA_DIR = ROOT_DIR / "datasets_pathology"
MODEL_PATH = MODELS_DIR / "pathology_v2.pth"
MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


# ── SYNTHETIC DATA ────────────────────────────────────────────────────────────

_PATHOLOGY_PATTERNS = {
    "hidrocefalia": {"shape": "large_head", "color": [200, 220, 255]},
    "anencefalia": {"shape": "absent_head", "color": [100, 100, 100]},
    "espina_bifida": {"shape": "spine", "color": [180, 180, 220]},
    "labio_leporino": {"shape": "face_cleft", "color": [230, 180, 180]},
    "atresia_duodenal": {"shape": "double_bubble", "color": [200, 200, 150]},
    "cardiopatia_congenita": {"shape": "heart", "color": [255, 150, 150]},
    "oligohidramnios": {"shape": "sparse", "color": [80, 80, 80]},
    "polihidramnios": {"shape": "fluid", "color": [150, 200, 255]},
    "restriccion_crecimiento": {"shape": "small_fetus", "color": [170, 170, 170]},
    "macrosomia_fetal": {"shape": "large_fetus", "color": [220, 200, 180]},
    "placenta_previa": {"shape": "placenta_low", "color": [200, 180, 160]},
    "preeclampsia_signos": {"shape": "vascular", "color": [255, 200, 200]},
    "muerte_fetal": {"shape": "static", "color": [60, 60, 60]},
    "embarazo_multiple": {"shape": "twins", "color": [180, 220, 180]},
    "normal": {"shape": "normal", "color": [150, 150, 150]},
}


def gen_img(class_name: str) -> np.ndarray:
    """Gen img"""
    rng = np.random.default_rng()
    h, w = IMG_SIZE, IMG_SIZE
    img = rng.integers(20, 60, (h, w, 3), dtype=np.uint8).astype(np.float32)
    pattern = _PATHOLOGY_PATTERNS.get(class_name, {"shape": "normal", "color": [150, 150, 150]})
    color = pattern["color"]
    cx, cy = w // 2, h // 2

    y_grid, x_grid = np.ogrid[:h, :w]
    mask = ((x_grid - cx) ** 2 / 60 ** 2 + (y_grid - cy) ** 2 / 50 ** 2) <= 1
    img[mask] = np.array(color, dtype=np.float32)

    noise = rng.normal(0, 10, img.shape).astype(np.float32)
    return np.clip(img + noise, 0, 255).astype(np.uint8)


def gen_dataset(base: Path, per_class: int = 300) -> None:
    """Gen dataset"""
    logger.info("Generando dataset rapido (%d imgs/clase)...", per_class)
    t0 = time.time()
    for split, count in [("train", int(per_class * 0.8)), ("validation", int(per_class * 0.2))]:
        for cls in CLASSES:
            d = base / split / cls
            d.mkdir(parents=True, exist_ok=True)
            for i in range(count):
                Image.fromarray(gen_img(cls)).save(str(d / f"{i:04d}.png"))
    logger.info("Dataset generado en %.1fs", time.time() - t0)


# ── DATASET ──────────────────────────────────────────────────────────────────

class PathologyDataset(Dataset):
    """Pathologydataset"""
    def __init__(self, root_dir: Path, transform=None):
        """Init"""
        self.transform = transform
        self.samples = []
        self.class_to_idx = {c: i for i, c in enumerate(CLASSES)}
        for cls in CLASSES:
            cls_dir = root_dir / cls
            if cls_dir.exists():
                for p in cls_dir.glob("*.png"):
                    self.samples.append((p, self.class_to_idx[cls]))

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


TRAIN_TF = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.3, contrast=0.3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

VAL_TF = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


# ── MODEL ────────────────────────────────────────────────────────────────────

def build_model() -> nn.Module:
    """Build model"""
    if TIMM_AVAILABLE:
        return _timm.create_model("efficientnet_b4", pretrained=False, num_classes=NUM_CLASSES)
    return nn.Sequential(
        nn.Conv2d(3, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(1),
        nn.Flatten(), nn.Linear(128, NUM_CLASSES),
    )


# ── TRAIN LOOP ───────────────────────────────────────────────────────────────

def run_epoch(model, loader, criterion, optimizer, device, training: bool):
    """Run epoch"""
    model.train(training)
    total_loss, correct, total = 0.0, 0, 0
    ctx = torch.enable_grad() if training else torch.no_grad()
    with ctx:
        for imgs, labels in loader:
            imgs, labels = imgs.to(device), labels.to(device)
            if training:
                optimizer.zero_grad()
            out = model(imgs)
            loss = criterion(out, labels)
            if training:
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * len(labels)
            correct += (out.argmax(1) == labels).sum().item()
            total += len(labels)
    return total_loss / max(total, 1), correct / max(total, 1)


def train():
    """Train"""
    print("=" * 60)
    print("  ENTRENAMIENTO RAPIDO PATOLOGIAS v2.0 (PyTorch)")
    print(f"  {NUM_CLASSES} clases | EfficientNet-B4")
    print("=" * 60)

    tr_d = DATA_DIR / "train"
    if not tr_d.exists() or len(list(tr_d.glob("*/*.png"))) < 500:
        gen_dataset(DATA_DIR, 300)

    train_ds = PathologyDataset(DATA_DIR / "train", TRAIN_TF)
    val_ds = PathologyDataset(DATA_DIR / "validation", VAL_TF)
    train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=BATCH, shuffle=False, num_workers=0)

    logger.info("Train: %d | Val: %d", len(train_ds), len(val_ds))

    device: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model().to(device)

    # Fase 1: cabeza solamente (si hay pretrained weights podriamos congelar backbone)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS_PHASE1)

    best_val_acc = 0.0
    total_epochs = EPOCHS_PHASE1 + EPOCHS_PHASE2

    for epoch in range(1, total_epochs + 1):
        if epoch == EPOCHS_PHASE1 + 1:
            logger.info("Fase 2: fine-tuning completo con LR reducido")
            for pg in optimizer.param_groups:
                pg["lr"] = 1e-4
            scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS_PHASE2)

        tr_loss, tr_acc = run_epoch(model, train_loader, criterion, optimizer, device, True)
        v_loss, v_acc = run_epoch(model, val_loader, criterion, optimizer, device, False)
        scheduler.step()

        if v_acc > best_val_acc:
            best_val_acc = v_acc
            torch.save(model.state_dict(), MODEL_PATH)

        logger.info(
            "Epoch %02d/%02d | loss %.4f/%.4f | acc %.4f/%.4f %s",
            epoch, total_epochs, tr_loss, v_loss, tr_acc, v_acc,
            "[BEST]" if v_acc >= best_val_acc else "",
        )

    print(f"\n{'=' * 60}")
    print(f"  COMPLETADO | Mejor Val Acc: {best_val_acc:.4f}")
    print(f"  Modelo: {MODEL_PATH}")
    print(f"{'=' * 60}")

    with open(MODELS_DIR / "pathology_history.json", "w", encoding="utf-8") as f:
        json.dump({
            "best_val_accuracy": best_val_acc,
            "classes": CLASSES,
            "date": datetime.now().isoformat(),
            "framework": "pytorch",
        }, f, indent=2)


if __name__ == "__main__":
    train()
