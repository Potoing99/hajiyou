"""
데이터 증강 - 이미지 수가 부족한 클래스를 보완
각 클래스당 최소 200장까지 증강
"""

import random
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
TARGET_PER_CLASS = 150  # 클래스당 목표 이미지 수 (300→150, 과적합 방지)


def augment_image(img: Image.Image) -> list[Image.Image]:
    """한 이미지에서 여러 증강 이미지 생성"""
    results = []
    w, h = img.size

    # 1. 좌우 반전
    results.append(img.transpose(Image.FLIP_LEFT_RIGHT))

    # 2. 밝기 조절
    for factor in [0.7, 1.3]:
        results.append(ImageEnhance.Brightness(img).enhance(factor))

    # 3. 대비 조절
    results.append(ImageEnhance.Contrast(img).enhance(1.3))

    # 4. 회전
    for angle in [-15, -10, 10, 15]:
        results.append(img.rotate(angle, expand=False, fillcolor=(200, 200, 200)))

    # 5. 크롭 + 리사이즈
    for _ in range(3):
        margin_x = int(w * 0.1)
        margin_y = int(h * 0.1)
        x1 = random.randint(0, margin_x)
        y1 = random.randint(0, margin_y)
        x2 = w - random.randint(0, margin_x)
        y2 = h - random.randint(0, margin_y)
        cropped = img.crop((x1, y1, x2, y2)).resize((w, h), Image.LANCZOS)
        results.append(cropped)

    # 6. 채도 조절
    results.append(ImageEnhance.Color(img).enhance(1.4))
    results.append(ImageEnhance.Color(img).enhance(0.7))

    # 7. 샤프닝
    results.append(img.filter(ImageFilter.SHARPEN))

    return results


def augment_class(split: str, class_name: str):
    class_dir = DATA_DIR / split / class_name
    if not class_dir.exists():
        return 0

    existing = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
    current_count = len(existing)

    if current_count >= TARGET_PER_CLASS:
        print(f"  {class_name}: {current_count}장 (증강 불필요)")
        return 0

    needed = TARGET_PER_CLASS - current_count
    generated = 0
    idx = current_count + 1

    for src_path in existing:
        if generated >= needed:
            break
        try:
            img = Image.open(src_path).convert("RGB").resize((224, 224))
            augmented = augment_image(img)
            for aug_img in augmented:
                if generated >= needed:
                    break
                save_path = class_dir / f"aug_{idx:05d}.jpg"
                aug_img.resize((224, 224)).save(save_path, "JPEG", quality=90)
                idx += 1
                generated += 1
        except Exception as e:
            print(f"  오류 ({src_path.name}): {e}")

    print(f"  {class_name}: {current_count}장 → {current_count + generated}장 (+{generated}장 증강)")
    return generated


def main():
    print("=" * 50)
    print("데이터 증강 시작 (train 세트만)")
    print("=" * 50)

    total_added = 0
    for class_dir in sorted((DATA_DIR / "train").iterdir()):
        if class_dir.is_dir():
            added = augment_class("train", class_dir.name)
            total_added += added

    print(f"\n증강 완료: 총 {total_added}장 추가")


if __name__ == "__main__":
    main()
