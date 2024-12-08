import streamlit as st
import openai
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# ตั้งค่า Sidebar สำหรับ API Key
st.sidebar.title("API Key")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
if not api_key:
    st.warning("Please enter your API key to proceed.")
else:
    openai.api_key = api_key

# หัวข้อหลักของแอป
st.title("Japanese Content Analyzer")
st.write("**ใส่ข้อความภาษาญี่ปุ่น หรือ ลิงก์ของบทความ/เนื้อหาใด ๆ** -> **แปลและวิเคราะห์คำศัพท์**")

# Input: ข้อความหรือลิงก์
user_input = st.text_area("กรอกข้อความหรือใส่ลิงก์ภาษาญี่ปุ่นที่นี่:")

if st.button("เริ่มวิเคราะห์"):
    if user_input:
        # ตรวจสอบว่าเป็นลิงก์หรือข้อความ
        parsed = urlparse(user_input)
        if parsed.scheme and parsed.netloc:  # ตรวจสอบว่าเป็น URL
            st.write("**Input นี้เป็นลิงก์**")
            try:
                # ดึงข้อมูลจากลิงก์
                response = requests.get(user_input)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # พยายามดึงเนื้อหาหลัก
                possible_tags = ['article', 'div', 'main', 'section']  # แท็กที่มักใช้ในเนื้อหาหลัก
                japanese_text = None
                for tag in possible_tags:
                    content = soup.find(tag)
                    if content:
                        japanese_text = content.get_text(strip=True)
                        break

                if not japanese_text:
                    st.error("ไม่สามารถดึงเนื้อหาหลักจากลิงก์ได้ กรุณาลองลิงก์อื่น")
                else:
                    st.write("### เนื้อหาที่ดึงมา:")
                    st.write(japanese_text)
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลจากลิงก์: {e}")
                japanese_text = None
        else:
            st.write("**Input นี้เป็นข้อความธรรมดา**")
            japanese_text = user_input

        # หากดึงข้อความสำเร็จ
        if japanese_text:
            # แปลข้อความ
            st.write("### การแปลข้อความทั้งหมด")
            translation_prompt = f"แปลข้อความนี้จากภาษาญี่ปุ่นเป็นภาษาไทย:\n{japanese_text}"
            try:
                translation = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": translation_prompt}]
                )['choices'][0]['message']['content']
                st.write(translation)
            except Exception as e:
                st.error(f"การแปลข้อความล้มเหลว: {e}")

            # วิเคราะห์คำศัพท์
            st.write("### คำศัพท์ที่แยกตามระดับความยาก")
            vocab_prompt = (
                f"จากข้อความด้านล่างนี้ ให้คุณรวบรวมคำศัพท์ให้มากที่สุดที่มีระดับความยาก N3, N2, และ N1 "
                f"โดยจัดทำในรูปแบบตารางแยกตามระดับความยาก (N3, N2, N1) "
                f"แต่ละรายการในตารางให้ประกอบด้วย:\n"
                f"1. คำศัพท์\n"
                f"2. คำอ่าน (Hiragana และในวงเล็บ Romaji)\n"
                f"3. คำแปล\n"
                f"4. ตัวอย่างการใช้ในประโยค (พร้อมแปลประโยคเป็นภาษาไทย)\n\n"
                f"ข้อความ:\n{japanese_text}"
            )
            try:
                vocab_response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": vocab_prompt}]
                )['choices'][0]['message']['content']

                # แยกคำศัพท์ตามระดับความยาก
                tables = {"N3": [], "N2": [], "N1": []}
                for line in vocab_response.split('\n'):
                    if line.startswith("N3:"):
                        tables["N3"].append(line[3:].split('\t'))
                    elif line.startswith("N2:"):
                        tables["N2"].append(line[3:].split('\t'))
                    elif line.startswith("N1:"):
                        tables["N1"].append(line[3:].split('\t'))

                # แสดงผลคำศัพท์สำหรับแต่ละระดับ
                for level, data in tables.items():
                    if data:
                        st.write(f"#### คำศัพท์ระดับ {level}")
                        df = pd.DataFrame(data, columns=["คำศัพท์", "คำอ่าน (Hiragana และ Romaji)", "คำแปล", "ตัวอย่างการใช้ในประโยค"])
                        st.dataframe(df)

                        # ดาวน์โหลดคำศัพท์ในแต่ละระดับ
                        csv = df.to_csv(index=False)
                        st.download_button(f"ดาวน์โหลดคำศัพท์ระดับ {level} เป็น CSV", data=csv, file_name=f"vocabulary_{level}.csv", mime="text/csv")
                    else:
                        st.write(f"ไม่มีคำศัพท์ในระดับ {level}")
            except Exception as e:
                st.error(f"การวิเคราะห์คำศัพท์ล้มเหลว: {e}")
    else:
        st.warning("กรุณากรอกข้อความหรือใส่ลิงก์ก่อนเริ่มทำงาน")
