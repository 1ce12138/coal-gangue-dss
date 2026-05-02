"""
数据处理工具 — 负责 CSV 读取、验证与预处理
"""

import pandas as pd
import streamlit as st
import io
from typing import Optional


def load_csv(uploaded_file) -> Optional[pd.DataFrame]:
    """从上传的文件对象中读取 CSV 数据"""
    try:
        # 尝试多种编码
        for encoding in ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1"]:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding=encoding)
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue
        st.error("❌ 无法识别文件编码，请确保文件为 UTF-8 或 GBK 编码的 CSV。")
        return None
    except Exception as e:
        st.error(f"❌ 读取文件失败: {str(e)}")
        return None


def load_demo_data() -> pd.DataFrame:
    """加载内置的示例数据"""
    from config import DEMO_SCHEMES
    return pd.DataFrame(DEMO_SCHEMES)


def get_data_summary(df: pd.DataFrame) -> dict:
    """生成数据集的统计概览"""
    summary = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "null_percentage": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
    }

    # 数值列统计
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols:
        summary["numeric_stats"] = df[numeric_cols].describe().to_dict()

    return summary


def validate_evaluation_data(df: pd.DataFrame) -> dict:
    """验证数据是否适合送入评估系统"""
    issues = []
    warnings = []

    if len(df) == 0:
        issues.append("数据集为空")
    if df.isnull().any().any():
        null_cols = df.columns[df.isnull().any()].tolist()
        warnings.append(f"以下列存在缺失值: {', '.join(null_cols)}")

    # 检查是否有方案描述列
    desc_candidates = ["方案描述", "描述", "方案说明", "description", "scheme_desc"]
    has_desc = any(col in df.columns for col in desc_candidates)
    if not has_desc:
        warnings.append('未检测到方案描述列（建议包含方案描述列以获得更准确的评估）')

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
    }


def prepare_evaluation_input(row: pd.Series) -> str:
    """将一行数据组装为送入 LLM 评估的文本"""
    parts = []
    for col, val in row.items():
        if pd.notna(val) and str(val).strip():
            parts.append(f"**{col}**：{val}")
    return "\n".join(parts)


def export_results(df: pd.DataFrame, format: str = "csv") -> bytes:
    """将评估结果导出为指定格式"""
    if format == "csv":
        return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    elif format == "xlsx":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="评估结果")
        return buffer.getvalue()
    else:
        raise ValueError(f"不支持的导出格式: {format}")
