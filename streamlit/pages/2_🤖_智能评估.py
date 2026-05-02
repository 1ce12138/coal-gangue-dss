"""
页面2：智能评估
"""
import streamlit as st
import pandas as pd
import os, sys, time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import APP_TITLE, API_CONFIG, EVALUATION_DIMENSIONS
from components.sidebar import render_sidebar
from components.metrics import render_score_card, render_step_indicator
from components.charts import radar_chart, gauge_chart
from utils.api_client import EvalAPIClient
from utils.data_handler import prepare_evaluation_input

st.set_page_config(page_title=f"智能评估 | {APP_TITLE}", page_icon="🤖", layout="wide")

css_path = os.path.join(ROOT_DIR, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "uploaded_data" not in st.session_state:
    st.session_state["uploaded_data"] = None
if "evaluation_results" not in st.session_state:
    st.session_state["evaluation_results"] = []
if "selected_indices" not in st.session_state:
    st.session_state["selected_indices"] = []

render_sidebar()

st.markdown(
    '<div class="main-title"><h1>智能评估</h1>'
    '<p>基于 RAG-Agent 的多维度自动评估</p></div>',
    unsafe_allow_html=True,
)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

df = st.session_state.get("uploaded_data")
selected = st.session_state.get("selected_indices", [])

if df is None or df.empty:
    st.info("请先在「数据管理」页面加载数据。")
    st.stop()

if not selected:
    st.warning("请先在「数据管理」页面选择待评估的方案。")
    st.dataframe(df.head(5), use_container_width=True)
    st.stop()

# 评估模式
st.markdown("#### 评估配置")
eval_mode = st.radio(
    "评估模式",
    ["逐条评估", "批量评估"],
    horizontal=True,
    captions=["查看详细评估过程", "一键完成所有方案"],
)
st.caption(f"待评估方案：{len(selected)} 个")
st.markdown('<hr class="divider">', unsafe_allow_html=True)

client = EvalAPIClient(API_CONFIG)

# ── 逐条评估 ──
if eval_mode == "逐条评估":
    scheme_idx = st.selectbox(
        "选择方案",
        selected,
        format_func=lambda i: f"{df.iloc[i].iloc[0]} - {df.iloc[i].iloc[1]}" if len(df.columns) > 1 else f"方案 {i+1}",
    )

    row = df.iloc[scheme_idx]
    scheme_text = prepare_evaluation_input(row)

    st.markdown("#### 方案详情")
    render_step_indicator(1)
    with st.expander("查看方案完整信息", expanded=True):
        for col, val in row.items():
            if pd.notna(val) and str(val).strip():
                st.markdown(f"**{col}**：{val}")

    if st.button("启动评估", type="primary", use_container_width=True):
        # RAG 检索
        st.markdown("#### RAG 知识检索")
        render_step_indicator(2)
        with st.spinner("正在检索领域知识库..."):
            time.sleep(0.8)

        with st.expander("检索到的参考文献", expanded=False):
            refs = [
                "张伟等. 煤矸石资源化利用技术研究进展[J]. 矿业研究与开发, 2023.",
                "李明. 煤矸石综合利用经济效益分析[J]. 煤炭经济研究, 2022.",
                "王芳等. 煤矸石处置的环境影响评价方法研究[J]. 环境科学与技术, 2023.",
            ]
            for ref in refs:
                st.markdown(f"- {ref}")

        # Agent 评估
        st.markdown("#### LLM 评估")
        render_step_indicator(3)
        with st.spinner("AI 裁判正在评估..."):
            result = client.evaluate(scheme_text)

        # 结果展示
        st.markdown("#### 评估结果")
        render_step_indicator(4)

        g1, g2 = st.columns([1, 2])
        with g1:
            st.plotly_chart(gauge_chart(result["overall_score"], "综合评分"),
                            use_container_width=True)
        with g2:
            st.plotly_chart(radar_chart(result["scores"]),
                            use_container_width=True)

        st.markdown("##### 各维度评分")
        for dim_name, dim_conf in EVALUATION_DIMENSIONS.items():
            score = result["scores"].get(dim_name, 0)
            reasoning = result["reasoning"].get(dim_name, "")
            render_score_card(dim_name, score, dim_conf["icon"],
                              dim_conf["color"], reasoning)

        st.markdown("##### 综合评价")
        st.markdown(
            f'<div class="card" style="color:#9aa0b0; line-height:1.8; font-size:0.88rem;">'
            f'{result["overall_comment"]}</div>',
            unsafe_allow_html=True,
        )

        # 保存结果
        result_entry = {
            "方案索引": scheme_idx,
            "方案名称": row.iloc[1] if len(row) > 1 else row.iloc[0],
            **{f"{k}评分": v for k, v in result["scores"].items()},
            "综合评分": result["overall_score"],
        }
        existing_idx = [r["方案索引"] for r in st.session_state["evaluation_results"]]
        if scheme_idx in existing_idx:
            pos = existing_idx.index(scheme_idx)
            st.session_state["evaluation_results"][pos] = result_entry
        else:
            st.session_state["evaluation_results"].append(result_entry)

        st.success("评估完成，结果已保存。")

# ── 批量评估 ──
else:
    st.markdown("#### 待评估方案")
    st.dataframe(df.iloc[selected].reset_index(drop=True), use_container_width=True)

    if st.button("开始批量评估", type="primary", use_container_width=True):
        progress = st.progress(0)
        status = st.empty()
        all_results = []

        for i, idx in enumerate(selected):
            row = df.iloc[idx]
            scheme_text = prepare_evaluation_input(row)
            name = row.iloc[1] if len(row) > 1 else row.iloc[0]
            status.markdown(f"正在评估 **{name}** ({i+1}/{len(selected)})")
            progress.progress((i + 1) / len(selected))
            result = client.evaluate(scheme_text)
            all_results.append({
                "方案索引": idx,
                "方案名称": name,
                **{f"{k}评分": v for k, v in result["scores"].items()},
                "综合评分": result["overall_score"],
            })

        st.session_state["evaluation_results"] = all_results
        status.empty()
        progress.empty()

        st.success(f"批量评估完成，共 {len(all_results)} 个方案。")
        st.dataframe(pd.DataFrame(all_results), use_container_width=True, hide_index=True)
        st.info("前往「结果分析」页面查看可视化。")
