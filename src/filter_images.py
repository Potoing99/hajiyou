"""
CLIP 기반 이미지 품질 필터링
- 다리/정맥 관련 이미지만 남기고 무관한 이미지 제거
- 필터링된 이미지는 data/raw/rejected/ 로 이동 (삭제 아님)
"""

import shutil
import torch
import open_clip
from pathlib import Path
from PIL import Image
from tqdm import tqdm

RAW_DIR      = Path(__file__).parent.parent / "data" / "raw"
CRAWLED_DIR  = RAW_DIR / "crawled"
REJECTED_DIR = RAW_DIR / "rejected"
DEVICE       = "cuda" if torch.cuda.is_available() else "cpu"

# CLIP에게 물어볼 텍스트 프롬프트
POSITIVE_PROMPTS = [
    "a clinical photo of varicose veins on human leg",
    "a medical image of leg with spider veins",
    "a photo of human leg showing venous disease",
    "a close up photo of swollen veins on legs",
    "a dermatology photo of lower leg with skin condition",
    "a photo of human ankle and lower leg",
]

NEGATIVE_PROMPTS = [
    "a photo of a camera or photography equipment",
    "a landscape photo of nature",
    "a photo of food",
    "a photo of a car or vehicle",
    "a photo of a building or architecture",
    "a photo of an animal",
    "a graph or chart or diagram",
    "a photo of hands or arms",
    "a photo of face or portrait",
    "a text document or article",
    "an illustration or cartoon",
    "a product photo of medicine or drug packaging",
]

# 클래스별 threshold (분석 결과 기반)
# C0_normal은 재수집 후 0.0 기준 적용
# C1/C2/C3/C4/C5C6은 0.08 기준 적용 (하위 노이즈 제거)
CLASS_THRESHOLDS = {
    "C0_normal":        0.0,
    "C1_spider_veins":  0.08,
    "C2_varicose_veins":0.08,
    "C3_edema":         0.08,
    "C4_skin_changes":  0.08,
    "C5_healed_ulcer":  0.08,
    "C6_active_ulcer":  0.08,
}
THRESHOLD = 0.08  # 기본값


def load_clip():
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai"
    )
    model.eval().to(DEVICE)
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    return model, preprocess, tokenizer


def get_relevance_score(model, preprocess, tokenizer,
                         image_path: Path) -> float:
    """0~1 점수: 높을수록 다리/정맥 관련 이미지"""
    try:
        img = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(DEVICE)

        pos_tokens = tokenizer(POSITIVE_PROMPTS).to(DEVICE)
        neg_tokens = tokenizer(NEGATIVE_PROMPTS).to(DEVICE)

        with torch.no_grad():
            img_feat  = model.encode_image(img)
            pos_feat  = model.encode_text(pos_tokens)
            neg_feat  = model.encode_text(neg_tokens)

            img_feat  = img_feat  / img_feat.norm(dim=-1, keepdim=True)
            pos_feat  = pos_feat  / pos_feat.norm(dim=-1, keepdim=True)
            neg_feat  = neg_feat  / neg_feat.norm(dim=-1, keepdim=True)

            pos_score = (img_feat @ pos_feat.T).mean().item()
            neg_score = (img_feat @ neg_feat.T).mean().item()

        # positive - negative 차이로 점수 계산
        return pos_score - neg_score

    except Exception:
        return -999.0


def filter_class(cls_dir: Path, model, preprocess, tokenizer,
                  threshold: float = None):
    images = list(cls_dir.glob("*.jpg")) + list(cls_dir.glob("*.png"))
    if not images:
        return 0, 0

    if threshold is None:
        threshold = CLASS_THRESHOLDS.get(cls_dir.name, THRESHOLD)

    rejected_dir = REJECTED_DIR / cls_dir.name
    rejected_dir.mkdir(parents=True, exist_ok=True)

    kept = rejected = 0
    scores = []

    for img_path in tqdm(images, desc=f"  {cls_dir.name}", leave=False):
        score = get_relevance_score(model, preprocess, tokenizer, img_path)
        scores.append((img_path, score))

    # 점수 분포 출력
    all_scores = [s for _, s in scores]
    print(f"  {cls_dir.name}: 평균={sum(all_scores)/len(all_scores):.4f}, "
          f"최소={min(all_scores):.4f}, 최대={max(all_scores):.4f}")

    for img_path, score in scores:
        if score < threshold:
            shutil.move(str(img_path), str(rejected_dir / img_path.name))
            rejected += 1
        else:
            kept += 1

    return kept, rejected


def main():
    print("=" * 50)
    print("CLIP 기반 이미지 필터링 시작")
    print(f"임계값(threshold): {THRESHOLD}")
    print("=" * 50)

    print("\nCLIP 모델 로딩...")
    model, preprocess, tokenizer = load_clip()
    print("로딩 완료")

    total_kept = total_rejected = 0

    for cls_dir in sorted(CRAWLED_DIR.iterdir()):
        if not cls_dir.is_dir():
            continue
        print(f"\n[{cls_dir.name}]")
        kept, rejected = filter_class(cls_dir, model, preprocess, tokenizer)
        print(f"  유지: {kept}장 | 제거: {rejected}장")
        total_kept     += kept
        total_rejected += rejected

    print("\n" + "=" * 50)
    print(f"필터링 완료")
    print(f"  유지:  {total_kept}장")
    print(f"  제거:  {total_rejected}장 (→ data/raw/rejected/ 이동)")
    print(f"  제거율: {total_rejected/(total_kept+total_rejected)*100:.1f}%")
    print("\n※ 제거된 이미지는 삭제가 아닌 rejected/ 폴더로 이동됩니다.")
    print("  threshold 조정 후 다시 실행하면 복구 가능합니다.")


if __name__ == "__main__":
    main()
