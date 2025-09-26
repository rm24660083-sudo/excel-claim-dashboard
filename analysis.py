import pandas as pd
import numpy as np

def load_excel(file) -> pd.DataFrame:
    # รองรับ Excel ที่มี header ภาษาไทยและวันที่หลากหลาย
    df = pd.read_excel(file, engine="openpyxl")
    # จัดคอลัมน์ให้ชื่อมาตรฐาน (หากชื่อไม่ตรงให้ปรับ mapping ตรงนี้)
    rename_map = {
        "SUP": "SUP",
        "เดือน": "Month",
        "Month": "Month",
        "Week": "Week",
        "วันที่ส่งของ": "ShipDate",
        "วันที่ออก": "IssueDate",
        "เลขที่เอกสาร": "DocNo",
        "เลขที่ส่งของ": "ShipNo",
        "เกรดแกรม": "Grade",
        "หน้ากว้าง": "Width",
        "Lot": "Lot",
        "น้ำหนัก": "Weight",
        "Code": "Code",
        "สิ่งที่ไม่เป็นไปตามข้อกำหนด": "Defect",
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

    # แปลงวันที่ให้เป็น datetime อย่างปลอดภัย
    for col in ["ShipDate", "IssueDate"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    # Month/Week ถ้ายังไม่มี จะคำนวณจาก ShipDate (หรือ IssueDate)
    if "Month" not in df.columns:
        base = df["ShipDate"] if "ShipDate" in df.columns else df["IssueDate"]
        df["Month"] = base.dt.month
    if "Week" not in df.columns:
        base = df["ShipDate"] if "ShipDate" in df.columns else df["IssueDate"]
        df["Week"] = base.dt.isocalendar().week

    # Quarter สำหรับการวิเคราะห์รายไตรมาส
    if "Quarter" not in df.columns:
        base = df["ShipDate"] if "ShipDate" in df.columns else df["IssueDate"]
        df["Quarter"] = base.dt.quarter

    # สะอาดข้อมูลเบื้องต้น
    # Trim ชิดซ้าย-ขวา และ normalize defect text
    if "Defect" in df.columns:
        df["Defect"] = df["Defect"].astype(str).str.strip()

    return df


def defect_counts_by_sup(df: pd.DataFrame):
    if "SUP" in df.columns and "Defect" in df.columns:
        return df.groupby("SUP")["Defect"].count().reset_index(name="DefectCount")
    return pd.DataFrame()


def defect_counts_by_month(df: pd.DataFrame):
    if "Month" in df.columns and "Defect" in df.columns:
        return df.groupby("Month")["Defect"].count().reset_index(name="DefectCount")
    return pd.DataFrame()


def defect_counts_by_quarter(df: pd.DataFrame):
    if "Quarter" in df.columns and "Defect" in df.columns:
        return df.groupby("Quarter")["Defect"].count().reset_index(name="DefectCount")
    return pd.DataFrame()


def top_defects(df: pd.DataFrame, top_n=10):
    if "Defect" not in df.columns:
        return pd.DataFrame()
    return (
        df["Defect"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Defect", "Defect": "Count"})
        .head(top_n)
    )


def iqr_outliers(series: pd.Series):
    # ตรวจ outlier ด้วย IQR
    s = pd.to_numeric(series, errors="coerce")
    s = s.dropna()
    if s.empty:
        return 0, (None, None)
    q1, q3 = np.percentile(s, [25, 75])
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outlier_count = ((s < low) | (s > high)).sum()
    return outlier_count, (low, high)


def risk_assessment_oct_q4(df: pd.DataFrame):
    # วิเคราะห์เจาะจง October (เดือน 10) และ Q4 (ไตรมาส 4)
    res = {}
    if "Month" in df.columns:
        res["Oct_Defects"] = int(df[df["Month"] == 10].shape[0])
    if "Quarter" in df.columns:
        res["Q4_Defects"] = int(df[df["Quarter"] == 4].shape[0])
    # วิเคราะห์ defect type ใน Oct/Q4
    for label, cond in [("Oct", df["Month"] == 10 if "Month" in df.columns else None),
                        ("Q4", df["Quarter"] == 4 if "Quarter" in df.columns else None)]:
        if cond is not None and "Defect" in df.columns:
            res[f"{label}_TopDefects"] = (
                df[cond]["Defect"].value_counts().head(5).to_dict()
            )
        else:
            res[f"{label}_TopDefects"] = {}
    return res