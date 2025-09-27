import streamlit as st
import pandas as pd
import plotly.express as px
import re
import numpy as np
import html

st.set_page_config(page_title="📊 วิเคราะห์ปัญหาเคลมแผ่น", layout="wide")
st.title("📊 รายงานวิเคราะห์ข้อบกพร่องจากเคลมแผ่น")

# -----------------------------
# Utility functions
# -----------------------------
def median(arr):
    if len(arr) == 0:
        return 0
    return float(np.median(arr))

def escape_html(s):
    return html.escape(str(s))

# Root cause mapping
root_cause_rules = [
    (r"carl?ender|คาเลนเดอร์|คาร์เลนเดอร์|จุดดำ", "รอยลูกรีด/ผิวหน้า (Calender mark / Black spots)"),
    (r"ยับ|รอยยับ|ยับในม้วน|ม้วนหย่อน", "Tension/การกรอ-ขนส่ง"),
    (r"รอยเส้น|สันนูน", "การรีด/การกรอ/ตั้งค่าลูกกลิ้ง"),
    (r"กระดาษสกปรก|หัวม้วนสกปรก|กระดาษด่าง|ด่าง", "การปนเปื้อน/สิ่งสกปรกในระบบ"),
    (r"wax|คราบ", "คราบ WAX/เคมีค้าง"),
    (r"ความชื้น|Cobb", "ความชื้น/การอบไม่เหมาะสม"),
    (r"Bursting", "ความแข็งแรงเนื้อกระดาษต่ำ (Bursting)"),
    (r"แกรมสูง|แกรมต่ำ", "น้ำหนักพื้นฐานคลาดเคลื่อน (Basis weight)"),
    (r"หน้ากว้าง.*(ต่ำ|หด|เกิน|สูง)|หน้ากว้างไม่เป็นไปตาม", "ความกว้างคลาดเคลื่อน (Slitting/Trim control)"),
    (r"แกนเบี้ยว|หัวม้วนแตก", "แกน/การแพ็ค/ขนส่ง"),
    (r"รอยกระแทก|เศษกรีด|รอยทับยาง", "Handling/ขนส่ง/ใบมีด"),
    (r"สีตก", "การเคลือบ/หมึก/โค้ทติ้ง (Color off-spec)")
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
    if re.search(r"สันนูน|รอยเส้น|เศษกรีด|รอยกระแทก", t, re.I):
        return "ทบทวน slitting/ใบมีด/แนวตัด, tension กรอ, handling และการรองกันกระแทก"
    if re.search(r"carl?ender|จุดดำ|ด่าง|สกปรก", t, re.I):
        return "ทำความสะอาดลูกกลิ้ง/ไลน์, ตรวจของแปลกปลอม, ตั้งรอบทำความสะอาดและบันทึก"
    if re.search(r"แกรม|หน้ากว้าง", t, re.I):
        return "สอบเทียบเครื่องชั่ง/Trim, ยืนยันแผน sampling และ Alarm limits"
    if re.search(r"Bursting", t, re.I):
        return "ทบทวนสูตร/ไฟเบอร์/เคมี, ตรวจ Lab control และแนวโน้มคุณสมบัติวัตถุดิบ"
    if re.search(r"ความชื้น|Cobb", t, re.I):
        return "ควบคุม RH โกดัง, ตรวจซีลกันชื้น, ตรวจ oven/profile ช่วงปลายไลน์"
    if re.search(r"แกนเบี้ยว|ม้วนหย่อน|หัวม้วนแตก", t, re.I):
        return "ตรวจแกน, core plug, tension cut-over, วิธีแพ็ค/บล็อกมุม"
    if re.search(r"สีตก", t, re.I):
        return "ปรับโค้ทติ้ง/หมึก, ตรวจความหนาเคลือบและสภาวะอบแห้ง"
    return "กำหนดแผนตรวจจุดวิกฤตในไลน์ + sampling เพิ่มเติมช่วงรับเข้า"

# -----------------------------
# File upload
# -----------------------------
uploaded_file = st.file_uploader("📄 อัปโหลดไฟล์ Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Rename columns
    rename_map = {
        "SUP": "SUP",
        "ซัพพลายเออร์": "SUP",
        "Supplier": "SUP",
        "สิ่งที่ไม่เป็นไปตามข้อกำหนด": "Defect",
        "ข้อบกพร่อง": "Defect",
        "อาการ": "Defect",
        "เกรดแกรม": "Grade",
        "Grade": "Grade",
        "วันที่ออก": "Date",
        "Date": "Date",
        "วันที่เอกสาร": "Date",
        "Lot": "Lot",
        "Code": "Code",
        "วันที่ส่งของ": "ShipDate"
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

    # Date handling
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
        df["MonthKey"] = df["Date"].dt.strftime("%Y-%m")
        df["Month"] = df["Date"].dt.month
        df["Quarter"] = df["Date"].dt.quarter
    else:
        df["MonthKey"] = "ไม่ระบุ"

    # Add RootCause + Advice
    df["RootCause"] = df["Defect"].apply(map_root_cause)
    df["Advice"] = df["Defect"].apply(advise_for)

    # -----------------------------
    # KPI Cards
    # -----------------------------
    st.subheader("📌 สรุปภาพรวม")
    col1, col2, col3 = st.columns(3)
    col1.metric("จำนวนรายการข้อบกพร่อง", len(df))
    col2.metric("ซัพพลายเออร์ที่เกี่ยวข้อง", df["SUP"].nunique())
    col3.metric("ประเภทข้อบกพร่องที่พบ", df["Defect"].nunique())

    # -----------------------------
    # Supplier Bar
    # -----------------------------
    st.subheader("🏭 อันดับ SUP โดยจำนวนข้อบกพร่อง (Top 12)")
    sup_count = df.groupby("SUP").size().reset_index(name="Count").sort_values("Count", ascending=False).head(12)
    fig1 = px.bar(sup_count, x="SUP", y="Count", text="Count", title="จำนวน defect ต่อ SUP")
    st.plotly_chart(fig1, use_container_width=True)

    # -----------------------------
    # Defect Pie
    # -----------------------------
    st.subheader("🧩 สัดส่วนประเภทข้อบกพร่อง (Top 12)")
    defect_count = df.groupby("Defect").size().reset_index(name="Count").sort_values("Count", ascending=False).head(12)
    fig2 = px.pie(defect_count, names="Defect", values="Count", title="Defect Breakdown")
    st.plotly_chart(fig2, use_container_width=True)

    # -----------------------------
    # Monthly Trend
    # -----------------------------
    st.subheader("📅 แนวโน้มรายเดือน (จำนวนเคส)")
    monthly = df.groupby("MonthKey").size().reset_index(name="Count").sort_values("MonthKey")
    fig3 = px.line(monthly, x="MonthKey", y="Count", markers=True, title="จำนวน defect รายเดือน")
    st.plotly_chart(fig3, use_container_width=True)

    # -----------------------------
    # Top Defect by Supplier
    # -----------------------------
    st.subheader("🔥 Top Defect ของแต่ละ SUP (Top 8)")
    sup_summary = df.groupby(["SUP","Defect"]).size().reset_index(name="Count")
    top_sups = sup_summary.groupby("SUP")["Count"].sum().sort_values(ascending=False).head(8).index
    df_top = sup_summary[sup_summary["SUP"].isin(top_sups)]
    fig4 = px.bar(df_top, x="SUP", y="Count", color="Defect", barmode="group", title="Top 8 SUP และอาการเด่น")
    st.plotly_chart(fig4, use_container_width=True)

    # -----------------------------
# Summary Table
# -----------------------------
st.subheader("📊 ตารางสรุปตาม SUP")

summary = []
for sup, g in df.groupby("SUP"):
    total = len(g)
    # Top 3 อาการ
    top3 = g["Defect"].value_counts().head(3).to_dict()
    top3_str = ", ".join([f"{k} ({v})" for k, v in top3.items()])
    # เดือนล่าสุด
    latest_month = g["MonthKey"].max()
    latest_count = len(g[g["MonthKey"] == latest_month])
    summary.append({
        "SUP": sup,
        "รวมเคส": total,
        "Top 3 อาการ": top3_str,
        "เดือนล่าสุด": f"{latest_month}: {latest_count}" if latest_month else "-"
    })

summary_df = pd.DataFrame(summary).sort_values("รวมเคส", ascending=False)
st.dataframe(summary_df, hide_index=True)
