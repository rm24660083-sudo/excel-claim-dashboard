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
        if "สันนูน" in t or "รอยเส้น" in t or "เศษกรีด" in t:
            return "ตรวจสอบ slitting/ใบมีด และ tension กรอ"
        if "Calender" in t or "จุดดำ" in t or "ด่าง" in t:
            return "ทำความสะอาดลูกกลิ้งและตรวจสิ่งปนเปื้อน"
        if "แกรม" in t or "หน้ากว้าง" in t:
            return "สอบเทียบเครื่องชั่ง/Trim และยืนยันแผน sampling"
        if "Bursting" in t:
            return "ทบทวนสูตร/ไฟเบอร์/เคมี และแนวโน้ม Lab"
        if "ความชื้น" in t or "Cobb" in t:
            return "ควบคุม RH โกดัง/ซีลกันชื้น และโปรไฟล์อบ"
        if "แกนเบี้ยว" in t or "ม้วนหย่อน" in t:
            return "ตรวจแกน/core plug/tension cut-over และวิธีแพ็ค"
        if "สีตก" in t:
            return "ปรับโค้ทติ้ง/หมึก ตรวจความหนาเคลือบและการอบแห้ง"
        return "กำหนดแผนตรวจจุดวิกฤตในไลน์ + sampling เพิ่มเติมช่วงรับเข้า"

    if "Defect" in df.columns:
        df["Advice"] = df["Defect"].apply(advise_for)

    st.subheader("📌 สรุปภาพรวม")
    col1, col2, col3 = st.columns(3)
    col1.metric("จำนวนรายการข้อบกพร่อง", len(df))
    col2.metric("ซัพพลายเออร์ที่เกี่ยวข้อง", df["SUP"].nunique() if "SUP" in df.columns else 0)
    col3.metric("ประเภทข้อบกพร่องที่พบ", df["Defect"].nunique() if "Defect" in df.columns else 0)

    st.subheader("📅 แนวโน้มรายเดือน (จำนวนเคส) แยกตาม SUP")
    if "MonthKey" in df.columns and "SUP" in df.columns:
        monthly_sup = df.groupby(["MonthKey", "SUP"]).size().reset_index(name="Count")
        fig = px.line(monthly_sup, x="MonthKey", y="Count", color="SUP", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("💡 คำแนะนำอัตโนมัติ (Advisor)")
    if "SUP" in df.columns and "Defect" in df.columns:
        advisor_unique = df[["SUP", "Defect", "Advice"]].drop_duplicates()
        st.dataframe(advisor_unique, hide_index=True)

    st.subheader("📥 Export ข้อมูล")
    excel_data = to_excel(df)
    st.download_button("ดาวน์โหลด Excel", excel_data, "claim_roll.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    pdf_data = generate_pdf(df)
    st.download_button("ดาวน์โหลด PDF", pdf_data, "claim_roll.pdf", mime="application/pdf")

# -----------------------------
# ฟังก์ชัน: เคลมแผ่น (โครงสร้างพร้อมต่อยอด)
# -----------------------------
def process_claim_sheet(df):
    st.title("📊 รายงานวิเคราะห์ข้อบกพร่องจากเคลมแผ่น")
    st.info("⚙️ ยังไม่ได้กำหนด logic สำหรับเคลมแผ่น กรุณาส่งโครงสร้างคอลัมน์มาให้ผมช่วยเขียนต่อได้เลยครับ")

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
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="รายงานวิเคราะห์ข้อบกพร่อง", ln=True, align="C")
    for i, row in df.iterrows():
        line = f"{row.get('SUP','')} - {row.get('Defect','')}"
        pdf.cell(200, 10, txt=line, ln=True)
    return pdf.output(dest="S").encode("latin-1")
