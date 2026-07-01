"""
指标卡片与可复用 UI 组件
"""

import streamlit as st


def render_metric_card(value: str, label: str, color: str = "#4a9eff"):
    """渲染指标卡片"""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {color};">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_card(dimension: str, score: float, icon: str, color: str,
                      reasoning: str = ""):
    """渲染评分维度卡片"""
    if score >= 85:
        level = "优秀"
    elif score >= 70:
        level = "良好"
    elif score >= 60:
        level = "中等"
    else:
        level = "待改进"

    bar_width = min(score, 100)
    weights = {"技术可行性": "45%", "经济可行性": "45%", "实施风险与约束": "10%"}
    weight = weights.get(dimension, "")

    reasoning_html = ""
    if reasoning:
        reasoning_html = (
            '<div style="margin-top: 0.6rem; padding-top: 0.6rem; '
            'border-top: 1px solid var(--border); '
            f'font-size: 0.82rem; color: var(--text-secondary); line-height: 1.7;">{reasoning}</div>'
        )

    st.markdown(
        f"""
        <div class="card" style="border-left: 3px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                <div style="font-size: 0.95rem; font-weight: 500; color: var(--text-primary);">{dimension}</div>
                <div>
                    <span style="font-size: 1.5rem; font-weight: 600; color: {color};">{score:.1f}</span>
                    <span style="font-size: 0.78rem; color: var(--text-dim); margin-left: 2px;">/ 100</span>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {bar_width}%; background: {color};"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 0.3rem; font-size: 0.75rem; color: var(--text-dim);">
                <span>{level}</span>
                <span>权重 {weight}</span>
            </div>
            {reasoning_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_steps():
    """渲染工作流程"""
    st.markdown(
        """
        <div class="workflow-container">
            <div class="workflow-step">
                <div class="step-num">Step 1</div>
                <div class="step-label">多源数据提取</div>
            </div>
            <span class="workflow-arrow">→</span>
            <div class="workflow-step">
                <div class="step-num">Step 2</div>
                <div class="step-label">知识检索增强(RAG)</div>
            </div>
            <span class="workflow-arrow">→</span>
            <div class="workflow-step">
                <div class="step-num">Step 3</div>
                <div class="step-label">大模型逻辑推理</div>
            </div>
            <span class="workflow-arrow">→</span>
            <div class="workflow-step">
                <div class="step-num">Step 4</div>
                <div class="step-label">多维量化评分</div>
            </div>
            <span class="workflow-arrow">→</span>
            <div class="workflow-step">
                <div class="step-num">Step 5</div>
                <div class="step-label">人机一致性验证</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_step_indicator(current_step: int, total_steps: int = 4,
                          labels: list = None):
    """渲染步骤进度指示器"""
    if labels is None:
        labels = ["原始数据输入", "知识库检索(RAG)", "多维逻辑推理", "评分结果输出"]

    html_parts = ['<div class="step-indicator">']
    for i in range(total_steps):
        step_num = i + 1
        if step_num < current_step:
            cls, icon = "completed", "✓"
        elif step_num == current_step:
            cls, icon = "active", str(step_num)
        else:
            cls, icon = "pending", str(step_num)
        html_parts.append(f'<div class="step-dot {cls}">{icon}</div>')
        if i < total_steps - 1:
            line_cls = "completed" if step_num < current_step else ""
            html_parts.append(f'<div class="step-line {line_cls}"></div>')
    html_parts.append("</div>")

    html_parts.append('<div style="display: flex; justify-content: space-between; padding: 0 0.5rem;">')
    for label in labels:
        html_parts.append(
            f'<span style="font-size: 0.7rem; color: var(--text-dim); text-align: center; flex: 1;">{label}</span>'
        )
    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)
