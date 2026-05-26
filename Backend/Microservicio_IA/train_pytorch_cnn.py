"""=============================================================================
ENTRENAMIENTO CNN FETAL — EfficientNet-B4 Produccion
=============================================================================
RTX 4070 Laptop | PyTorch 2.6 + CUDA 12.4
AMP (FP16) + Focal Loss + 2-Phase Transfer Learning + Gradient Accumulation
=============================================================================
"""

import logging
import os
import sys
import time
import warnings

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:256,garbage_collection_threshold:0.8"

import numpy as np
import torch
import torch.nn.functional as F
from contextlib import nullcontext
from PIL import Image
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms

warnings.filterwarnings("ignore", category=UserWarning)

# Logger placeholder — se configura dentro de main() para que los workers
# del DataLoader (que re-importan este modulo en Windows) no hereden el setup
logger = logging.getLogger("fetal_train")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importacion diferida: se ejecuta en main(), no al importar el modulo
PATHOLOGY_CLASSES = None  # type: ignore
BIOMETRY_FIELDS   = None  # type: ignore
EfficientNetB4CNN = None  # type: ignore

# ── HIPERPARAMETROS ───────────────────────────────────────────────────────────
EPOCHS_PHASE1 = 10
EPOCHS_PHASE2 = 38
BATCH = 8
LR_PHASE1 = 3e-4
LR_PHASE2 = 5e-5
ACCUM_STEPS = 8  # efectivo=64 igual que antes
PATIENCE = 12
FOCAL_GAMMA = 2.0

# Normalizacion de biometria para evitar que MSE domine la perdida.
# Valores maximos aproximados para cada campo → escala a [0,1]
BIO_NORM = torch.tensor([100.0, 400.0, 400.0, 100.0, 5000.0], dtype=torch.float32)

# ── BIOMETRIA PSEUDO-REAL POR PATOLOGIA ───────────────────────────────────────
BIO_PARAMS = {
    "normal":               (80, 280, 250, 60, 3100),
    "hidrocefalia":         (90, 340, 260, 61, 3000),
    "anencefalia":          (55, 160, 200, 55, 2100),
    "espina_bifida":        (79, 278, 248, 59, 2900),
    "labio_leporino":       (81, 282, 252, 61, 3150),
    "atresia_duodenal":     (80, 280, 255, 60, 2800),
    "cardiopatia_congenita":(82, 285, 260, 62, 2950),
    "oligohidramnios":      (75, 260, 230, 56, 2500),
    "polihidramnios":       (85, 300, 280, 63, 3400),
    "restriccion_crecimiento": (68, 240, 210, 52, 1900),
    "macrosomia_fetal":     (92, 320, 310, 70, 4600),
    "placenta_previa":      (81, 283, 253, 61, 3100),
    "preeclampsia_signos":  (80, 278, 249, 60, 2850),
    "muerte_fetal":         (78, 270, 240, 58, 2700),
    "embarazo_multiple":    (72, 255, 220, 55, 2400),
}


def gen_biometry(class_name: str) -> torch.Tensor:
    bpd, hc, ac, fl, peso = BIO_PARAMS.get(class_name, (80, 280, 250, 60, 3000))
    return torch.tensor(
        [float(np.random.normal(bpd, 3)), float(np.random.normal(hc, 10)),
         float(np.random.normal(ac, 10)), float(np.random.normal(fl, 3)),
         float(np.random.normal(peso, 150))],
        dtype=torch.float32,
    )


# ── FOCAL LOSS ────────────────────────────────────────────────────────────────
class FocalBCELoss(nn.Module):
    def __init__(self, gamma: float = 2.0, class_weights: torch.Tensor | None = None):
        super().__init__()
        self.gamma = gamma
        self.register_buffer("class_weights", class_weights)

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        bce = F.binary_cross_entropy_with_logits(logits, target, reduction="none")
        p_t = torch.exp(-bce)
        focal = ((1.0 - p_t) ** self.gamma) * bce
        if self.class_weights is not None:
            focal = focal * self.class_weights.to(focal.device)
        return focal.mean()


