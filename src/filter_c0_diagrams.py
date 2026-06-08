"""
C0_normal 폴더에서 CEAP 분류 다이어그램/비교 이미지 제거
- 분류표, 모든 단계 비교 이미지, 의학 일러스트 등 제거
- 실제 정상 다리 임상 사진만 남김
"""

import shutil
import torch
import open_clip
from pathlib import Path
from PIL import Image

CRAWLED_DIR  = Path("data/raw/crawled/C0_normal")
PROCESSED_TRAIN = Path("data/processed/train/C0_normal")
REJECTED_DIR = Path("data/raw/rejected/C0_normal_diagrams")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 실제 임상 사진 vs 다이어그램/비교표 구분
REAL_PHOTO_PROMPTS = [
    "a clinical photograph of normal healthy human leg",
    "a photo of normal leg skin with no visible veins",
    "a medical photo of healthy lower leg",
]

DIAGRAM_PROMPTS = [
    "a medical diagram showing multiple stages of varicose veins",
    "a CEAP classification chart comparing C0 to C6",
    "an illustration showing venous disease stages",
    "a comparison chart of vein conditions",
    "a medical textbook diagram",
    "an infographic showing vascular disease progression",
    "a drawing or illustration of leg anatomy",
]

THRESHOLD = 0.05  # 다이어그램 점수가 이것보다 높으면 제거


def check_is_diagram(model, preprocess, tokenizer, img_path: Path) -> tuple[float, bool]:
    try:
        img = preprocess(Image.open(img_path).convert("RGB")).unsqueeze(0).to(DEVICE)
        real_tokens = tokenizer(REAL_PHOTO_PROMPTS).to(DEVICE)
        diag_tokens = tokenizer(DIAGRAM_PROMPTS).to(DEVICE)

        with torch.no_grad():
            img_feat   = model.encode_image(img)
            real_feat  = model.encode_text(real_tokens)
            diag_feat  = model.encode_text(diag_tokens)

            img_feat  = img_feat  / img_feat.norm(dim=-1, keepdim=True)
            real_feat = real_feat / real_feat.norm(dim=-1, keepdim=True)
            diag_feat = diag_feat / diag_feat.norm(dim=-1, keepdim=True)

            real_score = (img_feat @ real_feat.T).mean().item()
            diag_score = (img_feat @ diag_feat.T).mean().item()

        diff = diag_score - real_score
        return diff, diff > THRESHOLD
    except Exception:
        return 0.0, False


def main():
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    print("CLIP 모델 로딩...")
    model, preprocess, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
    model.eval().to(DEVICE)
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    print("완료\n")

    images = list(CRAWLED_DIR.glob("*.jpg")) + list(CRAWLED_DIR.glob("*.png"))
    print(f"C0_normal 이미지 총 {len(images)}장 검사 중...\n")

    kept = removed = 0
    diagram_list = []

    for img_path in images:
        diff, is_diagram = check_is_diagram(model, preprocess, tokenizer, img_path)
        if is_diagram:
            shutil.move(str(img_path), str(REJECTED_DIR / img_path.name))
            diagram_list.append((img_path.name, diff))
            removed += 1
        else:
            kept += 1

    print(f"결과: {kept}장 유지 | {removed}장 제거 (→ {REJECTED_DIR})")
    if diagram_list:
        print("\n제거된 이미지 (다이어그램 의심):")
        for name, score in sorted(diagram_list, key=lambda x: -x[1]):
            print(f"  {name}  (score={score:.4f})")


if __name__ == "__main__":
    main()
