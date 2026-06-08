"""
EfficientNet-B0 전이학습 기반 하지정맥류 분류 모델 학습
"""

import os
import json
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from pathlib import Path
from tqdm import tqdm

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

CLASSES = ["C0_normal", "C1_watch", "C2_consult", "C34_danger", "C56_emergency"]
CLASS_LABELS = {
    "C0_normal":     "정상 (C0)",
    "C1_watch":      "관찰 단계 (C1)",
    "C2_consult":    "진료 권고 (C2)",
    "C34_danger":    "병원 필수 (C3-C4)",
    "C56_emergency": "즉시 방문 (C5-C6)",
}

BATCH_SIZE = 16
EPOCHS = 50
LR = 1e-4
IMG_SIZE = 224
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_transforms():
    train_tf = transforms.Compose([
        transforms.Resize((IMG_SIZE + 32, IMG_SIZE + 32)),
        transforms.RandomCrop(IMG_SIZE),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])
    val_tf = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])
    return train_tf, val_tf


def build_model(num_classes: int = 7) -> nn.Module:
    model = models.efficientnet_b2(weights=models.EfficientNet_B2_Weights.DEFAULT)
    for param in model.features.parameters():
        param.requires_grad = False
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.4),
        nn.Linear(256, num_classes),
    )
    return model


def unfreeze_backbone(model, lr: float = 1e-5):
    """백본 동결 해제 후 차등 LR 적용"""
    for param in model.features.parameters():
        param.requires_grad = True
    # 백본은 낮은 LR, 분류기는 기존 LR 유지
    return [
        {"params": model.features.parameters(), "lr": lr},
        {"params": model.classifier.parameters(), "lr": lr * 10},
    ]


def train_one_epoch(model, loader, criterion, optimizer):
    model.train()
    total_loss, correct, total = 0.0, 0, 0

    for imgs, labels in tqdm(loader, desc="  학습", leave=False):
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * imgs.size(0)
        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += imgs.size(0)

    return total_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0

    for imgs, labels in loader:
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        outputs = model(imgs)
        loss = criterion(outputs, labels)

        total_loss += loss.item() * imgs.size(0)
        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += imgs.size(0)

    return total_loss / total, correct / total


def save_checkpoint(epoch, model, optimizer, scheduler, best_val_acc, history):
    torch.save({
        "epoch": epoch,
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "scheduler_state": scheduler.state_dict(),
        "best_val_acc": best_val_acc,
        "history": history,
    }, MODEL_DIR / "checkpoint.pth")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="checkpoint.pth에서 이어서 학습")
    args = parser.parse_args()

    print(f"학습 디바이스: {DEVICE}")

    train_tf, val_tf = get_transforms()

    train_ds = datasets.ImageFolder(DATA_DIR / "train", transform=train_tf)
    val_ds   = datasets.ImageFolder(DATA_DIR / "val",   transform=val_tf)
    test_ds  = datasets.ImageFolder(DATA_DIR / "test",  transform=val_tf)

    print(f"Train: {len(train_ds)}장 | Val: {len(val_ds)}장 | Test: {len(test_ds)}장")
    print(f"클래스: {train_ds.classes}")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model = build_model(num_classes=len(train_ds.classes)).to(DEVICE)

    class_counts = [len(list((DATA_DIR / "train" / c).glob("*"))) for c in train_ds.classes]
    weights = torch.tensor([1.0 / c for c in class_counts], dtype=torch.float).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.1)

    UNFREEZE_EPOCH = 8
    best_val_acc = 0.0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    start_epoch = 1

    ckpt_path = MODEL_DIR / "checkpoint.pth"
    if args.resume and ckpt_path.exists():
        ckpt = torch.load(ckpt_path, map_location=DEVICE)
        start_epoch = ckpt["epoch"] + 1
        best_val_acc = ckpt["best_val_acc"]
        history = ckpt["history"]
        model.load_state_dict(ckpt["model_state"])

        # resume 시 백본은 이미 언프리즈 상태로 복원
        param_groups = unfreeze_backbone(model, lr=1e-5)
        optimizer = optim.AdamW(param_groups, weight_decay=1e-3)
        scheduler = optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=EPOCHS - UNFREEZE_EPOCH + 1)
        optimizer.load_state_dict(ckpt["optimizer_state"])
        scheduler.load_state_dict(ckpt["scheduler_state"])
        print(f"  → checkpoint 불러옴: epoch {start_epoch}부터 재개 (best={best_val_acc:.4f})")
    else:
        optimizer = optim.AdamW(model.classifier.parameters(), lr=LR, weight_decay=1e-3)
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    print(f"\n학습 시작 (Epoch {start_epoch}-{EPOCHS})")
    for epoch in range(start_epoch, EPOCHS + 1):
        if epoch == UNFREEZE_EPOCH and not args.resume:
            param_groups = unfreeze_backbone(model, lr=1e-5)
            optimizer = optim.AdamW(param_groups, weight_decay=1e-3)
            scheduler = optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=EPOCHS - UNFREEZE_EPOCH + 1)
            print(f"  [Epoch {epoch}] 백본 동결 해제, 차등 LR 적용")

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss,   val_acc   = evaluate(model, val_loader, criterion)
        scheduler.step()

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        print(f"Epoch {epoch:02d}/{EPOCHS} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), MODEL_DIR / "best_model.pth")
            print(f"  → 최고 모델 저장 (val_acc={val_acc:.4f})")

        save_checkpoint(epoch, model, optimizer, scheduler, best_val_acc, history)

    model.load_state_dict(torch.load(MODEL_DIR / "best_model.pth"))
    test_loss, test_acc = evaluate(model, test_loader, criterion)
    print(f"\n최종 Test Accuracy: {test_acc:.4f}")

    with open(MODEL_DIR / "history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"\n모델 저장 완료: {MODEL_DIR / 'best_model.pth'}")


if __name__ == "__main__":
    main()
