import streamlit as st
from supabase import create_client
import re
import pandas as pd

# --- [1. 페이지 설정 및 커스텀 디자인] ---
st.set_page_config(page_title="설문지", layout="centered")

# 눈이 편안한 모던 디자인을 위한 커스텀 CSS
st.markdown("""
    <style>
    /* 기본 배경 및 폰트 설정 */
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
    }
    
    /* 제목 스타일링: 아이콘 없이 깔끔하게 */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-align: left;
    }
    
    /* 카드형 메트릭 박스 */
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 사이드바 메뉴 스타일 */
    .stRadio > div {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 15px;
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [2. Supabase 연결] ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- [3. ID 생성 로직] ---
def get_next_id():
    try:
        response = supabase.table("project").select("id").execute()
        data = response.data
        if not data: return "S_011" # 10번까지 이미 있으니 11번부터 시작
        nums = []
        for item in data:
            match = re.search(r'S_(\d+)', item['id'])
            if match: nums.append(int(match.group(1)))
        if not nums: return "S_011"
        next_num = max(nums) + 1
        return f"S_{next_num:03d}"
    except: return "S_ERR"

# --- [4. 메뉴 구성] ---
st.sidebar.markdown("### 설문 관리")
page = st.sidebar.radio("이동할 페이지", ["설문 작성", "데이터 분석"], label_visibility="collapsed")

# --- [페이지 1: 설문 작성] ---
if page == "설문 작성":
    st.markdown('<h1 class="main-title">설문지</h1>', unsafe_allow_html=True)
    
    current_id = get_next_id()
    st.markdown(f"현재 참여 번호: **{current_id}**")
    st.write("보다 나은 학습 환경을 위한 데이터 수집에 참여해주세요.")
    
    with st.form("modern_survey", clear_on_submit=True):
        grade_class = st.text_input("학년-반", placeholder="예: 2-8")
        
        col1, col2 = st.columns(2)
        with col1:
            study_hours = st.slider("하루 평균 공부 시간", 0.0, 15.0, 3.0, 0.5)
            academic_score = st.number_input("평균 성적", 0, 100, 70)
        with col2:
            sleep_hours = st.slider("평균 수면 시간", 0.0, 15.0, 7.0, 0.5)
            tired_score = st.select_slider("피곤함 점수", options=list(range(1, 11)), value=5)
            
        favorite_subject = st.selectbox("좋아하는 과목", ["국어", "수학", "영어", "과학", "사회", "체육", "음악", "미술", "정보", "기타"])
        
        submitted = st.form_submit_button("설문지 제출")
        
        if submitted:
            if not grade_class:
                st.error("학년-반 정보를 입력해주세요.")
            else:
                new_row = {
                    "id": current_id, "grade_class": grade_class, 
                    "study_hours": study_hours, "academic_score": academic_score,
                    "sleep_hours": sleep_hours, "tired_score": tired_score, 
                    "favorite_subject": favorite_subject
                }
                supabase.table("project").insert(new_row).execute()
                st.success("소중한 의견 감사합니다.")

# --- [페이지 2: 데이터 분석] ---
else:
    st.markdown('<h1 class="main-title">데이터 분석</h1>', unsafe_allow_html=True)
    st.write("학습량, 수면, 성적의 상관관계를 심플한 차트로 분석합니다.")
    
    try:
        res = supabase.table("project").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            
            # 요약 지표 (심플한 카드형)
            c1, c2, c3 = st.columns(3)
            c1.metric("총 응답", f"{len(df)}명")
            c2.metric("평균 공부", f"{df['study_hours'].mean():.1f}h")
            c3.metric("평균 성적", f"{df['academic_score'].mean():.0f}점")
            
            st.markdown("---")
            
            # 분석 그래프: 가독성을 위해 간결한 설명 추가
            st.subheader("공부 시간과 수면 시간의 관계")
            st.scatter_chart(df, x="study_hours", y="sleep_hours")
            
            st.subheader("공부 시간에 따른 피로도 변화")
            st.area_chart(df.set_index("study_hours")["tired_score"])
            
            st.subheader("과목별 선호도")
            st.bar_chart(df["favorite_subject"].value_counts())
            
        else:
            st.info("데이터가 충분하지 않습니다.")
    except Exception as e:
        st.error("분석 데이터를 불러올 수 없습니다.")