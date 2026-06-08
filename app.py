"""
하지정맥류 AI 자가진단 서비스
병무청·방위사업청·질병관리청 합동 공공데이터·AI 활용 경진대회 출품작
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

st.set_page_config(
    page_title="하지정맥류 AI 자가진단",
    page_icon="assets/favicon.ico" if Path("assets/favicon.ico").exists() else None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── 전역 배경 ── */
[data-testid="stAppViewContainer"] { background: #f0f2f5; }
[data-testid="stMain"] { background: #f0f2f5; }

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0;
}
[data-testid="stSidebar"] * { color: #334155 !important; }

/* ── 사이드바 버튼 탭 ── */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background: transparent !important;
    border: none !important;
    color: #64748b !important;
    font-size: 0.88rem !important;
    font-weight: 400 !important;
    text-align: left !important;
    padding: 0.55rem 0.9rem !important;
    border-radius: 6px !important;
    width: 100% !important;
    margin-bottom: 2px !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
    background: #f1f5f9 !important;
    color: #1e293b !important;
    border: none !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
    background: #eff6ff !important;
    border: none !important;
    border-left: 3px solid #1d4ed8 !important;
    color: #1d4ed8 !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    text-align: left !important;
    padding: 0.55rem 0.9rem !important;
    border-radius: 0 6px 6px 0 !important;
    width: 100% !important;
    margin-bottom: 2px !important;
    box-shadow: none !important;
}

/* ── 타이포그래피 ── */
.page-title {
    font-size: 1.75rem; font-weight: 700;
    color: #0f172a; letter-spacing: -0.5px;
    margin-bottom: 0.25rem; line-height: 1.2;
}
.page-sub {
    font-size: 0.88rem; color: #64748b;
    margin-bottom: 1.5rem;
}

/* ── 카드 ── */
.result-box {
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    margin: 0.6rem 0;
}

/* ── 진행 단계 ── */
.step-active {
    background: #0f172a; color: #ffffff;
    padding: 0.55rem 1rem; border-radius: 6px;
    font-weight: 600; font-size: 0.85rem; text-align: center;
}
.step-done {
    background: #dcfce7; color: #166534;
    padding: 0.55rem 1rem; border-radius: 6px;
    font-weight: 600; font-size: 0.85rem; text-align: center;
}
.step-todo {
    background: #f1f5f9; color: #94a3b8;
    padding: 0.55rem 1rem; border-radius: 6px;
    font-size: 0.85rem; text-align: center;
}

/* ── 주의 박스 ── */
.notice-box {
    background: #fffbeb;
    border-left: 3px solid #f59e0b;
    padding: 0.75rem 0.9rem;
    border-radius: 4px;
    font-size: 0.8rem;
    color: #78350f;
    line-height: 1.55;
}

/* ── 기타 ── */
h1, h2, h3, h4 { color: #0f172a; }
hr { border-color: #e2e8f0; }
[data-testid="stMetricValue"] { color: #1d4ed8 !important; }

/* ── 반응형 (모바일) ── */
@media (max-width: 640px) {
    /* 컬럼 세로 쌓기 */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0.5rem !important;
    }
    [data-testid="column"] {
        width: 100% !important;
        flex: none !important;
        min-width: 100% !important;
    }

    /* 폰트 크기 조정 */
    .page-title { font-size: 1.3rem !important; }
    .page-sub { font-size: 0.8rem !important; }
    .step-active, .step-done, .step-todo {
        font-size: 0.75rem !important;
        padding: 0.4rem 0.6rem !important;
    }

    /* 이미지 넘침 방지 */
    img { max-width: 100% !important; height: auto !important; }

    /* 여백 축소 */
    [data-testid="stMain"] .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }

    /* 메트릭 카드 크기 */
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }
}

@media (max-width: 480px) {
    .page-title { font-size: 1.1rem !important; }
    .notice-box { font-size: 0.72rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ───────── CEAP 정보 ─────────
CEAP_ORDER = ["C0_normal", "C1_watch", "C2_consult", "C34_danger", "C56_emergency"]

RESULT_INFO = {
    "C0_normal": {
        "label": "정상 (C0)", "color": "#2ecc71",
        "desc": "육안으로 혈관 이상 소견이 없습니다.",
        "advice": "현재 증상이 없더라도 위험인자가 있다면 주기적으로 확인하세요. 압박 스타킹 착용을 권장합니다.",
        "urgency": "정상",
    },
    "C1_watch": {
        "label": "관찰 단계 (C1)", "color": "#27ae60",
        "desc": "거미줄 모양의 가는 혈관(모세혈관 확장)이 관찰됩니다.",
        "advice": "당장 치료가 필요하지 않지만 압박 스타킹 착용을 권장합니다. 증상이 심해지면 전문의 상담을 받으세요.",
        "urgency": "경과 관찰",
    },
    "C2_consult": {
        "label": "진료 권고 (C2)", "color": "#f39c12",
        "desc": "굵고 구불구불한 정맥류가 관찰됩니다 (3mm 이상).",
        "advice": "혈관외과 전문의 진료를 권장합니다. 경화요법, 레이저, 고주파 치료 등 다양한 치료법이 있습니다.",
        "urgency": "진료 권장",
    },
    "C34_danger": {
        "label": "병원 필수 (C3-C4)", "color": "#e74c3c",
        "desc": "정맥성 부종(붓기) 또는 피부 색소침착·습진·경화 등 피부 변화가 관찰됩니다.",
        "advice": "빠른 시일 내 혈관외과 전문의 진료를 받으세요. 방치하면 궤양으로 악화될 수 있습니다.",
        "urgency": "병원 방문 필요",
    },
    "C56_emergency": {
        "label": "즉시 방문 (C5-C6)", "color": "#c0392b",
        "desc": "정맥 궤양(치유된 흔적 또는 현재 진행 중인 궤양)이 의심됩니다.",
        "advice": "즉시 혈관외과 전문의 진료를 받으시기 바랍니다. 방치 시 감염 및 심각한 합병증 위험이 있습니다.",
        "urgency": "즉시 진료",
    },
}

# ───────── 사이드바 ─────────
if 'page' not in st.session_state:
    st.session_state.page = "홈"

MENU_ITEMS = ["홈", "AI 진단", "통계", "치료법 안내", "보험·비용", "CEAP 안내", "병원 찾기"]

with st.sidebar:
    st.markdown("<div style='padding:1.2rem 0 0.3rem; font-size:1rem; font-weight:700; color:#0f172a; letter-spacing:-0.3px;'>하지정맥류 AI 자가진단</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.75rem; color:#94a3b8; margin-bottom:1rem;'>VCSS 기반 설문 + AI 이미지 분석</div>", unsafe_allow_html=True)
    st.markdown("---")
    for menu in MENU_ITEMS:
        is_active = st.session_state.page == menu
        if st.button(menu, key=f"nav_{menu}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.page = menu
            st.rerun()
    st.markdown("---")
    st.markdown("""
    <div class='notice-box'>
    본 서비스는 의료기기가 아닙니다.<br>
    진단 결과는 참고용이며 반드시 전문의 진료를 받으시기 바랍니다.
    </div>
    """, unsafe_allow_html=True)

page = st.session_state.page


# ───────── 단계별 가이드 데이터 ─────────
CEAP_GUIDE = {
    "C0_normal": {
        "stocking": "예방용 15-20mmHg (선택)",
        "exercise": ["걷기 30분/일", "수영·자전거 (다리 부담 적음)", "발목 올리기·내리기 반복"],
        "lifestyle": ["장시간 기립/좌식 시 틈틈이 다리 움직이기", "잠잘 때 다리 15-20cm 높이기", "체중 정상 범위 유지", "꽉 끼는 옷·하이힐 피하기"],
        "caution": "현재 정상이나 위험인자가 있으면 6개월-1년마다 자가 확인을 권장합니다.",
    },
    "C1_watch": {
        "stocking": "15-20mmHg (착용 권장)",
        "exercise": ["걷기·수영·자전거", "다리 올리기 (하루 2-3회, 15분)", "발목 회전 운동"],
        "lifestyle": ["오래 서 있을 때 발목 운동 병행", "다리 꼬는 자세 금지", "잠잘 때 다리 높이기", "저염식으로 붓기 예방"],
        "caution": "치료가 급하지 않지만 악화 예방을 위해 생활습관 관리가 중요합니다.",
    },
    "C2_consult": {
        "stocking": "20-30mmHg (강력 권장)",
        "exercise": ["수영·자전거 (달리기보다 권장)", "다리 올리기 하루 3회 이상", "장시간 기립 직업이면 중간중간 앉아서 쉬기"],
        "lifestyle": ["전문의 진료 후 치료 계획 수립", "압박 스타킹 아침에 기상 직후 착용", "열탕·사우나 피하기 (혈관 확장)", "장거리 비행 시 압박 스타킹 필수"],
        "caution": "방치하면 C3 이상으로 진행될 수 있습니다. 혈관외과 진료를 받으세요.",
    },
    "C34_danger": {
        "stocking": "30-40mmHg (처방 권장)",
        "exercise": ["가벼운 걷기만 권장", "격렬한 운동 자제", "다리 올리기 하루 수회"],
        "lifestyle": ["빠른 시일 내 전문의 진료 필수", "피부 보습 관리 (건조하면 악화)", "상처나 긁힘 주의", "부종 심할 때 다리 올리고 안정"],
        "caution": "이 단계에서 방치하면 궤양으로 악화될 수 있습니다. 반드시 치료를 받으세요.",
    },
    "C56_emergency": {
        "stocking": "30-40mmHg (치료 후 처방)",
        "exercise": ["치료 중 격렬한 운동 금지", "가벼운 발목 운동만"],
        "lifestyle": ["즉시 혈관외과 방문", "상처 부위 청결 유지", "임의로 상처 건드리지 않기", "치료 중 의료진 지시 준수"],
        "caution": "즉시 진료가 필요한 상태입니다. 감염 및 심각한 합병증 예방을 위해 병원을 방문하세요.",
    },
}

# ───────── 치료법 데이터 ─────────
TREATMENTS = [
    {
        "name": "압박 스타킹",
        "type": "보존적 치료",
        "ceap": "C0-C6 (전 단계)",
        "method": "의료용 압박 스타킹 착용으로 정맥 압력 감소 및 증상 완화",
        "pros": ["비침습적", "즉시 시작 가능", "보험 적용 가능", "수술 후 필수 관리"],
        "cons": ["완치 불가 (증상 관리)", "매일 착용 필요", "여름철 불편", "역류 있어야 급여"],
        "recovery": "없음",
        "insurance": "✅ 급여 — 하지정맥류 진단 + 역류 소견 시 처방전으로 연 2켤레 건강보험 적용",
        "color": "#2ecc71",
    },
    {
        "name": "경화요법",
        "type": "비수술적 치료",
        "ceap": "C1-C3 (수술 후 잔존 혈관 포함)",
        "method": "경화제(폴리도카놀 등)를 정맥에 주사해 혈관벽 염증 유발 후 폐쇄",
        "pros": ["외래 시술 (입원 불필요)", "흉터 거의 없음", "C1 모세혈관에 효과적"],
        "cons": ["굵은 혈관(C2 이상)은 재발률 높음", "여러 번 시술 필요", "색소침착 부작용 가능"],
        "recovery": "당일 귀가, 1-2주 압박 스타킹 착용",
        "insurance": "✅ 일반 경화요법: 역류 소견 + 증상 동반 시 급여\n\n❌ 초음파 유도하 경화요법: 비급여",
        "color": "#3498db",
    },
    {
        "name": "레이저 치료 (EVLT)",
        "type": "비수술적 치료",
        "ceap": "C2-C4 (복재정맥 역류 동반)",
        "method": "카테터로 레이저를 삽입, 광에너지로 정맥 내벽을 태워 혈관 폐쇄",
        "pros": ["절개 최소화", "흉터 거의 없음", "재발률 낮음", "수술 대비 빠른 회복"],
        "cons": ["비급여 (비용 부담)", "복재정맥 외 적용 제한", "열 손상 부작용 가능"],
        "recovery": "4-5일 후 일상 복귀, 수주간 압박 스타킹 착용",
        "insurance": "❌ 비급여 (2025년 NECA 의료기술재평가 안전유효 권고, 건강보험 급여는 미전환)",
        "color": "#9b59b6",
    },
    {
        "name": "고주파 치료 (RFA)",
        "type": "비수술적 치료",
        "ceap": "C2-C4 (복재정맥 역류 동반)",
        "method": "카테터로 고주파 열에너지를 전달해 정맥벽 콜라겐 변성 후 폐쇄",
        "pros": ["EVLT 대비 통증 적음", "멍·혈종 발생 빈도 낮음", "빠른 회복", "재발률 낮음"],
        "cons": ["비급여 (비용 부담)", "모든 병원에서 시행하지 않음"],
        "recovery": "4-5일 후 일상 복귀, 수주간 압박 스타킹 착용",
        "insurance": "❌ 비급여 (2025년 NECA 의료기술재평가 안전유효 권고, 건강보험 급여는 미전환)",
        "color": "#e67e22",
    },
    {
        "name": "수술 (정맥 발거술)",
        "type": "수술적 치료",
        "ceap": "C2-C6 (역류 동반)",
        "method": "피부를 절개해 역류가 있는 복재정맥을 직접 제거 (스트리핑)",
        "pros": ["근본적 치료", "재발률 낮음", "건강보험 급여 적용"],
        "cons": ["척추마취 또는 전신마취 필요", "회복 기간 상대적으로 길음", "흉터 가능"],
        "recovery": "약 1주일 회복, 4-6주 압박 스타킹 착용",
        "insurance": "✅ 건강보험 급여 — 혈관초음파상 역류 0.5초 이상 + 증상으로 일상생활 지장 조건 충족 시",
        "color": "#e74c3c",
    },
]

# ───────── 헬퍼 함수 ─────────

def calculate_risk(part1: dict) -> tuple:
    score = 0
    factors = []

    age = part1.get('age', '선택 안함')
    if age in ['50대', '60대', '70대 이상']:
        score += 2; factors.append('고령(50대+)')
    elif age == '40대':
        score += 1; factors.append('중년(40대)')

    if part1.get('gender') == '여성':
        score += 2; factors.append('여성')

    bmi = part1.get('bmi', '선택 안함')
    if bmi == '비만 (25 이상)':
        score += 2; factors.append('비만')
    elif bmi == '과체중 (23~25)':
        score += 1; factors.append('과체중')

    standing = part1.get('standing', '선택 안함')
    if standing == '8시간 이상':
        score += 3; factors.append('장시간 기립(8h+)')
    elif standing == '4~8시간':
        score += 1; factors.append('기립 4~8h')

    if part1.get('family') == '있음':
        score += 3; factors.append('가족력')

    pregnancy = part1.get('pregnancy', '없음')
    if pregnancy == '2회 이상':
        score += 3; factors.append('임신 2회 이상')
    elif pregnancy == '1회':
        score += 2; factors.append('임신 경험')

    if part1.get('hormone') == '예':
        score += 1; factors.append('호르몬 치료')

    if score <= 2:
        level, color = '낮음', '#2ecc71'
    elif score <= 5:
        level, color = '보통', '#f39c12'
    elif score <= 9:
        level, color = '높음', '#e74c3c'
    else:
        level, color = '매우 높음', '#c0392b'

    return score, level, color, factors


def survey_ceap_estimate(part2: dict) -> str:
    ulcer      = part2.get('ulcer', False)
    skin       = part2.get('skin_change', False)
    edema      = part2.get('edema', False)
    pain       = part2.get('pain', False)
    cramp      = part2.get('cramp', False)
    vein       = part2.get('visible_vein', 0)  # 0=없음, 1=거미줄, 2=굵고구불구불

    if ulcer:
        return 'C56_emergency'
    if skin and edema:
        return 'C34_danger'
    if edema and (pain or cramp):
        return 'C34_danger'
    if vein == 2:
        return 'C2_consult'
    if vein == 1:
        return 'C1_watch'
    return 'C0_normal'


def combine_ai_survey(ai_result: dict | None, survey_ceap: str) -> tuple:
    """Returns (final_class, note)"""
    if ai_result is None:
        return survey_ceap, None

    ai_class = ai_result['class']
    ai_conf  = ai_result['confidence']

    if ai_class == 'uncertain' or ai_conf < 0.65:
        return survey_ceap, '⚠️ AI 신뢰도 낮음 — 재촬영을 권장합니다'

    ai_idx     = CEAP_ORDER.index(ai_class)
    survey_idx = CEAP_ORDER.index(survey_ceap)

    if survey_idx > ai_idx:
        higher = RESULT_INFO[survey_ceap]['label']
        return ai_class, f'⚠️ 증상 기반 {higher} 가능성 있음 — 전문의 확인 권장'
    elif survey_idx < ai_idx:
        return ai_class, '📋 현재 자각 증상 없음 (무증상)'
    else:
        return ai_class, None


# ═══════════════════════════════
# 홈 페이지
# ═══════════════════════════════
if page == "홈":
    st.markdown('<p class="page-title">하지정맥류 AI 자가진단 서비스</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">VCSS 기반 설문과 AI 이미지 분석으로 하지정맥류 단계를 확인합니다</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("AI 분류 정확도", "84.2%", "EfficientNet-B2")
    with col2:
        st.metric("진단 단계", "5단계", "CEAP C0-C6")
    with col3:
        st.metric("설문 기반", "VCSS + KNHANES", "질병관리청 연계")

    st.markdown("---")

    cta_col, _ = st.columns([1, 1])
    with cta_col:
        if st.button("AI 진단 시작하기", type="primary", use_container_width=True):
            for k in ['diag_step', 'part1', 'part2', 'ai_result', 'survey_ceap']:
                st.session_state.pop(k, None)
            st.session_state.page = "AI 진단"
            st.rerun()

    st.markdown("")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### 사용 방법
        1. **설문** — 위험인자 + 현재 증상 입력 (필수)
        2. **AI 분석** — 다리 사진 업로드 (선택, 권장)
        3. **결과 확인** — 종합 판정 및 권고사항
        4. **병원 안내** — 가까운 혈관외과 찾기

        #### 주요 기능
        - **VCSS 기반 설문**: 위험인자 + 증상 스크리닝
        - **AI 이미지 분석**: EfficientNet-B2로 CEAP 단계 판별
        - **통합 결과**: 설문 + AI 결합 분석
        - **질병관리청 공공데이터**: KNHANES 위험인자 통계 연계
        """)
    with col2:
        st.markdown("""
        #### 서비스 특징
        - 설문만으로도 CEAP 단계 추정 가능
        - AI 사진 분석으로 정확도 향상
        - 두 결과가 다를 경우 안전한 방향으로 안내
        - 사진은 서버에 저장되지 않습니다

        #### 출처
        - 설문 위험 가중치: 질병관리청 국민건강영양조사(KNHANES)
        - 증상 분류 기준: VCSS(Venous Clinical Severity Score)
        - 임상 근거: 한국정맥학회 임상진료지침
        - AI 모델: EfficientNet-B2 전이학습 (ImageNet)
        """)


