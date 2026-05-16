"""
评估逻辑工具 — 指标计算、一致性检验等
"""

import warnings
import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional


def calculate_weighted_score(scores: dict, weights: Optional[dict] = None) -> float:
    """计算加权综合评分"""
    if weights is None:
        weights = {"技术可行性": 0.45, "经济可行性": 0.45, "实施风险与约束": 0.10}

    total = sum(scores.get(dim, 0) * w for dim, w in weights.items())
    return round(total, 2)


def get_score_level(score: float) -> dict:
    """根据分数判定等级"""
    if score >= 90:
        return {"level": "优秀", "color": "#2d6a4f", "badge": "badge-success"}
    elif score >= 80:
        return {"level": "良好", "color": "#40916c", "badge": "badge-success"}
    elif score >= 70:
        return {"level": "中等", "color": "#f48c06", "badge": "badge-warning"}
    elif score >= 60:
        return {"level": "及格", "color": "#e76f51", "badge": "badge-warning"}
    else:
        return {"level": "不及格", "color": "#e63946", "badge": "badge-warning"}


def calculate_consistency(human_scores: np.ndarray, ai_scores: np.ndarray) -> dict:
    """
    计算人机一致性指标。
    Returns:
        dict: 包含多种一致性指标
    """
    human_scores, ai_scores = _prepare_score_arrays(human_scores, ai_scores)
    results = {}
    n = len(human_scores)

    if n == 0:
        return {
            "n": 0,
            "rmse": np.nan,
            "mae": np.nan,
            "bland_altman": {
                "mean_diff": np.nan,
                "std_diff": np.nan,
                "upper_loa": np.nan,
                "lower_loa": np.nan,
                "means": [],
                "diffs": [],
            },
        }

    results["n"] = n

    # 1. Pearson 相关系数
    if n >= 3:
        r, p = _safe_corr(stats.pearsonr, human_scores, ai_scores)
        results["pearson"] = {"r": round(r, 4), "p_value": round(p, 6),
                              "interpretation": _interpret_correlation(r)}

    # 2. Spearman 秩相关系数
    if n >= 3:
        rho, p = _safe_corr(stats.spearmanr, human_scores, ai_scores)
        results["spearman"] = {"rho": round(rho, 4), "p_value": round(p, 6),
                               "interpretation": _interpret_correlation(rho)}

    # 3. Kendall τ 相关系数
    if n >= 3:
        tau, p = _safe_corr(stats.kendalltau, human_scores, ai_scores)
        results["kendall"] = {"tau": round(tau, 4), "p_value": round(p, 6),
                              "interpretation": _interpret_correlation(tau)}

    # 4. 均方根误差 (RMSE)
    rmse = np.sqrt(np.mean((human_scores - ai_scores) ** 2))
    results["rmse"] = round(rmse, 4)

    # 5. 平均绝对误差 (MAE)
    mae = np.mean(np.abs(human_scores - ai_scores))
    results["mae"] = round(mae, 4)

    # 6. 组内相关系数 (ICC) — 简化版本
    if n >= 3:
        grand_mean = np.mean(np.concatenate([human_scores, ai_scores]))
        row_means = (human_scores + ai_scores) / 2
        ms_between = 2 * np.sum((row_means - grand_mean) ** 2) / (n - 1)
        residuals = np.concatenate([
            human_scores - row_means,
            ai_scores - row_means
        ])
        ms_within = np.sum(residuals ** 2) / n
        if (ms_between + ms_within) > 0:
            icc = (ms_between - ms_within) / (ms_between + ms_within)
            results["icc"] = round(max(0, icc), 4)

    # 7. Bland-Altman 分析数据
    diff = ai_scores - human_scores
    mean_scores = (human_scores + ai_scores) / 2
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1) if n >= 2 else 0.0

    results["bland_altman"] = {
        "mean_diff": round(mean_diff, 4),
        "std_diff": round(std_diff, 4),
        "upper_loa": round(mean_diff + 1.96 * std_diff, 4),
        "lower_loa": round(mean_diff - 1.96 * std_diff, 4),
        "means": mean_scores.tolist(),
        "diffs": diff.tolist(),
    }

    return results


def _prepare_score_arrays(human_scores: np.ndarray, ai_scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """转换并成对保留有效数值，避免两列分别 dropna 后错位。"""
    paired = pd.DataFrame({
        "human": pd.to_numeric(pd.Series(human_scores), errors="coerce"),
        "ai": pd.to_numeric(pd.Series(ai_scores), errors="coerce"),
    }).replace([np.inf, -np.inf], np.nan).dropna()
    return paired["human"].to_numpy(dtype=float), paired["ai"].to_numpy(dtype=float)


def _safe_corr(func, human_scores: np.ndarray, ai_scores: np.ndarray) -> tuple[float, float]:
    """相关系数容错：常数列或异常输入返回 0 与非显著 p 值。"""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=stats.ConstantInputWarning)
            value, p_value = func(human_scores, ai_scores)
        if not np.isfinite(value):
            value = 0.0
        if not np.isfinite(p_value):
            p_value = 1.0
        return float(value), float(p_value)
    except Exception:
        return 0.0, 1.0


def _interpret_correlation(r: float) -> str:
    """解释相关系数强度"""
    abs_r = abs(r)
    if abs_r >= 0.9:
        return "极强相关"
    elif abs_r >= 0.7:
        return "强相关"
    elif abs_r >= 0.5:
        return "中等相关"
    elif abs_r >= 0.3:
        return "弱相关"
    else:
        return "极弱/无相关"


def generate_demo_consistency_data(n: int = 30) -> pd.DataFrame:
    """生成用于一致性检验的模拟数据"""
    np.random.seed(42)

    schemes = [f"CG-{i+1:03d}" for i in range(n)]

    # 人工专家评分（基准）
    human_tech = np.random.normal(75, 10, n).clip(40, 100)
    human_econ = np.random.normal(72, 12, n).clip(40, 100)
    human_env = np.random.normal(78, 9, n).clip(40, 100)
    human_overall = human_tech * 0.35 + human_econ * 0.35 + human_env * 0.30

    # AI 评分（加入一定噪声，但保持高相关性）
    noise_factor = 0.15
    ai_tech = (human_tech + np.random.normal(2, 5, n) * noise_factor + np.random.normal(0, 3, n)).clip(40, 100)
    ai_econ = (human_econ + np.random.normal(1, 6, n) * noise_factor + np.random.normal(0, 4, n)).clip(40, 100)
    ai_env = (human_env + np.random.normal(-1, 4, n) * noise_factor + np.random.normal(0, 3, n)).clip(40, 100)
    ai_overall = ai_tech * 0.35 + ai_econ * 0.35 + ai_env * 0.30

    df = pd.DataFrame({
        "方案编号": schemes,
        "人工_技术可行性": np.round(human_tech, 1),
        "人工_经济效益": np.round(human_econ, 1),
        "人工_环境合规性": np.round(human_env, 1),
        "人工_综合评分": np.round(human_overall, 1),
        "AI_技术可行性": np.round(ai_tech, 1),
        "AI_经济效益": np.round(ai_econ, 1),
        "AI_环境合规性": np.round(ai_env, 1),
        "AI_综合评分": np.round(ai_overall, 1),
    })

    return df
