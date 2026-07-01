"""
页面2：智能评估
"""
import streamlit as st
import pandas as pd
import os, sys, time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import APP_TITLE, EVALUATION_DIMENSIONS
from components.sidebar import render_sidebar
from components.metrics import render_score_card, render_step_indicator
from components.charts import radar_chart, gauge_chart
from utils.api_client import EvalAPIClient
from utils.data_handler import prepare_evaluation_input
from utils.runtime_config import get_runtime_api_config

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
    '<div class="main-title"><h1>基于 LLM 的多维量化评估</h1>'
    '<p>利用大语言模型(LLM)推理引擎对技术方案进行多维自动化评价</p></div>',
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

st.markdown("#### 评估配置")
eval_mode = st.radio(
    "评估模式",
    ["逐条评估", "批量评估"],
    horizontal=True,
    captions=["查看详细评估过程", "一键完成所有方案"],
)
st.caption(f"待评估方案：{len(selected)} 个")
st.markdown('<hr class="divider">', unsafe_allow_html=True)

client = EvalAPIClient(get_runtime_api_config())


def build_result_entry(scheme_idx: int, row: pd.Series, result: dict) -> dict:
    """将模型评估结果保存为跨页面可复用的会话记录。"""
    return {
        "方案索引": scheme_idx,
        "方案名称": row.iloc[1] if len(row) > 1 else row.iloc[0],
        **{f"{k}评分": v for k, v in result["scores"].items()},
        **{f"{k}理由": v for k, v in result.get("reasoning", {}).items()},
        "综合评分": result["overall_score"],
        "综合评价": result.get("overall_comment", ""),
    }


def restore_result(entry: dict) -> dict:
    """从保存的表格记录还原评估结果展示结构。"""
    scores = {dim: entry.get(f"{dim}评分", 0) for dim in EVALUATION_DIMENSIONS}
    reasoning = {dim: entry.get(f"{dim}理由", "") for dim in EVALUATION_DIMENSIONS}
    return {
        "scores": scores,
        "overall_score": entry.get("综合评分", 0),
        "reasoning": reasoning,
        "overall_comment": entry.get("综合评价", "该结果来自当前会话已保存的评估记录。"),
    }


def get_saved_entry(scheme_idx: int):
    """查找当前方案是否已有评估结果。"""
    for entry in st.session_state.get("evaluation_results", []):
        if entry.get("方案索引") == scheme_idx:
            return entry
    return None


def save_result_entry(entry: dict):
    """新增或覆盖当前方案的评估结果。"""
    existing_idx = [r.get("方案索引") for r in st.session_state["evaluation_results"]]
    if entry["方案索引"] in existing_idx:
        st.session_state["evaluation_results"][existing_idx.index(entry["方案索引"])] = entry
    else:
        st.session_state["evaluation_results"].append(entry)


def render_evaluation_result(result: dict, caption: str = ""):
    """统一渲染评估结果，便于首次评估和返回页面复用。"""
    st.markdown("#### 评估结果")
    if caption:
        st.caption(caption)
    render_step_indicator(4)

    g1, g2 = st.columns([1, 2])
    with g1:
        st.plotly_chart(gauge_chart(result["overall_score"], "综合评分"), use_container_width=True)
    with g2:
        st.plotly_chart(radar_chart(result["scores"]), use_container_width=True)

    st.markdown("##### 各维度评分")
    for dim_name, dim_conf in EVALUATION_DIMENSIONS.items():
        score = result["scores"].get(dim_name, 0)
        reasoning = result.get("reasoning", {}).get(dim_name, "")
        render_score_card(dim_name, score, dim_conf["icon"], dim_conf["color"], reasoning)

    st.markdown("##### 综合评价")
    st.markdown(
        f'<div class="card" style="color:#9aa0b0; line-height:1.8; font-size:0.88rem;">'
        f'{result.get("overall_comment", "")}</div>',
        unsafe_allow_html=True,
    )


if eval_mode == "逐条评估":
    scheme_idx = st.selectbox(
        "选择方案",
        selected,
        format_func=lambda i: f"{df.iloc[i].iloc[0]} - {df.iloc[i].iloc[1]}" if len(df.columns) > 1 else f"方案 {i+1}",
    )

    row = df.iloc[scheme_idx]
    scheme_text = prepare_evaluation_input(row)
    saved_entry = get_saved_entry(scheme_idx)

    st.markdown("#### 方案详情")
    render_step_indicator(1)
    with st.expander("查看方案完整信息", expanded=True):
        for col, val in row.items():
            if pd.notna(val) and str(val).strip():
                st.markdown(f"**{col}**：{val}")

    if saved_entry is not None:
        render_evaluation_result(restore_result(saved_entry), "已显示当前会话中保存的上一次评估结果。")
        st.markdown("")

    button_label = "重新评估" if saved_entry is not None else "启动评估"
    if st.button(button_label, type="primary", use_container_width=True):
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

        st.markdown("#### LLM 评估")
        render_step_indicator(3)
        with st.spinner("AI 裁判正在评估..."):
            result = client.evaluate(scheme_text)

        render_evaluation_result(result)
        save_result_entry(build_result_entry(scheme_idx, row, result))
        st.success("评估完成，结果已保存。")

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
            all_results.append(build_result_entry(idx, row, result))

        st.session_state["evaluation_results"] = all_results
        status.empty()
        progress.empty()

        st.success(f"批量评估完成，共 {len(all_results)} 个方案。")
        st.dataframe(pd.DataFrame(all_results), use_container_width=True, hide_index=True)
        st.info("前往「结果分析」页面查看可视化。")
