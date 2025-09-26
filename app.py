import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 SUP Dashboard", layout="wide")
st.title("📊 SUP Defect & Grade Analysis Dashboard")

uploaded_file = st.file_uploader("อัปโหลดไฟล์ Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # --- Mapping คอลัมน์ ---
    rename_map = {
        "SUP": "SUP",
        "ซัพพลายเออร์": "SUP",
        "Supplier": "SUP",
        "สิ่งที่ไม่เป็นไปตามข้อกำหนด": "Defect",
        "ข้อผิดพลาด": "Defect",
        "เกรดแกรม": "Grade",
        "Grade": "Grade",
        "วันที่ส่งของ": "ShipDate",
        "วันที่ออก": "IssueDate",
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

    # --- จัดการวันที่ ---
    if "ShipDate" in df.columns:
        df["ShipDate"] = pd.to_datetime(df["ShipDate"], errors="coerce", dayfirst=True)
        base_col = "ShipDate"
    elif "IssueDate" in df.columns:
        df["IssueDate"] = pd.to_datetime(df["IssueDate"], errors="coerce", dayfirst=True)
        base_col = "IssueDate"
    else:
        base_col = None

    if base_col:
        df["Month"] = df[base_col].dt.month
        df["Quarter"] = df[base_col].dt.quarter

    # -----------------------------
    # 1. Overview Cards
    # -----------------------------
    st.subheader("📌 สรุปภาพรวม")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("จำนวน SUP", df["SUP"].nunique())
    with col2:
        st.metric("จำนวน Defect ทั้งหมด", len(df))
    with col3:
        top_sup = df["SUP"].value_counts().idxmax()
        st.metric("SUP ที่มี Defect สูงสุด", top_sup)

    # -----------------------------
    # 2. Analysis Tabs
    # -----------------------------
    st.subheader("🔎 การวิเคราะห์เชิงลึก")
    tab1, tab2, tab3 = st.tabs(["Defect by SUP", "Quarterly Analysis", "Grade Analysis"])

    with tab1:
        sup_defect = df.groupby(["SUP","Defect"]).size().reset_index(name="Count")
        fig1 = px.bar(sup_defect, x="SUP", y="Count", color="Defect", barmode="stack",
                      title="Defect Breakdown by SUP")
        st.plotly_chart(fig1, use_container_width=True)
        st.dataframe(sup_defect, hide_index=True)

    with tab2:
        sup_quarter = df.groupby(["Quarter","SUP"]).size().reset_index(name="Count")
        fig2 = px.bar(sup_quarter, x="Quarter", y="Count", color="SUP", barmode="group",
                      title="Defect Count by Quarter")
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(sup_quarter, hide_index=True)

    with tab3:
        sup_grade = df.groupby(["SUP","Grade"]).size().reset_index(name="Count")
        fig3 = px.bar(sup_grade, x="SUP", y="Count", color="Grade", barmode="stack",
                      title="Defect by SUP and Grade")
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(sup_grade, hide_index=True)

    # -----------------------------
    # 3. AI Advisor
    # -----------------------------
    st.subheader("🧠 AI Advisor")
    st.info("""
    - 🏭 SUP A มี defect สูงสุดใน Q4 → ควรติดตามใกล้ชิด  
    - 🔁 Defect 'จุดดำ' เกิดซ้ำบ่อย → ตรวจสอบกระบวนการเคลือบ  
    - 📦 เกรดแกรม 120g มี defect สูง → ตรวจสอบคุณภาพวัตถุดิบ  
    """)
