import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import re
import html

# -----------------------------
# Config
# -----------------------------

st.set_page_config(page_title="📊 วิเคราะห์ปัญหาเคลมแผ่น", layout="wide")

# -----------------------------
# Logo + Credit (เหนือ Title)
# -----------------------------
import streamlit as st
import os

# หา path ของไฟล์ Logo.png ที่อยู่โฟลเดอร์เดียวกับ app.py
logo_path = os.path.join(os.path.dirname(__file__), "Logo.png")

# แสดงโลโก้
st.image(logo_path, width=120)

# แสดงเครดิตใต้โลโก้
st.markdown(
    """
    <div style="font-size:16px; font-weight:bold; margin-top:5px;">
        Powered by <span style="color:#d62728;">ยุทธพิชัย ไก่ฟ้า หัวหน้าแผนก Sup-Ramaterial</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.title("📊 รายงานวิเคราะห์ข้อบกพร่องจากเคลมม้วน")
# -----------------------------
# Utility Functions (ส่วนที่ 7)
# -----------------------------
def median(arr):
    if len(arr) == 0:
        return 0
    return float(np.median(arr))

def escape_html(s):
    return html.escape(str(s))

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
# Upload file (ส่วนที่ 1)
# -----------------------------
# 🔹 เลือกประเภทไฟล์ก่อนอัปโหลด
file_type = st.selectbox("📂 เลือกประเภทข้อมูล", ["เคลมม้วน", "เคลมแผ่น"])
uploaded_file = st.file_uploader("📄 อัปโหลดไฟล์ Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if file_type == "เคลมม้วน":
        # 🔹 เคลมม้วน: Rename + Date
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
            df["Month"] = None
            df["Quarter"] = None

        df["RootCause"] = df["Defect"].apply(map_root_cause)
        df["Advice"] = df["Defect"].apply(advise_for)

        # 🔹 เคลมม้วน: กราฟและตาราง
        st.subheader("📌 สรุปภาพรวม")
        col1, col2, col3 = st.columns(3)
        col1.metric("จำนวนรายการข้อบกพร่อง", len(df))
        col2.metric("ซัพพลายเออร์ที่เกี่ยวข้อง", df["SUP"].nunique())
        col3.metric("ประเภทข้อบกพร่องที่พบ", df["Defect"].nunique())

        st.subheader("🏭 อันดับ SUP โดยจำนวนข้อบกพร่อง (Top 12)")
        sup_count = df.groupby("SUP").size().reset_index(name="Count").sort_values("Count", ascending=False).head(12)
        fig1 = px.bar(sup_count, x="SUP", y="Count", text="Count", title="จำนวน defect ต่อ SUP")
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("🧩 สัดส่วนประเภทข้อบกพร่อง (Top 12)")
        defect_count = df.groupby("Defect").size().reset_index(name="Count").sort_values("Count", ascending=False).head(12)
        fig2 = px.pie(defect_count, names="Defect", values="Count", title="Defect Breakdown")
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📅 แนวโน้มรายเดือน (จำนวนเคส) แยกตาม SUP")
        monthly_sup = df.groupby(["MonthKey", "SUP"]).size().reset_index(name="Count").sort_values("MonthKey")
        fig3 = px.line(monthly_sup, x="MonthKey", y="Count", color="SUP", markers=True, title="จำนวน defect รายเดือนแยกตาม SUP")
        fig3.update_layout(xaxis_title="เดือน", yaxis_title="จำนวนเคส", legend_title="SUP", height=500)
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("💡 คำแนะนำอัตโนมัติ (Advisor)")
        advisor_unique = df[["SUP", "Defect", "Advice"]].drop_duplicates().sort_values(["SUP", "Defect"])
        st.dataframe(advisor_unique, hide_index=True)

        st.subheader("📋 รายละเอียดข้อผิดพลาดตาม SUP")
        detail = df.groupby(["SUP", "Defect", "Advice", "Grade"]).size().reset_index(name="จำนวนเคส").sort_values(["SUP", "Defect"])
        st.dataframe(detail, hide_index=True)

        # 🔮 วิเคราะห์ล่วงหน้าเคลมม้วน
        st.subheader("🔮 ข้อควรระวังล่วงหน้าในเดือนถัดไป")
        if "Month" in df.columns and "SUP" in df.columns and "Defect" in df.columns:
            recent_months = sorted(df["Month"].dropna().unique())[-3:]
            recent_df = df[df["Month"].isin(recent_months)]

            sup_trend = recent_df.groupby(["Month", "SUP"]).size().reset_index(name="Count")
            sup_pivot = sup_trend.pivot(index="SUP", columns="Month", values="Count").fillna(0)

            rising_sups = [sup for sup, row in sup_pivot.iterrows() if len(row) >= 3 and row[2] > row[1] > row[0]]

            defect_trend = recent_df.groupby(["Month", "Defect"]).size().reset_index(name="Count")
            defect_pivot = defect_trend.pivot(index="Defect", columns="Month", values="Count").fillna(0)

            persistent_defects = [defect for defect, row in defect_pivot.iterrows() if len(row) >= 2 and row[-1] > 0 and row[-2] > 0]

            if rising_sups:
                st.markdown("**SUP ที่ควรเฝ้าระวังเป็นพิเศษ:**")
                for sup in rising_sups:
                    recent_defects = recent_df[recent_df["SUP"] == sup]["Defect"].value_counts().head(2).index.tolist()
                    st.write(f"- 🏭 `{sup}` → อาการเด่น: {', '.join(recent_defects)}")

            if persistent_defects:
                st.markdown("**อาการที่ยังพบต่อเนื่องและควรติดตาม:**")
                for defect in persistent_defects:
                    cause = map_root_cause(defect)
                    advice = advise_for(defect)
                    st.write(f"- ⚠️ `{defect}` → สาเหตุ: **{cause}** → แนวทางป้องกัน: _{advice}_")

            if not rising_sups and not persistent_defects:
                st.info("✅ ไม่พบแนวโน้ม SUP หรืออาการที่ควรเฝ้าระวังเป็นพิเศษในเดือนถัดไป")
        else:
            st.warning("⚠️ ไม่พบคอลัมน์ Month / SUP / Defect")

    elif file_type == "เคลมแผ่น":
        # 🔹 เคลมแผ่น: Rename + Date
        rename_map_sheet = {
            "Supplier": "SUP",
            "DefectType": "Defect",
            "Grade": "Grade",
            "Date": "Date",
            "Lot": "Lot",
            "Thickness": "Thickness",
            "Size": "Size",
            "ClaimReason": "Reason"
        }
        df = df.rename(columns={c: rename_map_sheet.get(c, c) for c in df.columns})

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
            df["MonthKey"] = df["Date"].dt.strftime("%Y-%m")
            df["Month"] = df["Date"].dt.month
            df["Quarter"] = df["Date"].dt.quarter
        else:
            df["MonthKey"] = "ไม่ระบุ"
            df["Month"] = None
            df["Quarter"] = None

        df["RootCause"] = df["Defect"].apply(map_root_cause)
        df["Advice"] = df["Defect"].apply(advise_for)

        # 🔹 เคลมแผ่น: วิเคราะห์ตาม 5 ข้อ
        # (คุณสามารถวางบล็อกวิเคราะห์ที่ผมจัดให้ก่อนหน้านี้ในส่วนนี้ได้เลย)
