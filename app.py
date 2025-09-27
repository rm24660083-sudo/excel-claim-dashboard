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

st.markdown(
    """
    <div style="text-align:left;">
        <img src="Logo.png" width="120">
        <div style="font-size:16px; font-weight:bold; margin-top:5px;">
            Powered by <span style="color:#d62728;">The Beyonder RM</span>
        </div>
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
uploaded_file = st.file_uploader("📄 อัปโหลดไฟล์ Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Rename columns
    rename_map = {
        "SUP": "SUP", "ซัพพลายเออร์": "SUP", "Supplier": "SUP",
        "สิ่งที่ไม่เป็นไปตามข้อกำหนด": "Defect", "ข้อบกพร่อง": "Defect", "อาการ": "Defect",
        "เกรดแกรม": "Grade", "Grade": "Grade",
        "วันที่ออก": "Date", "Date": "Date", "วันที่เอกสาร": "Date",
        "Lot": "Lot", "Code": "Code", "วันที่ส่งของ": "ShipDate"
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
    if "Defect" in df.columns:
        df["RootCause"] = df["Defect"].apply(map_root_cause)
        df["Advice"] = df["Defect"].apply(advise_for)

    # -----------------------------
    # KPI Cards (ส่วนที่ 1)
    # -----------------------------
    st.subheader("📌 สรุปภาพรวม")
    col1, col2, col3 = st.columns(3)
    col1.metric("จำนวนรายการข้อบกพร่อง", len(df))
    col2.metric("ซัพพลายเออร์ที่เกี่ยวข้อง", df["SUP"].nunique() if "SUP" in df.columns else 0)
    col3.metric("ประเภทข้อบกพร่องที่พบ", df["Defect"].nunique() if "Defect" in df.columns else 0)

        # -----------------------------
    # Supplier Bar
    # -----------------------------
    st.subheader("🏭 อันดับ SUP โดยจำนวนข้อบกพร่อง (Top 12)")
    if "SUP" in df.columns:
        sup_count = (
            df.groupby("SUP")
              .size()
              .reset_index(name="Count")
              .sort_values("Count", ascending=False)
              .head(12)
        )
        fig1 = px.bar(
            sup_count,
            x="SUP",
            y="Count",
            text="Count",
            title="จำนวน defect ต่อ SUP"
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("⚠️ ไม่พบคอลัมน์ SUP ในไฟล์")

    # -----------------------------
    # Defect Pie
    # -----------------------------
    st.subheader("🧩 สัดส่วนประเภทข้อบกพร่อง (Top 12)")
    if "Defect" in df.columns:
        defect_count = (
            df.groupby("Defect")
              .size()
              .reset_index(name="Count")
              .sort_values("Count", ascending=False)
              .head(12)
        )
        fig2 = px.pie(
            defect_count,
            names="Defect",
            values="Count",
            title="Defect Breakdown"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("⚠️ ไม่พบคอลัมน์ Defect ในไฟล์")


    # -----------------------------
    # Monthly Trend
    # -----------------------------
    st.subheader("📅 แนวโน้มรายเดือน (จำนวนเคส)")
    if "MonthKey" in df.columns:
        monthly = (
            df.groupby("MonthKey")
              .size()
              .reset_index(name="Count")
              .sort_values("MonthKey")
        )
        fig3 = px.line(
            monthly,
            x="MonthKey",
            y="Count",
            markers=True,
            title="จำนวน defect รายเดือน"
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("⚠️ ไม่พบคอลัมน์ MonthKey")

    # -----------------------------
    # Top Defect by Supplier (go.Bar เวอร์ชันแท่งหนา)
    # -----------------------------
    import plotly.graph_objects as go

    st.subheader("🔥 ประเภทอาการเด่นของแต่ละ SUP (Top 8)")
    if "SUP" in df.columns and "Defect" in df.columns:
        sup_summary = df.groupby(["SUP","Defect"]).size().reset_index(name="Count")
        # เลือก SUP ที่มี defect รวมสูงสุด 8 ราย
        top_sups = (
            sup_summary.groupby("SUP")["Count"]
            .sum()
            .sort_values(ascending=False)
            .head(8)
            .index
        )
        df_top = sup_summary[sup_summary["SUP"].isin(top_sups)]

        fig4 = go.Figure()

        # วาดแท่ง defect แยกสี และกำหนดความกว้างแท่ง
        for defect in df_top["Defect"].unique():
            sub = df_top[df_top["Defect"] == defect]
            fig4.add_trace(go.Bar(
                x=sub["SUP"],
                y=sub["Count"],
                name=defect,
                width=0.1   # 👈 ปรับตรงนี้ (0–1) ค่าใหญ่ = แท่งหนา (0.8 ~ หนาขึ้น 2 เท่า)
            ))

        fig4.update_layout(
            barmode="group",
            bargap=0.05,       # ช่องว่างระหว่างกลุ่ม SUP
            bargroupgap=0.02,  # ช่องว่างระหว่างแท่งในกลุ่มเดียวกัน
            height=700,
            title="Top 8 SUP และอาการเด่น"
        )

        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("⚠️ ไม่พบคอลัมน์ SUP หรือ Defect")

    # -----------------------------
    # Summary Table
    # -----------------------------
    st.subheader("📊 ตารางสรุปตาม SUP")

    if "SUP" in df.columns and "Defect" in df.columns:
        summary = []
        for sup, g in df.groupby("SUP"):
            total = len(g)
            # Top 3 อาการ
            top3 = g["Defect"].value_counts().head(3).to_dict()
            top3_str = ", ".join([f"{k} ({v})" for k, v in top3.items()])
            # เดือนล่าสุด
            latest_month = g["MonthKey"].max() if "MonthKey" in g.columns else None
            latest_count = len(g[g["MonthKey"] == latest_month]) if latest_month else 0
            summary.append({
                "SUP": sup,
                "รวมเคส": total,
                "Top 3 อาการ": top3_str,
                "เดือนล่าสุด": f"{latest_month}: {latest_count}" if latest_month else "-"
            })

        summary_df = pd.DataFrame(summary).sort_values("รวมเคส", ascending=False)
        st.dataframe(summary_df, hide_index=True)
    else:
        st.warning("⚠️ ไม่พบคอลัมน์ SUP หรือ Defect")

    # -----------------------------
    # Watchlist SUP
    # -----------------------------
    st.subheader("⚠️ Watchlist SUP ที่ควรระวัง")

    if "SUP" in df.columns and "MonthKey" in df.columns:
        sup_stats = []
        for sup, g in df.groupby("SUP"):
            total = len(g)
            # 3 เดือนล่าสุด
            last3_keys = sorted(g["MonthKey"].dropna().unique())[-3:]
            last3_sum = len(g[g["MonthKey"].isin(last3_keys)])
            top_def = g["Defect"].value_counts().idxmax() if not g["Defect"].empty else "-"
            sup_stats.append({
                "SUP": sup,
                "รวมทั้งปี": total,
                "3 เดือนล่าสุด": last3_sum,
                "อาการเด่น": top_def
            })

        watchlist = pd.DataFrame(sup_stats)
        median_val = watchlist["รวมทั้งปี"].median()
        # เกณฑ์: รวมทั้งปี > median หรือ 3 เดือนล่าสุด >= 1/4 ของทั้งหมด
        watchlist = watchlist[
            (watchlist["รวมทั้งปี"] > median_val) |
            (watchlist["3 เดือนล่าสุด"] >= watchlist["รวมทั้งปี"]/4)
        ]
        watchlist = watchlist.sort_values("3 เดือนล่าสุด", ascending=False).head(10)
        st.dataframe(watchlist, hide_index=True)
    else:
        st.warning("⚠️ ไม่พบคอลัมน์ SUP หรือ MonthKey")


        # -----------------------------
    # Month 10 Watchouts
    # -----------------------------
    st.subheader("📌 อาการ/สาเหตุที่ควรเฝ้าระวังในเดือน 10")

    if "Month" in df.columns and "Defect" in df.columns:
        # เลือก 3 เดือนล่าสุด
        recent = df[df["Month"] >= (df["Month"].max() - 2)]
        by_def_recent = recent["Defect"].value_counts().head(8)

        # จัดกลุ่ม defect ตาม root cause
        grouped = {}
        for defect in by_def_recent.index:
            cause = map_root_cause(defect)
            grouped.setdefault(cause, []).append(defect)

        for cause, defs in grouped.items():
            st.write(f"**{cause}** — อาการที่พบ: {', '.join(defs[:4])}")

        # Extra tips (เหมือนใน HTML เดิม)
        extra = [
            "สันนูน/รอยเส้น/เศษกรีด: ทวนสภาพใบมีด-แรงกด-แนว Slitting และ tension ช่วงต้น-ท้ายม้วน",
            "Calender mark/จุดดำ: ตรวจความสะอาดลูกกลิ้ง การไหลของเยื่อ/รีเจ็ครีไซเคิล และแผนทำความสะอาด",
            "ความชื้น/Cobb: ยืนยันโปรไฟล์อบ, ควบคุม RH โกดัง, บรรจุห่อกันชื้น",
            "Bursting: ทบทวนไฟเบอร์/เคมี, targeting basis weight และการกดรีด",
            "หน้ากว้าง/แกรม: ตรวจตั้งค่า Trim/เครื่องชั่ง และการสอบเทียบอย่างน้อยรายสัปดาห์"
        ]
        st.markdown("**คำแนะนำเพิ่มเติม:**")
        for tip in extra:
            st.write(f"- {tip}")
    else:
        st.warning("⚠️ ไม่พบคอลัมน์ Month หรือ Defect")

    # -----------------------------
    # Advisor Column (Unique per SUP + Defect)
    # -----------------------------
    st.subheader("💡 คำแนะนำอัตโนมัติ (Advisor)")

    if "SUP" in df.columns and "Defect" in df.columns:
        df["Advice"] = df["Defect"].apply(advise_for)

        # ลบแถวที่ซ้ำกัน (SUP + Defect + Advice)
        advisor_unique = df[["SUP","Defect","Advice"]].drop_duplicates()

        # เรียงให้อ่านง่าย
        advisor_unique = advisor_unique.sort_values(["SUP","Defect"])

        st.dataframe(advisor_unique, hide_index=True)
    else:
        st.warning("⚠️ ไม่พบคอลัมน์ SUP หรือ Defect")

    # -----------------------------
    # Detail Table (ปรับให้รวมซ้ำ)
    # -----------------------------
    st.subheader("📋 รายละเอียดข้อผิดพลาดตาม SUP")

    if all(col in df.columns for col in ["SUP","Defect","Advice","Grade"]):
        # รวมข้อมูลตาม SUP + Defect + Advice + Grade
        detail = (
            df.groupby(["SUP","Defect","Advice","Grade"])
              .size()
              .reset_index(name="จำนวนเคส")
              .sort_values(["SUP","Defect"])
        )

        st.dataframe(detail, hide_index=True)
    else:
        st.warning("⚠️ ไม่พบคอลัมน์ SUP / Defect / Advice / Grade")

        # -----------------------------
    # Utility Functions (Python version)
    # -----------------------------
    import numpy as np
    import html

    def median(arr):
        """หาค่ามัธยฐานของ list/Series"""
        if len(arr) == 0:
            return 0
        return float(np.median(arr))

    def escape_html(s):
        """Escape อักขระพิเศษ ป้องกัน HTML injection"""
        return html.escape(str(s))




