"""
추가 이미지 수집 스크립트
- 학습 후 성능이 낮은 클래스를 보강할 때 사용
- 넓은 CEAP 키워드로 수집 → label_tool.py로 수동 분류
- 또는 특정 클래스만 선택적으로 추가 수집
"""

import time
import requests
import argparse
from pathlib import Path
from ddgs import DDGS

BASE_DIR = Path(__file__).parent.parent / "data" / "raw"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 기존 키워드에서 더 다양한 각도로 추가
EXTRA_QUERIES = {
    "C0_normal": [
        "bare legs photo",
        "human lower leg skin close up",
        "legs calf skin photo",
        "bare foot and ankle photo",
        "human leg skin texture photo",
        "legs standing bare skin photo",
        "lower leg close up photo",
    ],
    "C1_spider_veins": [
        "telangiectasia leg spider veins close up photo",
        "reticular veins leg blue red thread veins",
        "spider veins leg skin dermatology",
        "thread veins leg close up clinical",
        "leg spider angioma small veins photo",
    ],
    "C2_varicose": [
        "varicose veins leg bulging prominent clinical photo",
        "saphenous vein varicosity leg medical",
        "varicose veins leg treatment before photo",
        "bulging twisted veins leg photo",
        "large varicose vein leg close up",
    ],
    "C3_edema": [
        "venous edema ankle leg swelling photo",
        "pitting edema leg sock mark indentation photo",
        "ankle swelling venous insufficiency clinical",
        "leg edema swollen ankle dermatology",
        "bilateral leg edema venous photo",
        "foot ankle swelling pitting clinical",
    ],
    "C4_skin_changes": [
        "lipodermatosclerosis leg skin hardening brown photo",
        "venous stasis dermatitis hyperpigmentation leg",
        "hemosiderin staining leg venous insufficiency",
        "venous eczema leg skin discoloration photo",
        "stasis dermatitis leg brown pigmentation clinical",
    ],
    "C5_healed_ulcer": [
        "healed venous ulcer scar leg photo",
        "venous ulcer healed scarring gaiter area",
        "post venous ulcer leg scar pigmentation",
        "healed leg ulcer white scar tissue photo",
        "venous ulcer healed clinical before after",
    ],
    "C6_active_ulcer": [
        "venous leg ulcer open wound clinical photo",
        "active venous ulcer wound lower leg medical",
        "chronic venous ulcer gaiter area open",
        "leg ulcer wound exudate clinical photo",
        "venous stasis ulcer open wound dermatology",
    ],
}

# 넓은 검색어 - label_tool로 수동 분류할 이미지 수집
GENERAL_QUERIES = [
    "varicose vein CEAP classification clinical photo",
    "chronic venous disease leg CEAP stages photo",
    "venous insufficiency leg clinical stages photo",
    "varicose vein leg clinical examination photo",
    "CEAP venous disease leg dermatology photo",
]


def download_image(url: str, save_path: Path) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200 and len(resp.content) > 5000:
            save_path.write_bytes(resp.content)
            return True
    except Exception:
        pass
    return False


def collect_for_class(category: str, queries: list[str], max_per_query: int = 50):
    save_dir = BASE_DIR / "crawled" / category
    save_dir.mkdir(parents=True, exist_ok=True)

    existing = list(save_dir.glob("*.jpg")) + list(save_dir.glob("*.png"))
    idx = len(existing) + 1
    total_saved = 0

    for query in queries:
        print(f"  검색: '{query}'")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(query, max_results=max_per_query))
            for r in results:
                save_path = save_dir / f"extra_{idx:04d}.jpg"
                if download_image(r["image"], save_path):
                    idx += 1
                    total_saved += 1
                time.sleep(0.3)
        except Exception as e:
            print(f"  오류: {e}")
        time.sleep(2)

    print(f"  → {category}: +{total_saved}장 추가")
    return total_saved


def collect_general(max_per_query: int = 80):
    """넓은 검색어로 수집 → data/raw/crawled/unlabeled/ 에 저장 → label_tool로 분류"""
    save_dir = BASE_DIR / "crawled" / "unlabeled"
    save_dir.mkdir(parents=True, exist_ok=True)

    existing = list(save_dir.glob("*.jpg")) + list(save_dir.glob("*.png"))
    idx = len(existing) + 1
    total_saved = 0

    print(f"\n[일반 수집] → data/raw/crawled/unlabeled/ (label_tool로 수동 분류 필요)")
    for query in GENERAL_QUERIES:
        print(f"  검색: '{query}'")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(query, max_results=max_per_query))
            for r in results:
                save_path = save_dir / f"gen_{idx:04d}.jpg"
                if download_image(r["image"], save_path):
                    idx += 1
                    total_saved += 1
                time.sleep(0.3)
        except Exception as e:
            print(f"  오류: {e}")
        time.sleep(2)

    print(f"  → 일반 수집: {total_saved}장 (label_tool로 분류 필요)")
    return total_saved


def main():
    parser = argparse.ArgumentParser(description="추가 이미지 수집")
    parser.add_argument("--classes", nargs="+",
                        choices=list(EXTRA_QUERIES.keys()) + ["all"],
                        default=["all"],
                        help="보강할 클래스 (예: C5_healed_ulcer C6_active_ulcer)")
    parser.add_argument("--general", action="store_true",
                        help="넓은 키워드로 수집 후 label_tool로 분류")
    parser.add_argument("--max", type=int, default=50,
                        help="쿼리당 최대 수집 수 (기본: 50)")
    args = parser.parse_args()

    print("=" * 50)
    print("추가 이미지 수집")
    print("=" * 50)

    if args.general:
        collect_general(max_per_query=args.max)

    target = list(EXTRA_QUERIES.keys()) if "all" in args.classes else args.classes
    if target:
        print(f"\n[클래스별 추가 수집] 대상: {target}")
        for cls in target:
            print(f"\n클래스: {cls}")
            collect_for_class(cls, EXTRA_QUERIES[cls], max_per_query=args.max)

    print("\n완료!")
    print("다음 단계:")
    if args.general:
        print("  1. streamlit run label_tool.py 로 unlabeled 이미지 분류")
    print("  2. python src/filter_images.py 로 CLIP 필터링")
    print("  3. python run_pipeline.py --skip-collect 로 재학습")


if __name__ == "__main__":
    main()
