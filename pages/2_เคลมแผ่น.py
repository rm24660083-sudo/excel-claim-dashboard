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

        # -----------------------------
    # 🧩 สัดส่วนประเภทข้อบกพร่อง (Top 12)
    # -----------------------------
    st.subheader("🧩 สัดส่วนประเภทข้อบกพร่อง (Top 12)")

    defect_count = (
        df.groupby("Defect")
          .size()
          .reset_index(name="Count")
          .sort_values("Count", ascending=False)
          .head(12)
    )

    fig_pie = px.pie(
        defect_count,
        names="Defect",
        values="Count",
        title="สัดส่วนประเภทข้อบกพร่อง (Top 12)",
        hole=0.3  # ถ้าอยากให้เป็น donut chart
    )

    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

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

    # -----------------------------
    # 🤖 AI วิเคราะห์เชิงลึกเคลมแผ่น
    # -----------------------------
    st.subheader("🤖 AI วิเคราะห์เชิงลึกเคลมแผ่น")

    # 1) Watchlist SUP + Defect
    sup_defect = (
        df.groupby(["SUP", "Defect"])
          .size()
          .reset_index(name="จำนวนเคส")
          .sort_values("จำนวนเคส", ascending=False)
    )

    threshold = sup_defect["จำนวนเคส"].mean()
    watchlist = sup_defect[sup_defect["จำนวนเคส"] > threshold]

    st.markdown("**📌 SUP ที่ต้องเฝ้าระวัง (เกินค่าเฉลี่ย):**")
    st.dataframe(watchlist, hide_index=True)

    # 2) คำแนะนำเชิงกลยุทธ์
    st.subheader("💡 สรุปเชิงกลยุทธ์สำหรับผู้บริหาร")
    for _, row in watchlist.iterrows():
        sup = row["SUP"]
        defect = row["Defect"]
        count = row["จำนวนเคส"]

        if "ยับ" in defect:
            advice = (
                f"SUP {sup} พบปัญหา “{defect}” จำนวน {count} ครั้ง "
                "ซึ่งสะท้อนถึงความเสี่ยงด้านการจัดการวัสดุและการขนส่ง "
                "ข้อเสนอเชิงกลยุทธ์คือการทบทวนขั้นตอนการจัดเก็บและการเคลื่อนย้ายภายในโรงงาน "
                "รวมถึงกำหนดมาตรการควบคุมคุณภาพในจุดรับเข้า"
            )
        else:
            advice = (
                f"SUP {sup} พบปัญหา “{defect}” จำนวน {count} ครั้ง "
                "ซึ่งควรได้รับการจัดลำดับความสำคัญในการแก้ไข "
                "ข้อเสนอเชิงกลยุทธ์คือการทบทวนกระบวนการผลิตโดยรวม "
                "และกำหนดมาตรการเชิงป้องกันในระยะกลางถึงยาว"
            )

        st.success(advice)

    # 3) Forecasting เดือนถัดไป
    st.subheader("📈 การพยากรณ์ปัญหาเดือนถัดไป")

    monthly = (
        df.groupby(["MonthKey", "SUP", "Defect"])
          .size()
          .reset_index(name="จำนวนเคส")
    )

    forecast_results = []
    for (sup, defect), group in monthly.groupby(["SUP", "Defect"]):
        ts = group.set_index("MonthKey")["จำนวนเคส"]
        ts.index = pd.to_datetime(ts.index + "-01", errors="coerce")
        ts = ts.sort_index().asfreq("MS").fillna(0)

        if len(ts) >= 3:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            model = ExponentialSmoothing(ts, trend="add", seasonal=None)
            fit = model.fit()
            pred = fit.forecast(1)
            forecast_results.append([sup, defect, int(pred.values[0])])

    forecast_df = pd.DataFrame(forecast_results, columns=["SUP", "Defect", "คาดการณ์เดือนหน้า"])
    st.dataframe(forecast_df, hide_index=True)

    if not forecast_df.empty:
        fig_forecast = px.bar(
            forecast_df,
            x="SUP",
            y="คาดการณ์เดือนหน้า",
            color="Defect",
            title="📊 คาดการณ์จำนวนปัญหา SUP + Defect เดือนถัดไป"
        )
        st.plotly_chart(fig_forecast, use_container_width=True)
