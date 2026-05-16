"""
运行时配置工具 — 统一管理后台 API Key、模型与评估参数。
"""

from collections.abc import Mapping

import streamlit as st

from config import API_CONFIG


def get_runtime_api_config() -> dict:
    """合并全局配置、Streamlit secrets 与当前会话评估参数。"""
    secret_config = _get_minimax_secrets()
    return {
        **API_CONFIG,
        "base_url": secret_config.get("base_url", API_CONFIG["base_url"]),
        "api_key": secret_config.get("api_key", API_CONFIG["api_key"]),
        "model": secret_config.get("model", API_CONFIG["model"]),
        "temperature": st.session_state.get("eval_temperature", API_CONFIG["temperature"]),
    }


def _get_minimax_secrets() -> dict:
    """读取 .streamlit/secrets.toml 中的 [minimax] 配置。"""
    try:
        minimax_config = st.secrets.get("minimax", {})
    except Exception:
        minimax_config = {}

    if isinstance(minimax_config, Mapping):
        return {
            "base_url": str(minimax_config.get("base_url", "")).strip() or API_CONFIG["base_url"],
            "api_key": str(minimax_config.get("api_key", "")).strip() or API_CONFIG["api_key"],
            "model": str(minimax_config.get("model", "")).strip() or API_CONFIG["model"],
        }

    return {}
