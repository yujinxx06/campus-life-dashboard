import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from collections import Counter

# -----------------------------------------------------------------------------
# 한글 폰트 설정 (그래프에서 한글 깨짐 방지)
# -----------------------------------------------------------------------------
plt.rc('font', family='Malgun Gothic') # Windows 환경 기준 폰트
plt.rc('axes', unicode_minus=False)    # 마이너스 기호 깨짐 방지


# -----------------------------------------------------------------------------
# 1. 제목: 상단 메인 타이틀 및 앱 소개 문구
# -----------------------------------------------------------------------------
st.title("🎓 인문사회대 캠퍼스 생활 설문조사 분석 웹앱 (의견 분석 추가)")
st.write(
    "안녕하세요! 이 웹앱은 설문조사 데이터 통계 분석과 더불어 "
    "학생들이 작성한 **'한줄의견'**의 자주 등장하는 키워드와 긍정·부정 감성 단어를 "
    "실시간으로 분석해 주는 업그레이드된 프로그램입니다."
)
st.markdown("---")


# -----------------------------------------------------------------------------
# 2. CSV 업로드: 파일 업로더 위젯 제공 (없을 경우 기본 파일 자동 로드)
# -----------------------------------------------------------------------------
st.header("📂 1. 데이터 파일 불러오기")

uploaded_file = st.file_uploader("설문조사 CSV 파일을 업로드해주세요.", type=["csv"])

if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)
    st.success("업로드한 CSV 파일을 성공적으로 불러왔습니다!")
else:
    try:
        df_raw = pd.read_csv("campus_life.csv")
        st.info("기본 제공 파일('campus_life.csv')을 로드했습니다.")
    except FileNotFoundError:
        st.error("기본 데이터 파일('campus_life.csv')을 찾을 수 없습니다. CSV 파일을 업로드해주세요.")
        st.stop()


# -----------------------------------------------------------------------------
# 3. 데이터 미리보기: 원본 데이터 구조 확인
# -----------------------------------------------------------------------------
st.header("👀 2. 원본 데이터 미리보기")
st.dataframe(df_raw.head())
st.caption(f"총 {df_raw.shape[0]}개의 응답 데이터와 {df_raw.shape[1]}개의 항목(열)이 있습니다.")


# -----------------------------------------------------------------------------
# 4. 전처리 결과: 데이터 정제 과정 및 결과 요약
# -----------------------------------------------------------------------------
st.header("🧹 3. 데이터 전처리 결과")

df_clean = df_raw.copy()

# (1) '만족도' 열의 잘못된 문자('모름' 등)를 숫자로 변환 (오류 발생 시 NaN 처리)
df_clean['만족도'] = pd.to_numeric(df_clean['만족도'], errors='coerce')

# (2) 수치형 컬럼 결측치(NaN)를 각 열의 평균값으로 안전하게 대체
numeric_cols = ['통학시간', '공부시간', '스마트폰', '수면시간', '만족도']
for col in numeric_cols:
    if df_clean[col].isnull().sum() > 0:
        mean_val = round(df_clean[col].mean(), 1)
        df_clean[col] = df_clean[col].fillna(mean_val)

st.success("✅ '모름' 등 이상치 수치 변환 및 결측치 평균값 대체 전처리가 완료되었습니다!")

with st.expander("전처리 완료된 데이터 통계 요약 보기"):
    st.dataframe(df_clean[numeric_cols].describe())


# -----------------------------------------------------------------------------
# 5. 학과 선택: 다중 선택 필터 (st.multiselect) 적용
# -----------------------------------------------------------------------------
st.header("🔍 4. 학과별 다중 선택 필터링")

# 데이터셋의 전체 학과 목록 추출
dept_list = list(df_clean['학과'].unique())

# st.multiselect를 이용해 여러 학과를 동시에 선택할 수 있도록 구현 (기본값으로 전체 학과 지정)
selected_depts = st.multiselect(
    "조회할 학과를 선택하세요 (복수 선택 가능):",
    options=dept_list,
    default=dept_list
)

# 학과가 선택되지 않은 경우 전체 데이터 선택
if not selected_depts:
    st.warning("선택된 학과가 없어 전체 학과 데이터로 조회합니다.")
    filtered_df = df_clean
else:
    filtered_df = df_clean[df_clean['학과'].isin(selected_depts)]


# -----------------------------------------------------------------------------
# 6. 주요 요약 지표 카드 & 한줄의견 분석 및 시각화 렌더링
# -----------------------------------------------------------------------------
st.header("📊 5. 선택 학과 통합 분석 및 한줄의견 분석 결과")

# (1) 주요 요약 지표 카드 (st.metric)
col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_sat = filtered_df['만족도'].mean() if len(filtered_df) > 0 else 0
    st.metric(label="평균 만족도", value=f"{avg_sat:.2f}점")

with col2:
    avg_study = filtered_df['공부시간'].mean() if len(filtered_df) > 0 else 0
    st.metric(label="평균 공부시간", value=f"{avg_study:.1f}시간")

