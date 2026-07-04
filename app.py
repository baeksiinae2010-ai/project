import streamlit as st
from supabase import create_client
import re
import pandas as pd

# --- [페이지 기본 설정] ---
# 아이콘 없이 깔끔하게 이름만 지정합니다.
st.set_page_config(page_title="설문지", layout="centered")

# --- [Supabase 연결] ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- [ID 생성 함수] ---
def get_next_id():
    try:
        response = supabase.table("project").select("id").execute()
        data = response.data
        if not data: return "S_001"
        nums = []
        for item in data:
            match = re.search(r'S_(\d+)', item['id'])
            if match: nums.append(int(match.group(1)))
        if not nums: return "S_001"
        next_num = max(nums) + 1
        return f"S_{next_num:03d}"
    except: return "S_ERR"

# --- [사이드바 메뉴] ---
st.sidebar.title("메뉴")
page = st.sidebar.radio("이동", ["설문 작성", "데이터 분석"])

# --- [페이지 1: 설문 작성] ---
if page == "설문 작성":
    st.title("설문지")
    
    current_id = get_next_id()
    st.caption(f"현재 설문 번호: {current_id}")
    st.write("학생들의 학습과 생활 패턴을 알아보기 위한 설문입니다.")
    
    # 폼 영역: 입력 칸 사이의 여백을 확보하는 심플한 구조
    with st.form("survey_form", clear_on_submit=True):
        grade_class = st.text_input("학년-반 (예: 1-3)")
        study_hours = st.slider("하루 평균 공부 시간 (시간)", 0.0, 24.0, 3.0, 0.5)
        academic_score = st.number_input("직전 시험 평균 성적 (점)", min_value=0, max_value=100, value=70)
        sleep_hours = st.slider("하루 평균 수면 시간 (시간)", 0.0, 24.0, 7.0, 0.5)
        tired_score = st.slider("오늘 느낀 피곤함 정도 (1: 상쾌함 ~ 10: 매우 피곤함)", 1, 10, 5)
        favorite_subject = st.selectbox("가장 좋아하는 과목", ["국어", "수학", "영어", "과학", "사회", "체육", "음악", "미술", "정보", "기타"])
        
        submitted = st.form_submit_button("제출")
        
        if submitted:
            if not grade_class:
                st.error("학년-반을 입력해주세요.")
            else:
                new_data = {
                    "id": current_id, 
                    "grade_class": grade_class, 
                    "study_hours": study_hours,
                    "academic_score": academic_score,
                    "sleep_hours": sleep_hours,
                    "tired_score": tired_score, 
                    "favorite_subject": favorite_subject
                }
                try:
                    supabase.table("project").insert(new_data).execute()
                    st.success("제출이 완료되었습니다.")
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

# --- [페이지 2: 데이터 분석] ---
elif page == "데이터 분석":
    st.title("데이터 분석")
    st.write("수집된 데이터를 바탕으로 학습과 생활 패턴의 관계를 확인합니다.")
    
    try:
        response = supabase.table("project").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            
            # 1. 핵심 요약 지표 (심플한 숫자형 데이터)
            col1, col2, col3 = st.columns(3)
            col1.metric("총 응답수", f"{len(df)}명")
            col2.metric("평균 공부 시간", f"{df['study_hours'].mean():.1f}시간")
            col3.metric("평균 피곤함", f"{df['tired_score'].mean():.1f}점")
            
            st.divider()
            
            # 2. 분석 차트: 직관적인 점 그래프 (Scatter Chart) 활용
            # 산점도는 두 데이터(X축, Y축)의 상관관계를 한눈에 파악하기 가장 좋은 모던한 차트입니다.
            
            st.subheader("공부 시간과 수면 시간의 관계")
            st.caption("점이 어떻게 분포하는지 확인하여 공부와 수면의 상관관계를 파악합니다.")
            st.scatter_chart(df, x="study_hours", y="sleep_hours")
            
            st.divider()
            
            st.subheader("공부 시간에 따른 피곤함")
            st.caption("공부 시간이 길어질수록 피곤함 점수가 높아지는지 확인합니다.")
            st.scatter_chart(df, x="study_hours", y="tired_score")
            
            st.divider()
            
            # 3. 빈도 분석 차트: 막대 그래프 (Bar Chart)
            st.subheader("가장 좋아하는 과목")
            subject_counts = df['favorite_subject'].value_counts()
            st.bar_chart(subject_counts)
            
        else:
            st.info("아직 수집된 데이터가 없습니다.")
    except Exception as e:
        st.error("데이터를 불러오는 중 문제가 발생했습니다.")
