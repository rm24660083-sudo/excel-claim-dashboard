import streamlit as st
import pandas as pd
import plotly.express as px

from analysis import (
    load_excel,
    defect_counts_by_sup,
    defect_counts_by_month,
    defect_counts_by_quarter,
    top_defects,
    risk_assessment_oct_q4,
)
from ai_rules import generate_ai_tips

st.set_page_config(page_title="Excel Claim Dashboard", layout="wide")

st.title("📊 เคลมม้วน — Excel Analyzer + AI Advisor")

st.markdown("> อัปโหลดไฟล์ Excel เพื่อวิเคราะห์เคลมและรับคำแนะนำอัตโนมัติ")

uploaded = st.file_uploader("อัปโหลดไฟล์ Excel (.xlsx)", type=["xlsx"])

if not uploaded:
    st.info("โปรดอัปโหลดไฟล์ Excel ที่มีข้อมูลคอลัมน์ เช่น SUP, Defect, ShipDate/IssueDate, Width, Weight, Month, Week")
else:
    # โหลดและทำความสะอาดข้อมูล
    df = load_excel(uploaded)

    # สรุปภาพรวม
    with st.expander("ภาพรวมข้อมูล", expanded=True):
        col1, col2, col3 = st.columns([2,2,2])
        with col1:
            st.metric("จำนวนรายการทั้งหมด", len(df))
        with col2:
            st.metric("ชนิด Defect ที่แตกต่าง", df["Defect"].nunique() if "Defect" in df.columns else 0)
        with col3:
            st.metric("จำนวน SUP", df["SUP"].nunique() if "SUP" in df.columns else 0)
        st.dataframe(df.head(50), use_container_width=True)

    # กราฟตาม SUP
    sup_counts = defect_counts_by_sup(df)
    with st.expander("สรุปตาม SUP", expanded=True):
        if not sup_counts.empty:
            fig = px.bar(sup_counts, x="SUP", y="DefectCount", title="Defect Count by SUP")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(sup_counts, use_container_width=True)
        else:
            st.warning("ไม่พบคอลัมน์ SUP หรือ Defect")

    # กราฟตามเดือน
    month_counts = defect_counts_by_month(df)
    with st.expander("สรุปตามเดือน (Month)", expanded=False):
        if not month_counts.empty:
            fig = px.bar(month_counts, x="Month", y="DefectCount", title="Defect Count by Month")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(month_counts, use_container_width=True)
        else:
            st.warning("ไม่พบคอลัมน์ Month หรือ Defect")

    # กราฟตามไตรมาส
    q_counts = defect_counts_by_quarter(df)
    with st.expander("สรุปตามไตรมาส (Quarter)", expanded=False):
        if not q_counts.empty:
            fig = px.bar(q_counts, x="Quarter", y="DefectCount", title="Defect Count by Quarter")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q_counts, use_container_width=True)
        else:
            st.warning("ไม่พบคอลัมน์ Quarter หรือ Defect")

    # Top defects
    topd = top_defects(df, top_n=12)
    with st.expander("Defect ที่พบมากที่สุด", expanded=False):
        if not topd.empty:
            fig = px.bar(topd, x="Defect", y="Count", title="Top Defects", text="Count")
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(topd, use_container_width=True)
        else:
            st.warning("ไม่พบคอลัมน์ Defect")

    # วิเคราะห์เฉพาะ October/Q4
    with st.expander("การประเมินความเสี่ยง: October และ Q4", expanded=False):
        risk = risk_assessment_oct_q4(df)
        st.write(risk)

    # Download ส่วนสรุป
    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button("ดาวน์โหลดข้อมูลทั้งหมดเป็น CSV", data=df.to_csv(index=False), file_name="claims_clean.csv", mime="text/csv")
    with col_b:
        if not sup_counts.empty:
            st.download_button("ดาวน์โหลดสรุป SUP เป็น CSV", data=sup_counts.to_csv(index=False), file_name="claims_by_sup.csv", mime="text/csv")

    # AI Advisor
    st.subheader("🧠 AI ข้อแนะนำ/ข้อควรระวัง")
    tips = generate_ai_tips(df)
    for tip in tips:
        st.write(tip)

    # กลุ่มตาม SUP (collapsible)
    st.subheader("🔍 เจาะลึกตาม SUP")
    if "SUP" in df.columns:
        for sup in sorted(df["SUP"].dropna().unique()):
            with st.expander(f"SUP: {sup}", expanded=False):
                sub = df[df["SUP"] == sup]
                st.write(f"จำนวนเคส: {len(sub)}")
                if "Defect" in sub.columns:
                    st.write(sub["Defect"].value_counts().head(10))
                st.dataframe(sub.head(100), use_container_width=True)
