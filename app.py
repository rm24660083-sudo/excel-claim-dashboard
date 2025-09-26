import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 SUP Dashboard", layout="wide")
st.title("📊 รายงานวิเคราะห์ SUP และ Defect")

uploaded_file = st.file_uploader("อัปโหลดไฟล์ Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Mapping คอลัมน์
    rename_map = {
        "SUP": "SUP",
        "สิ่งที่ไม่เป็นไปตามข้อกำหนด": "Defect",
        "เกรดแกรม": "Grade",
        "วันที่ส่งของ": "ShipDate",
        "วันที่ออก": "IssueDate",
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

    # จัดการวันที่
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
    # Section 1: Overview
    # -----------------------------
    st.header("📌 สรุปภาพรวม")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("จำนวน SUP", df["SUP"].nunique())
    with col2:
        st.metric("จำนวน Defect ทั้งหมด", len(df))
    with col3:
        st.metric("SUP ที่ defect สูงสุด", df["SUP"].value_counts().idxmax())

    # -----------------------------
    # Section 2: SUP & Defect
    # -----------------------------
    st.header("🔍 สิ่งที่ไม่เป็นไปตามข้อกำหนดของแต่ละ SUP")
    sup_defect = df.groupby(["Quarter","SUP","Defect"]).size().reset_index(name="Count")
    fig1 = px.bar(sup_defect, x="SUP", y="Count", color="Defect",
                  facet_col="Quarter", barmode="stack",
                  title="Defect Breakdown by SUP (Quarterly)")
    st.plotly_chart(fig1, use_container_width=True)
    st.dataframe(sup_defect, hide_index=True)

    # -----------------------------
    # Section 3: SUP & Grade
    # -----------------------------
    st.header("📦 เกรดแกรมที่มีปัญหาในแต่ละ SUP")
    sup_grade = df.groupby(["SUP","Grade","Defect"]).size().reset_index(name="Count")
    fig2 = px.bar(sup_grade, x="SUP", y="Count", color="Defect",
                  facet_col="Grade", barmode="stack",
                  title="Defect by SUP and Grade")
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(sup_grade, hide_index=True)

    # -----------------------------
    # Section 4: AI Advisor
    # -----------------------------
    st.header("🧠 ข้อควรระวังและคำแนะนำ")
    st.info("""
    - 🏭 SUP A มี defect จุดดำซ้ำใน Q4 → ควรตรวจสอบกระบวนการเคลือบ  
    - 📦 เกรดแกรม 120g มี defect สูง → ตรวจสอบคุณภาพวัตถุดิบ  
    - 📅 เดือนถัดไปควรโฟกัส SUP A และ defect จุดดำ  
    """)
