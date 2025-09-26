import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 SUP Defect Dashboard", layout="wide")
st.title("📊 รายงานวิเคราะห์ SUP และ Defect")

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

    # แนวทางเดือนถัดไป
    if "Month" in df.columns:
        next_month = df["Month"].max() + 1
        tips.append(f"📅 เดือนถัดไป (เดือน {next_month}) ควรโฟกัส SUP และ defect ที่ recurring")

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
    # 1. SUP × Defect
    # -----------------------------
    st.header("1️⃣ SUP ไหนมี Defect อะไรบ้าง และจำนวนเท่าไหร่")
    if {"SUP","Defect"}.issubset(df.columns):
        sup_defect = df.groupby(["SUP","Defect"]).size().reset_index(name="Count")
        fig1 = px.bar(sup_defect, x="SUP", y="Count", color="Defect", barmode="stack",
                      title="Defect Breakdown by SUP")
        st.plotly_chart(fig1, use_container_width=True)
        st.dataframe(sup_defect, hide_index=True)

    # -----------------------------
    # 2. SUP × Grade
    # -----------------------------
    st.header("2️⃣ SUP ที่มี Defect → เกรดแกรมที่เกี่ยวข้อง")
    if {"SUP","Grade","Defect"}.issubset(df.columns):
        sup_grade = df.groupby(["SUP","Grade","Defect"]).size().reset_index(name="Count")
        fig2 = px.bar(sup_grade, x="SUP", y="Count", color="Defect", facet_col="Grade",
                      title="Defect by SUP and Grade", barmode="stack")
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(sup_grade, hide_index=True)

    # -----------------------------
    # 3. Monthly Trend
    # -----------------------------
    st.header("3️⃣ กราฟวิเคราะห์ผลรายเดือน (เปรียบเทียบข้อผิดพลาด)")
    if {"SUP","Defect","Month"}.issubset(df.columns):
        monthly = df.groupby(["Month","SUP","Defect"]).size().reset_index(name="Count")
        fig3 = px.bar(monthly, x="Month", y="Count", color="Defect", facet_col="SUP",
                      title="Monthly Defect Trend by SUP", barmode="stack")
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(monthly, hide_index=True)

    # -----------------------------
    # 4. SUP ที่ควรติดตาม
    # -----------------------------
    st.header("4️⃣ SUP ที่ควรติดตามเป็นพิเศษ")
    tips = ai_advisor(df)
    for t in tips:
        st.write("- " + t)

    # -----------------------------
    # 5. แนวทางป้องกัน/แก้ไข
    # -----------------------------
    st.header("5️⃣ แนวทางการป้องกันและแก้ไข (เดือน 10 หรือถัดไป)")
    st.success("""
    - ตรวจสอบ SUP ที่ defect ซ้ำบ่อยใน Q ล่าสุด  
    - โฟกัส defect ประเภท recurring เช่น จุดดำ / ตาไม้  
    - ตรวจสอบคุณภาพวัตถุดิบของเกรดแกรมที่ defect สูง  
    - ทำ CAPA ร่วมกับ SUP ที่มี defect สูงสุด  
    - เพิ่มการสุ่มตรวจคุณภาพในเดือน 10 และต่อไป  
    """)
