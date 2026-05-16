"""
图表组件 — 基于 Plotly 的交互式图表
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd


# ── 通用布局模板 ──
_LAYOUT_TEMPLATE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Noto Sans SC, sans-serif", color="#4b5563"),
    margin=dict(l=40, r=40, t=50, b=40),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(0,0,0,0.1)",
        borderwidth=1,
        font=dict(size=12),
    ),
)


def radar_chart(scores: dict, title: str = "多维度评估雷达图") -> go.Figure:
    """绘制单个方案的多维度评估雷达图"""
    dims = list(scores.keys())
    values = list(scores.values())
    # 闭合雷达图
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
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color="#6b7280"),
                gridcolor="rgba(0,0,0,0.08)",
                linecolor="rgba(0,0,0,0.08)",
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#4b5563"),
                gridcolor="rgba(0,0,0,0.08)",
                linecolor="rgba(0,0,0,0.08)",
            ),
        ),
        showlegend=False,
        height=400,
    )

    return fig


def multi_radar_chart(schemes_scores: dict, title: str = "多方案对比雷达图") -> go.Figure:
    """绘制多个方案的雷达图对比"""
    colors = ["#00b4d8", "#f59e0b", "#16a34a", "#dc2626", "#a855f7"]

    fig = go.Figure()

    for i, (name, scores) in enumerate(schemes_scores.items()):
        dims = list(scores.keys())
        values = list(scores.values())
        dims_closed = dims + [dims[0]]
        values_closed = values + [values[0]]
        color = colors[i % len(colors)]

        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=dims_closed,
            fill="toself",
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
            line=dict(color=color, width=2),
            marker=dict(size=6, color=color),
            name=name,
            hovertemplate=f"{name}<br>%{{theta}}: %{{r:.1f}}分<extra></extra>",
        ))

    fig.update_layout(
        **_LAYOUT_TEMPLATE,
        title=dict(text=title, x=0.5, font=dict(size=16)),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color="#6b7280"),
                gridcolor="rgba(0,0,0,0.08)",
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#4b5563"),
                gridcolor="rgba(0,0,0,0.08)",
            ),
        ),
        height=450,
    )

    return fig


def score_bar_chart(df: pd.DataFrame, score_col: str = "综合评分",
                    name_col: str = "方案名称", title: str = "方案综合评分排名") -> go.Figure:
    """绘制方案综合评分排名柱状图"""
    df_sorted = df.sort_values(score_col, ascending=True)

    # 渐变色映射
    scores = df_sorted[score_col].values
    colors = [
        f"rgba({int(0 + (0 - 0) * (s - scores.min()) / max(scores.max() - scores.min(), 1))},"
        f"{int(150 + (180 - 150) * (s - scores.min()) / max(scores.max() - scores.min(), 1))},"
        f"{int(199 + (108 - 199) * (s - scores.min()) / max(scores.max() - scores.min(), 1))}, 0.85)"
        for s in scores
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df_sorted[name_col],
        x=df_sorted[score_col],
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(color="rgba(0,0,0,0.1)", width=1),
            cornerradius=4,
        ),
        text=[f"{s:.1f}" for s in df_sorted[score_col]],
        textposition="outside",
        textfont=dict(size=12, color="#4b5563"),
        hovertemplate="%{y}<br>综合评分: %{x:.1f}<extra></extra>",
    ))

    fig.update_layout(
        **_LAYOUT_TEMPLATE,
        title=dict(text=title, x=0.5, font=dict(size=16)),
        xaxis=dict(
            title="综合评分",
            range=[0, 110],
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=False,
        ),
        yaxis=dict(title=""),
        height=max(300, len(df_sorted) * 50 + 100),
        showlegend=False,
    )

    return fig


def dimension_heatmap(df: pd.DataFrame, title: str = "各维度评分热力图") -> go.Figure:
    """绘制各方案各维度的评分热力图"""
    score_cols = [c for c in df.columns if any(
        dim in c for dim in ["技术可行性", "经济可行性", "实施风险与约束", "经济效益", "环境合规性", "综合评分"]
    )]
    name_col = next((c for c in df.columns if "方案" in c and "编号" not in c), df.columns[0])

    if not score_cols:
        score_cols = [c for c in df.columns if df[c].dtype in ["float64", "int64"]]

    z_data = df[score_cols].values
    x_labels = [c.replace("AI_", "").replace("人工_", "") for c in score_cols]
    y_labels = df[name_col].tolist()

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=x_labels,
        y=y_labels,
        colorscale=[
            [0, "#1a1a2e"],
            [0.3, "#0f3460"],
            [0.5, "#0096c7"],
            [0.7, "#00b4d8"],
            [0.85, "#16a34a"],
            [1, "#2d6a4f"],
        ],
        text=np.round(z_data, 1).astype(str),
        texttemplate="%{text}",
        textfont=dict(size=11, color="#1f2937"),
        hoverongaps=False,
        hovertemplate="%{y}<br>%{x}: %{z:.1f}分<extra></extra>",
        colorbar=dict(
            title=dict(text="评分", font=dict(size=12)),
            tickfont=dict(size=10),
        ),
    ))

    fig.update_layout(
        **_LAYOUT_TEMPLATE,
        title=dict(text=title, x=0.5, font=dict(size=16)),
        xaxis=dict(tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11), autorange="reversed"),
        height=max(300, len(y_labels) * 40 + 150),
    )

    return fig


def scatter_consistency(human: np.ndarray, ai: np.ndarray,
                        title: str = "人工评分 vs AI 评分") -> go.Figure:
    """绘制一致性散点图"""
    fig = go.Figure()

    # 数据点
    fig.add_trace(go.Scatter(
        x=human,
        y=ai,
        mode="markers",
        marker=dict(
            size=10,
            color="#00b4d8",
            opacity=0.7,
            line=dict(color="rgba(0,0,0,0.3)", width=1),
        ),
        hovertemplate="人工: %{x:.1f}<br>AI: %{y:.1f}<extra></extra>",
        name="评分对",
    ))

    # 理想对角线 y=x
    min_val = min(min(human), min(ai)) - 5
    max_val = max(max(human), max(ai)) + 5
    fig.add_trace(go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode="lines",
        line=dict(color="#dc2626", dash="dash", width=2),
        name="理想一致线 (y=x)",
        hoverinfo="skip",
    ))

    # 线性回归拟合
    from scipy import stats as sp_stats
    slope, intercept, r, p, se = sp_stats.linregress(human, ai)
    fit_x = np.linspace(min_val, max_val, 100)
    fit_y = slope * fit_x + intercept
    fig.add_trace(go.Scatter(
        x=fit_x,
        y=fit_y,
        mode="lines",
        line=dict(color="#16a34a", width=2),
        name=f"回归线 (R²={r**2:.3f})",
        hoverinfo="skip",
    ))

    fig.update_layout(
        **_LAYOUT_TEMPLATE,
        title=dict(text=title, x=0.5, font=dict(size=16)),
        xaxis=dict(
            title="人工专家评分",
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=False,
        ),
        yaxis=dict(
            title="AI 自动评分",
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=False,
        ),
        height=450,
    )

    return fig


def bland_altman_plot(human: np.ndarray, ai: np.ndarray,
                      title: str = "Bland-Altman 一致性分析") -> go.Figure:
    """绘制 Bland-Altman 图"""
    means = (human + ai) / 2
    diffs = ai - human
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    upper_loa = mean_diff + 1.96 * std_diff
    lower_loa = mean_diff - 1.96 * std_diff

    fig = go.Figure()

    # 散点
    fig.add_trace(go.Scatter(
        x=means,
        y=diffs,
        mode="markers",
        marker=dict(size=10, color="#00b4d8", opacity=0.7,
                    line=dict(color="rgba(0,0,0,0.3)", width=1)),
        hovertemplate="均值: %{x:.1f}<br>差值: %{y:.1f}<extra></extra>",
        name="评分差值",
    ))

    x_range = [min(means) - 5, max(means) + 5]

    # 均值线
    fig.add_hline(y=mean_diff, line=dict(color="#f59e0b", width=2),
                  annotation_text=f"Mean = {mean_diff:.2f}",
                  annotation_position="top right",
                  annotation_font=dict(color="#f59e0b", size=11))

    # 上限
    fig.add_hline(y=upper_loa, line=dict(color="#dc2626", dash="dash", width=1.5),
                  annotation_text=f"+1.96SD = {upper_loa:.2f}",
                  annotation_position="top right",
                  annotation_font=dict(color="#dc2626", size=11))

    # 下限
    fig.add_hline(y=lower_loa, line=dict(color="#dc2626", dash="dash", width=1.5),
                  annotation_text=f"-1.96SD = {lower_loa:.2f}",
                  annotation_position="bottom right",
                  annotation_font=dict(color="#dc2626", size=11))

    # 零线
    fig.add_hline(y=0, line=dict(color="rgba(0,0,0,0.2)", width=1))

    fig.update_layout(
        **_LAYOUT_TEMPLATE,
        title=dict(text=title, x=0.5, font=dict(size=16)),
        xaxis=dict(
            title="两种评分均值",
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=False,
        ),
        yaxis=dict(
            title="评分差值（AI − 人工）",
            gridcolor="rgba(0,0,0,0.05)",
            zeroline=False,
        ),
        height=450,
        showlegend=False,
    )

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
            axis=dict(range=[0, max_val], tickfont=dict(size=10, color="#6b7280"),
                      dtick=20),
            bar=dict(color=color, thickness=0.3),
            bgcolor="rgba(0,0,0,0.05)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
            steps=[
                dict(range=[0, 60], color="rgba(230, 57, 70, 0.1)"),
                dict(range=[60, 80], color="rgba(244, 140, 6, 0.1)"),
                dict(range=[80, 100], color="rgba(45, 106, 79, 0.1)"),
            ],
            threshold=dict(
                line=dict(color="#1f2937", width=2),
                thickness=0.8,
                value=score,
            ),
        ),
    ))

    fig.update_layout(
        **_LAYOUT_TEMPLATE,
        height=250,
        margin=dict(l=30, r=30, t=50, b=20),
    )

    return fig
