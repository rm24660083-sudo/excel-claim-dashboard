import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 วิเคราะห์ปัญหาเคลมแผ่น", layout="wide")
st.title("📊 รายงานวิเคราะห์ข้อบกพร่องจากเคลมแผ่น")

uploaded_file = st.file_uploader("📄 อัปโหลดไฟล์ Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ✅ Mapping คอลัมน์
    rename_map = {
        "SUP": "SUP",
        "ซัพพลายเออร์": "SUP",
        "สิ่งที่ไม่เป็นไปตามข้อกำหนด": "Defect",
        "ข้อบกพร่อง": "Defect",
        "เกรดแกรม": "Grade",
        "วันที่ออก": "Date",
        "วันที่ส่งของ": "ShipDate",
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

    # ✅ จัดการวันที่
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
        df["Month"] = df["Date"].dt.to_period("M").astype(str)
        df["Quarter"] = df["Date"].dt.quarter

    # -----------------------------
    # KPI Cards
    # -----------------------------
    st.subheader("📌 สรุปภาพรวม")
    col1, col2, col3 = st.columns(3)
    col1.metric("จำนวนรายการข้อบกพร่อง", len(df))
    col2.metric("จำนวน SUP", df["SUP"].nunique())
    col3.metric("ประเภท Defect", df["Defect"].nunique())

    # -----------------------------
    # อันดับ SUP โดยจำนวน defect
    # -----------------------------
    st.subheader("🏭 อันดับ SUP โดยจำนวนข้อบกพร่อง")
    sup_count = df["SUP"].value_counts().reset_index()
    sup_count.columns = ["SUP","Count"]
    fig1 = px.bar(sup_count, x="SUP", y="Count", title="จำนวน defect ต่อ SUP")
    st.plotly_chart(fig1, use_container_width=True)

    # -----------------------------
    # Pie chart defect breakdown
    # -----------------------------
    st.subheader("🧩 สัดส่วนประเภทข้อบกพร่อง")
    defect_count = df["Defect"].value_counts().reset_index()
    defect_count.columns = ["Defect","Count"]
    fig2 = px.pie(defect_count, names="Defect", values="Count", title="Defect Breakdown")
    st.plotly_chart(fig2, use_container_width=True)

    # -----------------------------
    # แนวโน้มรายเดือน
    # -----------------------------
    st.subheader("📅 แนวโน้มรายเดือน")
    if "Month" in df.columns:
        monthly = df.groupby("Month").size().reset_index(name="Count")
        fig3 = px.line(monthly, x="Month", y="Count", markers=True, title="จำนวน defect รายเดือน")
        st.plotly_chart(fig3, use_container_width=True)

    # -----------------------------
    # Watchlist SUP ที่ควรระวัง
    # -----------------------------
    st.subheader("⚠️ Watchlist SUP ที่ควรระวัง")
    watchlist = df.groupby("SUP").size().reset_index(name="Count").sort_values("Count", ascending=False).head(10)
    st.dataframe(watchlist, hide_index=True)

    # -----------------------------
    # ตารางสรุป SUP + defect เด่น
    # -----------------------------
    st.subheader("📊 ตารางสรุปตาม SUP")
    summary = df.groupby(["SUP","Defect"]).size().reset_index(name="Count")
    st.dataframe(summary, hide_index=True)

    # -----------------------------
    # ตารางรายละเอียด defect
    # -----------------------------
    st.subheader("📋 รายละเอียดข้อผิดพลาด")
    st.dataframe(df[["SUP","Defect","Grade"]], hide_index=True)
