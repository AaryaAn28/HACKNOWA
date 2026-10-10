"""
Reality Sculptor ML -- 07_train_landcover.py
=============================================
MODEL B: Land-Cover Classification using EuroSAT dataset.

Architecture: ResNet-18 (transfer learning from ImageNet)
Dataset: EuroSAT (27,000 Sentinel-2 satellite images, 10 classes)
Training: 150 epochs with early stopping, cosine annealing LR
Validation: Stratified split preserving class distribution
Calibration: Temperature scaling for calibrated probabilities
Uncertainty: MC Dropout at inference time

Classes: AnnualCrop, Forest, HerbaceousVegetation, Highway,
         Industrial, Pasture, PermanentCrop, Residential, River, SeaLake
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import time
import random
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, Subset
from torchvision import transforms, models

from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix, f1_score,
    precision_score, recall_score, accuracy_score
)

# ── Paths ────────────────────────────────────────────────────────────────────
RAW_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\datasets\raw")
MODEL_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\models\landcover")
CHECKPOINT_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\checkpoints\landcover")
REPORT_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\reports")
REGISTRY_DIR = Path(r"C:\Users\Aryan kumar\Downloads\reality-sculptor\ml\registry")

for d in [MODEL_DIR, CHECKPOINT_DIR, REPORT_DIR, REGISTRY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Reproducibility ─────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

# ── Configuration ────────────────────────────────────────────────────────────
CONFIG = {
    "model_id": "landcover_resnet18_v1",
    "architecture": "resnet18_transfer",
    "dataset": "eurosat",
    "num_classes": 10,
    "classes": [
        "AnnualCrop", "Forest", "HerbaceousVegetation", "Highway",
        "Industrial", "Pasture", "PermanentCrop", "Residential",
        "River", "SeaLake"
    ],
    "input_size": 64,
    "batch_size": 64,
    "epochs": 150,
    "early_stopping_patience": 20,
    "lr": 1e-3,
    "weight_decay": 1e-4,
    "seed": SEED,
    "device": "cuda" if torch.cuda.is_available() else "cpu",
}

DEVICE = torch.device(CONFIG["device"])
print(f"Using device: {DEVICE}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# ── Dataset ──────────────────────────────────────────────────────────────────
class EuroSATDataset(Dataset):
    """EuroSAT satellite land-cover classification dataset."""
    
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img = Image.open(self.image_paths[idx]).convert("RGB")
        label = self.labels[idx]
        
        if self.transform:
            img = self.transform(img)
        
        return img, label


def load_eurosat_data():
    """Load EuroSAT dataset from extracted directory."""
    eurosat_dir = RAW_DIR / "eurosat" / "EuroSAT"
    
    if not eurosat_dir.exists():
        print(f"EuroSAT directory not found at {eurosat_dir}")
        print("Checking alternative paths...")
        alt = RAW_DIR / "eurosat"
        if alt.exists():
            subdirs = [d for d in alt.iterdir() if d.is_dir()]
            print(f"  Found subdirs: {[d.name for d in subdirs]}")
            # Try to find the right one
            for sub in subdirs:
                if any((sub / c).exists() for c in CONFIG["classes"]):
                    eurosat_dir = sub
                    break
    
    print(f"Loading EuroSAT from: {eurosat_dir}")
    
    image_paths = []
    labels = []
    class_to_idx = {cls: i for i, cls in enumerate(CONFIG["classes"])}
    
    for cls_name, cls_idx in class_to_idx.items():
        cls_dir = eurosat_dir / cls_name
        if not cls_dir.exists():
            print(f"  WARNING: Class directory not found: {cls_dir}")
            continue
        
        files = sorted(cls_dir.glob("*.jpg"))
        if not files:
            files = sorted(cls_dir.glob("*.tif"))
        if not files:
            files = sorted(cls_dir.glob("*.png"))
        
        print(f"  {cls_name}: {len(files)} images")
        for f in files:
            image_paths.append(str(f))
            labels.append(cls_idx)
    
    print(f"  Total: {len(image_paths)} images across {len(class_to_idx)} classes")
    return image_paths, labels


def create_splits(image_paths, labels):
    """Create stratified train/val/test splits."""
    # First split: train+val vs test (85/15)
    train_val_paths, test_paths, train_val_labels, test_labels = train_test_split(
        image_paths, labels, test_size=0.15, random_state=SEED, stratify=labels
    )
    
    # Second split: train vs val from train_val (82.35/17.65 of remaining = 70/15 of total)
    train_paths, val_paths, train_labels, val_labels = train_test_split(
        train_val_paths, train_val_labels, test_size=0.176, random_state=SEED, stratify=train_val_labels
    )
    
    print(f"\n  Split sizes:")
    print(f"    Train: {len(train_paths)} ({len(train_paths)/len(image_paths)*100:.1f}%)")
    print(f"    Val:   {len(val_paths)} ({len(val_paths)/len(image_paths)*100:.1f}%)")
    print(f"    Test:  {len(test_paths)} ({len(test_paths)/len(image_paths)*100:.1f}%)")
    
    # Verify class distribution
    for name, lbls in [("Train", train_labels), ("Val", val_labels), ("Test", test_labels)]:
        dist = Counter(lbls)
        print(f"    {name} class dist: {dict(sorted(dist.items()))}")
    
    return (train_paths, train_labels), (val_paths, val_labels), (test_paths, test_labels)


# ── Transforms ───────────────────────────────────────────────────────────────
def get_transforms():
    """Create train/val transforms with data augmentation."""
    train_transform = transforms.Compose([
        transforms.Resize((CONFIG["input_size"], CONFIG["input_size"])),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((CONFIG["input_size"], CONFIG["input_size"])),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    return train_transform, val_transform


# ── Model ────────────────────────────────────────────────────────────────────
def build_model():
    """Build ResNet-18 with transfer learning."""
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    
    # Freeze early layers (conv1, bn1, layer1, layer2)
    for name, param in model.named_parameters():
        if any(n in name for n in ['conv1', 'bn1', 'layer1', 'layer2']):
            param.requires_grad = False
    
    # Replace classifier head
    num_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(num_features, CONFIG["num_classes"])
    )
    
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"  Model: ResNet-18 (transfer)")
    print(f"  Total params: {total:,}")
    print(f"  Trainable params: {trainable:,} ({trainable/total*100:.1f}%)")
    
    return model.to(DEVICE)


# ── Temperature Scaling for Calibration ──────────────────────────────────────
class TemperatureScaler(nn.Module):
    """Post-hoc temperature scaling for calibrated probabilities."""
    
    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)
    
    def forward(self, logits):
        return logits / self.temperature


def calibrate_temperature(model, val_loader):
    """Learn optimal temperature on validation set."""
    model.eval()
    scaler = TemperatureScaler().to(DEVICE)
    optimizer_t = optim.LBFGS([scaler.temperature], lr=0.01, max_iter=50)
    criterion = nn.CrossEntropyLoss()
    
    # Collect all val logits
    all_logits = []
    all_labels = []
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            logits = model(images)
            all_logits.append(logits)
            all_labels.append(labels)
    
    all_logits = torch.cat(all_logits)
    all_labels = torch.cat(all_labels)
    
    def eval_fn():
        optimizer_t.zero_grad()
        scaled_logits = scaler(all_logits)
        loss = criterion(scaled_logits, all_labels)
        loss.backward()
        return loss
    
    optimizer_t.step(eval_fn)
    
    optimal_temp = scaler.temperature.item()
    print(f"  Optimal temperature: {optimal_temp:.4f}")
    return optimal_temp


# ── Training Loop ────────────────────────────────────────────────────────────
def train_one_epoch(model, train_loader, criterion, optimizer, epoch):
    """Train for one epoch."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for batch_idx, (images, labels) in enumerate(train_loader):
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
    
    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc


