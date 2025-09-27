import streamlit as st
import pandas as pd
import numpy as np
import os
from io import BytesIO
from fpdf import FPDF
import plotly.express as px

# -----------------------------
# Config + Logo + Credit
# -----------------------------
st.set_page_config(page_title="📊 วิเคราะห์เคลม", layout="wide")

logo_path = os.path.join(os.path.dirname(__file__), "Logo.png")
st.image(logo_path, width=120)
st.markdown(
    """
    <div style="font-size:16px; font-weight:bold; margin-top:5px;">
        Powered by <span style="color:#d62728;">The Beyonder RM</span>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# เลือกประเภทไฟล์ + อัปโหลด
# -----------------------------
file_type = st.selectbox("📂 เลือกประเภทข้อมูล", ["เคลมม้วน", "เคลมแผ่น"])
uploaded_file = st.file_uploader("📄 อัปโหลดไฟล์ Excel", type=["xlsx"])

# -----------------------------
# ประมวลผลตามประเภท
# -----------------------------
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if file_type == "เคลมม้วน":
        process_claim_roll(df)

    elif file_type == "เคลมแผ่น":
        process_claim_sheet(df)

# -----------------------------
# ฟังก์ชัน: เคลมม้วน
# -----------------------------
def process_claim_roll(df):
    st.title("📊 รายงานวิเคราะห์ข้อบกพร่องจากเคลมม้วน")

    rename_map = {
        "SUP": "SUP", "ซัพพลายเออร์": "SUP", "Supplier": "SUP",
        "สิ่งที่ไม่เป็นไปตามข้อกำหนด": "Defect", "ข้อบกพร่อง": "Defect", "อาการ": "Defect",
        "เกรดแกรม": "Grade", "Grade": "Grade",
        "วันที่ออก": "Date", "Date": "Date", "วันที่เอกสาร": "Date",
        "Lot": "Lot", "Code": "Code", "วันที่ส่งของ": "ShipDate"
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
        df["MonthKey"] = df["Date"].dt.strftime("%Y-%m")
        df["Month"] = df["Date"].dt.month
        df["Quarter"] = df["Date"].dt.quarter
    else:
        df["MonthKey"] = "ไม่ระบุ"

    def advise_for(defect):
        t = str(defect)
        if "จุดดำ" in t or "ตาไม้" in t:
            return "ทำความสะอาดลูกกลิ้งและตรวจสิ่งปนเปื้อน"
        if "ยับ" in t or "ม้วน" in t:
            return "ตรวจ tension cut-over และวิธีแพ็ค"
        if "กระดาษแตก" in t or "กระดาษด่าง" in t:
            return "ตรวจสอบคุณภาพเยื่อและการอบแห้ง"
        if "Carlender" in t:
            return "ทำความสะอาดลูกกลิ้ง Calender และตรวจแรงกด"
        return "ตรวจสอบจุดวิกฤตในไลน์ผลิตและเพิ่ม sampling"

    if "สิ่งที่ไม่เป็นไปตามข้อกำหนด" in df.columns:
        df["Defect"] = df["สิ่งที่ไม่เป็นไปตามข้อกำหนด"]
        df["Advice"] = df["Defect"].apply(advise_for)

    st.subheader("📌 สรุปภาพรวม")
    col1, col2, col3 = st.columns(3)
    col1.metric("จำนวนรายการข้อบกพร่อง", len(df))
    col2.metric("ซัพพลายเออร์ที่เกี่ยวข้อง", df["SUP"].nunique() if "SUP" in df.columns else 0)
    col3.metric("ประเภทข้อบกพร่องที่พบ", df["Defect"].nunique() if "Defect" in df.columns else 0)

    st.subheader("📅 แนวโน้มรายเดือน (จำนวนเคส) แยกตาม SUP")
    if "MONTH" in df.columns and "SUP" in df.columns:
        monthly_sup = df.groupby(["MONTH", "SUP"]).size().reset_index(name="Count")
        fig = px.line(monthly_sup, x="MONTH", y="Count", color="SUP", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("💡 คำแนะนำอัตโนมัติ (Advisor)")
    if "SUP" in df.columns and "Defect" in df.columns:
        advisor_unique = df[["SUP", "Defect", "Advice"]].drop_duplicates()
        st.dataframe(advisor_unique, hide_index=True)

    st.subheader("📥 Export ข้อมูล")
    excel_data = to_excel(df)
    st.download_button("ดาวน์โหลด Excel", excel_data, "claim_sheet.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    pdf_data = generate_pdf(df)
    st.download_button("ดาวน์โหลด PDF", pdf_data, "claim_sheet.pdf", mime="application/pdf")

# -----------------------------
# ฟังก์ชัน: เคลมแผ่น
# -----------------------------
def process_claim_sheet(df):
    st.title("📊 รายงานวิเคราะห์ข้อบกพร่องจากเคลมแผ่น")

    df = df.rename(columns={
        "SUPPLIER": "SUP",
        "สิ่งที่ไม่เป็นไปตามข้อกำหนด": "Defect",
        "เดือน": "MONTH"
    })

    def advise_for(defect):
        t = str(defect)
        if "จุดดำ" in t or "ตาไม้" in t:
            return "ทำความสะอาดลูกกลิ้งและตรวจสิ่งปนเปื้อน"
        if "ยับ" in t or "ม้วน" in t:
            return "ตรวจ tension cut-over และวิธีแพ็ค"
        if "กระดาษแตก" in t or "กระดาษด่าง" in t:
            return "ตรวจสอบคุณภาพเยื่อและการอบแห้ง"
        if "Carlender" in t:
            return "ทำความสะอาดลูกกลิ้ง Calender และตรวจแรงกด"
        return "ตรวจสอบจุดวิกฤตในไลน์ผลิตและเพิ่ม sampling"

    df["Advice"] = df["Defect"].apply(advise_for)

    st.subheader("📌 สรุปภาพรวม")
    col1, col2, col3 = st.columns(3)
    col1.metric("จำนวนรายการข้อบกพร่อง", len(df))
    col2.metric("ซัพพลายเออร์ที่เกี่ยวข้อง", df["SUP"].nunique())
    col3.metric("ประเภทข้อบกพร่องที่พบ", df["Defect"].nunique())

    st.subheader("📅 แนวโน้มรายเดือน (จำนวนเคส) แยกตาม SUP")
    monthly_sup = df.groupby(["MONTH", "SUP"]).size().reset_index(name="Count")
    fig = px.line(monthly_sup, x="MONTH", y="Count", color="SUP", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("💡 คำแนะนำอัตโนมัติ (Advisor)")
    advisor_unique = df[["SUP", "Defect", "Advice"]].drop_duplicates()
    st.dataframe(advisor_unique, hide_index=True)

    st.subheader("📥 Export ข้อมูล")
    excel_data = to_excel(df)
    st.download_button("ดาวน์โหลด Excel", excel_data, "claim_sheet.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    pdf_data = generate_pdf(df)
    st.download_button("ดาวน์โหลด PDF", pdf_data, "claim_sheet.pdf", mime="application/pdf")

# -----------------------------
# Export Excel / PDF
# -----------------------------
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Analysis")
        writer.save()
    return output.getvalue()

def generate_pdf(df):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # หัวเรื่อง
    pdf.cell(200, 10, txt="รายงานวิเคราะห์ข้อบกพร่อง", ln=True, align="C")
    pdf.ln(10)

    # ตรวจว่ามีคอลัมน์ที่ต้องใช้หรือไม่
    required_cols = ["SUP", "Defect", "Advice"]
    for col in required_cols:
        if col not in df.columns:
            pdf.cell(200, 10, txt=f"⚠️ ไม่พบคอลัมน์ '{col}' ในข้อมูล", ln=True)
            return pdf.output(dest="S").encode("latin-1")

    # แสดงข้อมูลทีละแถว
    for i, row in df.iterrows():
        sup = str(row.get("SUP", "")).strip()
        defect = str(row.get("Defect", "")).strip()
        advice = str(row.get("Advice", "")).strip()

        line = f"SUP: {sup} | Defect: {defect} | Advice: {advice}"
        pdf.multi_cell(0, 10, txt=line)

    return pdf.output(dest="S").encode("latin-1")
