import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 SUP Defect & Grade Analysis + AI Advisor", layout="wide")
st.title("📊 SUP Defect & Grade Analysis + AI Advisor")

# -----------------------------
# ฟังก์ชัน AI Advisor (Advance)
# -----------------------------
def advanced_ai_advisor(df):
    tips = []
    if df.empty:
        return ["⚠️ ไม่พบข้อมูลสำหรับการวิเคราะห์"]

    latest_q = df["Quarter"].max()
    q_data = df[df["Quarter"] == latest_q]

    if "SUP" in q_data.columns:
        sup_counts = q_data["SUP"].value_counts()
        if not sup_counts.empty:
            top_sup = sup_counts.index[0]
            top_count = sup_counts.iloc[0]
            tips.append(f"🏭 SUP {top_sup} มี defect {top_count} ครั้งใน Q{latest_q}")

    if "Defect" in q_data.columns:
        defect_counts = q_data["Defect"].value_counts()
        if not defect_counts.empty:
            top_defect = defect_counts.index[0]
            tips.append(f"🔁 Defect '{top_defect}' เกิดซ้ำบ่อยที่สุดใน Q{latest_q}")

    if {"Grade","Defect"}.issubset(q_data.columns):
        grade_defect = q_data.groupby("Grade")["Defect"].count().sort_values(ascending=False)
        if not grade_defect.empty:
            top_grade = grade_defect.index[0]
            tips.append(f"📦 เกรดแกรม {top_grade} มี defect สูงสุดใน Q{latest_q}")

    return tips


# -----------------------------
# อัปโหลดไฟล์
# -----------------------------
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
    # 1. ข้อผิดพลาดของแต่ละ SUP
    # -----------------------------
    st.subheader("🔍 ข้อผิดพลาดของแต่ละ SUP")
    if {"SUP","Defect"}.issubset(df.columns):
        for sup in df["SUP"].unique():
            st.markdown(f"### SUP: {sup}")
            sup_df = df[df["SUP"] == sup]
            defect_table = sup_df["Defect"].value_counts().reset_index()
            defect_table.columns = ["Defect", "Count"]
            st.dataframe(defect_table)
            st.plotly_chart(px.bar(defect_table, x="Defect", y="Count",
                                   title=f"Defect Breakdown - {sup}"), use_container_width=True)

    # -----------------------------
    # 2. ข้อผิดพลาดรายไตรมาส
    # -----------------------------
    st.subheader("📅 ข้อผิดพลาดรายไตรมาส")
    if {"SUP","Quarter"}.issubset(df.columns):
        for sup in df["SUP"].unique():
            st.markdown(f"### SUP: {sup}")
            sup_df = df[df["SUP"] == sup]
            quarter_table = sup_df["Quarter"].value_counts().reset_index()
            quarter_table.columns = ["Quarter", "Count"]
            st.dataframe(quarter_table)
            st.plotly_chart(px.bar(quarter_table, x="Quarter", y="Count",
                                   title=f"Quarter Breakdown - {sup}"), use_container_width=True)

    # -----------------------------
    # 3. เกรดแกรมที่มีปัญหาในแต่ละ SUP
    # -----------------------------
    st.subheader("📦 เกรดแกรมที่มีปัญหาในแต่ละ SUP")
    if {"SUP","Grade"}.issubset(df.columns):
        for sup in df["SUP"].unique():
            st.markdown(f"### SUP: {sup}")
            sup_df = df[df["SUP"] == sup]
            grade_table = sup_df["Grade"].value_counts().reset_index()
            grade_table.columns = ["Grade", "Count"]
            st.dataframe(grade_table)
            st.plotly_chart(px.bar(grade_table, x="Grade", y="Count",
                                   title=f"Grade Breakdown - {sup}"), use_container_width=True)

    # -----------------------------
    # AI Advisor
    # -----------------------------
    st.subheader("🧠 AI Advisor (Advance)")
    if "Quarter" in df.columns:
        tips = advanced_ai_advisor(df)
        for t in tips:
            st.write("- " + t)
