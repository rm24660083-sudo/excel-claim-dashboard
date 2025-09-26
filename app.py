import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 SUP Defect & Grade Analysis + AI Advisor", layout="wide")
st.title("📊 SUP Defect & Grade Analysis + AI Advisor")

# ฟังก์ชัน AI Advisor (Advance)
def advanced_ai_advisor(df):
    tips = []
    if df.empty:
        return ["⚠️ ไม่พบข้อมูลสำหรับการวิเคราะห์"]

    latest_q = df["Quarter"].max()
    q_data = df[df["Quarter"] == latest_q]

    # SUP ที่มี defect สูงสุด
    if "SUP" in q_data.columns:
        sup_counts = q_data["SUP"].value_counts()
        if not sup_counts.empty:
            top_sup = sup_counts.index[0]
            top_count = sup_counts.iloc[0]
            tips.append(f"🏭 SUP {top_sup} มี defect {top_count} ครั้งใน Q{latest_q} — ควรติดตามใกล้ชิด")

    # Defect ที่ recurring
    if "Defect" in q_data.columns:
        defect_counts = q_data["Defect"].value_counts()
        if not defect_counts.empty:
            top_defect = defect_counts.index[0]
            tips.append(f"🔁 Defect '{top_defect}' เกิดซ้ำบ่อยที่สุดใน Q{latest_q} — ควรตรวจสอบกระบวนการที่เกี่ยวข้อง")

    # เกรดแกรมที่เกี่ยวข้อง
    if {"Grade","Defect"}.issubset(q_data.columns):
        grade_defect = q_data.groupby("Grade")["Defect"].count().sort_values(ascending=False)
        if not grade_defect.empty:
            top_grade = grade_defect.index[0]
            tips.append(f"📦 เกรดแกรม {top_grade} มี defect สูงสุดใน Q{latest_q} — ควรตรวจสอบคุณภาพวัตถุดิบ/การผลิต")

    # แนวทางเดือนถัดไป
    if "Month" in df.columns:
        next_month = df["Month"].max() + 1
        tips.append(f"📅 เดือนถัดไป (เดือน {next_month}) ควรโฟกัส SUP และ defect ที่ recurring เป็นพิเศษ")

    # ข้อเสนอแนะทั่วไป
    tips.append("✅ แนะนำทำ CAPA (Corrective Action) ร่วมกับ SUP ที่มี defect สูงสุด")
    tips.append("🧪 ควรสุ่มตรวจคุณภาพเกรดแกรมที่มี defect สูงก่อนการผลิตล็อตใหม่")

    return tips


# อัปโหลดไฟล์
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

    # --- 1. SUP → Defect ---
    st.subheader("🔍 ข้อผิดพลาดของแต่ละ SUP")
    if {"SUP","Defect"}.issubset(df.columns):
        sup_defect = df.groupby(["SUP","Defect"]).size().reset_index(name="Count")
        st.dataframe(sup_defect)
        fig = px.bar(sup_defect, x="SUP", y="Count", color="Defect",
                     title="Defect Breakdown by SUP", barmode="stack")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ ไม่พบคอลัมน์ SUP หรือ Defect")

    # --- 2. SUP → Quarter ---
    st.subheader("📅 ข้อผิดพลาดรายไตรมาส")
    if {"SUP","Quarter"}.issubset(df.columns):
        sup_quarter = df.groupby(["Quarter","SUP"]).size().reset_index(name="Count")
        st.dataframe(sup_quarter)
        fig2 = px.bar(sup_quarter, x="Quarter", y="Count", color="SUP",
                      title="Defect Count by Quarter", barmode="group")
        st.plotly_chart(fig2, use_container_width=True)

    # --- 3. SUP → Grade ---
    st.subheader("📦 เกรดแกรมที่มีปัญหาในแต่ละ SUP")
    if {"SUP","Grade"}.issubset(df.columns):
        sup_grade = df.groupby(["SUP","Grade"]).size().reset_index(name="Count")
        st.dataframe(sup_grade)
        fig3 = px.bar(sup_grade, x="SUP", y="Count", color="Grade",
                      title="Defect by SUP and Grade", barmode="stack")
        st.plotly_chart(fig3, use_container_width=True)

    # --- 4. AI Advisor ---
    st.subheader("🧠 AI Advisor (Advance)")
    if "Quarter" in df.columns:
        tips = advanced_ai_advisor(df)
        for t in tips:
            st.write("- " + t)
    else:
        st.warning("⚠️ ไม่มีข้อมูล Quarter สำหรับการวิเคราะห์ AI Advisor")
