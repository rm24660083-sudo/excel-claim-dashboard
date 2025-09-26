import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 SUP Dashboard", layout="wide")
st.title("📊 SUP Defect & Grade Analysis Dashboard")

# -----------------------------
# ฟังก์ชัน AI Advisor
# -----------------------------
def ai_advisor(df):
    tips = []
    if df.empty:
        return ["⚠️ ไม่มีข้อมูลสำหรับวิเคราะห์"]

    latest_q = df["Quarter"].max()
    q_data = df[df["Quarter"] == latest_q]

    # SUP ที่ defect สูงสุด
    if "SUP" in q_data.columns:
        sup_counts = q_data["SUP"].value_counts()
        if not sup_counts.empty:
            sup = sup_counts.index[0]
            count = sup_counts.iloc[0]
            tips.append(f"🏭 SUP {sup} มี defect {count} ครั้งใน Q{latest_q}")

    # Defect ที่ recurring
    if "Defect" in q_data.columns:
        defect_counts = q_data["Defect"].value_counts()
        if not defect_counts.empty:
            defect = defect_counts.index[0]
            tips.append(f"🔁 Defect '{defect}' เกิดซ้ำบ่อยที่สุดใน Q{latest_q}")

    # Grade ที่เกี่ยวข้อง
    if {"Grade","Defect"}.issubset(q_data.columns):
        grade_counts = q_data["Grade"].value_counts()
        if not grade_counts.empty:
            grade = grade_counts.index[0]
            tips.append(f"📦 เกรดแกรม {grade} มี defect สูงสุดใน Q{latest_q}")

    tips.append("✅ ทำ CAPA (Corrective Action) ร่วมกับ SUP ที่ defect สูงสุด")
    tips.append("🧪 ตรวจสอบคุณภาพเกรดแกรมที่ defect สูงก่อนผลิตล็อตใหม่")

    return tips


# -----------------------------
# อัปโหลดไฟล์
# -----------------------------
uploaded_file = st.file_uploader("อัปโหลดไฟล์ Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Mapping คอลัมน์
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
    # Overview
    # -----------------------------
    st.subheader("📌 สรุปภาพรวม")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("จำนวน SUP", df["SUP"].nunique())
    with col2:
        st.metric("จำนวน Defect ทั้งหมด", len(df))
    with col3:
        top_sup = df["SUP"].value_counts().idxmax()
        st.metric("SUP ที่ defect สูงสุด", top_sup)

    # -----------------------------
    # Tabs
    # -----------------------------
    tab1, tab2, tab3 = st.tabs(["Defect by SUP", "Grade by SUP", "AI Advisor"])

    # Tab 1: Defect by SUP (รายเดือน/Quarter)
    with tab1:
        st.markdown("### 🔍 Defect by SUP (รายเดือน/Quarter)")
        if {"SUP","Defect","Quarter"}.issubset(df.columns):
            sup_defect = df.groupby(["Quarter","SUP","Defect"]).size().reset_index(name="Count")
            fig1 = px.bar(sup_defect, x="SUP", y="Count", color="Defect",
                          facet_col="Quarter", barmode="stack",
                          title="Defect Breakdown by SUP (Quarterly)")
            st.plotly_chart(fig1, use_container_width=True)
            st.dataframe(sup_defect, hide_index=True)

    # Tab 2: Grade by SUP
    with tab2:
        st.markdown("### 📦 Grade by SUP (Defect Breakdown)")
        if {"SUP","Grade","Defect"}.issubset(df.columns):
            sup_grade = df.groupby(["SUP","Grade","Defect"]).size().reset_index(name="Count")
            fig2 = px.bar(sup_grade, x="SUP", y="Count", color="Defect",
                          facet_col="Grade", barmode="stack",
                          title="Defect by SUP and Grade")
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(sup_grade, hide_index=True)

    # Tab 3: AI Advisor
    with tab3:
        st.markdown("### 🧠 ข้อควรระวังและคำแนะนำ")
        tips = ai_advisor(df)
        for t in tips:
            st.write("- " + t)
