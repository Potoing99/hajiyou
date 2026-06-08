"""
CEAP 비교표 이미지를 C0~C6 개별 이미지로 크롭
- 가로로 7단계가 나란히 있는 비교표 → 7등분 저장
- data/raw/crawled/ 전체 폴더에서 비교표 찾아서 처리
"""

import shutil
from pathlib import Path
from PIL import Image

RAW_DIR     = Path("data/raw")
CRAWLED_DIR = RAW_DIR / "crawled"
CHARTS_DIR  = RAW_DIR / "rejected" / "charts_backup"  # 원본 백업

CLASSES = [
    "C0_normal",
    "C1_spider_veins",
    "C2_varicose_veins",
    "C3_edema",
    "C4_skin_changes",
    "C5_healed_ulcer",
    "C6_active_ulcer",
]

# 비교표 판별 기준
MIN_ASPECT_RATIO = 2.0   # 가로/세로 비율
MIN_WIDTH        = 500   # 최소 가로 픽셀
MIN_CROP_SIZE    = 80    # 크롭 후 최소 크기


def is_comparison_chart(img: Image.Image) -> bool:
    w, h = img.size
    ratio = w / h
    return ratio >= MIN_ASPECT_RATIO and w >= MIN_WIDTH


def crop_7_sections(img: Image.Image) -> list[Image.Image]:
    """가로 7등분 크롭"""
    w, h = img.size
    section_w = w // 7
    crops = []
    for i in range(7):
        x1 = i * section_w
        x2 = (i + 1) * section_w if i < 6 else w
        crop = img.crop((x1, 0, x2, h))
        crops.append(crop)
    return crops


def save_crop(crop: Image.Image, class_name: str) -> bool:
    cw, ch = crop.size
    if cw < MIN_CROP_SIZE or ch < MIN_CROP_SIZE:
        return False

    dest_dir = CRAWLED_DIR / class_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    existing = list(dest_dir.glob("crop_*.jpg"))
    idx = len(existing) + 1
    save_path = dest_dir / f"crop_{idx:04d}.jpg"
    crop.resize((224, 224), Image.LANCZOS).save(save_path, "JPEG", quality=90)
    return True


def process_image(img_path: Path) -> bool:
    """비교표이면 크롭 후 저장, 아니면 False 반환"""
    try:
        img = Image.open(img_path).convert("RGB")
        if not is_comparison_chart(img):
            return False

        crops = crop_7_sections(img)
        if len(crops) != 7:
            return False

        saved = 0
        for cls, crop in zip(CLASSES, crops):
            if save_crop(crop, cls):
                saved += 1

        if saved == 7:
            # 원본 비교표 백업
            CHARTS_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(img_path), str(CHARTS_DIR / img_path.name))
            return True

    except Exception as e:
        print(f"  오류 ({img_path.name}): {e}")
    return False


def main():
    print("=" * 50)
    print("CEAP 비교표 크롭 시작")
    print(f"판별 기준: 가로/세로 비율 >= {MIN_ASPECT_RATIO}, 가로 >= {MIN_WIDTH}px")
    print("=" * 50)

    # 모든 crawled 폴더에서 비교표 탐색
    all_images = []
    for cls_dir in sorted(CRAWLED_DIR.iterdir()):
        if cls_dir.is_dir() and cls_dir.name in CLASSES:
            imgs = list(cls_dir.glob("*.jpg")) + list(cls_dir.glob("*.png"))
            all_images.extend(imgs)

    # rejected 폴더에서도 탐색 (이전에 제거된 이미지 포함)
    for rejected_dir in sorted((RAW_DIR / "rejected").iterdir()):
        if rejected_dir.is_dir():
            imgs = list(rejected_dir.glob("*.jpg")) + list(rejected_dir.glob("*.png"))
            all_images.extend(imgs)

    print(f"\n총 {len(all_images)}장 검사 중...\n")

    found = cropped = 0
    for img_path in all_images:
        if process_image(img_path):
            found += 1
            cropped += 7
            print(f"  [비교표 발견] {img_path.name} → C0~C6 각 1장씩 크롭")

    print(f"\n완료: {found}개 비교표 발견 → {cropped}장 크롭 생성")

    if found == 0:
        print("비교표가 없거나 가로/세로 비율이 기준 미달입니다.")
        print(f"기준 완화 시도: MIN_ASPECT_RATIO = {MIN_ASPECT_RATIO} → 2.0 으로 낮춰보세요.")

    # 현재 데이터 현황 출력
    print("\n현재 crawled 이미지 수:")
    for cls in CLASSES:
        d = CRAWLED_DIR / cls
        n = len(list(d.glob("*.jpg")) + list(d.glob("*.png"))) if d.exists() else 0
        print(f"  {cls}: {n}장")


if __name__ == "__main__":
    main()
