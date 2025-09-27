import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import re

st.title("📑 วิเคราะห์เคลมม้วน")

# -----------------------------
# Utility Functions
# -----------------------------
root_cause_rules = [
    (r"carl?ender|คาเลนเดอร์|คาร์เลนเดอร์|จุดดำ", "รอยลูกรีด/ผิวหน้า"),
    (r"ยับ|รอยยับ|ม้วนหย่อน", "Tension/การกรอ-ขนส่ง"),
    (r"รอยเส้น|สันนูน", "การรีด/การกรอ/ตั้งค่าลูกกลิ้ง"),
]

def map_root_cause(defect_text):
    if not defect_text or pd.isna(defect_text):
        return "อื่น ๆ/ไม่ระบุ"
    for pattern, cause in root_cause_rules:
        if re.search(pattern, str(defect_text), flags=re.IGNORECASE):
            return cause
    return "อื่น ๆ/ไม่ระบุ"

def advise_for(defect):
    t = str(defect)
    if re.search(r"สันนูน|รอยเส้น", t, re.I):
        return "ตรวจสอบ slitting/ใบมีด และ tension"
    return "ตรวจสอบกระบวนการผลิต"

# -----------------------------
# Upload File
# -----------------------------
uploaded_file = st.file_uploader("📄 อัปโหลดไฟล์ Excel (เคลมม้วน)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Rename columns
    rename_map = {
        "SUP": "SUP", "Supplier": "SUP",
        "สิ่งที่ไม่เป็นไปตามข้อกำหนด": "Defect", "ข้อบกพร่อง": "Defect",
        "เกรดแกรม": "Grade", "Grade": "Grade",
        "วันที่ออก": "Date", "Date": "Date"
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
        df["MonthKey"] = df["Date"].dt.strftime("%Y-%m")
        df["Month"] = df["Date"].dt.month
        df["Quarter"] = df["Date"].dt.quarter

    df["RootCause"] = df["Defect"].apply(map_root_cause)
    df["Advice"] = df["Defect"].apply(advise_for)

    # KPI
    st.subheader("📌 สรุปภาพรวม")
    col1, col2, col3 = st.columns(3)
    col1.metric("จำนวนรายการข้อบกพร่อง", len(df))
    col2.metric("ซัพพลายเออร์", df["SUP"].nunique())
    col3.metric("ประเภทข้อบกพร่อง", df["Defect"].nunique())

    # กราฟ SUP
    st.subheader("🏭 อันดับ SUP (Top 12)")
    sup_count = df.groupby("SUP").size().reset_index(name="Count").sort_values("Count", ascending=False).head(12)
    fig1 = px.bar(sup_count, x="SUP", y="Count", text="Count")
    st.plotly_chart(fig1, use_container_width=True)

    # กราฟ Defect
    st.subheader("🧩 สัดส่วนประเภทข้อบกพร่อง (Top 12)")
    defect_count = df.groupby("Defect").size().reset_index(name="Count").sort_values("Count", ascending=False).head(12)
    fig2 = px.pie(defect_count, names="Defect", values="Count")
    st.plotly_chart(fig2, use_container_width=True)

    # แนวโน้มรายเดือน
    st.subheader("📅 แนวโน้มรายเดือน (จำนวนเคส) แยกตาม SUP")
    monthly_sup = df.groupby(["MonthKey", "SUP"]).size().reset_index(name="Count")
    fig3 = px.line(monthly_sup, x="MonthKey", y="Count", color="SUP", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

    # ตารางคำแนะนำ
    st.subheader("💡 คำแนะนำอัตโนมัติ")
    advisor_unique = df[["SUP", "Defect", "Advice"]].drop_duplicates()
    st.dataframe(advisor_unique, hide_index=True)
