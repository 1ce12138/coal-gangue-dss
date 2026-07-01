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
if "selected_indices" not in st.session_state:
    st.session_state["selected_indices"] = []

render_sidebar()

st.markdown(
    '<div class="main-title"><h1>技术经济方案数据管理</h1>'
    '<p>上传、加载或手动录入煤矸石资源化利用方案</p></div>',
    unsafe_allow_html=True,
)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["上传数据", "手动录入", "示例数据"])

with tab1:
    uploaded_file = st.file_uploader("选择 CSV 文件（支持 UTF-8 / GBK 编码）", type=["csv"])
    if uploaded_file is not None:
        df = load_csv(uploaded_file)
        if df is not None:
            st.session_state["uploaded_data"] = df
            st.success(f"成功加载 {len(df)} 条数据，{len(df.columns)} 个字段")

with tab2:
    st.markdown("输入单个技术方案文本，系统会将其转换为可评估的决策对象。")
    with st.form("manual_scheme_form", clear_on_submit=False):
        scheme_name = st.text_input("方案名称", placeholder="例如：煤矸石制备轻质陶粒")
        scheme_desc = st.text_area("方案描述", placeholder="说明原料来源、处理路径、产品形态、建设条件、预期目标等。", height=150)
        c1, c2 = st.columns(2)
        with c1:
            tech_route = st.text_input("技术路线", placeholder="破碎→配料→造粒→焙烧→筛分")
            scale = st.text_input("处理规模", placeholder="例如：年处理煤矸石20万吨")
            maturity = st.selectbox("技术成熟度", ["已有工业化案例", "中试验证阶段", "实验室阶段", "尚待论证"])
        with c2:
            investment = st.text_input("投资估算", placeholder="例如：5000万元")
            operating_cost = st.text_input("年运营成本", placeholder="例如：1200万元/年")
            expected_return = st.text_input("预期收益/产品去向", placeholder="例如：陶粒骨料销售、建材企业消纳")
        risk_note = st.text_area("主要约束与风险", placeholder="可填写市场需求、环保约束、政策要求、二次污染、资金压力等。", height=90)
        submitted = st.form_submit_button("加入待评估方案", type="primary", use_container_width=True)

    if submitted:
        if not scheme_desc.strip() and not scheme_name.strip():
            st.warning("请至少填写方案名称或方案描述。")
        else:
            current_df = st.session_state.get("uploaded_data")
            next_no = 1 if current_df is None or current_df.empty else len(current_df) + 1
            new_row = pd.DataFrame([{
                "方案编号": f"MANUAL-{next_no:03d}",
                "方案名称": scheme_name.strip() or f"手动录入方案{next_no}",
                "方案描述": scheme_desc.strip(),
                "技术路线": tech_route.strip(),
                "处理规模": scale.strip(),
                "投资估算": investment.strip(),
                "年运营成本": operating_cost.strip(),
                "预期收益/产品去向": expected_return.strip(),
                "技术成熟度": maturity,
                "主要约束与风险": risk_note.strip(),
                "数据来源": "用户手动录入",
            }])
            updated_df = new_row if current_df is None or current_df.empty else pd.concat([current_df, new_row], ignore_index=True, sort=False)
            st.session_state["uploaded_data"] = updated_df
            st.session_state["selected_indices"] = [len(updated_df) - 1]
            st.success("已加入待评估方案，并自动选中该方案。")
            st.rerun()

with tab3:
    st.markdown("内置 5 种典型煤矸石资源化利用方案，可直接体验系统全流程。")
    if st.button("加载示例数据", type="primary"):
        st.session_state["uploaded_data"] = load_demo_data()
        st.success("已加载 5 条示例方案数据")
        st.rerun()

st.markdown('<hr class="divider">', unsafe_allow_html=True)

df = st.session_state.get("uploaded_data")

if df is not None and not df.empty:
    st.markdown("#### 数据概览")
    summary = get_data_summary(df)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card(str(summary["total_rows"]), "方案总数")
    with m2:
        render_metric_card(str(summary["total_columns"]), "字段数量")
    with m3:
        null_count = sum(summary["null_counts"].values())
        render_metric_card(str(null_count), "缺失值", "#34a853" if null_count == 0 else "#ea4335")
    with m4:
        numeric_count = len([c for c in df.columns if df[c].dtype in ["float64", "int64"]])
        render_metric_card(str(numeric_count), "数值字段")

    validation = validate_evaluation_data(df)
    for w in validation.get("warnings", []):
        st.warning(w)

    st.markdown("#### 数据预览")
    st.dataframe(df.head(25), use_container_width=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("#### 选择待评估方案")

    col_all, col_clear, _ = st.columns([1, 1, 4])
    with col_all:
        if st.button("全选"):
            st.session_state["selected_indices"] = list(range(len(df)))
    with col_clear:
        if st.button("清空"):
            st.session_state["selected_indices"] = []

    selected = st.multiselect(
        "选择方案",
        options=list(range(len(df))),
        default=st.session_state["selected_indices"],
        format_func=lambda i: f"{df.iloc[i].iloc[0]} - {df.iloc[i].iloc[1]}" if len(df.columns) > 1 else f"方案 {i+1}",
        label_visibility="collapsed",
    )
    st.session_state["selected_indices"] = selected

    if selected:
        st.info(f"已选择 {len(selected)} 个方案，前往「智能评估」页面启动评估。")
else:
    st.markdown(
        '<div class="card" style="text-align:center; padding:2rem; color:#6b7280;">暂无数据，请上传 CSV 文件、手动录入或加载示例数据。</div>',
        unsafe_allow_html=True,
    )
