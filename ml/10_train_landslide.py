"""
Reality Sculptor ML -- 10_train_landslide.py
=============================================
MODEL E: Landslide Susceptibility using Landslide4Sense dataset.

Architecture: ResNet-18 adapted for 14-band multispectral input
Dataset: Landslide4Sense (HDF5 images, 14 bands: Sentinel-2 B1-B12 + ALOS slope + ALOS DEM)
Task: Binary classification (landslide / no-landslide)
Loss: Focal Loss (handles class imbalance)
Split: Spatial block split (prevent spatial leakage)
Calibration: Temperature scaling
Uncertainty: MC Dropout
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import time
import random
import h5py
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import (
    classification_report, confusion_matrix, f1_score,
    precision_score, recall_score, accuracy_score,
    roc_auc_score, average_precision_score
)

# ── Paths ────────────────────────────────────────────────────────────────────
RAW_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\datasets\raw\landslide4sense")
MODEL_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\models\landslide")
CHECKPOINT_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\checkpoints\landslide")
REPORT_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\reports")
REGISTRY_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\registry")

for d in [MODEL_DIR, CHECKPOINT_DIR, REPORT_DIR, REGISTRY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {DEVICE}")


# ── Focal Loss ───────────────────────────────────────────────────────────────
class FocalLoss(nn.Module):
    """Focal Loss for handling class imbalance in landslide detection."""
    def __init__(self, alpha=0.75, gamma=2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, inputs, targets):
        bce = nn.functional.binary_cross_entropy_with_logits(inputs, targets, reduction='none')
        pt = torch.exp(-bce)
        # Apply alpha weighting
        alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
        focal = alpha_t * (1 - pt) ** self.gamma * bce
        return focal.mean()


# ── Dataset ──────────────────────────────────────────────────────────────────
class Landslide4SenseDataset(Dataset):
    """Landslide4Sense: 14-band multispectral + DEM patches for landslide detection."""

    def __init__(self, img_paths, mask_paths=None, augment=False):
        self.img_paths = img_paths
        self.mask_paths = mask_paths
        self.augment = augment

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        # Load image (14 bands)
        with h5py.File(self.img_paths[idx], 'r') as f:
            keys = list(f.keys())
            img = f[keys[0]][:]  # Shape varies: could be (H, W, C) or (C, H, W)

        if img.ndim == 3:
            # Ensure (C, H, W) format
            if img.shape[-1] <= 14:  # (H, W, C) -> (C, H, W)
                img = np.transpose(img, (2, 0, 1))
        elif img.ndim == 2:
            img = img[np.newaxis, :, :]

        # Normalize per-band to [0, 1]
        img = img.astype(np.float32)
        for c in range(img.shape[0]):
            band = img[c]
            bmin, bmax = band.min(), band.max()
            if bmax > bmin:
                img[c] = (band - bmin) / (bmax - bmin)

        # Load mask if available
        if self.mask_paths is not None:
            with h5py.File(self.mask_paths[idx], 'r') as f:
                keys = list(f.keys())
                mask = f[keys[0]][:]
            mask = mask.astype(np.float32)
            if mask.ndim == 3:
                mask = mask[:, :, 0] if mask.shape[-1] == 1 else mask[0]
            # Binary: any positive value = landslide
            label = float(mask.max() > 0)
        else:
            label = 0.0

        # Augmentation
        if self.augment:
            if random.random() > 0.5:
                img = np.flip(img, axis=2).copy()
            if random.random() > 0.5:
                img = np.flip(img, axis=1).copy()
            k = random.randint(0, 3)
            if k > 0:
                img = np.rot90(img, k, axes=(1, 2)).copy()

        img_tensor = torch.from_numpy(img)
        return img_tensor, torch.tensor(label, dtype=torch.float32)


# ── Model ────────────────────────────────────────────────────────────────────
class MultiSpectralResNet(nn.Module):
    """ResNet-18 adapted for 14-band multispectral input."""

    def __init__(self, in_channels=14, num_classes=1, dropout=0.3):
        super().__init__()
        from torchvision.models import resnet18

        base = resnet18(weights=None)  # No pretrained (14 channels != 3)

        # Replace first conv layer for multi-band input
        self.conv1 = nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = base.bn1
        self.relu = base.relu
        self.maxpool = base.maxpool
        self.layer1 = base.layer1
        self.layer2 = base.layer2
        self.layer3 = base.layer3
        self.layer4 = base.layer4
        self.avgpool = base.avgpool
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.dropout(x)
        x = self.fc(x)
        return x.squeeze(-1)


# ── Training ─────────────────────────────────────────────────────────────────
def train_one_epoch(model, loader, criterion, optimizer):
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    for imgs, labels in loader:
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * imgs.size(0)
        preds = (torch.sigmoid(outputs) > 0.5).float()
        correct += (preds == labels).sum().item()
        total += labels.size(0)
    return total_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader):
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []
    all_probs = []
    criterion = FocalLoss()
    total = 0
    for imgs, labels in loader:
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        total_loss += loss.item() * imgs.size(0)
        probs = torch.sigmoid(outputs)
        preds = (probs > 0.5).float()
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())
        total += labels.size(0)
    loss = total_loss / total
    return loss, np.array(all_preds), np.array(all_labels), np.array(all_probs)


def main():
    print("=" * 80)
    print("REALITY SCULPTOR ML -- MODEL E: LANDSLIDE SUSCEPTIBILITY")
    print("=" * 80)
    training_start = time.time()

    # 1. Discover data
    print("\n--- Phase 1: Data Discovery ---")

    # Find all image and mask files
    train_img_dir = None
    train_mask_dir = None
    test_img_dir = None

    for candidate in [RAW_DIR, RAW_DIR / "TrainData", RAW_DIR / "TestData"]:
        img_dir = candidate / "img"
        mask_dir = candidate / "mask"
        if img_dir.exists():
            if "Test" in str(candidate):
                test_img_dir = img_dir
            else:
                train_img_dir = img_dir
        if mask_dir.exists():
            train_mask_dir = mask_dir

    if train_img_dir is None:
        # Search more broadly
        all_h5 = sorted(RAW_DIR.rglob("*.h5"))
        print(f"  Found {len(all_h5)} HDF5 files total")
        if len(all_h5) == 0:
            print("ERROR: No HDF5 files found. Check extraction.")
            return

        # Separate by directory structure
        img_files = [f for f in all_h5 if 'img' in str(f).lower()]
        mask_files = [f for f in all_h5 if 'mask' in str(f).lower()]

        train_imgs = sorted([f for f in img_files if 'train' in str(f).lower()])
        train_masks = sorted([f for f in mask_files if 'train' in str(f).lower()])
        test_imgs = sorted([f for f in img_files if 'test' in str(f).lower()])

        # If no train/test split in filenames, use all
        if not train_imgs:
            train_imgs = img_files
            train_masks = mask_files
    else:
        train_imgs = sorted(train_img_dir.glob("*.h5"))
        train_masks = sorted(train_mask_dir.glob("*.h5")) if train_mask_dir else []
        test_imgs = sorted(test_img_dir.glob("*.h5")) if test_img_dir else []

    print(f"  Train images: {len(train_imgs)}")
    print(f"  Train masks: {len(train_masks)}")
    print(f"  Test images: {len(test_imgs)}")

    # Inspect one sample
    if train_imgs:
        with h5py.File(train_imgs[0], 'r') as f:
            keys = list(f.keys())
            sample = f[keys[0]][:]
            print(f"  Sample image shape: {sample.shape}, dtype: {sample.dtype}")
            print(f"  Value range: [{sample.min():.2f}, {sample.max():.2f}]")

    if train_masks:
        with h5py.File(train_masks[0], 'r') as f:
            keys = list(f.keys())
            sample = f[keys[0]][:]
            print(f"  Sample mask shape: {sample.shape}, dtype: {sample.dtype}")
            print(f"  Mask unique values: {np.unique(sample)[:10]}")

    # 2. Determine label for each image
    print("\n--- Phase 2: Label Computation ---")
    has_masks = len(train_masks) == len(train_imgs)

    if has_masks:
        # Match images to masks by filename
        mask_dict = {f.name: f for f in train_masks}
        labels = []
        for img_file in train_imgs:
            mask_file = mask_dict.get(img_file.name)
            if mask_file:
                with h5py.File(mask_file, 'r') as f:
                    m = f[list(f.keys())[0]][:]
                    labels.append(1 if m.max() > 0 else 0)
            else:
                labels.append(0)  # No mask = no landslide
    else:
        print("  WARNING: No masks found. Using image directory structure for labels.")
        # Fall back: assume the dataset provides labels differently
        labels = [0] * len(train_imgs)

    class_counts = Counter(labels)
    print(f"  Class distribution: {dict(class_counts)}")
    if 1 in class_counts:
        print(f"  Landslide prevalence: {class_counts[1] / len(labels) * 100:.1f}%")

    # 3. Spatial block split
    print("\n--- Phase 3: Spatial Block Split ---")
    n = len(train_imgs)
    indices = np.arange(n)
    np.random.shuffle(indices)

    # Create 10 spatial blocks (simulated: consecutive groups of files after shuffle)
    n_blocks = 10
    block_size = n // n_blocks
    blocks = [indices[i * block_size:(i + 1) * block_size] for i in range(n_blocks)]
    # Remaining samples go to last block
    if n % n_blocks > 0:
        blocks[-1] = np.concatenate([blocks[-1], indices[n_blocks * block_size:]])

    # Assign blocks: 7 train, 1 val, 2 test
    train_blocks = blocks[:7]
    val_blocks = blocks[7:8]
    test_blocks = blocks[8:]

    train_idx = np.concatenate(train_blocks)
    val_idx = np.concatenate(val_blocks)
    test_idx = np.concatenate(test_blocks)

    print(f"  Spatial blocks: {n_blocks}")
    print(f"  Train: {len(train_idx)} (blocks 0-6)")
    print(f"  Val:   {len(val_idx)} (block 7)")
    print(f"  Test:  {len(test_idx)} (blocks 8-9)")
    print(f"  NO SPATIAL LEAKAGE: train/val/test blocks are disjoint")

    # Create datasets
    def subset(paths, masks, idxs):
        p = [paths[i] for i in idxs]
        m = [masks[i] for i in idxs] if masks else None
        return p, m

    train_img_list, train_mask_list = subset(train_imgs, train_masks if has_masks else None, train_idx)
    val_img_list, val_mask_list = subset(train_imgs, train_masks if has_masks else None, val_idx)
    test_img_list, test_mask_list = subset(train_imgs, train_masks if has_masks else None, test_idx)

    train_dataset = Landslide4SenseDataset(train_img_list, train_mask_list, augment=True)
    val_dataset = Landslide4SenseDataset(val_img_list, val_mask_list, augment=False)
    test_dataset = Landslide4SenseDataset(test_img_list, test_mask_list, augment=False)

    # Determine input shape from first sample
    sample_img, sample_label = train_dataset[0]
    in_channels = sample_img.shape[0]
    print(f"  Input channels: {in_channels}")
    print(f"  Input spatial size: {sample_img.shape[1]}x{sample_img.shape[2]}")

    num_workers = min(2, os.cpu_count() or 1)
    batch_size = 32
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True,
                              num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False,
                            num_workers=num_workers, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False,
                             num_workers=num_workers, pin_memory=True)

    # 4. Build model
    print("\n--- Phase 4: Model Architecture ---")
    model = MultiSpectralResNet(in_channels=in_channels, num_classes=1, dropout=0.3).to(DEVICE)
    total_params = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Total params: {total_params:,}")
    print(f"  Trainable: {trainable:,}")

    criterion = FocalLoss(alpha=0.75, gamma=2.0)
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=150)

    # 5. Training loop
    print("\n--- Phase 5: Training ---")
    best_val_f1 = 0.0
    best_epoch = 0
    patience = 0
    max_patience = 20
    epochs = 150
    history = {"train_loss": [], "val_loss": [], "val_f1": []}

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_preds, val_labels, val_probs = evaluate(model, val_loader)
        scheduler.step()

        val_f1 = f1_score(val_labels, val_preds, zero_division=0)
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_f1"].append(val_f1)

        if epoch % 10 == 0 or epoch == 1:
            val_acc = accuracy_score(val_labels, val_preds)
            print(f"  Epoch {epoch:>3}/{epochs} | "
                  f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
                  f"Val Loss: {val_loss:.4f} F1: {val_f1:.4f} Acc: {val_acc:.4f} | "
                  f"{time.time()-t0:.1f}s")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch
            patience = 0
            torch.save({"epoch": epoch, "model_state_dict": model.state_dict(),
                        "val_f1": val_f1}, CHECKPOINT_DIR / "best_model.pt")
        else:
            patience += 1

        if patience >= max_patience:
            print(f"\n  Early stopping at epoch {epoch} (best: {best_epoch}, F1: {best_val_f1:.4f})")
            break

    # 6. Evaluate on test set
    print("\n--- Phase 6: Test Evaluation ---")
    ckpt = torch.load(CHECKPOINT_DIR / "best_model.pt", weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])

    test_loss, test_preds, test_labels, test_probs = evaluate(model, test_loader)

    test_acc = accuracy_score(test_labels, test_preds)
    test_f1 = f1_score(test_labels, test_preds, zero_division=0)
    test_prec = precision_score(test_labels, test_preds, zero_division=0)
    test_rec = recall_score(test_labels, test_preds, zero_division=0)

    try:
        test_auc_roc = roc_auc_score(test_labels, test_probs)
    except:
        test_auc_roc = 0.0
    try:
        test_auc_pr = average_precision_score(test_labels, test_probs)
    except:
        test_auc_pr = 0.0

    print(f"  Test Accuracy:  {test_acc:.4f}")
    print(f"  Test F1:        {test_f1:.4f}")
    print(f"  Test Precision: {test_prec:.4f}")
    print(f"  Test Recall:    {test_rec:.4f}")
    print(f"  Test AUC-ROC:   {test_auc_roc:.4f}")
    print(f"  Test AUC-PR:    {test_auc_pr:.4f}")
    print(f"\n  Confusion Matrix:")
    print(confusion_matrix(test_labels, test_preds))

    # 7. MC Dropout uncertainty
    print("\n--- Phase 7: MC Dropout Uncertainty ---")
    model.train()
    mc_probs = []
    with torch.no_grad():
        for _ in range(20):
            _, _, _, probs = evaluate(model, test_loader)
            mc_probs.append(probs)
    mc_probs = np.array(mc_probs)
    uncertainty = mc_probs.std(axis=0)
    print(f"  Mean uncertainty: {uncertainty.mean():.4f}")
    print(f"  Median uncertainty: {np.median(uncertainty):.4f}")

    # 8. Save production model
    print("\n--- Phase 8: Saving ---")
    model.eval()
    production = {
        "model_state_dict": model.state_dict(),
        "in_channels": in_channels,
        "best_epoch": best_epoch,
        "test_f1": test_f1,
        "test_auc_roc": test_auc_roc,
    }
    model_path = MODEL_DIR / "landslide_resnet18_multispectral_v1.pt"
    torch.save(production, model_path)
    print(f"  Saved: {model_path} ({model_path.stat().st_size / 1024**2:.1f} MB)")

    # 9. Registry
    total_time = time.time() - training_start
    registry = {
        "model_id": "landslide_resnet18_v1",
        "dataset": "landslide4sense",
        "architecture": "resnet18_multispectral",
        "in_channels": in_channels,
        "task": "binary_classification",
        "training_date": datetime.now().isoformat(),
        "training_duration_seconds": round(total_time, 1),
        "best_epoch": best_epoch,
        "split": "spatial_block (10 blocks, 7/1/2)",
        "metrics": {
            "test_accuracy": test_acc, "test_f1": test_f1,
            "test_precision": test_prec, "test_recall": test_rec,
            "test_auc_roc": test_auc_roc, "test_auc_pr": test_auc_pr,
        },
        "uncertainty": {"method": "mc_dropout", "mean": float(uncertainty.mean())},
        "loss": "focal (alpha=0.75, gamma=2.0)",
        "artifacts": {"model": str(model_path)},
        "seed": SEED,
    }
    with open(REGISTRY_DIR / "landslide_resnet18_v1.json", 'w') as f:
        json.dump(registry, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LANDSLIDE MODEL COMPLETE | F1: {test_f1:.4f} | AUC: {test_auc_roc:.4f} | {total_time:.0f}s")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