# ── DATASET ───────────────────────────────────────────────────────────────────
class FetalDataset(Dataset):
    def __init__(self, root_dir: str, transform=None):
        self.transform = transform
        self.samples = []
        if not os.path.isdir(root_dir):
            raise FileNotFoundError(f"Directorio no encontrado: {root_dir}")
        class_to_idx = {c: i for i, c in enumerate(PATHOLOGY_CLASSES)}
        total = 0
        for class_name in PATHOLOGY_CLASSES:
            class_dir = os.path.join(root_dir, class_name)
            if not os.path.isdir(class_dir):
                continue
            label = torch.zeros(len(PATHOLOGY_CLASSES), dtype=torch.float32)
            label[class_to_idx[class_name]] = 1.0
            for fname in sorted(os.listdir(class_dir)):
                if fname.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    self.samples.append((
                        os.path.join(class_dir, fname),
                        label.clone(),
                        gen_biometry(class_name),
                    ))
                    total += 1
        logger.info("  %s: %s imagenes | %s clases", root_dir, total, len(PATHOLOGY_CLASSES))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label, bio = self.samples[idx]
        img = Image.open(img_path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label, bio


# ── TRANSFORMACIONES ──────────────────────────────────────────────────────────
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

train_tf = transforms.Compose([
    transforms.Resize((384, 384)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.2),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.1),
    transforms.RandomRotation(10),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])

