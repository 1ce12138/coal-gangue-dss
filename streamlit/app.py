"""
煤矸石资源化利用多维评估决策支持系统
主页
"""

import streamlit as st
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import APP_TITLE, APP_SUBTITLE, APP_DESCRIPTION
from components.sidebar import render_sidebar
from components.metrics import render_metric_card, render_workflow_steps

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="⚒️",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = os.path.join(ROOT_DIR, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "uploaded_data" not in st.session_state:
    st.session_state["uploaded_data"] = None
if "evaluation_results" not in st.session_state:
    st.session_state["evaluation_results"] = []

render_sidebar()

# ── 标题 ──
st.markdown(
    f'<div class="main-title"><h1>{APP_TITLE}</h1><p>{APP_SUBTITLE}</p></div>',
    unsafe_allow_html=True,
)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── 简介 ──
st.markdown(
    f"""
    <div class="card">
        <p style="font-size: 0.9rem; line-height: 1.8; color: var(--text-secondary); margin: 0;">
            {APP_DESCRIPTION}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 工作流程 ──
st.markdown("#### 系统工作流程")
render_workflow_steps()

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── 创新点 ──
st.markdown("#### 核心创新点")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="info-card">
            <div class="card-title">评估范式创新</div>
            <div class="card-desc">
                在煤基固废管理领域提出基于 RAG 驱动的 LLM-as-a-Judge 自动化评估范式，
                克服通用大模型在垂直领域的幻觉问题。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="info-card">
            <div class="card-title">管科决策智能化</div>
            <div class="card-desc">
                将 AHP 层次分析法等多准则决策方法深度内化到 Agent 结构化提示词模板中，
                保障评估的可解释性与稳健性。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="info-card">
            <div class="card-title">全链路 DSS 落地</div>
            <div class="card-desc">
                构建端到端的 Web 决策支持系统，利用人工评测数据集进行大样本人机一致性检验，
                实现煤矸石管理决策的工具化。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── 系统参数 ──
st.markdown("#### 系统参数")

m1, m2, m3, m4 = st.columns(4)
with m1:
    render_metric_card("3", "评估维度")
with m2:
    render_metric_card("12", "子评价指标")
with m3:
    render_metric_card("MiniMax", "裁判引擎")
with m4:
    render_metric_card("RAG", "知识增强")

# ── 底部 ──
st.markdown("")
st.markdown(
    '<div style="text-align: center; padding: 1.5rem 0; color: var(--text-dim); font-size: 0.75rem;">'
    "基于 RAG-Agent 的煤矸石资源化利用多维评估决策支持系统 v1.0.0"
    "</div>",
    unsafe_allow_html=True,
)
