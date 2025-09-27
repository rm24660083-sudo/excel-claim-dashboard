import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import re

st.title("📑 วิเคราะห์เคลมแผ่น")

# -----------------------------
# Utility Functions
# -----------------------------
def map_root_cause(defect_text):
    if not defect_text or pd.isna(defect_text):
        return "อื่น ๆ/ไม่ระบุ"
    if "ยับ" in str(defect_text):
        return "Tension/Handling"
    return "อื่น ๆ/ไม่ระบุ"

def advise_for(defect):
    if "ยับ" in str(defect):
        return "ตรวจสอบการขนส่งและการจัดเก็บ"
    return "ตรวจสอบกระบวนการผลิต"

# -----------------------------
# Upload File
# -----------------------------
uploaded_file = st.file_uploader("📄 อัปโหลดไฟล์ Excel (เคลมแผ่น)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Rename columns
    rename_map_sheet = {
        "SUPPLIER": "SUP",
        "สิ่งที่ไม่เป็นไปตามข้อกำหนด": "Defect",
        "เกรดแกรม": "Grade",
        "วันที่รับของ": "Date",
        "MONTH": "Month",
        "QUARTER": "Quarter",
        "YEAR": "Year"
    }
    df = df.rename(columns={c: rename_map_sheet.get(c, c) for c in df.columns})

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
        df["MonthKey"] = df["Date"].dt.strftime("%Y-%m")
        df["Month"] = df["Date"].dt.month
        df["Quarter"] = df["Date"].dt.quarter
    elif "Month" in df.columns and "Year" in df.columns:
        df["MonthKey"] = df["Year"].astype(str) + "-" + df["Month"].astype(str).str.zfill(2)

    df["RootCause"] = df["Defect"].apply(map_root_cause)
    df["Advice"] = df["Defect"].apply(advise_for)

    # 1) สรุปภาพรวม
    st.subheader("📌 สรุปภาพรวมเคลมแผ่น")
    col1, col2, col3 = st.columns(3)
    col1.metric("จำนวนเคส", len(df))
    col2.metric("ซัพพลายเออร์", df["SUP"].nunique())
    col3.metric("ประเภทข้อบกพร่อง", df["Defect"].nunique())

    # 2) ข้อบกพร่องรายเดือน/Quarter
    st.subheader("📊 จำนวนข้อบกพร่องรายเดือน/Quarter")
    monthly_summary = df.groupby(["MonthKey", "SUP", "Defect"]).size().reset_index(name="จำนวนเคส")
    st.dataframe(monthly_summary, hide_index=True)

    # 3) เกรดแกรมแต่ละอาการ
    st.subheader("📋 เกรดแกรมของแต่ละสาเหตุ")
    defect_grade = df.groupby(["Defect", "Grade", "SUP"]).size().reset_index(name="จำนวนเคส")
    st.dataframe(defect_grade, hide_index=True)

    # 4) แนวโน้มรายเดือน
    st.subheader("📅 แนวโน้มรายเดือน (จำนวนเคส) แยกตาม SUP")

    monthly_sup = (
        df.groupby(["MonthKey", "SUP"])
          .size()
          .reset_index(name="Count")
          .sort_values("MonthKey")
    )

    fig_monthly = px.line(
        monthly_sup,
        x="MonthKey",
        y="Count",
        color="SUP",
        markers=True,
        title="จำนวนเคลมรายเดือนแยกตาม SUP"
    )

    fig_monthly.update_layout(
        xaxis_title="เดือน",
        yaxis_title="จำนวนเคส",
        legend_title="SUP",
        height=500
    )

    st.plotly_chart(fig_monthly, use_container_width=True)