# ═══════════════════════════════
# AI 진단 페이지
# ═══════════════════════════════
elif page == "AI 진단":

    # 세션 상태 초기화
    for key, val in [('diag_step', 1), ('part1', {}), ('part2', {}),
                     ('ai_result', None), ('survey_ceap', None)]:
        if key not in st.session_state:
            st.session_state[key] = val

    step = st.session_state.diag_step

    # 진행 단계 표시
    step_labels = ["01  설문", "02  AI 분석 (선택)", "03  결과"]
    cols = st.columns(3)
    for i, (col, label) in enumerate(zip(cols, step_labels)):
        with col:
            if i + 1 == step:
                st.markdown(f"<div class='step-active'>▶ {label}</div>", unsafe_allow_html=True)
            elif i + 1 < step:
                st.markdown(f"<div class='step-done'>✅ {label}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='step-todo'>{label}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ── STEP 1: 설문 ──────────────────────────────────────
    if step == 1:
        st.markdown('<p class="page-title">위험인자 + 증상 설문</p>', unsafe_allow_html=True)
        st.caption("위험 가중치: 질병관리청 KNHANES | 증상 항목: VCSS(Venous Clinical Severity Score) 기반")

        with st.form("survey_form"):
            st.markdown("#### 파트 1 — 배경 위험인자")
            c1, c2, c3 = st.columns(3)
            with c1:
                age     = st.selectbox("연령대", ["선택 안함", "20대", "30대", "40대", "50대", "60대", "70대 이상"])
                gender  = st.selectbox("성별", ["선택 안함", "남성", "여성"])
            with c2:
                bmi      = st.selectbox("BMI (체질량지수)", ["선택 안함", "정상 (18.5~23)", "과체중 (23~25)", "비만 (25 이상)"])
                standing = st.selectbox("하루 기립 시간", ["선택 안함", "4시간 미만", "4~8시간", "8시간 이상"])
            with c3:
                family = st.selectbox("가족력 (부모/형제 하지정맥류)", ["선택 안함", "없음", "있음"])
                if gender == "여성":
                    pregnancy = st.selectbox("임신 경험", ["없음", "1회", "2회 이상"])
                    hormone   = st.selectbox("피임약 또는 호르몬 치료 중", ["아니오", "예"])
                else:
                    pregnancy = "없음"
                    hormone   = "아니오"
                    st.caption("임신/호르몬 항목은 여성만 해당됩니다.")

            st.markdown("---")
            st.markdown("#### 파트 2 — 현재 증상 (VCSS 기반)")
            st.caption("현재 경험하고 있는 증상을 모두 선택하세요")

            s1, s2 = st.columns([1, 1])
            with s1:
                pain  = st.checkbox("다리가 무겁거나 통증/쑤심이 있다")
                edema = st.checkbox("저녁에 발목이나 종아리가 붓는다")
                cramp = st.checkbox("새벽에 종아리 쥐가 나서 깬다 (야간 경련)")
            with s2:
                visible_vein = st.radio(
                    "다리에 혈관이 보이나요?",
                    ["없음",
                     "가는 거미줄/실핏줄이 보인다",
                     "굵고 구불구불한 혈관이 튀어나와 보인다"],
                )
                skin_change = st.checkbox("다리 피부색이 변하거나 갈색·검붉은 반점이 생겼다")
                ulcer       = st.checkbox("다리에 잘 낫지 않는 상처나 궤양이 있다")

            st.markdown("")
            submitted = st.form_submit_button("설문 완료", type="primary", use_container_width=True)

        if submitted:
            required = {'age': age, 'gender': gender, 'bmi': bmi,
                        'standing': standing, 'family': family}
            missing = [k for k, v in required.items() if v == '선택 안함']
            if missing:
                label_map = {
                    'age': '연령대', 'gender': '성별', 'bmi': 'BMI',
                    'standing': '하루 기립 시간', 'family': '가족력',
                }
                st.warning(f"파트 1에서 선택하지 않은 항목이 있습니다: **{', '.join(label_map[k] for k in missing)}** — 정확한 위험도 산출을 위해 가능한 한 모두 입력해주세요.")

            vein_map = {
                "없음": 0,
                "가는 거미줄/실핏줄이 보인다": 1,
                "굵고 구불구불한 혈관이 튀어나와 보인다": 2,
            }
            st.session_state.part1 = {
                'age': age, 'gender': gender, 'bmi': bmi,
                'standing': standing, 'family': family,
                'pregnancy': pregnancy, 'hormone': hormone,
            }
            st.session_state.part2 = {
                'pain': pain, 'edema': edema, 'cramp': cramp,
                'visible_vein': vein_map[visible_vein],
                'skin_change': skin_change, 'ulcer': ulcer,
            }
            st.session_state.survey_ceap = survey_ceap_estimate(st.session_state.part2)
            st.session_state.diag_step   = 2
            st.rerun()

    # ── STEP 2: AI 분석 ────────────────────────────────────
    elif step == 2:
        st.markdown('<p class="page-title">AI 이미지 분석</p>', unsafe_allow_html=True)

        survey_ceap  = st.session_state.survey_ceap
        survey_info  = RESULT_INFO[survey_ceap]
        survey_color = survey_info['color']

        st.markdown(f"""
        <div style='background:{survey_color}15; border:1px solid {survey_color};
                    padding:1rem; border-radius:8px; margin-bottom:1rem;'>
            <b>설문 기반 추정:</b>
            <span style='color:{survey_color}; font-weight:bold; font-size:1.1rem'>
                {survey_info['label']}
            </span>
            <span style='color:#888; font-size:0.85rem'> — 설문 단독, 정확도 낮음</span>
        </div>
        """, unsafe_allow_html=True)

        st.info("📷 AI 사진 분석을 추가하면 정확도가 높아집니다. 사진 촬영이 어려우면 아래 '설문 결과로 보기'를 누르세요.")

        col1, col2 = st.columns([1, 1])
        with col1:
            uploaded = st.file_uploader("다리 사진 업로드 (JPG, PNG)", type=["jpg", "jpeg", "png"])
            if uploaded:
                image = Image.open(uploaded)
                st.image(image, caption="업로드된 이미지", use_column_width=True)
            st.markdown("""
            **촬영 가이드**
            - ✅ 무릎 아래 ~ 발목 부위 포함
            - ✅ 자연광 또는 밝은 조명
            - ✅ 다리를 펴고 정면에서 촬영
            - ❌ 스타킹·양말 착용 불가
            """)

        with col2:
            if uploaded:
                model_path = Path("models/best_model.pth")
                if model_path.exists():
                    with st.spinner("AI 분석 중..."):
                        try:
                            from predict import predict
                            result = predict(image)
                            st.session_state.ai_result = result
                            color = result['info']['color']
                            st.markdown(f"""
                            <div class='result-box' style='background:{color}22; border:2px solid {color};'>
                                <b>AI 분석 결과</b><br>
                                <h3 style='color:{color}'>{result['label']}</h3>
                                <p>신뢰도: {result['confidence']:.1%}</p>
                                <p style='font-size:0.9rem'>{result['info']['desc']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"분석 오류: {e}")
                            st.session_state.ai_result = None
                else:
                    st.warning("모델 파일을 찾을 수 없습니다.")
            else:
                st.info("👆 사진을 업로드하면 AI 분석 결과가 여기에 표시됩니다.")

        st.markdown("---")
        col_skip, col_next = st.columns(2)
        with col_skip:
            if st.button("설문 결과로 보기", use_container_width=True):
                st.session_state.ai_result = None
                st.session_state.diag_step = 3
                st.rerun()
        with col_next:
            ai_ready = st.session_state.ai_result is not None
            if st.button("AI 분석 결과 포함", type="primary",
                         use_container_width=True, disabled=not ai_ready):
                st.session_state.diag_step = 3
                st.rerun()

    # ── STEP 3: 결과 ───────────────────────────────────────
    elif step == 3:
        st.markdown('<p class="page-title">종합 결과</p>', unsafe_allow_html=True)

        survey_ceap = st.session_state.survey_ceap
        ai_result   = st.session_state.ai_result
        part1       = st.session_state.part1
        part2       = st.session_state.part2

        final_class, note = combine_ai_survey(ai_result, survey_ceap)
        final_info        = RESULT_INFO[final_class]
        risk_score, risk_level, risk_color, risk_factors = calculate_risk(part1)

        ai_used  = ai_result is not None and ai_result.get('class') != 'uncertain'
        source   = "AI + 설문 종합 판정" if ai_used else "설문 기반 추정 (AI 미실시)"
        color    = final_info['color']

        # 최종 판정 박스
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class='result-box' style='background:{color}22; border:2px solid {color};'>
                <p style='color:#888; font-size:0.8rem; margin:0'>{source}</p>
                <h2 style='color:{color}; margin:0.3rem 0'>{final_info['label']}</h2>
                <p style='margin:0.3rem 0'>{final_info['desc']}</p>
                <p style='font-size:0.85rem; color:#666; margin:0'>{final_info['urgency']}</p>
                {"<hr style='margin:0.8rem 0'><p style='color:#e67e22; font-size:0.9rem; margin:0'>" + note + "</p>" if note else ""}
            </div>
            """, unsafe_allow_html=True)

            if not ai_used:
                st.caption("※ AI 사진 분석을 하지 않아 정확도가 낮을 수 있습니다. 사진 분석을 권장합니다.")

            st.info(f"💡 {final_info['advice']}")

        with col2:
            st.markdown(f"""
            <div class='result-box' style='background:{risk_color}15; border:1px solid {risk_color};'>
                <b>위험인자 분석</b>
                <h3 style='color:{risk_color}; margin:0.3rem 0'>위험도 {risk_level}</h3>
                <p style='margin:0'>해당 위험인자: {', '.join(risk_factors) if risk_factors else '없음'}</p>
            </div>
            """, unsafe_allow_html=True)
            st.caption("※ 출처: 질병관리청 국민건강영양조사(KNHANES), 2023 한국정맥학회 임상진료지침")

            # AI 확률 분포
            if ai_used and ai_result.get('probabilities'):
                label_map = {
                    "C0_normal": "정상(C0)", "C1_watch": "관찰(C1)",
                    "C2_consult": "진료권고(C2)", "C34_danger": "병원필수(C3-4)",
                    "C56_emergency": "즉시방문(C5-6)",
                }
                probs = {label_map[k]: v for k, v in ai_result["probabilities"].items()}
                fig = px.bar(
                    x=list(probs.values()), y=list(probs.keys()),
                    orientation="h", color=list(probs.values()),
                    color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
                    labels={"x": "확률", "y": ""},
                )
                fig.update_layout(height=200, showlegend=False,
                                  coloraxis_showscale=False,
                                  margin=dict(l=0, r=0, t=20, b=0),
                                  title="AI 단계별 확률")
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # 두 결과 비교 (AI 사용한 경우)
        if ai_used:
            survey_info = RESULT_INFO[survey_ceap]
            ai_info     = RESULT_INFO[ai_result['class']]
            sc, ac = survey_info['color'], ai_info['color']
            st.markdown("#### 판정 근거 비교")
            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown(f"""
                <div style='background:{sc}15; border:1px solid {sc};
                            padding:0.8rem; border-radius:8px;'>
                    <b>설문 추정</b><br>
                    <span style='color:{sc}; font-weight:bold'>{survey_info['label']}</span>
                </div>
                """, unsafe_allow_html=True)
            with cc2:
                st.markdown(f"""
                <div style='background:{ac}15; border:1px solid {ac};
                            padding:0.8rem; border-radius:8px;'>
                    <b>AI 분석</b><br>
                    <span style='color:{ac}; font-weight:bold'>{ai_info['label']}</span>
                    <span style='font-size:0.85rem; color:#888'> ({ai_result['confidence']:.1%})</span>
                </div>
                """, unsafe_allow_html=True)

        # 단계별 생활습관 가이드
        st.markdown("---")
        guide = CEAP_GUIDE[final_class]
        with st.expander(f"📋 {final_info['label']} 단계 — 생활습관 가이드", expanded=True):
            g1, g2, g3 = st.columns(3)
            with g1:
                st.markdown("**🧦 압박 스타킹**")
                st.info(guide["stocking"])
                st.markdown("**⚠️ 주의사항**")
                st.warning(guide["caution"])
            with g2:
                st.markdown("**🏃 권장 운동**")
                for ex in guide["exercise"]:
                    st.markdown(f"- {ex}")
            with g3:
                st.markdown("**🌿 생활습관**")
                for tip in guide["lifestyle"]:
                    st.markdown(f"- {tip}")

        st.markdown("---")
        col_r, col_h = st.columns(2)
        with col_r:
            if st.button("다시 진단하기", use_container_width=True):
                for k in ['diag_step', 'part1', 'part2', 'ai_result', 'survey_ceap']:
                    st.session_state.pop(k, None)
                st.rerun()
        with col_h:
            if st.button("병원 찾기", use_container_width=True, type="primary"):
                st.session_state.page = "병원 찾기"
                st.rerun()


# ═══════════════════════════════
# 치료법 안내 페이지
# ═══════════════════════════════
elif page == "치료법 안내":
    st.markdown('<p class="page-title">하지정맥류 치료법 안내</p>', unsafe_allow_html=True)
    st.caption("CEAP 단계별 치료 옵션을 비교합니다. 보험·비용 정보는 왼쪽 '보험·비용' 탭을 확인하세요.")

    import re
    def is_applicable(t: dict, n: int) -> bool:
        nums = list(map(int, re.findall(r'C(\d+)', t["ceap"])))
        if len(nums) >= 2:
            return nums[0] <= n <= nums[1]
        return nums[0] <= n if nums else True

    st.markdown("#### 내 단계에 맞는 치료법 보기")
    filter_ceap = st.select_slider(
        "CEAP 단계 선택 — 해당 단계에 적합한 치료법이 강조 표시됩니다",
        options=["C1", "C2", "C3", "C4", "C5", "C6"],
        value="C2",
    )
    ceap_num = int(filter_ceap[1])
    applicable_names = {t["name"] for t in TREATMENTS if is_applicable(t, ceap_num)}

    st.markdown("---")
    st.markdown("### 전체 치료법 비교")
    st.caption(f"🔵 파란 테두리 = **{filter_ceap} 단계에 적합한 치료법**")

    for treat in TREATMENTS:
        is_match = treat["name"] in applicable_names
        color = treat["color"]
        badge = "✅ 내 단계 적합" if is_match else ""
        with st.expander(f"{'🔵 ' if is_match else ''}{treat['name']} — {treat['type']} | {treat['ceap']}  {badge}", expanded=is_match):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown("**시술 방법**")
                st.markdown(treat["method"])
                st.markdown("**회복 기간**")
                st.markdown(treat["recovery"])
                st.markdown(treat["insurance"])
            with col2:
                st.markdown("**장점**")
                for p in treat["pros"]:
                    st.markdown(f"✅ {p}")
                st.markdown("**단점**")
                for c in treat["cons"]:
                    st.markdown(f"⚠️ {c}")
            with col3:
                st.markdown(f"""
                <div style='background:{color}22; border:2px solid {color};
                            border-radius:8px; padding:0.8rem; text-align:center;'>
                    <b style='color:{color}'>{treat['name']}</b><br>
                    <small>{treat['ceap']}</small>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 단계별 치료 선택 가이드")
    guide_table = pd.DataFrame({
        "CEAP 단계":  ["C1 (관찰)", "C2 (진료권고)", "C3 (부종)", "C4 (피부변화)", "C5-C6 (궤양)"],
        "1차 선택":   ["압박 스타킹", "압박 스타킹 + 경화요법", "레이저/고주파 또는 수술", "레이저/고주파 + 수술", "수술"],
        "보조 치료":  ["생활습관 개선", "생활습관 개선", "경화요법 병행", "압박 치료 병행", "상처 치료 병행"],
        "✅ 급여":    [
            "압박스타킹 (역류 소견 시)",
            "경화요법·수술 (역류 확인 시)",
            "수술 (역류 확인 시)",
            "수술",
            "수술·상처치료",
        ],
        "❌ 비급여":  [
            "경화요법 (미용 목적)",
            "레이저·고주파",
            "레이저·고주파",
            "레이저·고주파",
            "해당없음",
        ],
    })
    st.dataframe(guide_table, use_container_width=True)
    st.caption("※ 급여 기준: 혈관초음파상 역류 0.5초 이상 + 증상으로 일상생활 지장 조건 충족 시")
    st.info("💡 하지정맥류는 재발이 잦은 질환입니다. 치료 후에도 압박 스타킹 착용과 생활습관 관리가 중요합니다.")


# ═══════════════════════════════
# 보험·비용 페이지
# ═══════════════════════════════
elif page == "보험·비용":
    st.markdown('<p class="page-title">보험·비용 안내</p>', unsafe_allow_html=True)
    st.caption("건강보험 급여 기준, 실손보험 세대별 보장, 2026년 기준 시술 비용을 안내합니다.")

    st.markdown("### 건강보험 급여 안내")
    st.markdown("하지정맥류 치료는 **전통적 치료는 급여, 최신 시술은 비급여**로 나뉩니다.")

    ins_col1, ins_col2 = st.columns(2)
    with ins_col1:
        st.markdown("""
        <div style='background:#dcfce7; border-left:4px solid #16a34a;
                    padding:1rem; border-radius:4px; height:100%;'>
        <b style='color:#15803d; font-size:1rem'>✅ 건강보험 급여</b><br>
        <small style='color:#166534'>역류 0.5초 이상 + 증상 동반 조건 충족 시</small><br><br>
        <b>압박 스타킹</b><br>
        · 의사 처방전으로 연 2켤레 급여<br>
        · 의료기기 허가 제품(mmHg 표기)만 해당<br>
        · 본인부담금: 외래 30%, 입원 20%<br><br>
        <b>일반 경화요법</b><br>
        · 역류 소견 + 증상 동반 시 급여<br>
        · 미용 목적은 비급여<br><br>
        <b>수술 (발거술·스트리핑)</b><br>
        · 역류 0.5초 이상 + 증상 동반 시 급여<br>
        · 본인부담: 외래(의원) 30%, 입원 20%<br>
        · 실제 부담금: 한쪽 약 30만원 수준
        </div>
        """, unsafe_allow_html=True)
    with ins_col2:
        st.markdown("""
        <div style='background:#fee2e2; border-left:4px solid #dc2626;
                    padding:1rem; border-radius:4px; height:100%;'>
        <b style='color:#b91c1c; font-size:1rem'>❌ 비급여 (전액 본인부담)</b><br>
        <small style='color:#991b1b'>2026년 6월 현재 급여 전환 미완료</small><br><br>
        <b>레이저 치료 (EVLT)</b><br>
        · 2025년 9월 NECA 안전유효 권고 완료<br>
        · 건강보험 급여 전환 행정 절차 진행 중<br>
        · 비용: 한쪽 100~300만원 (중간값 약 200만원)<br><br>
        <b>고주파 치료 (RFA)</b><br>
        · 2025년 9월 NECA 안전유효 권고 완료<br>
        · 건강보험 급여 전환 행정 절차 진행 중<br>
        · 비용: 한쪽 150~200만원<br><br>
        <b>초음파 유도하 경화요법</b><br>
        · 심부 혈관 치료에 사용<br>
        · 비용: 20~50만원/회 (반복 시술 필요)
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 치료법별 예상 비용 (2026년 기준)")
    cost_df = pd.DataFrame({
        "치료법":         ["압박 스타킹", "일반 경화요법", "초음파유도 경화요법", "레이저 EVLT", "고주파 RFA", "수술 발거술"],
        "급여":           ["✅ 급여", "✅ 급여", "❌ 비급여", "❌ 비급여", "❌ 비급여", "✅ 급여"],
        "한쪽 예상 비용":  ["본인부담 소액", "급여 적용 시 소액", "20~50만원/회", "100~300만원", "150~200만원", "본인부담 약 30만원"],
        "양쪽 예상 비용":  ["-", "-", "40~100만원", "200~350만원", "250~400만원", "본인부담 약 60만원"],
        "실손보험":       ["-", "-", "치료목적 시 가능", "치료목적 시 가능", "치료목적 시 가능", "- (급여)"],
    })
    st.dataframe(cost_df, use_container_width=True, hide_index=True)
    st.caption("※ 심평원 비급여 진료비 공개 기준 (2025년 10월). 병원·시술 범위에 따라 편차 큼. hira.or.kr/npay 에서 병원별 조회 가능.")

    st.markdown("---")
    st.markdown("### 실손보험 세대별 보장 안내")
    st.markdown("레이저·고주파는 비급여이므로 **실손보험** 가입 여부가 실제 부담 비용을 결정합니다.")

    silson_df = pd.DataFrame({
        "세대":            ["1세대", "2세대", "3세대", "4세대", "5세대 (2026.5~)"],
        "가입기간":        ["~2009.9", "2009.10~2017.3", "2017.4~2021.6", "2021.7~2026.4", "2026.5~"],
        "비급여 자기부담": ["0%(손보)/20%(생보)", "10~20%", "20~30%", "30%", "50%"],
        "연간 한도":       ["5,000만원", "5,000만원", "5,000만원", "5,000만원", "1,000만원"],
        "EVLT 200만원 시 부담": ["0~40만원", "20~40만원", "40~60만원", "60만원", "100만원"],
    })
    st.dataframe(silson_df, use_container_width=True, hide_index=True)

    st.warning(
        "2026년 5월 출시된 5세대 실손보험은 비중증 비급여 자기부담이 50%, 연간 한도 1,000만원으로 "
        "이전 세대 대비 보장이 크게 줄었습니다. 양쪽 시술 시 한도 부족 위험이 있습니다."
    )

    st.markdown("**실손보험 적용 조건**")
    st.markdown("""
    - **치료 목적**이어야 함 — 미용 목적은 실손도 적용 불가
    - 병원에서 **치료 목적 확인서 + 진단서** 발급 필요 (질병코드 I83)
    - 시술 전 가입 보험사 고객센터에 보장 여부 반드시 확인
    - 당일입원(6시간 이상) 처리 시 외래 한도 제한 없이 청구 가능
    """)

    st.markdown("---")
    st.markdown("### 보험 청구 체크리스트")
    ch1, ch2, ch3 = st.columns(3)
    with ch1:
        st.markdown("**진료 전**")
        st.markdown("""
        - 실손보험 약관 비급여 보장 범위 확인
        - 보험사 고객센터에 해당 시술 보장 여부 문의
        - 급여 조건 충족 여부 확인 (역류 초음파 필요)
        """)
    with ch2:
        st.markdown("**진료 시**")
        st.markdown("""
        - 치료 목적임을 의사에게 명확히 전달
        - **진단서** (질병코드 I83) 발급 요청
        - **치료 목적 확인서** 별도 요청
        - 진료비 영수증·세부 내역서 수령
        """)
    with ch3:
        st.markdown("**청구 시**")
        st.markdown("""
        - 진단서, 영수증, 세부 내역서 보험사 제출
        - 보험사 앱 또는 팩스 청구 가능
        - 청구 기한: 진료일로부터 **3년 이내**
        - 입원 처리 여부 확인 후 청구
        """)
    st.caption("※ 출처: 심평원 비급여 진료비 정보(hira.or.kr/npay), NECA 의료기술재평가보고서 2025, 금융감독원 실손보험 표준약관")


# ═══════════════════════════════
# 질병관리청 통계 페이지
# ═══════════════════════════════
elif page == "통계":
    st.markdown('<p class="page-title">하지정맥류 위험인자 통계</p>', unsafe_allow_html=True)
    st.caption("출처: 질병관리청 국민건강영양조사 2024(knhanes.kdca.go.kr) · 지역사회건강조사 2025(chs.kdca.go.kr)")

    # ── 공공데이터: 전국 비만율 추이 (국민건강영양조사 2024) ──
    OBESITY_TREND = {
        1998: 25.8, 2001: 30.3, 2005: 31.4, 2007: 32.1,
        2008: 31.0, 2009: 31.9, 2010: 31.4, 2011: 31.9,
        2012: 32.8, 2013: 32.5, 2014: 31.5, 2015: 34.1,
        2016: 35.5, 2017: 34.8, 2018: 35.0, 2019: 34.4,
        2020: 38.4, 2021: 37.2, 2022: 37.2, 2023: 37.1,
        2024: 37.9,
    }

    # ── 공공데이터: 시도별 비만율 2025 (지역사회건강조사 2025) ──
    REGIONAL_OBESITY = {
        "서울": 29.4, "부산": 31.1, "대구": 30.6, "인천": 35.3,
        "광주": 31.4, "대전": 29.4, "울산": 36.3, "세종": 29.5,
        "경기": 34.0, "강원": 35.5, "충북": 33.2, "충남": 36.1,
        "전북": 31.1, "전남": 35.6, "경북": 32.1, "경남": 32.7,
        "제주": 36.4,
    }

    # ── 공공데이터: 시도별 중강도이상 신체활동 실천율 2025 ──
    REGIONAL_ACTIVITY = {
        "서울": 25.1, "부산": 22.2, "대구": 20.8, "인천": 22.8,
        "광주": 22.4, "대전": 23.4, "울산": 27.5, "세종": 22.8,
        "경기": 22.7, "강원": 20.4, "충북": 27.6, "충남": 24.1,
        "전북": 22.9, "전남": 24.7, "경북": 24.0, "경남": 30.1,
        "제주": 35.8,
    }

    # ── HIRA 하지정맥류 직접 통계 (건강보험심사평가원 보건의료빅데이터개방시스템) ──
    HIRA_TOTAL = {
        2016:161537, 2017:177140, 2018:184239, 2019:216127,
        2020:215947, 2021:247964, 2022:255033, 2023:251076, 2024:236999
    }
    HIRA_MALE = {
        2016:51858, 2017:56460, 2018:59070, 2019:68581,
        2020:68018, 2021:76383, 2022:77797, 2023:77440, 2024:74806
    }
    HIRA_FEMALE = {
        2016:109679, 2017:120680, 2018:125169, 2019:147546,
        2020:147929, 2021:171581, 2022:177236, 2023:173636, 2024:162193
    }
    HIRA_AGE_2024_M = [19, 431, 3059, 6784, 10821, 15483, 20565, 13168, 5391]
    HIRA_AGE_2024_F = [14, 637, 7442, 14914, 28268, 41996, 43306, 21322, 6534]
    AGE_LABELS = ['0-9세','10-19세','20-29세','30-39세','40-49세','50-59세','60-69세','70-79세','80세이상']

    tab1, tab2, tab3, tab4 = st.tabs(["하지정맥류 현황", "혈관 건강 지표 추이", "지역별 위험인자", "위험요인 분석"])

    # ── 만성질환 추이 데이터 (출처: 질병관리청 국민건강영양조사 2024) ──
    HYPERTENSION = {
        1998:24.1, 2001:25.6, 2005:22.6, 2007:20.3, 2008:22.1, 2009:22.9,
        2010:23.7, 2011:26.2, 2012:26.3, 2013:25.3, 2014:23.8, 2015:26.5,
        2016:28.1, 2017:26.6, 2018:28.4, 2019:28.1, 2020:29.0, 2021:28.1,
        2022:29.7, 2023:28.6, 2024:30.7,
    }
    DIABETES = {
        2011:10.3, 2012:9.7, 2013:11.9, 2014:10.6, 2015:9.4,
        2016:11.9, 2017:11.3, 2018:11.5, 2019:12.2, 2020:13.9,
        2021:13.6, 2022:12.5, 2023:13.2, 2024:14.8,
    }
    CHOLESTEROL = {
        2005:6.6, 2007:9.0, 2008:9.4, 2009:10.0, 2010:11.7,
        2011:12.3, 2012:13.1, 2013:13.5, 2014:12.9, 2015:16.6,
        2016:19.1, 2017:20.6, 2018:20.5, 2019:21.9, 2020:23.7,
        2021:25.4, 2022:27.1, 2023:26.7, 2024:30.2,
    }

    # ── Tab 1: 하지정맥류 현황 (HIRA) ──
    with tab1:
        st.subheader("하지정맥류 진료 현황 (2016~2024년)")
        st.markdown("건강보험심사평가원 진료 데이터 기준 **실제 하지정맥류(I83) 환자 현황**입니다.")

        # 연도별 추이
        rows_hira = []
        for y in HIRA_TOTAL:
            rows_hira.append({"연도": y, "환자수": HIRA_MALE[y], "구분": "남성"})
            rows_hira.append({"연도": y, "환자수": HIRA_FEMALE[y], "구분": "여성"})
        df_hira = pd.DataFrame(rows_hira)

        fig_h = px.bar(
            df_hira, x="연도", y="환자수", color="구분", barmode="stack",
            title="연도별 하지정맥류 환자 수 (남/여)",
            color_discrete_map={"남성": "#4a90e2", "여성": "#e74c3c"},
        )
        fig_h.update_layout(height=360, margin=dict(l=0,r=0,t=40,b=0),
                             yaxis_tickformat=",")
        st.plotly_chart(fig_h, use_container_width=True)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("2024년 환자 수", f"{HIRA_TOTAL[2024]:,}명")
        with m2:
            st.metric("2016→2022 증가", "+57.9%", "6년간 최고치")
        with m3:
            st.metric("여성 비율 (2024)", "68.4%", "남성의 2.2배")
        with m4:
            st.metric("최다 연령대", "60대", f"{HIRA_AGE_2024_M[6]+HIRA_AGE_2024_F[6]:,}명")

        st.markdown("---")

        # 연령별 분포
        df_age = pd.DataFrame({
            "연령대": AGE_LABELS * 2,
            "환자수": HIRA_AGE_2024_M + HIRA_AGE_2024_F,
            "성별": ["남성"] * 9 + ["여성"] * 9,
        })
        fig_age = px.bar(
            df_age, x="연령대", y="환자수", color="성별", barmode="group",
            title="2024년 연령대별·성별 환자 수",
            color_discrete_map={"남성": "#4a90e2", "여성": "#e74c3c"},
        )
        fig_age.update_layout(height=340, margin=dict(l=0,r=0,t=40,b=0),
                               yaxis_tickformat=",")
        st.plotly_chart(fig_age, use_container_width=True)

        st.info(
            "50-60대 여성 환자가 가장 많습니다. 여성 호르몬(에스트로겐)이 정맥벽을 약화시키고, "
            "임신·출산이 복압을 높여 여성 발생률이 높습니다. "
            "2020년은 코로나19로 인한 의료 이용 감소로 환자 수가 정체됐습니다."
        )
        st.caption("※ 출처: 건강보험심사평가원 보건의료빅데이터개방시스템 (opendata.hira.or.kr), 질병코드 I83 (하지의 정맥류), 2016~2024년 심사년도 기준")

    # ── Tab 2: 혈관 건강 지표 추이 ──
    with tab2:
        st.subheader("혈관 건강 관련 만성질환 유병률 추이")
        st.markdown(
            "**비만·고혈압·당뇨·이상지질혈증**은 모두 정맥 기능 저하와 하지정맥류의 주요 위험인자입니다. "
            "비만율 상승과 함께 관련 만성질환 유병률도 함께 증가하고 있습니다."
        )

        rows = []
        for year, v in sorted(OBESITY_TREND.items()):
            rows.append({"연도": year, "유병률(%)": v, "지표": "비만(BMI≥25)"})
        for year, v in sorted(HYPERTENSION.items()):
            rows.append({"연도": year, "유병률(%)": v, "지표": "고혈압"})
        for year, v in sorted(CHOLESTEROL.items()):
            rows.append({"연도": year, "유병률(%)": v, "지표": "고콜레스테롤혈증"})
        for year, v in sorted(DIABETES.items()):
            rows.append({"연도": year, "유병률(%)": v, "지표": "당뇨병"})

        df_multi = pd.DataFrame(rows)
        fig = px.line(
            df_multi, x="연도", y="유병률(%)", color="지표", markers=True,
            title="만성질환 유병률 추이 — 19세 이상 (%)",
            color_discrete_map={
                "비만(BMI≥25)":     "#1d4ed8",
                "고혈압":            "#e74c3c",
                "고콜레스테롤혈증":  "#f59e0b",
                "당뇨병":            "#10b981",
            },
        )
        fig.update_traces(marker=dict(size=6))
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0),
                          legend=dict(orientation="h", y=1.12, x=0))
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("비만율 (2024)", "37.9%", "+12.1%p vs 1998")
        with col2:
            st.metric("고혈압 (2024)", "30.7%", "+6.6%p vs 1998")
        with col3:
            st.metric("고콜레스테롤 (2024)", "30.2%", "+23.6%p vs 2005")
        with col4:
            st.metric("당뇨병 (2024)", "14.8%", "+4.5%p vs 2011")

        st.info(
            "비만은 하지 정맥 내 압력을 높여 판막 기능을 저하시키고, 고혈압·당뇨는 혈관벽 탄성을 감소시켜 "
            "하지정맥류 발생·악화를 촉진합니다. 위험인자가 겹칠수록 발병 위험이 높아집니다."
        )
        st.caption(
            "※ 출처: 질병관리청 국민건강영양조사(KNHANES) 2024 — 표 15-1(비만), 표 16-1(고혈압), "
            "표 17-1(당뇨병), 표 18-1(고콜레스테롤혈증) / 19세 이상, BMI 기준 자가보고 제외"
        )

    # ── Tab 3: 지역별 위험인자 ──
    with tab3:
        st.subheader("시도별 하지정맥류 위험인자 현황 (2025년)")

        col_sel, _ = st.columns([2, 3])
        with col_sel:
            sort_by = st.selectbox("정렬 기준", ["비만율 높은 순", "비만율 낮은 순", "지역명 순"])

        regions = list(REGIONAL_OBESITY.keys())
        obes_vals = [REGIONAL_OBESITY[r] for r in regions]
        act_vals  = [REGIONAL_ACTIVITY[r] for r in regions]

        df_reg = pd.DataFrame({
            "지역": regions,
            "비만율(%)": obes_vals,
            "신체활동 실천율(%)": act_vals,
        })

        if sort_by == "비만율 높은 순":
            df_reg = df_reg.sort_values("비만율(%)", ascending=True)
        elif sort_by == "비만율 낮은 순":
            df_reg = df_reg.sort_values("비만율(%)", ascending=False)
        else:
            df_reg = df_reg.sort_values("지역")

        sub1, sub2 = st.columns(2)

        with sub1:
            fig1 = px.bar(
                df_reg, x="비만율(%)", y="지역", orientation="h",
                title="시도별 비만율(%) — 2025년",
                color="비만율(%)",
                color_continuous_scale=["#bbdefb", "#1d4ed8"],
                range_color=[27, 38],
            )
            fig1.update_layout(
                height=500, coloraxis_showscale=False,
                margin=dict(l=0, r=20, t=40, b=0),
                xaxis_range=[25, 40],
            )
            fig1.add_vline(x=sum(obes_vals)/len(obes_vals),
                           line_dash="dot", line_color="#e74c3c",
                           annotation_text=f"전국 평균 {sum(obes_vals)/len(obes_vals):.1f}%",
                           annotation_position="top right")
            st.plotly_chart(fig1, use_container_width=True)

        with sub2:
            df_act_sorted = df_reg.sort_values("신체활동 실천율(%)", ascending=True)
            fig2 = px.bar(
                df_act_sorted, x="신체활동 실천율(%)", y="지역", orientation="h",
                title="시도별 중강도이상 신체활동 실천율(%) — 2025년",
                color="신체활동 실천율(%)",
                color_continuous_scale=["#f87171", "#bbf7d0"],
                range_color=[18, 38],
            )
            fig2.update_layout(
                height=500, coloraxis_showscale=False,
                margin=dict(l=0, r=20, t=40, b=0),
                xaxis_range=[15, 42],
            )
            fig2.add_vline(x=sum(act_vals)/len(act_vals),
                           line_dash="dot", line_color="#888",
                           annotation_text=f"전국 평균 {sum(act_vals)/len(act_vals):.1f}%",
                           annotation_position="top right")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### 비만율 × 신체활동 실천율 — 복합 위험도 분석")
        obes_avg = sum(REGIONAL_OBESITY.values()) / len(REGIONAL_OBESITY)
        act_avg  = sum(REGIONAL_ACTIVITY.values()) / len(REGIONAL_ACTIVITY)

        df_reg2 = df_reg.copy()
        df_reg2["위험등급"] = df_reg2.apply(
            lambda r: "고위험 (비만↑·활동↓)" if r["비만율(%)"] > obes_avg and r["신체활동 실천율(%)"] < act_avg
            else ("주의 (비만↑)" if r["비만율(%)"] > obes_avg
            else ("주의 (활동↓)" if r["신체활동 실천율(%)"] < act_avg
            else "양호")), axis=1
        )
        color_map = {
            "고위험 (비만↑·활동↓)": "#ef4444",
            "주의 (비만↑)":         "#f97316",
            "주의 (활동↓)":         "#eab308",
            "양호":                  "#22c55e",
        }

        fig3 = px.scatter(
            df_reg2, x="비만율(%)", y="신체활동 실천율(%)",
            text="지역", color="위험등급",
            color_discrete_map=color_map,
            title="비만율 높고 신체활동 낮은 지역 = 하지정맥류 복합 위험",
            size=[14] * len(df_reg2),
            size_max=20,
        )
        fig3.update_traces(textposition="top center", textfont_size=12,
                           marker=dict(line=dict(width=1.5, color="white")))
        # 평균선
        fig3.add_vline(x=obes_avg, line_dash="dot", line_color="#94a3b8",
                       annotation_text=f"평균 {obes_avg:.1f}%", annotation_position="top right",
                       annotation_font_color="#64748b")
        fig3.add_hline(y=act_avg, line_dash="dot", line_color="#94a3b8",
                       annotation_text=f"평균 {act_avg:.1f}%", annotation_position="bottom right",
                       annotation_font_color="#64748b")
        # 사분면 배경
        x0, x1 = 27.5, 38.5
        y0, y1 = 18.0, 38.0
        fig3.add_shape(type="rect", x0=x0, y0=y0, x1=obes_avg, y1=act_avg,
                       fillcolor="#bbf7d0", opacity=0.15, line_width=0)
        fig3.add_shape(type="rect", x0=obes_avg, y0=y0, x1=x1, y1=act_avg,
                       fillcolor="#fecaca", opacity=0.25, line_width=0)
        fig3.add_shape(type="rect", x0=x0, y0=act_avg, x1=obes_avg, y1=y1,
                       fillcolor="#fef9c3", opacity=0.2, line_width=0)
        fig3.add_shape(type="rect", x0=obes_avg, y0=act_avg, x1=x1, y1=y1,
                       fillcolor="#fef9c3", opacity=0.1, line_width=0)
        fig3.update_layout(
            height=480,
            margin=dict(l=0, r=0, t=50, b=0),
            legend=dict(orientation="h", y=-0.12, x=0),
            xaxis=dict(range=[x0, x1]),
            yaxis=dict(range=[y0, y1]),
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.info("비만율이 높고 신체활동 실천율이 낮은 지역일수록 하지정맥류 발생 위험이 높습니다. 비만과 운동 부족은 정맥 기능 저하의 주요 원인입니다.")
        st.caption("※ 출처: 질병관리청 지역사회건강조사 2025, 부록표 1-13(시도별 비만율) · 부록표 1-10(중강도이상 신체활동 실천율)")

    # ── Tab 4: 위험요인 분석 ──
    with tab4:
        st.subheader("주요 위험요인 상대위험도 (OR)")
        st.markdown(
            "국내외 코호트 연구 메타분석 기반 상대위험도(Odds Ratio)입니다. "
            "OR > 1이면 해당 인자가 있을 때 하지정맥류 발생 위험이 높아짐을 의미합니다."
        )

        df_risk = pd.DataFrame({
            "위험요인": ["가족력", "장시간 기립(8h+)", "임신 경험", "고령(60대+)", "비만(BMI≥25)", "장시간 좌식"],
            "OR (중간값)": [2.8, 2.4, 2.1, 2.2, 1.9, 1.6],
            "OR 범위":     ["1.6~4.4", "1.4~3.0", "1.5~3.1", "1.5~3.2", "1.3~2.2", "1.2~2.0"],
            "비고":         ["유전적 소인", "직업 위험", "호르몬 변화·복압 상승", "혈관 노화", "복압 상승·운동 부족", "혈류 정체"],
        })

        col1, col2 = st.columns([3, 2])
        with col1:
            fig = px.bar(
                df_risk.sort_values("OR (중간값)"),
                x="OR (중간값)", y="위험요인", orientation="h",
                title="하지정맥류 위험요인별 OR (중간값)",
                color="OR (중간값)",
                color_continuous_scale=["#fde68a", "#dc2626"],
                text="OR (중간값)",
            )
            fig.update_traces(texttemplate="%{x:.1f}x", textposition="outside")
            fig.add_vline(x=1, line_dash="dash", line_color="#94a3b8",
                          annotation_text="OR=1 (기준)", annotation_position="top right")
            fig.update_layout(height=320, coloraxis_showscale=False,
                               margin=dict(l=0, r=60, t=40, b=0),
                               xaxis_range=[0, 3.8])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**위험요인 상세**")
            st.dataframe(
                df_risk[["위험요인", "OR 범위", "비고"]].set_index("위험요인"),
                use_container_width=True, height=280,
            )

        st.warning(
            "OR 수치는 국내외 코호트 연구 메타분석 기반 추정치입니다. "
            "연구 대상·측정 방법에 따라 범위가 다를 수 있습니다."
        )
        st.caption(
            "※ 참고 문헌: Fukaya et al. (2020) Int Angiol; Lee et al. (2021) J Korean Med Sci; "
            "Rabe et al. (2012) VASA — 한국인 대상 KNHANES 연계 분석 기반 추정치 포함"
        )


# ═══════════════════════════════
# 병원 찾기 페이지
# ═══════════════════════════════
elif page == "병원 찾기":
    st.markdown('<p class="page-title">병원 찾기</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">가까운 혈관외과 및 하지정맥류 전문 클리닉을 찾아보세요</p>', unsafe_allow_html=True)

    # 진단 결과 연동 안내
    final_class = st.session_state.get('survey_ceap')
    if final_class and st.session_state.get('diag_step', 1) > 1:
        info = RESULT_INFO[final_class]
        color = info['color']
        urgency_msg = {
            "C0_normal":    "현재 정상 단계입니다. 증상 변화 시 재진단을 권장합니다.",
            "C1_watch":     "경과 관찰 단계입니다. 증상이 심해지면 피부과 또는 혈관외과 상담을 받으세요.",
            "C2_consult":   "혈관외과 진료를 권장합니다. 가까운 병원을 검색해보세요.",
            "C34_danger":   "빠른 시일 내 혈관외과 방문이 필요합니다.",
            "C56_emergency":"즉시 혈관외과를 방문하세요.",
        }
        st.markdown(f"""
        <div style='background:{color}15; border-left:4px solid {color};
                    padding:0.8rem 1rem; border-radius:4px; margin-bottom:1rem;'>
            <b>진단 결과: {info['label']}</b> —
            <span style='color:{color}'>{urgency_msg[final_class]}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 지역별 빠른 검색")
    col1, col2 = st.columns(2)
    with col1:
        region = st.selectbox("지역 선택", [
            "서울", "경기", "인천", "부산", "대구",
            "광주", "대전", "울산", "세종",
            "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"
        ])
    with col2:
        keyword = st.text_input("검색어 직접 입력 (선택)", placeholder="예: 정맥류 클리닉, 정맥류 외과")

    from urllib.parse import quote
    base_keyword = keyword if keyword else "하지정맥류"
    search_keyword = f"{region} {base_keyword}"
    encoded = quote(search_keyword)

    col_n, col_k = st.columns(2)
    with col_n:
        naver_url = f"https://map.naver.com/v5/search/{encoded}"
        st.link_button("네이버 지도에서 검색", naver_url, use_container_width=True)
    with col_k:
        kakao_url = f"https://map.kakao.com/?q={encoded}"
        st.link_button("카카오맵에서 검색", kakao_url, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 진료 전 체크리스트")
    st.markdown("""
    병원 방문 시 다음을 준비하면 더 정확한 진료를 받을 수 있습니다:

    - 증상이 언제부터 시작됐는지
    - 통증·붓기·피로감 정도
    - 직업 및 하루 기립 시간
    - 가족 중 하지정맥류 병력 여부
    - 복용 중인 약물 목록
    - 이전 치료 경험 여부
    """)

    st.markdown("#### 전문과목 안내")
    st.markdown("""
    하지정맥류는 다음 진료과에서 진료받을 수 있습니다:
    - **혈관외과** (가장 전문적)
    - **외과** (혈관외과가 없는 병원)
    - **피부과** (C1 모세혈관 확장, 경화요법)
    """)
    st.caption("※ 정확한 진단을 위해 정맥 초음파 검사가 가능한 병원을 선택하는 것을 권장합니다.")


# ═══════════════════════════════
# CEAP 안내 페이지
# ═══════════════════════════════
elif page == "CEAP 안내":
    st.markdown('<p class="page-title">CEAP 분류 기준 안내</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">하지정맥류는 국제 표준인 CEAP 분류 (C0-C6)로 단계가 구분됩니다.</p>', unsafe_allow_html=True)

    CEAP_IMG_DIR = Path("assets/ceap")

    ceap_data = [
        (
            "C0", "c0", "정상", "#2ecc71", "생활습관 유지",
            "눈에 보이거나 만져지는 정맥 이상이 없는 상태입니다. 증상이 없더라도 위험인자(가족력·장시간 기립·비만 등)가 있다면 정기적인 자가 확인이 중요합니다.",
        ),
        (
            "C1", "c1", "모세혈관 확장 / 거미정맥", "#27ae60", "압박 스타킹",
            "직경 1~3mm 미만의 가는 실핏줄(거미정맥·모세혈관 확장)이나 청록색의 망상정맥이 피부 표면에 보입니다. 주로 허벅지 외측·종아리·발목 주변에 나타나며 대부분 미용적 문제이나 가려움이나 약한 통증이 동반될 수 있습니다.",
        ),
        (
            "C2", "c2", "정맥류", "#f39c12", "경화요법 / 고주파 / 레이저",
            "직경 3mm 이상의 굵고 구불구불한 정맥이 피부 위로 돌출됩니다. 다리 무거움·통증·야간 경련이 흔히 동반되며 오래 서 있으면 증상이 악화됩니다. 판막 기능 부전으로 혈액 역류가 발생한 상태로 적극적인 치료를 권장합니다.",
        ),
        (
            "C3", "c3", "정맥성 부종", "#e67e22", "압박치료 + 약물",
            "피부 변화 없이 발목·종아리에 부종이 나타납니다. 오전에는 호전되고 저녁에 악화되는 양상이 특징적입니다. 장기간 방치하면 피부 조직에 산소 공급이 줄어 C4 단계 피부 변화로 진행될 수 있습니다.",
        ),
        (
            "C4", "c4", "피부 변화", "#e74c3c", "전문의 상담 필수",
            "정맥 고혈압으로 발목 주변에 갈색·자색 색소침착(C4a), 가려움을 동반한 습진(C4a), 피부와 피하조직이 딱딱해지는 지방피부경화증(C4b), 흰 반점(위축성 백반, C4b)이 나타납니다. 궤양 직전 단계로 빠른 치료가 필요합니다.",
        ),
        (
            "C5", "c5", "치유된 궤양", "#c0392b", "재발 방지 치료",
            "과거 정맥성 궤양이 치유된 흔적(반흔·색소침착)이 남아 있는 상태입니다. 치유됐더라도 근본 원인인 정맥 역류를 교정하지 않으면 재발률이 높습니다. 압박 치료와 정맥 수술을 통한 재발 예방 관리가 필수적입니다.",
        ),
        (
            "C6", "c6", "활동성 궤양", "#8e0000", "즉시 진료",
            "발목 안쪽(내과 주변)에 잘 낫지 않는 개방 창상이 있는 상태입니다. 삼출물·통증·악취가 동반될 수 있으며 감염 및 봉와직염으로 악화될 위험이 있습니다. 즉시 혈관외과 전문의를 방문해야 합니다.",
        ),
    ]

    for stage, img_key, name, color, treat, detail in ceap_data:
        img_col, info_col = st.columns([1, 5])
        with img_col:
            if img_key:
                img_path = CEAP_IMG_DIR / f"{img_key}.png"
                if img_path.exists():
                    st.image(str(img_path), width=120)
            else:
                st.markdown(
                    "<div style='background:#f0fdf4; border-radius:8px; padding:1rem;"
                    "text-align:center; color:#166534; font-size:0.85rem;'>정상</div>",
                    unsafe_allow_html=True,
                )
        with info_col:
            st.markdown(f"""
            <div style='border-left:4px solid {color}; padding:0.7rem 1.1rem;
                        background:{color}11; border-radius:0 8px 8px 0;
                        box-sizing:border-box;'>
                <div style='margin-bottom:0.3rem'>
                    <span style='font-size:1rem; font-weight:700; color:{color}'>{stage}</span>
                    <span style='font-size:1rem; font-weight:600; color:#1e293b; margin-left:0.6rem'>{name}</span>
                    <span style='font-size:0.8rem; color:#64748b; margin-left:0.8rem; background:#f1f5f9;
                                 padding:0.1rem 0.5rem; border-radius:4px'>권장: {treat}</span>
                </div>
                <p style='font-size:0.88rem; color:#475569; margin:0; line-height:1.6'>{detail}</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<div style='margin:0.6rem 0'></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 자가 체크리스트")
    st.markdown("""
    다음 증상이 있다면 전문의 상담을 권장합니다:
    - 다리가 자주 무겁거나 피로감이 있다
    - 저녁에 발목이 붓는다
    - 다리에 파랗거나 구불구불한 혈관이 보인다
    - 다리가 자주 쥐가 난다 (야간 근경련)
    - 피부색이 변하거나 가렵다
    """)

    st.markdown("---")
    col_cta, _ = st.columns([1, 1])
    with col_cta:
        if st.button("내 상태 AI 진단하기", type="primary", use_container_width=True):
            for k in ['diag_step', 'part1', 'part2', 'ai_result', 'survey_ceap']:
                st.session_state.pop(k, None)
            st.session_state.page = "AI 진단"
            st.rerun()
