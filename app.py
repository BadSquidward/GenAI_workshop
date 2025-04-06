import streamlit as st
import pandas as pd
import google.generativeai as genai

# ตั้งค่าหน้าแอป
st.title('AI Chat Bot with CSV Analysis')

# ตั้งค่า session state สำหรับเก็บประวัติแชทและข้อมูล CSV
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None

# ตั้งค่า Gemini API
try:
    key = st.secrets['gemini_api_key']
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    # ส่วนอัปโหลดไฟล์ CSV
    st.subheader("Upload CSV for Analysis")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            # โหลดไฟล์ CSV ที่อัปโหลด
            st.session_state.uploaded_data = pd.read_csv(uploaded_file)
            st.success("File successfully uploaded and read.")
            
            # แสดงตัวอย่างข้อมูล
            st.write("### Uploaded Data Preview")
            st.dataframe(st.session_state.uploaded_data.head())
            
            # เพิ่มคำอธิบายของข้อมูล
            data_dict_text = "\n".join([
                f"- {col}: {st.session_state.uploaded_data[col].dtype}. Column {col}"
                for col in st.session_state.uploaded_data.columns
            ])
            st.session_state.data_dict_text = data_dict_text
            
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    # Checkbox สำหรับเลือกว่าจะวิเคราะห์ข้อมูลหรือไม่
    analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")
    
    # แสดงประวัติการแชท
    for message in st.session_state.chat_history:
        role, content = message
        st.chat_message(role).markdown(content)
    
    # รับข้อความจากผู้ใช้
    if user_input := st.chat_input("Type your message here..."):
        # เก็บและแสดงข้อความของผู้ใช้
        st.session_state.chat_history.append(("user", user_input))
        st.chat_message("user").markdown(user_input)
        
        try:
            # ตรวจสอบว่าผู้ใช้ต้องการวิเคราะห์ข้อมูลหรือไม่
            if st.session_state.uploaded_data is not None and analyze_data_checkbox:
                # ตรวจสอบว่าผู้ใช้ต้องการวิเคราะห์หรือขอข้อมูลเชิงลึก
                if any(keyword in user_input.lower() for keyword in ["analyze", "insight", "data"]):
                    # สร้างคำอธิบายข้อมูลสำหรับโมเดล AI
                    data_description = st.session_state.uploaded_data.describe().to_string()
                    example_record = st.session_state.uploaded_data.head(2).to_string()
                    
                    # สร้าง prompt สำหรับ RAG
                    prompt = f"""
                    You are a helpful Python code generator.
                    Your goal is to answer the user's question by analyzing the provided data.
                    
                    Here's the context:
                    **User Question:**
                    {user_input}
                    
                    **DataFrame Details:**
                    {st.session_state.data_dict_text}
                    
                    **Sample Data (Top 2 Rows):**
                    {example_record}
                    
                    **Data Summary:**
                    {data_description}
                    
                    Based on this information, please:
                    1. Write Python code that addresses the user's question
                    2. Execute the code to get the answer
                    3. Explain the results in a way that's easy to understand
                    """
                    
                    # สร้างคำตอบจาก AI สำหรับการวิเคราะห์ข้อมูล
                    response = model.generate_content(prompt)
                    bot_response = response.text
                else:
                    # พูดคุยปกติกับบอท
                    response = model.generate_content(user_input)
                    bot_response = response.text
            elif not analyze_data_checkbox and st.session_state.uploaded_data is not None:
                # แจ้งว่าการวิเคราะห์ไม่ได้เปิดใช้งาน
                bot_response = 'Data analysis is disabled. Please select the "Analyze CSV Data with AI" checkbox to enable analysis.'
            else:
                # แจ้งให้อัปโหลดไฟล์ CSV ก่อน
                bot_response = "Please upload a CSV file first, then ask me to analyze it."
            
            # เก็บและแสดงคำตอบจากบอท
            st.session_state.chat_history.append(("assistant", bot_response))
            st.chat_message("assistant").markdown(bot_response)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            
except Exception as e:
    st.error(f'Error initializing Gemini API: {e}')
