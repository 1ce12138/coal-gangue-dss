"""
页面4：一致性检验
"""
import streamlit as st
import pandas as pd
import numpy as np
import os, sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import APP_TITLE
from components.sidebar import render_sidebar
from components.metrics import render_metric_card
from components.charts import scatter_consistency, bland_altman_plot
from utils.evaluation import calculate_consistency, generate_demo_consistency_data
from utils.data_handler import load_csv

st.set_page_config(page_title=f"人机协同一致性统计检验 | {APP_TITLE}", page_icon="🔬", layout="wide")

css_path = os.path.join(ROOT_DIR, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

render_sidebar()

st.markdown(
    '<div class="main-title"><h1>人机协同一致性统计检验</h1>'
    '<p>通过大样本统计学检验，证明 LLM 评估与专家认知具备高度一致性，验证模型稳健性</p></div>',
    unsafe_allow_html=True,
)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["上传对比数据", "模拟数据"])
consistency_df = None

with tab1:
    st.caption("CSV 列名格式：人工_技术可行性、AI_技术可行性、人工_综合评分、AI_综合评分 等")
    uploaded = st.file_uploader("上传对比数据", type=["csv"], label_visibility="collapsed", key="c_upload")
    if uploaded:
        consistency_df = load_csv(uploaded)

with tab2:
    if st.button("生成 30 组模拟数据", type="primary"):
        consistency_df = generate_demo_consistency_data(30)
        st.session_state["consistency_data"] = consistency_df
        st.success("已生成 30 组模拟数据")
        st.rerun()

if "consistency_data" in st.session_state and consistency_df is None:
    consistency_df = st.session_state["consistency_data"]

if consistency_df is None:
    st.info("请上传对比数据或生成模拟数据。")
    st.stop()

st.markdown("#### 数据预览")
st.dataframe(consistency_df.head(10), use_container_width=True, hide_index=True)
st.caption(f"共 {len(consistency_df)} 组数据")
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# 维度选择
dimensions = ["综合评分", "技术可行性", "经济效益", "环境合规性"]
available = [d for d in dimensions if f"人工_{d}" in consistency_df.columns and f"AI_{d}" in consistency_df.columns]
if not available:
    st.error("数据中未找到匹配的人工/AI评分列。")
    st.stop()

selected_dim = st.selectbox("分析维度", available)
human = consistency_df[f"人工_{selected_dim}"].dropna().values
ai = consistency_df[f"AI_{selected_dim}"].dropna().values
metrics = calculate_consistency(human, ai)

st.markdown(f"#### {selected_dim} — 一致性指标")

m1, m2, m3, m4 = st.columns(4)
with m1:
    r = metrics.get("pearson", {}).get("r", 0)
    render_metric_card(f"{r:.4f}", "Pearson r", "#34a853" if abs(r) >= 0.7 else "#f5a623")
with m2:
    rho = metrics.get("spearman", {}).get("rho", 0)
    render_metric_card(f"{rho:.4f}", "Spearman rho", "#34a853" if abs(rho) >= 0.7 else "#f5a623")
with m3:
    tau = metrics.get("kendall", {}).get("tau", 0)
    render_metric_card(f"{tau:.4f}", "Kendall tau", "#34a853" if abs(tau) >= 0.5 else "#f5a623")
with m4:
    render_metric_card(f"{metrics['rmse']:.2f}", "RMSE", "#34a853" if metrics["rmse"] < 10 else "#f5a623")

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# 图表
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(scatter_consistency(human, ai, f"{selected_dim}"), use_container_width=True)
with c2:
    st.plotly_chart(bland_altman_plot(human, ai, f"{selected_dim}"), use_container_width=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# 统计报告
st.markdown("#### 统计检验报告")
rows = []
if "pearson" in metrics:
    p = metrics["pearson"]
    rows.append({"方法": "Pearson", "统计量": f"r = {p['r']:.4f}", "p 值": f"{p['p_value']:.6f}",
                 "显著性": "是" if p["p_value"] < 0.05 else "否", "强度": p["interpretation"]})
if "spearman" in metrics:
    s = metrics["spearman"]
    rows.append({"方法": "Spearman", "统计量": f"rho = {s['rho']:.4f}", "p 值": f"{s['p_value']:.6f}",
                 "显著性": "是" if s["p_value"] < 0.05 else "否", "强度": s["interpretation"]})
if "kendall" in metrics:
    k = metrics["kendall"]
    rows.append({"方法": "Kendall", "统计量": f"tau = {k['tau']:.4f}", "p 值": f"{k['p_value']:.6f}",
                 "显著性": "是" if k["p_value"] < 0.05 else "否", "强度": k["interpretation"]})
rows.append({"方法": "RMSE", "统计量": f"{metrics['rmse']:.4f}", "p 值": "-", "显著性": "-", "强度": "越小越好"})
rows.append({"方法": "MAE", "统计量": f"{metrics['mae']:.4f}", "p 值": "-", "显著性": "-", "强度": "越小越好"})
if "icc" in metrics:
    rows.append({"方法": "ICC", "统计量": f"{metrics['icc']:.4f}", "p 值": "-", "显著性": "-",
                 "强度": "优秀" if metrics["icc"] >= 0.9 else "良好" if metrics["icc"] >= 0.75 else "中等"})
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# 结论
if "pearson" in metrics and metrics["pearson"]["r"] >= 0.7:
    st.success(f"{selected_dim}维度 Pearson r={metrics['pearson']['r']:.4f}，人机一致性良好。")
else:
    st.warning(f"{selected_dim}维度一致性偏低，建议优化提示词或扩充知识库。")

# 全维度汇总
if len(available) > 1:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("#### 全维度汇总")
    summary = []
    for d in available:
        h = consistency_df[f"人工_{d}"].dropna().values
        a = consistency_df[f"AI_{d}"].dropna().values
        m = calculate_consistency(h, a)
        summary.append({"维度": d, "Pearson": f"{m.get('pearson',{}).get('r',0):.4f}",
                        "Spearman": f"{m.get('spearman',{}).get('rho',0):.4f}",
                        "RMSE": f"{m.get('rmse',0):.2f}", "MAE": f"{m.get('mae',0):.2f}"})
    st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)
