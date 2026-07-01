"""
图表组件 — 基于 Plotly 的交互式图表
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

_LAYOUT_TEMPLATE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Noto Sans SC, sans-serif", color="#4b5563"),
    margin=dict(l=40, r=40, t=50, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0.1)", borderwidth=1, font=dict(size=12)),
)


def radar_chart(scores: dict, title: str = "多维度评估雷达图") -> go.Figure:
    dims = list(scores.keys())
    values = list(scores.values())
    dims_closed = dims + [dims[0]]
    values_closed = values + [values[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=dims_closed,
        fill="toself",
        fillcolor="rgba(0, 150, 199, 0.15)",
        line=dict(color="#00b4d8", width=2),
        marker=dict(size=8, color="#00b4d8"),
        name="评估得分",
        hovertemplate="%{theta}: %{r:.1f}分<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT_TEMPLATE,
        title=dict(text=title, x=0.5, font=dict(size=16)),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10, color="#6b7280"), gridcolor="rgba(0,0,0,0.08)"),
            angularaxis=dict(tickfont=dict(size=12, color="#4b5563"), gridcolor="rgba(0,0,0,0.08)"),
        ),
        showlegend=False,
        height=400,
    )
    return fig


def multi_radar_chart(schemes_scores: dict, title: str = "多方案对比雷达图") -> go.Figure:
    colors = ["#00b4d8", "#f59e0b", "#16a34a", "#dc2626", "#a855f7"]
    fig = go.Figure()
    for i, (name, scores) in enumerate(schemes_scores.items()):
        dims = list(scores.keys())
        values = list(scores.values())
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=dims + [dims[0]],
            fill="toself",
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=6, color=colors[i % len(colors)]),
            name=name,
            hovertemplate=f"{name}<br>%{{theta}}: %{{r:.1f}}分<extra></extra>",
        ))
    fig.update_layout(
        **_LAYOUT_TEMPLATE,
        title=dict(text=title, x=0.5, font=dict(size=16)),
        polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(0,0,0,0.08)")),
        height=450,
    )
    return fig


def score_bar_chart(df: pd.DataFrame, score_col: str = "综合评分", name_col: str = "方案名称", title: str = "方案综合评分排名") -> go.Figure:
    df_sorted = df.sort_values(score_col, ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_sorted[name_col],
        x=df_sorted[score_col],
        orientation="h",
        marker=dict(color="#00b4d8", line=dict(color="rgba(0,0,0,0.1)", width=1)),
        text=[f"{s:.1f}" for s in df_sorted[score_col]],
        textposition="outside",
        hovertemplate="%{y}<br>综合评分: %{x:.1f}<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT_TEMPLATE,
        title=dict(text=title, x=0.5, font=dict(size=16)),
        xaxis=dict(title="综合评分", range=[0, 110], gridcolor="rgba(0,0,0,0.05)", zeroline=False),
        yaxis=dict(title=""),
        height=max(300, len(df_sorted) * 50 + 100),
        showlegend=False,
    )
    return fig


def dimension_heatmap(df: pd.DataFrame, title: str = "各维度评分热力图") -> go.Figure:
    score_cols = [c for c in df.columns if any(dim in c for dim in ["技术可行性", "经济可行性", "实施风险与约束", "经济效益", "环境合规性", "综合评分"])]
    name_col = next((c for c in df.columns if "方案" in c and "编号" not in c), df.columns[0])
    if not score_cols:
        score_cols = [c for c in df.columns if df[c].dtype in ["float64", "int64"]]
    z_data = df[score_cols].values
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=[c.replace("AI_", "").replace("人工_", "") for c in score_cols],
        y=df[name_col].tolist(),
        colorscale="Blues",
        text=np.round(z_data, 1).astype(str),
        texttemplate="%{text}",
        hovertemplate="%{y}<br>%{x}: %{z:.1f}分<extra></extra>",
    ))
    fig.update_layout(**_LAYOUT_TEMPLATE, title=dict(text=title, x=0.5, font=dict(size=16)), height=max(300, len(df) * 40 + 150))
    return fig


def scatter_consistency(human: np.ndarray, ai: np.ndarray, title: str = "人工评分 vs AI 评分") -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=human, y=ai, mode="markers", marker=dict(size=10, color="#00b4d8", opacity=0.7), name="评分对"))
    min_val = min(min(human), min(ai)) - 5
    max_val = max(max(human), max(ai)) + 5
    fig.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val], mode="lines", line=dict(color="#dc2626", dash="dash", width=2), name="理想一致线 (y=x)"))
    if len(human) >= 2:
        from scipy import stats as sp_stats
        slope, intercept, r, p, se = sp_stats.linregress(human, ai)
        fit_x = np.linspace(min_val, max_val, 100)
        fig.add_trace(go.Scatter(x=fit_x, y=slope * fit_x + intercept, mode="lines", line=dict(color="#16a34a", width=2), name=f"回归线 (R²={r**2:.3f})"))
    fig.update_layout(**_LAYOUT_TEMPLATE, title=dict(text=title, x=0.5, font=dict(size=16)), xaxis=dict(title="人工专家评分"), yaxis=dict(title="AI 自动评分"), height=450)
    return fig


def bland_altman_plot(human: np.ndarray, ai: np.ndarray, title: str = "Bland-Altman 一致性分析") -> go.Figure:
    means = (human + ai) / 2
    diffs = ai - human
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1) if len(diffs) >= 2 else 0
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=means, y=diffs, mode="markers", marker=dict(size=10, color="#00b4d8", opacity=0.7), name="评分差值"))
    fig.add_hline(y=mean_diff, line=dict(color="#f59e0b", width=2), annotation_text=f"Mean = {mean_diff:.2f}")
    fig.add_hline(y=mean_diff + 1.96 * std_diff, line=dict(color="#dc2626", dash="dash", width=1.5), annotation_text=f"+1.96SD = {mean_diff + 1.96 * std_diff:.2f}")
    fig.add_hline(y=mean_diff - 1.96 * std_diff, line=dict(color="#dc2626", dash="dash", width=1.5), annotation_text=f"-1.96SD = {mean_diff - 1.96 * std_diff:.2f}")
    fig.add_hline(y=0, line=dict(color="rgba(0,0,0,0.2)", width=1))
    fig.update_layout(**_LAYOUT_TEMPLATE, title=dict(text=title, x=0.5, font=dict(size=16)), xaxis=dict(title="两种评分均值"), yaxis=dict(title="评分差值（AI − 人工）"), height=450, showlegend=False)
    return fig


def gauge_chart(score: float, title: str = "综合评分", max_val: float = 100) -> go.Figure:
    """绘制仪表盘评分图"""
    color = "#2d6a4f" if score >= 80 else "#f59e0b" if score >= 60 else "#dc2626"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(font=dict(size=40, color=color), suffix="分"),
        title=dict(text=title, font=dict(size=14, color="#4b5563")),
        gauge=dict(
            axis=dict(range=[0, max_val], tickfont=dict(size=10, color="#6b7280"), dtick=20),
            bar=dict(color=color, thickness=0.3),
            bgcolor="rgba(0,0,0,0.05)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
            steps=[
                dict(range=[0, 60], color="rgba(230, 57, 70, 0.1)"),
                dict(range=[60, 80], color="rgba(244, 140, 6, 0.1)"),
                dict(range=[80, 100], color="rgba(45, 106, 79, 0.1)"),
            ],
            threshold=dict(line=dict(color="#1f2937", width=2), thickness=0.8, value=score),
        ),
    ))
    gauge_layout = {**_LAYOUT_TEMPLATE, "height": 250, "margin": dict(l=30, r=30, t=50, b=20)}
    fig.update_layout(**gauge_layout)
    return fig