val_tf = transforms.Compose([
    transforms.Resize((384, 384)),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


# ── METRICAS ──────────────────────────────────────────────────────────────────
def compute_metrics(all_preds: list, all_targets: list) -> tuple[float, float, float]:
    preds   = np.vstack(all_preds)
    targets = np.vstack(all_targets)
    preds_bin = (preds > 0.5).astype(float)

    tp = np.sum((preds_bin == 1) & (targets == 1), axis=0)
    fn = np.sum((preds_bin == 0) & (targets == 1), axis=0)
    fp = np.sum((preds_bin == 1) & (targets == 0), axis=0)
    tn = np.sum((preds_bin == 0) & (targets == 0), axis=0)

    with np.errstate(invalid="ignore"):
        sens = np.where((tp + fn) > 0, tp / (tp + fn), np.nan)
        spec = np.where((tn + fp) > 0, tn / (tn + fp), np.nan)
    sensibilidad = float(np.nanmean(sens))
    especificidad = float(np.nanmean(spec))

    try:
        from sklearn.metrics import roc_auc_score
        valid = targets.sum(axis=0) > 0
        auc = roc_auc_score(targets[:, valid], preds[:, valid], average="macro") if valid.sum() >= 2 else float("nan")
    except Exception:
        auc = float("nan")

    return sensibilidad, especificidad, auc


def log_per_class_sensitivity(all_preds: list, all_targets: list) -> None:
    preds   = np.vstack(all_preds)
    targets = np.vstack(all_targets)
    preds_bin = (preds > 0.5).astype(float)
    for i, cls in enumerate(PATHOLOGY_CLASSES):
        tp = np.sum((preds_bin[:, i] == 1) & (targets[:, i] == 1))
        fn = np.sum((preds_bin[:, i] == 0) & (targets[:, i] == 1))
        s = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
        flag = " <<< BAJO" if not np.isnan(s) and s < 0.85 else ""
        logger.info("    %-30s sens=%.3f%s", cls, s, flag)


# ── PHASE HELPERS ─────────────────────────────────────────────────────────────
def freeze_backbone(model: EfficientNetB4CNN) -> None:
    for p in model.backbone.parameters():
        p.requires_grad = False


def unfreeze_backbone(model: EfficientNetB4CNN) -> None:
    for p in model.backbone.parameters():
        p.requires_grad = True


# ── ENTRENAMIENTO ─────────────────────────────────────────────────────────────
def run_epoch(
    model, loader, crit_path, crit_bio,
    optimizer, scaler, device, is_train: bool,
    accum_steps: int = 1,
) -> tuple[float, list, list]:
    model.train(is_train)
    total_loss = 0.0
    nan_batches = 0
    preds_all, tgts_all = [], []
    if is_train:
        optimizer.zero_grad(set_to_none=True)

    bio_norm = BIO_NORM.to(device)

    for step, (x, y_path, y_bio) in enumerate(loader):
        x = x.to(device, non_blocking=True)
        y_path = y_path.to(device, non_blocking=True)
        y_bio = y_bio.to(device, non_blocking=True)

        # Autocast solo en training — validacion siempre en FP32 para evitar NaN/Inf FP16
        amp_ctx = torch.amp.autocast("cuda") if (is_train and device.type == "cuda") else nullcontext()
        with amp_ctx:
            out_path, out_bio = model(x)

        out_path_f32 = out_path.float()
        out_bio_f32 = out_bio.float()

        # Biometria normalizada a [0,1] para evitar que MSE (escala mm/gramos) domine
        loss_bio = crit_bio(out_bio_f32 / bio_norm, y_bio / bio_norm)
        loss = crit_path(out_path_f32, y_path) + loss_bio * 0.1

        if is_train:
            if torch.isnan(loss) or torch.isinf(loss):
                nan_batches += 1
                optimizer.zero_grad(set_to_none=True)
                if nan_batches <= 3:
                    logger.warning("Batch %d: loss=NaN/Inf — saltando", step)
                continue

            loss_scaled = loss / accum_steps
            scaler.scale(loss_scaled).backward()
            if (step + 1) % accum_steps == 0 or (step + 1) == len(loader):
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
            total_loss += loss.item()
        else:
            if not (torch.isnan(loss) or torch.isinf(loss)):
                total_loss += loss.item()

        probs = torch.sigmoid(out_path_f32.detach()).cpu().numpy()
        preds_all.append(probs)
        tgts_all.append(y_path.cpu().numpy())

    if nan_batches > 0:
        logger.warning("Epoch con %d batches NaN/Inf saltados de %d totales", nan_batches, len(loader))
    valid_steps = max(len(loader) - nan_batches, 1) if is_train else max(len(loader), 1)
    avg_loss = total_loss / valid_steps
    return avg_loss, preds_all, tgts_all


def main():
    global PATHOLOGY_CLASSES, BIOMETRY_FIELDS, EfficientNetB4CNN  # noqa: PLW0603

    # Configurar logging DENTRO de main() — los workers del DataLoader en Windows
    # re-importan el modulo pero NO llaman a main(), por lo que no configuran logging
    _log_dir = os.path.dirname(os.path.abspath(__file__))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                os.path.join(_log_dir, "training_progress.log"),
                mode="w", encoding="utf-8",
            ),
        ],
    )

    try:
        from app.models import (  # noqa: PLC0415
            BIOMETRY_FIELDS as BF,
            PATHOLOGY_CLASSES as PC,
            EfficientNetB4CNN as CNN,
        )
        PATHOLOGY_CLASSES = PC
        BIOMETRY_FIELDS   = BF
        EfficientNetB4CNN = CNN
        logger.info("Modelo importado. Patologias: %s, Biometrias: %s",
                    len(PATHOLOGY_CLASSES), len(BIOMETRY_FIELDS))
    except ImportError as e:
        logging.error("Error importando modelo: %s", e)
        sys.exit(1)

    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if DEVICE.type == "cuda":
        # benchmark=False evita que cuDNN perfile algoritmos en el primer batch
        # (ese profiling puede tardar 5-10s y dispara el TDR de Windows a 2s)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = False
        torch.backends.cudnn.allow_tf32 = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.cuda.empty_cache()

    logger.info("=" * 70)
    logger.info("  FETAL MEDICAL AI — EfficientNet-B4 Produccion")
    logger.info("=" * 70)
    logger.info("  Dispositivo  : %s", DEVICE)
    if DEVICE.type == "cuda":
        logger.info("  GPU          : %s", torch.cuda.get_device_name(0))
        logger.info("  VRAM         : %.1f GB", torch.cuda.get_device_properties(0).total_memory / 1e9)
    logger.info("  Fases        : Phase1=%s epocas (backbone frozen) | Phase2=%s epocas (fine-tuning)", EPOCHS_PHASE1, EPOCHS_PHASE2)
    logger.info("  Batch        : %s (acum=%s -> efectivo=%s)", BATCH, ACCUM_STEPS, BATCH * ACCUM_STEPS)
    logger.info("  LR Phase1/2  : %s / %s", LR_PHASE1, LR_PHASE2)
    logger.info("  Focal Loss   : gamma=%.1f", FOCAL_GAMMA)
    logger.info("  AMP (FP16)   : %s", DEVICE.type == "cuda")
    logger.info("=" * 70)

    train_dir = os.path.join(os.path.dirname(__file__), "datasets_pathology", "train")
    val_dir   = os.path.join(os.path.dirname(__file__), "datasets_pathology", "validation")

    train_ds = FetalDataset(train_dir, transform=train_tf)
    val_ds   = FetalDataset(val_dir,   transform=val_tf)

    if len(train_ds) == 0:
        logger.error("Dataset de entrenamiento vacio. Verifica datasets_pathology/train/")
        return

    cls_counts: dict[int, int] = {}
    for _, lbl, _ in train_ds.samples:
        idx = int(lbl.argmax().item())
        cls_counts[idx] = cls_counts.get(idx, 0) + 1

    max_count = max(cls_counts.values())
    class_weights_list = [max_count / cls_counts.get(i, 1) for i in range(len(PATHOLOGY_CLASSES))]
    class_weights_norm = [w / sum(class_weights_list) * len(PATHOLOGY_CLASSES) for w in class_weights_list]
    class_weights_t = torch.tensor(class_weights_norm, dtype=torch.float32)

    sample_weights = torch.tensor(
        [1.0 / cls_counts.get(int(lbl.argmax().item()), 1) for _, lbl, _ in train_ds.samples],
        dtype=torch.float64,
    )
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(train_ds), replacement=True)

    logger.info("  Distribucion de clases (train):")
    for ci in sorted(cls_counts):
        logger.info("    %-30s %5d imgs  peso_focal=%.3f",
                    PATHOLOGY_CLASSES[ci], cls_counts[ci], class_weights_norm[ci])

    # num_workers=0 en Windows evita el bug de re-importacion del modulo __main__
    # en procesos DataLoader worker (spawn method). Sin workers el RTX 3090 sigue
    # siendo el cuello de botella, no la carga de datos.
    _nw = 0
    train_loader = DataLoader(train_ds, batch_size=BATCH, sampler=sampler,
                              num_workers=_nw, pin_memory=(DEVICE.type == "cuda"))
    val_loader   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False,
                              num_workers=_nw, pin_memory=(DEVICE.type == "cuda"))

    model = EfficientNetB4CNN(pretrained=True).to(DEVICE)
    total_params = sum(p.numel() for p in model.parameters())
    trainable   = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("  Parametros: %s total  |  %s entrenables", total_params, trainable)

    crit_path = FocalBCELoss(gamma=FOCAL_GAMMA, class_weights=class_weights_t).to(DEVICE)
    crit_bio  = nn.MSELoss()
    scaler    = torch.amp.GradScaler("cuda") if DEVICE.type == "cuda" else torch.amp.GradScaler("cpu", enabled=False)

    save_dir  = os.path.join(os.path.dirname(__file__), "trained_models")
    save_path = os.path.join(save_dir, "efficientnet_b4.pth")
    ckpt_dir  = os.path.join(save_dir, "checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)

    best_auc      = 0.0
    no_improve    = 0
    global_epoch  = 0

    # Warm-up GPU: fuerza la inicializacion de kernels cuDNN antes del training
    # Evita que el primer batch real tarde >2s y dispare el TDR de Windows
    if DEVICE.type == "cuda":
        logger.info("  Warm-up GPU (inicializando kernels cuDNN)...")
        model.eval()
        with torch.no_grad():
            dummy = torch.randn(BATCH, 3, 384, 384, device=DEVICE)
            with torch.amp.autocast("cuda"):
                _ = model(dummy)
        torch.cuda.synchronize()
        del dummy
        torch.cuda.empty_cache()
        logger.info("  Warm-up completado.")
        model.train()

    # ── PHASE 1: solo cabezas, backbone congelado ─────────────────────────────
    logger.info("")
    logger.info("  === PHASE 1: Backbone congelado, entrenando solo cabezas ===")
    freeze_backbone(model)
    trainable_p1 = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("  Parametros entrenables Phase 1: %s", trainable_p1)

    optimizer_p1  = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=LR_PHASE1, weight_decay=1e-4)
    scheduler_p1  = optim.lr_scheduler.CosineAnnealingLR(optimizer_p1, T_max=EPOCHS_PHASE1)

    for epoch in range(1, EPOCHS_PHASE1 + 1):
        global_epoch += 1
        if DEVICE.type == "cuda":
            torch.cuda.empty_cache()
        t0 = time.time()

        train_loss, _, _ = run_epoch(model, train_loader, crit_path, crit_bio, optimizer_p1, scaler, DEVICE, is_train=True, accum_steps=ACCUM_STEPS)
        scheduler_p1.step()

        with torch.no_grad():
            val_loss, preds_all, tgts_all = run_epoch(model, val_loader, crit_path, crit_bio, optimizer_p1, scaler, DEVICE, is_train=False)

        sens, spec, auc = compute_metrics(preds_all, tgts_all)
        elapsed = time.time() - t0
        auc_str = f"{auc:.4f}" if not np.isnan(auc) else "N/D"
        logger.info("P1 Epoch %2d/%d [%.0fs]  Train:%.4f  Val:%.4f  Sens:%.4f  Spec:%.4f  AUC:%s",
                    epoch, EPOCHS_PHASE1, elapsed, train_loss, val_loss, sens, spec, auc_str)

        if not np.isnan(auc) and auc > best_auc:
            best_auc = auc
            torch.save(model.state_dict(), save_path)
            logger.info("  [BEST] AUC=%.4f guardado", best_auc)

    # ── PHASE 2: fine-tuning completo ─────────────────────────────────────────
    logger.info("")
    logger.info("  === PHASE 2: Fine-tuning completo (backbone desbloqueado) ===")
    unfreeze_backbone(model)
    trainable_p2 = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("  Parametros entrenables Phase 2: %s", trainable_p2)

    optimizer_p2 = optim.AdamW(model.parameters(), lr=LR_PHASE2, weight_decay=1e-4)
    scheduler_p2 = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer_p2, T_0=EPOCHS_PHASE2 // 3, T_mult=1, eta_min=1e-6)

    for epoch in range(1, EPOCHS_PHASE2 + 1):
        global_epoch += 1
        if DEVICE.type == "cuda":
            torch.cuda.empty_cache()
        t0 = time.time()

        train_loss, _, _ = run_epoch(model, train_loader, crit_path, crit_bio, optimizer_p2, scaler, DEVICE, is_train=True, accum_steps=ACCUM_STEPS)
        scheduler_p2.step()

        with torch.no_grad():
            val_loss, preds_all, tgts_all = run_epoch(model, val_loader, crit_path, crit_bio, optimizer_p2, scaler, DEVICE, is_train=False)

        sens, spec, auc = compute_metrics(preds_all, tgts_all)
        elapsed = time.time() - t0
        auc_str = f"{auc:.4f}" if not np.isnan(auc) else "N/D"
        logger.info("P2 Epoch %2d/%d [%.0fs]  Train:%.4f  Val:%.4f  Sens:%.4f  Spec:%.4f  AUC:%s",
                    epoch, EPOCHS_PHASE2, elapsed, train_loss, val_loss, sens, spec, auc_str)

        if not np.isnan(auc) and auc > best_auc:
            best_auc = auc
            no_improve = 0
            torch.save(model.state_dict(), save_path)
            logger.info("  [BEST] AUC=%.4f guardado", best_auc)
        else:
            no_improve += 1

        if epoch % 5 == 0:
            ckpt = os.path.join(ckpt_dir, f"ckpt_p2_ep{epoch:03d}_auc{auc_str}.pth")
            torch.save(model.state_dict(), ckpt)
            logger.info("  [CKPT] Checkpoint guardado: %s", os.path.basename(ckpt))

        if sens >= 0.92 and not np.isnan(auc) and auc >= 0.90:
            logger.info("  [OBJETIVO] METRICAS CLINICAS ALCANZADAS: Sens>=0.92, AUC>=0.90")

        if no_improve >= PATIENCE:
            logger.info("  [EARLY STOP] Sin mejora en %s epocas. Deteniendo Phase 2.", PATIENCE)
            break

    torch.save(model.state_dict(), save_path)
    logger.info("")
    logger.info("=" * 70)
    logger.info("  Entrenamiento finalizado.")
    logger.info("  Mejor AUC-ROC : %.4f", best_auc)
    logger.info("  Pesos guardados: %s", save_path)
    logger.info("=" * 70)

    logger.info("")
    logger.info("  Sensibilidad por clase (ultimo epoch):")
    log_per_class_sensitivity(preds_all, tgts_all)


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # requerido en Windows para PyInstaller + spawn
    try:
        main()
    except KeyboardInterrupt:
        print("Entrenamiento interrumpido por usuario (Ctrl+C)")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
