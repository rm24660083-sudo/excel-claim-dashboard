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
            tips.append(f"🏭 SUP {top_sup} มี defect {top_count} ครั้งใน Q{latest_q} — ควรติดตามใกล้ชิด")

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

    if "Month" in df.columns:
        next_month = df["Month"].max() + 1
        tips.append(f"📅 เดือนถัดไป (เดือน {next_month}) ควรโฟกัส SUP และ defect ที่ recurring")

    tips.append("✅ ทำ CAPA (Corrective Action) ร่วมกับ SUP ที่ defect สูงสุด")
    tips.append("🧪 สุ่มตรวจคุณภาพเกรดแกรมที่ defect สูงก่อนผลิตล็อตใหม่")

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
    # วิเคราะห์ SUP ทีละราย (Expander)
    # -----------------------------
    st.subheader("🔍 วิเคราะห์ SUP ทีละราย")

    if "SUP" in df.columns:
        for sup in df["SUP"].unique():
            with st.expander(f"SUP: {sup}", expanded=False):
                sup_df = df[df["SUP"] == sup]

                # Defect breakdown
                if "Defect" in sup_df.columns:
                    defect_table = sup_df["Defect"].value_counts().reset_index()
                    defect_table.columns = ["Defect", "Count"]
                    st.markdown("**รายละเอียดข้อผิดพลาด (Defect Breakdown)**")
                    st.dataframe(defect_table)
                    st.plotly_chart(px.bar(defect_table, x="Defect", y="Count",
                                           title=f"Defect Breakdown - {sup}"), use_container_width=True)

                # Quarter breakdown
                if "Quarter" in sup_df.columns:
                    quarter_table = sup_df["Quarter"].value_counts().reset_index()
                    quarter_table.columns = ["Quarter", "Count"]
                    st.markdown("**ข้อผิดพลาดรายไตรมาส (Quarter Breakdown)**")
                    st.dataframe(quarter_table)
                    st.plotly_chart(px.bar(quarter_table, x="Quarter", y="Count",
                                           title=f"Quarter Breakdown - {sup}"), use_container_width=True)

                # Grade breakdown
                if "Grade" in sup_df.columns:
                    grade_table = sup_df["Grade"].value_counts().reset_index()
                    grade_table.columns = ["Grade", "Count"]
                    st.markdown("**เกรดแกรมที่มีปัญหา (Grade Breakdown)**")
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
    else:
        st.warning("⚠️ ไม่มีข้อมูล Quarter สำหรับการวิเคราะห์ AI Advisor")
