"""
页面1：数据管理
"""
import streamlit as st
import pandas as pd
import os, sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import APP_TITLE
from components.sidebar import render_sidebar
from components.metrics import render_metric_card
from utils.data_handler import load_csv, load_demo_data, get_data_summary, validate_evaluation_data

st.set_page_config(page_title=f"数据管理 | {APP_TITLE}", page_icon="📊", layout="wide")

css_path = os.path.join(ROOT_DIR, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "uploaded_data" not in st.session_state:
    st.session_state["uploaded_data"] = None
if "evaluation_results" not in st.session_state:
    st.session_state["evaluation_results"] = []

render_sidebar()

st.markdown(
    '<div class="main-title"><h1>多源数据提取与预处理</h1>'
    '<p>加载与管理多源决策数据集（原型验证版）</p></div>',
    unsafe_allow_html=True,
)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["上传数据", "示例数据"])

with tab1:
    uploaded_file = st.file_uploader(
        "选择 CSV 文件（支持 UTF-8 / GBK 编码）",
        type=["csv"],
    )
    if uploaded_file is not None:
        df = load_csv(uploaded_file)
        if df is not None:
            st.session_state["uploaded_data"] = df
            st.success(f"成功加载 {len(df)} 条数据，{len(df.columns)} 个字段")

with tab2:
    st.markdown("内置 5 种典型煤矸石资源化利用方案，可直接体验系统全流程。")
    if st.button("加载示例数据", type="primary"):
        st.session_state["uploaded_data"] = load_demo_data()
        st.success("已加载 5 条示例方案数据")
        st.rerun()

st.markdown('<hr class="divider">', unsafe_allow_html=True)

df = st.session_state.get("uploaded_data")

if df is not None and not df.empty:
    # 统计概览
    st.markdown("#### 数据概览")
    summary = get_data_summary(df)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card(str(summary["total_rows"]), "方案总数")
    with m2:
        render_metric_card(str(summary["total_columns"]), "字段数量")
    with m3:
        null_count = sum(summary["null_counts"].values())
        render_metric_card(str(null_count), "缺失值",
                           "#34a853" if null_count == 0 else "#ea4335")
    with m4:
        numeric_count = len([c for c in df.columns if df[c].dtype in ["float64", "int64"]])
        render_metric_card(str(numeric_count), "数值字段")

    validation = validate_evaluation_data(df)
    for w in validation.get("warnings", []):
        st.warning(w)

    st.markdown("")

    # 数据预览
    st.markdown("#### 数据预览")
    col_search, col_rows = st.columns([3, 1])
    with col_search:
        search = st.text_input("搜索", placeholder="输入关键词...", label_visibility="collapsed")
    with col_rows:
        show_rows = st.selectbox("行数", [10, 25, 50, 100], index=0, label_visibility="collapsed")

    display_df = df.copy()
    if search:
        mask = display_df.astype(str).apply(
            lambda row: row.str.contains(search, case=False, na=False).any(), axis=1
        )
        display_df = display_df[mask]
        st.caption(f"找到 {len(display_df)} 条匹配结果")

    st.dataframe(display_df.head(show_rows), use_container_width=True)

    with st.expander("字段详情"):
        field_info = pd.DataFrame({
            "字段名": df.columns,
            "数据类型": df.dtypes.astype(str).values,
            "非空数量": df.notna().sum().values,
            "缺失率": (df.isnull().sum() / len(df) * 100).round(1).astype(str).values + "%",
            "示例值": [str(df[col].iloc[0]) if len(df) > 0 else "" for col in df.columns],
        })
        st.dataframe(field_info, use_container_width=True, hide_index=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # 选择方案
    st.markdown("#### 选择待评估方案")

    col_all, col_clear, _ = st.columns([1, 1, 4])
    with col_all:
        if st.button("全选"):
            st.session_state["selected_indices"] = list(range(len(df)))
    with col_clear:
        if st.button("清空"):
            st.session_state["selected_indices"] = []

    if "selected_indices" not in st.session_state:
        st.session_state["selected_indices"] = []

    selected = st.multiselect(
        "选择方案", options=list(range(len(df))),
        default=st.session_state["selected_indices"],
        format_func=lambda i: f"{df.iloc[i].iloc[0]} - {df.iloc[i].iloc[1]}" if len(df.columns) > 1 else f"方案 {i+1}",
        label_visibility="collapsed",
    )
    st.session_state["selected_indices"] = selected

    if selected:
        st.info(f"已选择 {len(selected)} 个方案，前往「智能评估」页面启动评估。")
else:
    st.markdown(
        '<div class="card" style="text-align:center; padding:2rem; color:#6b7280;">'
        "暂无数据，请上传 CSV 文件或加载示例数据。"
        "</div>",
        unsafe_allow_html=True,
    )
