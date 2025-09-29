import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import re

st.set_page_config(page_title="วิเคราะห์เคลมม้วน", layout="wide")
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

    # -----------------------------
    # KPI
    # -----------------------------
    st.subheader("📌 สรุปภาพรวม")
    col1, col2, col3 = st.columns(3)
    col1.metric("จำนวนรายการข้อบกพร่อง", len(df))
    col2.metric("ซัพพลายเออร์", df["SUP"].nunique())
    col3.metric("ประเภทข้อบกพร่อง", df["Defect"].nunique())

    # -----------------------------
    # กราฟ SUP
    # -----------------------------
    st.subheader("🏭 อันดับ SUP (Top 12)")
    sup_count = df.groupby("SUP").size().reset_index(name="Count").sort_values("Count", ascending=False).head(12)
    fig1 = px.bar(sup_count, x="SUP", y="Count", text="Count")
    st.plotly_chart(fig1, use_container_width=True)

    # -----------------------------
    # กราฟ Defect
    # -----------------------------
    st.subheader("🧩 สัดส่วนประเภทข้อบกพร่อง (Top 12)")
    defect_count = df.groupby("Defect").size().reset_index(name="Count").sort_values("Count", ascending=False).head(12)
    fig2 = px.pie(defect_count, names="Defect", values="Count")
    st.plotly_chart(fig2, use_container_width=True)

    # -----------------------------
    # แนวโน้มรายเดือน
    # -----------------------------
    st.subheader("📅 แนวโน้มรายเดือน (จำนวนเคส) แยกตาม SUP")
    monthly_sup = df.groupby(["MonthKey", "SUP"]).size().reset_index(name="Count")
    fig3 = px.line(monthly_sup, x="MonthKey", y="Count", color="SUP", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

    # -----------------------------
    # ตารางคำแนะนำอัตโนมัติ
    # -----------------------------
    st.subheader("💡 คำแนะนำอัตโนมัติ")
    advisor_unique = df[["SUP", "Defect", "Advice"]].drop_duplicates()
    st.dataframe(advisor_unique, hide_index=True)

    # -----------------------------
    # วิเคราะห์ SUP + เกรดแกรม + Defect รายเดือน/Quarter
    # -----------------------------
    st.subheader("📊 วิเคราะห์ SUP + เกรดแกรม + Defect รายเดือน/Quarter")

    monthly_sup_grade = (
        df.groupby(["MonthKey", "SUP", "Grade", "Defect"])
          .size()
          .reset_index(name="จำนวนเคส")
          .sort_values(["MonthKey", "SUP", "Grade", "Defect"])
    )
    st.markdown("**รายเดือน:**")
    st.dataframe(monthly_sup_grade, hide_index=True)

    quarterly_sup_grade = (
        df.groupby(["Quarter", "SUP", "Grade", "Defect"])
          .size()
          .reset_index(name="จำนวนเคส")
          .sort_values(["Quarter", "SUP", "Grade", "Defect"])
    )
    st.markdown("**ราย Quarter:**")
    st.dataframe(quarterly_sup_grade, hide_index=True)

    st.subheader("📈 แนวโน้มจำนวนเคสแยกตาม SUP และ Grade")
    fig_sup_grade = px.bar(
        quarterly_sup_grade,
        x="SUP",
        y="จำนวนเคส",
        color="Grade",
        facet_col="Quarter",
        text="Defect",
        title="จำนวนเคสต่อ SUP + Grade (ราย Quarter)"
    )
    st.plotly_chart(fig_sup_grade, use_container_width=True)

    # -----------------------------
    # 🤖 AI วิเคราะห์เชิงลึก
    # -----------------------------
    st.subheader("🤖 AI วิเคราะห์เชิงลึก")

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

    st.subheader("💡 สรุปเชิงกลยุทธ์สำหรับผู้บริหาร")
    for _, row in watchlist.iterrows():
        sup = row["SUP"]
        defect = row["Defect"]
        count = row["จำนวนเคส"]

        if "ขอบ" in defect:
            advice = (
                f"ในช่วงที่ผ่านมา SUP {sup} พบปัญหา “{defect}” จำนวน {count} ครั้ง "
                "ซึ่งสะท้อนถึงความเสี่ยงด้านคุณภาพที่ควรได้รับการติดตามอย่างใกล้ชิด "
                "ข้อเสนอเชิงกลยุทธ์คือการกำหนดมาตรการควบคุมคุณภาพเพิ่มเติม "
                "และติดตามผลการปรับปรุงอย่างต่อเนื่องในรอบการผลิตถัดไป"
            )
        elif "คราบ" in defect:
            advice = (
                f"ข้อมูลชี้ให้เห็นว่า SUP {sup} มีปัญหา “{defect}” เกิดขึ้น {count} ครั้ง "
                "แนวโน้มนี้อาจส่งผลต่อความน่าเชื่อถือของผลิตภัณฑ์ "
                "ข้อเสนอเชิงกลยุทธ์คือการยกระดับมาตรฐานการตรวจสอบความสะอาด "
                "และสร้างระบบติดตามผลเพื่อป้องกันการเกิดซ้ำ"
            )
        else:
            advice = (
                f"SUP {sup} พบปัญหา “{defect}” จำนวน {count} ครั้ง "
                "ซึ่งควรได้รับการจัดลำดับความสำคัญในการแก้ไข "
                "ข้อเสนอเชิงกลยุทธ์คือการทบทวนกระบวนการผลิตโดยรวม "
                "และกำหนดมาตรการเชิงป้องกันในระยะกลางถึงยาว"
            )

        st.success(advice)

        # -----------------------------
    # 📈 การพยากรณ์ปัญหาเดือนถัดไป
    # -----------------------------
    st.subheader("📈 การพยากรณ์ปัญหาเดือนถัดไป")

    monthly = (
        df.groupby(["MonthKey", "SUP", "Defect"])
          .size()
          .reset_index(name="จำนวนเคส")
    )

    forecast_results = []

    for (sup, defect), group in monthly.groupby(["SUP", "Defect"]):
        ts = group.set_index("MonthKey")["จำนวนเคส"]
        ts.index = pd.to_datetime(ts.index + "-01")  # แปลงเป็น datetime
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
        fig = px.bar(
            forecast_df,
            x="SUP",
            y="คาดการณ์เดือนหน้า",
            color="Defect",
            title="📊 คาดการณ์จำนวนปัญหา SUP + Defect เดือนถัดไป"
        )
        st.plotly_chart(fig, use_container_width=True)