with col3:
    avg_commute = filtered_df['통학시간'].mean() if len(filtered_df) > 0 else 0
    st.metric(label="평균 통학시간", value=f"{avg_commute:.1f}분")

with col4:
    avg_sleep = filtered_df['수면시간'].mean() if len(filtered_df) > 0 else 0
    st.metric(label="평균 수면시간", value=f"{avg_sleep:.1f}시간")

st.markdown("---")

# (2) '한줄의견' 텍스트 분석 영역
st.subheader("💬 '한줄의견' 감성 및 키워드 분석")

# 필터링된 데이터의 한줄의견 텍스트를 하나의 문자열로 결합
all_comments = " ".join(filtered_df['한줄의견'].dropna().astype(str))

# 정규식을 이용해 2글자 이상의 한글 단어 추출
words = re.findall(r'[가-힣]{2,}', all_comments)

# 빈도가 높지만 의미 없는 단어(불용어) 제외
stopwords = ['시간이', '기간에', '너무', '정말', '에서', '으로', '하고', '있는', '하는', '되는']
filtered_words = [w for w in words if w not in stopwords]

# 가장 많이 등장한 상위 10개 단어 빈도 계산
top_words = Counter(filtered_words).most_common(10)

# 긍정 단어 및 부정 단어 리스트 정의 후 등장 횟수 카운트
pos_words = ['좋아요', '재미있어요', '도움이', '예뻐서', '맛있어요', '친절해요', '만족해요', '훌륭해요', '최고', '유익해요', '돼요']
neg_words = ['피곤해요', '부족해요', '불편해요', '힘들어요', '아쉬워요', '후회돼요', '어려워요', '지루해요', '복잡해요', '걱정돼요', '비싸서', '붐벼서']

pos_count = sum(all_comments.count(pw) for pw in pos_words)
neg_count = sum(all_comments.count(nw) for nw in neg_words)

# 긍정 / 부정 단어 횟수를 눈에 띄게 메트릭 카드로 표시
sent_col1, sent_col2 = st.columns(2)
with sent_col1:
    st.metric(label="👍 긍정 단어 총 등장 횟수", value=f"{pos_count}회")
with sent_col2:
    st.metric(label="👎 부정 단어 총 등장 횟수", value=f"{neg_count}회")

st.write("")

# (3) 시각화 그래프 영역 (상위 10개 단어 막대그래프 & 산점도)
graph_col1, graph_col2 = st.columns(2)

# [그래프 1] 상위 10개 단어 빈도 막대그래프
with graph_col1:
    st.markdown("**1) 한줄의견 자주 등장 상위 10개 단어**")
    if top_words:
        word_df = pd.DataFrame(top_words, columns=['단어', '빈도수'])
        fig1, ax1 = plt.subplots(figsize=(5, 4))
        sns.barplot(data=word_df, x='빈도수', y='단어', palette='Blues_r', ax=ax1)
        ax1.set_title("상위 10개 키워드 빈도")
        ax1.set_xlabel("빈도수")
        ax1.set_ylabel("단어")
        ax1.grid(True, linestyle='--', alpha=0.5)
        st.pyplot(fig1)
    else:
        st.info("분석할 텍스트 데이터가 부족합니다.")

# [그래프 2] 공부시간 vs 만족도 산점도
with graph_col2:
    st.markdown("**2) 공부시간 vs 만족도 관계 (산점도)**")
    fig2, ax2 = plt.subplots(figsize=(5, 4))
    if len(filtered_df) > 0:
        sns.scatterplot(
            data=filtered_df,
            x='공부시간',
            y='만족도',
            hue='학과',
            palette='Set2',
            s=80,
            ax=ax2
        )
        ax2.set_title("공부시간 vs 만족도")
        ax2.set_xlabel("일일 공부시간 (시간)")
        ax2.set_ylabel("만족도 (1~10)")
        ax2.grid(True, linestyle='--', alpha=0.5)
        st.pyplot(fig2)
    else:
        st.warning("표시할 데이터가 없습니다.")

st.markdown("---")

# (4) 추가 시각화 (상관관계 히트맵) 및 상세 데이터 테이블
sub_col1, sub_col2 = st.columns(2)

with sub_col1:
    st.markdown("**3) 항목별 상관관계 히트맵**")
    fig3, ax3 = plt.subplots(figsize=(5, 4))
    if len(filtered_df) > 1:
        corr_data = filtered_df[['통학시간', '공부시간', '스마트폰', '수면시간', '만족도']].corr()
        sns.heatmap(corr_data, annot=True, fmt=".2f", cmap="Purples", linewidths=0.5, ax=ax3)
        ax3.set_title("상관관계 분석")
        st.pyplot(fig3)
    else:
        st.info("상관관계를 계산하기에 데이터가 부족합니다.")

with sub_col2:
    st.markdown("**4) 선택된 학과 상세 데이터 요약**")
    st.dataframe(filtered_df[['응답ID', '학과', '만족도', '한줄의견']], height=300)

# 전체 필터링된 데이터를 펼쳐볼 수 있는 영역
with st.expander("선택된 학과의 전체 데이터 테이블 보기"):
    st.dataframe(filtered_df)