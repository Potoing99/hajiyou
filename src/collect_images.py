"""
하지정맥류 CEAP 단계별 이미지 수집 스크립트
- DuckDuckGo 이미지 검색으로 각 클래스별 이미지 수집
- DermNet NZ 이미지 직접 다운로드
"""

import os
import time
import requests
from pathlib import Path
from ddgs import DDGS

BASE_DIR = Path(__file__).parent.parent / "data" / "raw"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# CEAP 단계별 검색 키워드 (영어 + 의학 용어 위주로 정확도 높임)
SEARCH_QUERIES = {
    "C0_normal": [
        "varicose vein CEAP C0 normal leg no symptoms clinical examination",
        "varicose vein classification C0 healthy leg dermatology photo",
        "CEAP C0 chronic venous disease normal leg",
    ],
    "C1_spider_veins": [
        "varicose vein CEAP C1 telangiectasia spider veins leg clinical",
        "varicose vein C1 reticular veins leg medical photo",
        "CEAP C1 telangiectases lower leg dermatology",
    ],
    "C2_varicose_veins": [
        "varicose vein CEAP C2 bulging twisted veins leg clinical photo",
        "varicose vein C2 lower leg prominent veins medical",
        "CEAP C2 varicose veins clinical examination leg",
    ],
    "C3_edema": [
        "varicose vein CEAP C3 venous edema ankle leg swelling",
        "varicose vein C3 leg edema chronic venous insufficiency medical",
        "CEAP C3 pitting edema leg venous disease",
    ],
    "C4_skin_changes": [
        "varicose vein CEAP C4 lipodermatosclerosis venous stasis eczema leg",
        "varicose vein C4 venous hyperpigmentation skin changes leg clinical",
        "CEAP C4a C4b stasis dermatitis lipodermatosclerosis leg",
    ],
    "C5_healed_ulcer": [
        "varicose vein CEAP C5 healed venous ulcer leg scar clinical",
        "CEAP C5 healed leg ulcer venous insufficiency medical photo",
        "varicose vein C5 scarring healed ulcer lower leg",
    ],
    "C6_active_ulcer": [
        "varicose vein CEAP C6 active venous ulcer open wound leg clinical",
        "CEAP C6 venous leg ulcer wound dermatology photo",
        "varicose vein C6 active ulcer gaiter area leg medical",
    ],
}

IMAGES_PER_QUERY = 80  # 쿼리당 수집 목표 수

DERMNETZ_IMAGES = {
    "C2_varicose_veins": [
        f"/assets/Uploads/varicose-veins-{i:02d}.jpg" for i in range(1, 7)
    ],
    "C4_skin_changes": [
        "/assets/Uploads/grav-derm-alt-v2.jpg",
        "/assets/Uploads/dermatitis/lipodermatosclerosis.jpg",
        "/assets/Uploads/acute-lipodermatosclerosis-18.jpg",
        "/assets/Uploads/acute-lipodermatosclerosis-10.jpg",
        "/assets/Uploads/acute-lipodermatosclerosis-06.jpg",
    ],
    "C5C6_ulcer": [
        "/assets/Uploads/dermatitis/ulcer.jpg",
    ],
}


def download_image(url: str, save_path: Path) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200 and len(resp.content) > 5000:
            save_path.write_bytes(resp.content)
            return True
    except Exception:
        pass
    return False


def collect_ddgs(category: str, queries: list[str], max_per_query: int = 80):
    save_dir = BASE_DIR / "crawled" / category
    save_dir.mkdir(parents=True, exist_ok=True)

    existing = len(list(save_dir.glob("*.jpg")) + list(save_dir.glob("*.png")))
    idx = existing + 1
    total_saved = 0

    for query in queries:
        print(f"    검색: '{query}'")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(query, max_results=max_per_query))

            for r in results:
                save_path = save_dir / f"ddgs_{idx:04d}.jpg"
                if download_image(r["image"], save_path):
                    idx += 1
                    total_saved += 1
                time.sleep(0.3)

        except Exception as e:
            print(f"    오류: {e}")
        time.sleep(2)

    print(f"    → {category}: {total_saved}장 수집")
    return total_saved


def collect_dermnetz():
    print("\n[DermNet NZ] 이미지 다운로드...")
    base = "https://dermnetnz.org"
    total = 0

    for category, paths in DERMNETZ_IMAGES.items():
        save_dir = BASE_DIR / "dermnetz" / category
        save_dir.mkdir(parents=True, exist_ok=True)

        for i, path in enumerate(paths):
            save_path = save_dir / f"dermnetz_{i+1:03d}.jpg"
            if save_path.exists():
                continue
            if download_image(base + path, save_path):
                total += 1
                print(f"  OK: {save_path.name}")
            else:
                print(f"  Skip: {path}")

    print(f"  → DermNet 총 {total}장 수집")


def print_summary():
    print("\n" + "=" * 50)
    print("수집 완료 요약:")
    grand_total = 0
    for sub in ["crawled", "dermnetz"]:
        sub_dir = BASE_DIR / sub
        if not sub_dir.exists():
            continue
        for cat_dir in sorted(sub_dir.iterdir()):
            if cat_dir.is_dir():
                count = len(list(cat_dir.glob("*.jpg")) + list(cat_dir.glob("*.png")))
                if count > 0:
                    print(f"  {sub}/{cat_dir.name}: {count}장")
                    grand_total += count
    print(f"\n  전체 합계: {grand_total}장")


def main():
    print("=" * 50)
    print("하지정맥류 이미지 수집 시작")
    print("=" * 50)

    collect_dermnetz()

    print("\n[DuckDuckGo] 이미지 크롤링...")
    for category, queries in SEARCH_QUERIES.items():
        print(f"\n  카테고리: {category}")
        collect_ddgs(category, queries, max_per_query=IMAGES_PER_QUERY)

    print_summary()


if __name__ == "__main__":
    main()
