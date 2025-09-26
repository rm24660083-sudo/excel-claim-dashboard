def generate_ai_tips(df):
    tips = []

    # โครงสร้างคอลัมน์
    required_cols = ["SUP", "Defect", "Month", "Week"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        tips.append(f"⚠️ คอลัมน์ขาด: {', '.join(missing)} — โปรดตรวจแหล่งข้อมูลหรือ mapping ชื่อคอลัมน์")

    # ข้อมูลวันที่
    if "ShipDate" in df.columns and df["ShipDate"].isna().mean() > 0.2:
        tips.append("⚠️ วันที่ส่งของ (ShipDate) มีค่าไม่สามารถแปลงเป็นวันที่ได้จำนวนมาก — รูปแบบวันที่อาจไม่สม่ำเสมอ")

    # ความเสี่ยงรายเดือน/รายไตรมาส
    if "Month" in df.columns:
        oct_count = int((df["Month"] == 10).sum())
        if oct_count > 0:
            tips.append(f"🔎 เดือนตุลาคมพบเคส {oct_count} รายการ — แนะนำวิเคราะห์สาเหตุเชิงลึกและวางแผน Q4")
    if "Quarter" in df.columns:
        q4_count = int((df["Quarter"] == 4).sum())
        if q4_count > 0:
            tips.append(f"🔎 Q4 พบเคส {q4_count} รายการ — ตรวจความพร้อมซัพพลายเออร์และกระบวนการก่อน peak")

    # รูปแบบ defect ที่พบซ้ำ
    if "Defect" in df.columns:
        common = df["Defect"].value_counts().head(3).index.tolist()
        if common:
            tips.append(f"📌 Defect ที่พบมาก: {', '.join(common)} — จัดทำมาตรการป้องกันที่จุดเกิดเหตุ")

    # ซัพพลายเออร์ที่มีเคสสูง
    if "SUP" in df.columns:
        sup_count = df["SUP"].value_counts()
        if not sup_count.empty:
            worst_sup = sup_count.idxmax()
            tips.append(f"🏭 SUP ที่มีเคสสูงสุด: {worst_sup} — แนะนำทำ CAPA ร่วมกันและตั้ง KPI รายไตรมาส")

    # ขนาดหน้ากว้าง/น้ำหนัก outlier
    for col in ["Width", "Weight"]:
        if col in df.columns:
            from analysis import iqr_outliers
            outliers, (low, high) = iqr_outliers(df[col])
            if outliers > 0:
                tips.append(f"📈 ค่าผิดปกติใน {col}: {outliers} รายการ — ช่วงคาดหวัง ~ {low:.2f} ถึง {high:.2f}")

    # ข้อแนะนำปฏิบัติ
    tips.append("✅ แนะนำตั้ง validation เมื่อรับข้อมูล: ตรวจชื่อคอลัมน์, วันที่, และประเภทค่า เพื่อป้องกัน error ในการสรุปผล")
    tips.append("🧪 ใช้การทดสอบ A/B กับแนวทางแก้ไขที่จุด defect สูง และติดตามผลรายสัปดาห์/รายไตรมาส")
    return tips