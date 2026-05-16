"""
页面3：结果分析
"""
import streamlit as st
import pandas as pd
import os, sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import APP_TITLE, EVALUATION_DIMENSIONS
from components.sidebar import render_sidebar
from components.metrics import render_metric_card
from components.charts import radar_chart, multi_radar_chart, score_bar_chart, dimension_heatmap
from utils.data_handler import export_results

st.set_page_config(page_title=f"结果分析 | {APP_TITLE}", page_icon="📈", layout="wide")

css_path = os.path.join(ROOT_DIR, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "evaluation_results" not in st.session_state:
    st.session_state["evaluation_results"] = []
render_sidebar()

st.markdown(
    '<div class="main-title"><h1>多维评估结果可视化分析</h1>'
    '<p>方案评估结果的高维展示与多视角对比分析</p></div>',
    unsafe_allow_html=True,
)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

results = st.session_state.get("evaluation_results", [])
if not results:
    st.info("暂无评估结果，请先完成评估。")
    st.stop()

results_df = pd.DataFrame(results)

st.markdown("#### 概览")
m1, m2, m3 = st.columns(3)
with m1:
    render_metric_card(str(len(results_df)), "方案数")
with m2:
    render_metric_card(f"{results_df['综合评分'].mean():.1f}", "平均分")
with m3:
    render_metric_card(str(results_df.loc[results_df['综合评分'].idxmax(), '方案名称']), "最优方案", "#34a853")

st.markdown('<hr class="divider">', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["综合排名", "雷达对比", "热力分布", "详细数据"])
with tab1:
    st.plotly_chart(score_bar_chart(results_df, "综合评分", "方案名称"), use_container_width=True)
with tab2:
    if len(results_df) == 1:
        r = results_df.iloc[0]
        scores = {d: r.get(f"{d}评分", 0) for d in EVALUATION_DIMENSIONS}
        st.plotly_chart(radar_chart(scores, r['方案名称']), use_container_width=True)
    else:
        compare = st.multiselect("选择对比方案", results_df["方案名称"].tolist(), default=results_df["方案名称"].tolist()[:5])
        if compare:
            s = {n: {d: results_df[results_df["方案名称"]==n].iloc[0].get(f"{d}评分",0) for d in EVALUATION_DIMENSIONS} for n in compare}
            st.plotly_chart(multi_radar_chart(s), use_container_width=True)
with tab3:
    cols = ["方案名称"] + [c for c in results_df.columns if "评分" in c]
    st.plotly_chart(dimension_heatmap(results_df[cols]), use_container_width=True)
with tab4:
    st.dataframe(results_df, use_container_width=True, hide_index=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown("#### 导出")
c1, c2, _ = st.columns([1, 1, 3])
with c1:
    st.download_button("CSV", export_results(results_df, "csv"), "results.csv", "text/csv", use_container_width=True)
with c2:
    st.download_button("Excel", export_results(results_df, "xlsx"), "results.xlsx", use_container_width=True)
