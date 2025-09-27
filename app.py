import streamlit as st

st.set_page_config(page_title="📊 ระบบวิเคราะห์ข้อบกพร่อง", layout="wide")

# -----------------------------
# ส่วนหัว + โลโก้มุมขวาบน
# -----------------------------
col1, col2 = st.columns([4, 1])  # col1 กว้างกว่า col2

with col1:
    st.title("📊 ระบบวิเคราะห์ข้อบกพร่อง")

with col2:
    st.markdown(
        """
        <div style="display:flex; flex-direction:column; align-items:center;">
            <img src="Logo.png" style="width:80px; margin-bottom:8px;">
            <div style="font-size:12px; color:gray; text-align:center;">
                Powered By <br>
                <b>ยุทธพิชัย ไก่ฟ้า</b><br>
                หัวหน้าแผนก Sup-Rawmaterial
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# เนื้อหาหน้าแรก
# -----------------------------
st.markdown("""
เลือกเมนูด้านซ้ายเพื่อเข้าสู่การวิเคราะห์:

- 📑 **เคลมม้วน**  
- 📑 **เคลมแผ่น**
""")









