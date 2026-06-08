"""
단일 이미지 추론 모듈 - Streamlit 앱에서 사용
"""

import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
from pathlib import Path

MODEL_PATH = Path(__file__).parent.parent / "models" / "best_model.pth"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

CLASSES = [
    "C0_normal",
    "C1_watch",
    "C2_consult",
    "C34_danger",
    "C56_emergency",
]

RESULT_INFO = {
    "C0_normal": {
        "label": "정상",
        "color": "#2ecc71",
        "desc": "육안으로 혈관 이상 소견이 없습니다.",
        "advice": "현재 증상이 없더라도 장시간 서 있거나 앉아 있는 경우 주기적으로 다리를 움직이고 압박 스타킹을 고려하세요.",
        "urgency": "정상",
    },
    "C1_watch": {
        "label": "관찰 단계 (C1)",
        "color": "#27ae60",
        "desc": "거미줄 모양의 가는 혈관(모세혈관 확장, 거미정맥)이 관찰됩니다.",
        "advice": "당장 치료가 필요하지 않지만 압박 스타킹 착용을 권장합니다. 증상이 심해지면 전문의 상담을 받으세요.",
        "urgency": "경과 관찰",
    },
    "C2_consult": {
        "label": "진료 권고 (C2)",
        "color": "#f39c12",
        "desc": "굵고 구불구불한 정맥류가 관찰됩니다 (3mm 이상).",
        "advice": "혈관외과 전문의 진료를 권장합니다. 경화요법, 레이저, 고주파 치료 등 다양한 치료법이 있습니다.",
        "urgency": "진료 권장",
    },
    "C34_danger": {
        "label": "병원 필수 (C3-C4)",
        "color": "#e74c3c",
        "desc": "정맥성 부종(붓기) 또는 피부 색소침착·습진·경화 등 피부 변화가 관찰됩니다.",
        "advice": "빠른 시일 내 혈관외과 전문의 진료를 받으세요. 방치하면 궤양으로 악화될 수 있습니다.",
        "urgency": "병원 방문 필요",
    },
    "C56_emergency": {
        "label": "즉시 방문 (C5-C6)",
        "color": "#c0392b",
        "desc": "정맥 궤양(치유된 흔적 또는 현재 진행 중인 궤양)이 의심됩니다.",
        "advice": "즉시 혈관외과 전문의 진료를 받으시기 바랍니다. 방치 시 감염 및 심각한 합병증 위험이 있습니다.",
        "urgency": "즉시 진료",
    },
}

_model = None


def load_model() -> nn.Module:
    global _model
    if _model is not None:
        return _model

    model = models.efficientnet_b2(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.4),
        nn.Linear(256, len(CLASSES)),
    )
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()
    model.to(DEVICE)
    _model = model
    return model


def preprocess(image: Image.Image) -> torch.Tensor:
    tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])
    return tf(image.convert("RGB")).unsqueeze(0).to(DEVICE)


def predict(image: Image.Image) -> dict:
    """
    Returns:
        {
            "class": "class_0_mild",
            "label": "정상 / 경증 (CEAP C0-C1)",
            "confidence": 0.87,
            "probabilities": {"class_0_mild": 0.87, ...},
            "info": {...}
        }
    """
    model = load_model()
    tensor = preprocess(image)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0].cpu().tolist()

    pred_idx = probs.index(max(probs))
    pred_class = CLASSES[pred_idx]

    confidence = probs[pred_idx]

    # 신뢰도 낮으면 불명확 처리
    if confidence < 0.60:
        return {
            "class": "uncertain",
            "label": "판단 불가",
            "confidence": confidence,
            "probabilities": dict(zip(CLASSES, probs)),
            "info": {
                "label": "판단 불가",
                "color": "#95a5a6",
                "desc": "사진이 불분명하거나 단계 판별이 어렵습니다.",
                "advice": "더 밝은 조명에서 다시 촬영하거나 전문의 진료를 받으시기 바랍니다.",
                "urgency": "재촬영 또는 전문의 상담",
            },
        }

    return {
        "class": pred_class,
        "label": RESULT_INFO[pred_class]["label"],
        "confidence": confidence,
        "probabilities": dict(zip(CLASSES, probs)),
        "info": RESULT_INFO[pred_class],
    }
