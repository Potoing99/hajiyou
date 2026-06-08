"""
이미지 전처리 및 데이터셋 구성
- 수집된 이미지를 train/val/test로 분할
- 품질 필터링 (너무 작거나 손상된 이미지 제거)
- 클래스 불균형 확인
"""

import os
import shutil
import random
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"

# CEAP C0~C6 전체 7단계 분류
CLASS_MAPPING = {
    "C0_normal":        ["C0_normal"],
    "C1_spider_veins":  ["C1_spider_veins"],
    "C2_varicose":      ["C2_varicose_veins"],
    "C3_edema":         ["C3_edema"],
    "C4_skin_changes":  ["C4_skin_changes"],
    "C5_healed_ulcer":  ["C5_healed_ulcer"],
    "C6_active_ulcer":  ["C6_active_ulcer"],
}

SPLIT_RATIO = (0.7, 0.15, 0.15)  # train / val / test
MIN_SIZE = (64, 64)


def is_valid_image(path: Path) -> bool:
    try:
        with Image.open(path) as img:
            w, h = img.size
            return w >= MIN_SIZE[0] and h >= MIN_SIZE[1]
    except Exception:
        return False


def collect_images_for_class(class_name: str, source_dirs: list[str]) -> list[Path]:
    images = []
    for src in source_dirs:
        for subdir in ["crawled", "dermnetz"]:
            d = RAW_DIR / subdir / src
            if d.exists():
                imgs = list(d.glob("*.jpg")) + list(d.glob("*.png")) + list(d.glob("*.jpeg"))
                valid = [p for p in imgs if is_valid_image(p)]
                images.extend(valid)
    return images


def split_and_copy(images: list[Path], class_name: str):
    random.shuffle(images)
    n = len(images)
    n_train = int(n * SPLIT_RATIO[0])
    n_val = int(n * SPLIT_RATIO[1])

    splits = {
        "train": images[:n_train],
        "val":   images[n_train:n_train + n_val],
        "test":  images[n_train + n_val:],
    }

    for split, files in splits.items():
        dest = PROCESSED_DIR / split / class_name
        dest.mkdir(parents=True, exist_ok=True)
        for i, src in enumerate(files):
            shutil.copy2(src, dest / f"{i:05d}{src.suffix}")

    return {k: len(v) for k, v in splits.items()}


def main():
    random.seed(42)
    print("=" * 50)
    print("데이터 전처리 시작")
    print("=" * 50)

    total_stats = {}
    for class_name, source_dirs in CLASS_MAPPING.items():
        images = collect_images_for_class(class_name, source_dirs)
        print(f"\n{class_name}: 유효 이미지 {len(images)}장")

        if len(images) == 0:
            print(f"  경고: 이미지 없음, 건너뜀")
            continue

        stats = split_and_copy(images, class_name)
        total_stats[class_name] = stats
        print(f"  train={stats['train']}, val={stats['val']}, test={stats['test']}")

    print("\n" + "=" * 50)
    print("전처리 완료")
    for cls, stats in total_stats.items():
        total = sum(stats.values())
        print(f"  {cls}: 총 {total}장")


if __name__ == "__main__":
    main()
