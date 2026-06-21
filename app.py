import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 웹앱 기본 설정
st.set_page_config(page_title="스마트 공정관리 대시보드", page_icon="🏭", layout="wide")

# --- UI 업그레이드: 커스텀 CSS 주입 (메트릭 카드 디자인) ---
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #f8f9fa;
    border: 1px solid #e0e0e0;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    transition: transform 0.2s;
}
div[data-testid="metric-container"]:hover {
    transform: scale(1.02);
}
</style>
""", unsafe_allow_html=True)

st.title("📊 스마트제조: 공정능력 & SPC 모니터링 대시보드")
st.markdown("현업 수준의 **통계적 공정관리(SPC)** 및 **공정능력지수(Cp, Cpk)** 실시간 분석 화면입니다.")

# 2. 사이드바 설정 (파라미터 입력 및 데이터 생성)
with st.sidebar:
    st.header("⚙️ 공정 제어반")
    st.markdown("---")
    # 규격 상한/하한 설정
    USL = st.number_input("규격 상한 (USL)", value=110.0, step=1.0)
    LSL = st.number_input("규격 하한 (LSL)", value=90.0, step=1.0)
    
    st.markdown("---")
    st.subheader("데이터 시뮬레이션")
    st.caption("새로운 센서 데이터를 실시간으로 수집합니다.")
    # 데이터 재생성 버튼 (색상 강조)
    if st.button("🔄 실시간 데이터 갱신", type="primary", use_container_width=True):
        st.session_state.clear()

# 3. 데이터 자동 생성 로직 (샘플크기 n=5, 부분군 25개)
if 'data' not in st.session_state:
    np.random.seed(np.random.randint(0, 10000))
    raw_data = np.random.normal(loc=100, scale=2.5, size=(25, 5))
    df = pd.DataFrame(raw_data, columns=['S1', 'S2', 'S3', 'S4', 'S5'])
    df.index = [f"Subgroup {i+1}" for i in range(25)]
    st.session_state['data'] = df

df = st.session_state['data']

# 부분군별 평균(X-bar)과 범위(R) 계산
df['X-bar'] = df.mean(axis=1)
df['R'] = df.max(axis=1) - df.min(axis=1)

X_double_bar = df['X-bar'].mean()
R_bar = df['R'].mean()

# 4. 공정능력분석 계산
sigma_hat = R_bar / 2.326
Cp = (USL - LSL) / (6 * sigma_hat)
Cpk_upper = (USL - X_double_bar) / (3 * sigma_hat)
Cpk_lower = (X_double_bar - LSL) / (3 * sigma_hat)
Cpk = min(Cpk_upper, Cpk_lower)

# 관리한계선 계산
A2, D3, D4 = 0.577, 0, 2.114
UCL_x, LCL_x = X_double_bar + (A2 * R_bar), X_double_bar - (A2 * R_bar)
UCL_r, LCL_r = D4 * R_bar, D3 * R_bar

# --- 대시보드 화면 구성 ---

st.markdown("### 🎯 1. 실시간 공정능력 지표 (Process Capability)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("전체 공정 평균 (X̿)", f"{X_double_bar:.2f}")
col2.metric("공정 산포 (추정 표준편차)", f"{sigma_hat:.2f}")
col3.metric("Cp (단순 공정능력)", f"{Cp:.2f}", "목표: 1.0 이상" if Cp >= 1.0 else "산포 불량", delta_color="normal" if Cp >= 1.0 else "inverse")
col4.metric("Cpk (치우침 고려 공정능력)", f"{Cpk:.2f}", "양호 (1.33 이상)" if Cpk >= 1.33 else "개선 필요", delta_color="normal" if Cpk >= 1.33 else "inverse")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📈 2. 통계적 공정관리 차트 (SPC Charts)")

# --- UI 업그레이드: 탭(Tab) 레이아웃 활용 ---
tab1, tab2, tab3 = st.tabs(["📊 X-bar 관리도 (평균 관리)", "📊 R 관리도 (산포 관리)", "📋 원본 데이터 테이블"])

with tab1:
    fig_x = go.Figure()
    fig_x.add_trace(go.Scatter(x=df.index, y=df['X-bar'], mode='lines+markers', name='X-bar', marker=dict(size=8, color='#1f77b4')))
    fig_x.add_hline(y=UCL_x, line_dash="dash", line_color="#d62728", annotation_text=f"UCL: {UCL_x:.2f}")
    fig_x.add_hline(y=LCL_x, line_dash="dash", line_color="#d62728", annotation_text=f"LCL: {LCL_x:.2f}")
    fig_x.add_hline(y=X_double_bar, line_dash="solid", line_color="#2ca02c", annotation_text=f"Center Line: {X_double_bar:.2f}")
    fig_x.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20), height=400)
    st.plotly_chart(fig_x, use_container_width=True)

with tab2:
    fig_r = go.Figure()
    fig_r.add_trace(go.Scatter(x=df.index, y=df['R'], mode='lines+markers', name='R', marker=dict(size=8, color='#ff7f0e')))
    fig_r.add_hline(y=UCL_r, line_dash="dash", line_color="#d62728", annotation_text=f"UCL: {UCL_r:.2f}")
    fig_r.add_hline(y=LCL_r, line_dash="dash", line_color="#d62728", annotation_text=f"LCL: {LCL_r:.2f}")
    fig_r.add_hline(y=R_bar, line_dash="solid", line_color="#2ca02c", annotation_text=f"Center Line: {R_bar:.2f}")
    fig_r.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20), height=400)
    st.plotly_chart(fig_r, use_container_width=True)

with tab3:
    st.dataframe(df.style.highlight_max(axis=0, color='#f0f2f6'), use_container_width=True)