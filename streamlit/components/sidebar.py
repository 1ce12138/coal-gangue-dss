"""
侧边栏组件
"""

import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import API_CONFIG
from utils.api_client import EvalAPIClient
from utils.runtime_config import get_runtime_api_config


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center; padding: 0.8rem 0 1rem;">
                <div style="font-size: 0.95rem; font-weight: 600; color: var(--text-primary);">
                    煤矸石评估 DSS
                </div>
                <div style="font-size: 0.72rem; color: var(--text-secondary); margin-top: 0.2rem;">
                    v1.0.0
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        st.caption("系统状态")
        client = EvalAPIClient(get_runtime_api_config())
        conn = client.check_connection()

        if conn["status"] == "demo":
            st.info("ℹ️ **原型验证模式** — 未配置 MiniMax API Key", icon="ℹ️")
        elif conn["status"] == "connected":
            st.success("API 已连接", icon="✅")
        else:
            st.error(conn["message"], icon="🚨")

        st.divider()

        st.caption("模型推理参数")
        temp = st.slider(
            "模型温度",
            min_value=0.0,
            max_value=1.0,
            value=API_CONFIG["temperature"],
            step=0.1,
            help="较低的温度使评估结果更稳定",
        )
        st.session_state["eval_temperature"] = temp

        st.divider()

        st.caption("当前会话")
        data_count = 0
        eval_count = 0
        if "uploaded_data" in st.session_state and st.session_state["uploaded_data"] is not None:
            data_count = len(st.session_state["uploaded_data"])
        if "evaluation_results" in st.session_state:
            eval_count = len(st.session_state["evaluation_results"])

        col1, col2 = st.columns(2)
        col1.metric("方案数", data_count)
        col2.metric("已评估", eval_count)
