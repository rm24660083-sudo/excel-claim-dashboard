import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📊 SUP Defect & Grade Analysis + AI Advisor")

uploaded_file = st.file_uploader("อัปโหลดไฟล์ Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # --- เตรียมข้อมูล ---
    # แปลงวันที่
    if "วันที่ส่งของ" in df.columns:
        df["ShipDate"] = pd.to_datetime(df["วันที่ส่งของ"], errors="coerce", dayfirst=True)
    elif "วันที่ออก" in df.columns:
        df["ShipDate"] = pd.to_datetime(df["วันที่ออก"], errors="coerce", dayfirst=True)

    df["Month"] = df["ShipDate"].dt.month
    df["Quarter"] = df["ShipDate"].dt.quarter

    # --- 1. SUP → Defect ---
    st.subheader("🔍 ข้อผิดพลาดของแต่ละ SUP")
    sup_defect = df.groupby(["SUP","Defect"]).size().reset_index(name="Count")
    st.dataframe(sup_defect)

    fig = px.bar(sup_defect, x="SUP", y="Count", color="Defect",
                 title="Defect Breakdown by SUP", barmode="stack")
    st.plotly_chart(fig, use_container_width=True)

    # --- 2. SUP → Quarter ---
    st.subheader("📅 ข้อผิดพลาดรายไตรมาส")
    sup_quarter = df.groupby(["Quarter","SUP"]).size().reset_index(name="Count")
    st.dataframe(sup_quarter)

    fig2 = px.bar(sup_quarter, x="Quarter", y="Count", color="SUP",
                  title="Defect Count by Quarter", barmode="group")
    st.plotly_chart(fig2, use_container_width=True)

    # --- 3. SUP → Grade ---
    st.subheader("📦 เกรดแกรมที่มีปัญหาในแต่ละ SUP")
    if "Grade" in df.columns:
        sup_grade = df.groupby(["SUP","Grade"]).size().reset_index(name="Count")
        st.dataframe(sup_grade)

        fig3 = px.bar(sup_grade, x="SUP", y="Count", color="Grade",
                      title="Defect by SUP and Grade", barmode="stack")
        st.plotly_chart(fig3, use_container_width=True)

    # --- 4. AI Advisor ---
    st.subheader("🧠 AI ข้อเสนอแนะ")
    latest_q = df["Quarter"].max()
    q_data = df[df["Quarter"] == latest_q]
    sup_risk = q_data["SUP"].value_counts().head(3)

    for sup, count in sup_risk.items():
        st.write(f"⚠️ SUP {sup} มีข้อผิดพลาด {count} ครั้งใน Q{latest_q} — ควรติดตามใกล้ชิด")

    st.write("✅ แนวทางเดือนถัดไป:")
    st.write("- ตรวจสอบ SUP ที่มี defect ซ้ำ ๆ ใน Quarter ล่าสุด")
    st.write("- วิเคราะห์ defect type ที่ recurring และทำ CAPA (Corrective Action)")
    st.write("- ตรวจสอบเกรดแกรมที่ defect สูงเป็นพิเศษ")
