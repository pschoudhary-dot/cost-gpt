import streamlit as st
from openai import OpenAI
import os
import bcrypt
import pdfkit
import json
import time
from dotenv import load_dotenv
from database import SessionLocal, User, ChatHistory
from sqlalchemy.orm import sessionmaker
from io import BytesIO

# Load environment variables
load_dotenv()
API_KEY = "ddc-rCd0jZ1ddZFNkv6qT3ahJkAfZgW43HjRBvu8Qzxuo29Vac4z0V"
BASE_URL = "https://api.sree.shop/v1"

# OpenAI Client Setup
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# Load Supported Models
model_data = {
    "data": [
        {"id": "claude-3-5-sonnet-20240620", "cost": 15},
        {"id": "claude-3-5-sonnet", "cost": 15},
        {"id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", "cost": 2},
        {"id": "deepseek-r1", "cost": 2.19},
        {"id": "deepseek-v3", "cost": 1.28},
        {"id": "gpt-4o", "cost": 5},
        {"id": "gpt-4o-2024-05-13", "cost": 5},
        {"id": "Meta-Llama-3.3-70B-Instruct-Turbo", "cost": 0.3}
    ]
}

# Extract model names and costs
model_options = {model["id"]: model["cost"] for model in model_data["data"]}

# Database Setup
Session = sessionmaker(bind=SessionLocal().bind)
db = Session()

# Streamlit UI
st.set_page_config(page_title="CostGPT", page_icon="💰", layout="wide")

# Sidebar for AI Model Selection
st.sidebar.title("⚙️ Settings")
st.sidebar.header("🤖 AI Model Selection")

# Allow user to choose a model and show cost
selected_model = st.sidebar.selectbox(
    "Choose AI Model",
    options=model_options.keys(),
    format_func=lambda x: f"{x} (${model_options[x]}/M tokens)"
)

# User authentication state
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "show_logout_popup" not in st.session_state:
    st.session_state.show_logout_popup = False

# Function to verify password
def verify_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

# Sidebar User Section
if st.session_state.user_id:
    user = db.query(User).filter(User.id == st.session_state.user_id).first()
    st.sidebar.subheader(f"👤 Welcome, {user.email}")

    # Logout Button with Confirmation
    if st.sidebar.button("🚪 Logout"):
        st.session_state.show_logout_popup = True

    if st.session_state.show_logout_popup:
        st.sidebar.warning("Are you sure you want to log out?")
        col1, col2 = st.sidebar.columns(2)
        if col1.button("✅ Yes"):
            st.session_state.user_id = None
            st.session_state.show_logout_popup = False
            st.rerun()
        if col2.button("❌ No"):
            st.session_state.show_logout_popup = False

else:
    # Authentication UI in Sidebar
    sidebar_tabs = st.sidebar.tabs(["🔑 Login", "📝 Signup"])

    # Login
    with sidebar_tabs[0]:
        st.write("Enter your email and password to login")
        email = st.text_input("Login Email", key="login_email")
        password = st.text_input("Login Password", type="password", key="login_password")

        if st.button("Login", key="login_btn"):
            user = db.query(User).filter(User.email == email).first()
            if user and verify_password(user.password, password):
                st.session_state.user_id = user.id
                st.sidebar.success("✅ Login successful!")
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid credentials")

    # Signup
    with sidebar_tabs[1]:
        st.write("Enter your email and password to signup")
        email_signup = st.text_input("Signup Email", key="signup_email")
        password_signup = st.text_input("Signup Password", type="password", key="signup_password")

        if st.button("Signup", key="signup_btn"):
            existing_user = db.query(User).filter(User.email == email_signup).first()
            if existing_user:
                st.sidebar.error("⚠️ Email already exists")
            else:
                hashed_password = bcrypt.hashpw(password_signup.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                new_user = User(email=email_signup, password=hashed_password)
                db.add(new_user)
                db.commit()
                st.sidebar.success("✅ Signup successful! Please login.")

# Main Section Layout
st.markdown("<h1 style='text-align: center;'>CostGPT - Find the Cost of Your Project 💰</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

if st.session_state.user_id:
    st.subheader("💡 Describe Your Project")
    user_input = st.text_input("Enter your project idea (e.g., I want to create an Instagram clone)", key="project_idea")

    if user_input:
        # Ask for more details
        st.subheader("📋 Additional Project Details")
        
        # Option to skip
        skip_details = st.checkbox("🚀 Skip additional details")
        
        responses = {}
        if not skip_details:
            details = [
                "What key features should your project have?",
                "Do you have a preferred tech stack?",
                "What is your estimated budget?",
                "Do you have a timeline for development?",
                "Would you need ongoing maintenance?"
            ]
            for i, question in enumerate(details):
                responses[i] = st.text_input(question, key=f"question_{i}")

        if st.button("🛠 Generate Project Plan"):
            with st.spinner("⚡ Preparing project outline..."):
                try:
                    query = f"User wants to build: {user_input}\n"
                    if not skip_details:
                        for key, value in responses.items():
                            if value:
                                query += f"{details[key]}: {value}\n"

                    # Attempt API Call
                    try:
                        response = client.chat.completions.create(
                            model=selected_model,
                            messages=[{"role": "user", "content": query}],
                        )
                        ai_response = response.choices[0].message.content
                    except Exception as e:
                        st.error("❌ OpenAI API Request Failed! Retrying in 3 seconds...")
                        time.sleep(3)  # Wait and retry once
                        response = client.chat.completions.create(
                            model=selected_model,
                            messages=[{"role": "user", "content": query}],
                        )
                        ai_response = response.choices[0].message.content

                    st.success("✅ Project Plan Generated Successfully!")

                    # Save chat history
                    chat_entry = ChatHistory(user_id=st.session_state.user_id, message=user_input, ai_response=ai_response)
                    db.add(chat_entry)
                    db.commit()

                    # Generate PDF
                    pdf_content = f"<h1>📌 Project Plan</h1><p>{ai_response.replace('\n', '<br>')}</p>"
                    pdf_path = "project_plan.pdf"
                    pdfkit.from_string(pdf_content, pdf_path)

                    # Show PDF
                    with open(pdf_path, "rb") as pdf_file:
                        pdf_bytes = BytesIO(pdf_file.read())
                        st.download_button("📥 Download Project Plan (PDF)", pdf_bytes, file_name="project_plan.pdf", mime="application/pdf")

                except Exception as e:
                    st.error("❌ Error: Failed to generate a response. Please try again.")
                    st.error(f"🔧 Debug Info: {str(e)}")

# Move Chat History to Sidebar
st.sidebar.subheader("📜 User Queries")
chat_history = db.query(ChatHistory).filter(ChatHistory.user_id == st.session_state.user_id).all()

for chat in chat_history:
    st.sidebar.text_area(f"🗣 {chat.message}", chat.ai_response, height=100)
