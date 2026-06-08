"""
모델 평가 및 결과 시각화
- Confusion Matrix
- Classification Report
- 클래스별 예시 이미지 + 예측 결과
"""

import json
import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix
from pathlib import Path

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

BASE_DIR  = Path(__file__).parent.parent
DATA_DIR  = BASE_DIR / "data" / "processed"
MODEL_DIR = BASE_DIR / "models"
DOCS_DIR  = BASE_DIR / "docs"
DOCS_DIR.mkdir(exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CLASS_NAMES_KO = ["정상/경증\n(C0-C1)", "중등도\n(C2-C3)", "중증\n(C4-C6)"]


def load_model(num_classes=3):
    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.4),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, num_classes),
    )
    model.load_state_dict(torch.load(MODEL_DIR / "best_model.pth", map_location=DEVICE))
    model.eval()
    return model.to(DEVICE)


def get_predictions(model, loader):
    all_preds, all_labels = [], []
    with torch.no_grad():
        for imgs, labels in loader:
            imgs = imgs.to(DEVICE)
            outputs = model(imgs)
            preds = outputs.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.numpy())
    return np.array(all_labels), np.array(all_preds)


def plot_confusion_matrix(y_true, y_pred, save_path):
    cm = confusion_matrix(y_true, y_pred)
    cm_pct = cm.astype(float) / cm.sum(axis=1, keepdims=True) * 100

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm_pct, cmap='Blues', vmin=0, vmax=100)
    plt.colorbar(im, ax=ax, label='비율 (%)')

    for i in range(len(cm)):
        for j in range(len(cm)):
            ax.text(j, i, f"{cm[i,j]}\n({cm_pct[i,j]:.1f}%)",
                    ha='center', va='center', fontsize=10,
                    color='white' if cm_pct[i,j] > 50 else 'black')

    ax.set_xticks(range(len(CLASS_NAMES_KO)))
    ax.set_yticks(range(len(CLASS_NAMES_KO)))
    ax.set_xticklabels(CLASS_NAMES_KO)
    ax.set_yticklabels(CLASS_NAMES_KO)
    ax.set_xlabel('예측 클래스')
    ax.set_ylabel('실제 클래스')
    ax.set_title('하지정맥류 분류 Confusion Matrix')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"저장: {save_path}")


def plot_training_history(save_path):
    history_path = MODEL_DIR / "history.json"
    if not history_path.exists():
        print("history.json 없음")
        return

    with open(history_path) as f:
        h = json.load(f)

    epochs = range(1, len(h["train_loss"]) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(epochs, h["train_loss"], label="Train")
    axes[0].plot(epochs, h["val_loss"],   label="Val")
    axes[0].set_title("Loss 추이")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()

    axes[1].plot(epochs, h["train_acc"], label="Train")
    axes[1].plot(epochs, h["val_acc"],   label="Val")
    axes[1].set_title("Accuracy 추이")
    axes[1].set_xlabel("Epoch")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def main():
    model = load_model()

    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    test_ds = datasets.ImageFolder(DATA_DIR / "test", transform=val_tf)
    test_loader = DataLoader(test_ds, batch_size=16, shuffle=False, num_workers=0)

    y_true, y_pred = get_predictions(model, test_loader)

    print("\n=== Classification Report ===")
    print(classification_report(y_true, y_pred,
                                 target_names=["정상/경증", "중등도", "중증"]))

    plot_confusion_matrix(y_true, y_pred, DOCS_DIR / "confusion_matrix.png")
    plot_training_history(DOCS_DIR / "training_history.png")


if __name__ == "__main__":
    main()