@torch.no_grad()
def evaluate(model, data_loader, enable_dropout=False):
    """Evaluate model on a dataset."""
    model.eval()
    if enable_dropout:
        for m in model.modules():
            if isinstance(m, nn.Dropout):
                m.train()
    running_loss = 0.0
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    all_probs = []
    criterion = nn.CrossEntropyLoss()
    
    for images, labels in data_loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        running_loss += loss.item() * images.size(0)
        probs = torch.softmax(outputs, dim=1)
        _, predicted = outputs.max(1)
        
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())
    
    loss = running_loss / total
    acc = correct / total
    return loss, acc, np.array(all_preds), np.array(all_labels), np.array(all_probs)


def main():
    print("=" * 80)
    print("REALITY SCULPTOR ML -- MODEL B: LAND-COVER CLASSIFICATION")
    print("=" * 80)
    print(f"Training started: {datetime.now().isoformat()}")
    print(f"Config: {json.dumps({k:v for k,v in CONFIG.items() if k != 'classes'}, indent=2)}")
    
    training_start = time.time()
    
    # 1. Load data
    print("\n--- Phase 1: Data Loading ---")
    image_paths, labels = load_eurosat_data()
    
    if len(image_paths) == 0:
        print("ERROR: No images found. Check dataset extraction.")
        return
    
    # 2. Create splits
    print("\n--- Phase 2: Creating Stratified Splits ---")
    (train_paths, train_labels), (val_paths, val_labels), (test_paths, test_labels) = \
        create_splits(image_paths, labels)
    
    # 3. Build datasets and loaders
    print("\n--- Phase 3: Building DataLoaders ---")
    train_transform, val_transform = get_transforms()
    
    train_dataset = EuroSATDataset(train_paths, train_labels, train_transform)
    val_dataset = EuroSATDataset(val_paths, val_labels, val_transform)
    test_dataset = EuroSATDataset(test_paths, test_labels, val_transform)
    
    num_workers = min(4, os.cpu_count() or 1)
    train_loader = DataLoader(train_dataset, batch_size=CONFIG["batch_size"],
                              shuffle=True, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=CONFIG["batch_size"],
                            shuffle=False, num_workers=num_workers, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=CONFIG["batch_size"],
                             shuffle=False, num_workers=num_workers, pin_memory=True)
    
    print(f"  Train batches: {len(train_loader)}")
    print(f"  Val batches: {len(val_loader)}")
    print(f"  Test batches: {len(test_loader)}")
    
    # 4. Build model
    print("\n--- Phase 4: Model Architecture ---")
    model = build_model()
    
    # 5. Training setup
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=CONFIG["lr"],
        weight_decay=CONFIG["weight_decay"]
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=CONFIG["epochs"])
    
    # 6. Training loop with early stopping
    print("\n--- Phase 5: Training ---")
    best_val_acc = 0.0
    best_val_loss = float('inf')
    best_epoch = 0
    patience_counter = 0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "lr": []}
    
    for epoch in range(1, CONFIG["epochs"] + 1):
        epoch_start = time.time()
        
        # Train
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, epoch)
        
        # Validate
        val_loss, val_acc, val_preds, val_labels_arr, val_probs = evaluate(model, val_loader)
        
        # Learning rate step
        current_lr = optimizer.param_groups[0]['lr']
        scheduler.step()
        
        # Record history
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["lr"].append(current_lr)
        
        epoch_time = time.time() - epoch_start
        
        # Print progress every 5 epochs
        if epoch % 5 == 0 or epoch == 1:
            val_f1 = f1_score(val_labels_arr, val_preds, average='macro')
            print(f"  Epoch {epoch:>3}/{CONFIG['epochs']} | "
                  f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
                  f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} F1: {val_f1:.4f} | "
                  f"LR: {current_lr:.6f} | {epoch_time:.1f}s")
        
        # Best model checkpoint
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_val_loss = val_loss
            best_epoch = epoch
            patience_counter = 0
            
            # Save best checkpoint
            checkpoint = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_acc": val_acc,
                "val_loss": val_loss,
                "config": CONFIG,
            }
            torch.save(checkpoint, CHECKPOINT_DIR / "best_model.pt")
        else:
            patience_counter += 1
        
        # Early stopping
        if patience_counter >= CONFIG["early_stopping_patience"]:
            print(f"\n  Early stopping at epoch {epoch} (patience {CONFIG['early_stopping_patience']})")
            print(f"  Best epoch: {best_epoch} with val_acc: {best_val_acc:.4f}")
            break
        
        # Save periodic checkpoint every 25 epochs
        if epoch % 25 == 0:
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_acc": val_acc,
            }, CHECKPOINT_DIR / f"checkpoint_epoch_{epoch}.pt")
    
    # 7. Load best model and evaluate on test set
    print("\n--- Phase 6: Final Evaluation on Test Set ---")
    best_ckpt = torch.load(CHECKPOINT_DIR / "best_model.pt", weights_only=False)
    model.load_state_dict(best_ckpt["model_state_dict"])
    
    test_loss, test_acc, test_preds, test_labels_arr, test_probs = evaluate(model, test_loader)
    
    # Classification report
    report = classification_report(test_labels_arr, test_preds,
                                    target_names=CONFIG["classes"], output_dict=True)
    report_str = classification_report(test_labels_arr, test_preds,
                                        target_names=CONFIG["classes"])
    
    print(f"\n  Test Accuracy: {test_acc:.4f}")
    print(f"  Test Loss: {test_loss:.4f}")
    print(f"  Test Macro F1: {report['macro avg']['f1-score']:.4f}")
    print(f"  Test Weighted F1: {report['weighted avg']['f1-score']:.4f}")
    print(f"\n{report_str}")
    
    # Confusion matrix
    cm = confusion_matrix(test_labels_arr, test_preds)
    print("\n  Confusion Matrix:")
    print(cm)
    
    # 8. Temperature scaling calibration
    print("\n--- Phase 7: Temperature Scaling Calibration ---")
    optimal_temp = calibrate_temperature(model, val_loader)
    
    # 9. MC Dropout uncertainty estimation
    print("\n--- Phase 8: MC Dropout Uncertainty Estimation ---")
    n_mc_samples = 20
    mc_predictions = []
    
    with torch.no_grad():
        for _ in range(n_mc_samples):
            _, _, preds, _, probs = evaluate(model, test_loader, enable_dropout=True)
            mc_predictions.append(probs)
    
    mc_predictions = np.array(mc_predictions)  # (n_mc, n_samples, n_classes)
    mean_probs = mc_predictions.mean(axis=0)
    epistemic_uncertainty = mc_predictions.std(axis=0).mean(axis=1)  # Per-sample uncertainty
    
    print(f"  MC Dropout samples: {n_mc_samples}")
    print(f"  Mean epistemic uncertainty: {epistemic_uncertainty.mean():.4f}")
    print(f"  Median epistemic uncertainty: {np.median(epistemic_uncertainty):.4f}")
    print(f"  Max epistemic uncertainty: {epistemic_uncertainty.max():.4f}")
    
    # 10. Save production model
    print("\n--- Phase 9: Saving Production Model ---")
    model.eval()
    production_model = {
        "model_state_dict": model.state_dict(),
        "config": CONFIG,
        "temperature": optimal_temp,
        "best_epoch": best_epoch,
        "test_accuracy": test_acc,
        "test_f1_macro": report['macro avg']['f1-score'],
        "test_f1_weighted": report['weighted avg']['f1-score'],
        "class_names": CONFIG["classes"],
        "training_date": datetime.now().isoformat(),
        "training_seed": SEED,
    }
    
    model_path = MODEL_DIR / "landcover_resnet18_v1_production.pt"
    torch.save(production_model, model_path)
    print(f"  Saved production model: {model_path}")
    print(f"  Model size: {model_path.stat().st_size / 1024**2:.1f} MB")
    
    # 11. Save to model registry
    total_time = time.time() - training_start
    registry_entry = {
        "model_id": CONFIG["model_id"],
        "model_type": "classification",
        "architecture": CONFIG["architecture"],
        "dataset": CONFIG["dataset"],
        "dataset_size": len(image_paths),
        "num_classes": CONFIG["num_classes"],
        "classes": CONFIG["classes"],
        "training_date": datetime.now().isoformat(),
        "training_duration_seconds": round(total_time, 1),
        "epochs_trained": best_epoch,
        "total_epochs_run": len(history["train_loss"]),
        "early_stopped": patience_counter >= CONFIG["early_stopping_patience"],
        "best_epoch": best_epoch,
        "hyperparameters": {
            "lr": CONFIG["lr"],
            "weight_decay": CONFIG["weight_decay"],
            "batch_size": CONFIG["batch_size"],
            "input_size": CONFIG["input_size"],
            "label_smoothing": 0.1,
            "frozen_layers": ["conv1", "bn1", "layer1", "layer2"],
        },
        "split": {
            "strategy": "stratified",
            "train_size": len(train_paths),
            "val_size": len(val_paths),
            "test_size": len(test_paths),
        },
        "metrics": {
            "best_val_accuracy": best_val_acc,
            "best_val_loss": best_val_loss,
            "test_accuracy": test_acc,
            "test_loss": test_loss,
            "test_f1_macro": report['macro avg']['f1-score'],
            "test_f1_weighted": report['weighted avg']['f1-score'],
            "test_precision_macro": report['macro avg']['precision'],
            "test_recall_macro": report['macro avg']['recall'],
            "per_class_f1": {cls: report[cls]['f1-score'] for cls in CONFIG["classes"]},
        },
        "calibration": {
            "method": "temperature_scaling",
            "temperature": optimal_temp,
        },
        "uncertainty": {
            "method": "mc_dropout",
            "n_samples": n_mc_samples,
            "mean_epistemic": float(epistemic_uncertainty.mean()),
            "median_epistemic": float(np.median(epistemic_uncertainty)),
        },
        "artifacts": {
            "production_model": str(model_path),
            "best_checkpoint": str(CHECKPOINT_DIR / "best_model.pt"),
        },
        "limitations": [
            "Trained on EuroSAT (European Sentinel-2 imagery) -- may have reduced accuracy on non-European regions",
            "64x64 input resolution -- may miss fine-grained features in very high-resolution imagery",
            "10 fixed classes -- cannot detect categories outside the training set",
        ],
        "device": CONFIG["device"],
        "seed": SEED,
    }
    
    registry_path = REGISTRY_DIR / "landcover_resnet18_v1.json"
    with open(registry_path, 'w') as f:
        json.dump(registry_entry, f, indent=2)
    print(f"  Registry entry saved: {registry_path}")
    
    # 12. Save training history
    history_path = REPORT_DIR / "landcover_training_history.json"
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"  Training history saved: {history_path}")
    
    # 13. Final summary
    print("\n" + "=" * 80)
    print("LAND-COVER MODEL TRAINING COMPLETE")
    print("=" * 80)
    print(f"  Architecture: ResNet-18 (ImageNet transfer)")
    print(f"  Dataset: EuroSAT ({len(image_paths)} images)")
    print(f"  Best Epoch: {best_epoch}/{len(history['train_loss'])}")
    print(f"  Test Accuracy: {test_acc:.4f}")
    print(f"  Test F1 (macro): {report['macro avg']['f1-score']:.4f}")
    print(f"  Calibration Temperature: {optimal_temp:.4f}")
    print(f"  Mean Uncertainty: {epistemic_uncertainty.mean():.4f}")
    print(f"  Training Time: {total_time:.0f}s ({total_time/60:.1f}min)")
    print(f"  Model Size: {model_path.stat().st_size / 1024**2:.1f} MB")


if __name__ == "__main__":
    main()
