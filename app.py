import streamlit as st
import pandas as pd
import os
import cv2
import smtplib
from email.message import EmailMessage

# -----------------------------------------
# PAGE CONFIG
# -----------------------------------------
st.set_page_config(page_title="Missing Person Detection", layout="wide")

# -----------------------------------------
# CUSTOM UI (GLASS + GRADIENT)
# -----------------------------------------
def set_ui():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }

    .glass {
        background: rgba(255, 255, 255, 0.1);
        padding: 25px;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        width: 400px;
        margin: auto;
        margin-top: 100px;
    }

    .card {
        background: rgba(255,255,255,0.1);
        padding: 20px;
        border-radius: 10px;
        margin: 10px;
    }

    input {
        background-color: rgba(255,255,255,0.2) !important;
        color: white !important;
    }

    button {
        background: linear-gradient(90deg, #ff6a00, #ee0979);
        color: white;
        border-radius: 8px;
    }

    </style>
    """, unsafe_allow_html=True)

set_ui()

# -----------------------------------------
# SIMPLE LOGIN (NO AUTH LIB)
# -----------------------------------------
USERNAME = "admin"
PASSWORD = "1234"

if "login" not in st.session_state:
    st.session_state.login = False

# -----------------------------------------
# LOGIN PAGE
# -----------------------------------------
if not st.session_state.login:

    st.markdown('<div class="glass">', unsafe_allow_html=True)

    st.subheader("Hello there 👋")
    st.write("Welcome Back")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == USERNAME and pwd == PASSWORD:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Invalid Credentials")

    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------
# MAIN APP
# -----------------------------------------
else:

    st.sidebar.title("👤 Dashboard")
    menu = st.sidebar.radio("Menu", ["🏠 Home", "➕ Report", "📋 Records", "🎥 Detection"])

    # -----------------------------------------
    # EMAIL FUNCTION
    # -----------------------------------------
    def send_email(to_email, subject, body):
        try:
            sender = "your_email@gmail.com"
            password = "your_app_password"

            msg = EmailMessage()
            msg.set_content(body)
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = to_email

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(sender, password)
                smtp.send_message(msg)

        except:
            pass

    # -----------------------------------------
    # HOME
    # -----------------------------------------
    if menu == "🏠 Home":
        st.title("🧭 Missing Person Detection System")

        st.markdown("""
        <div class="card">
        <h3>Welcome</h3>
        <p>This system helps identify missing persons using face detection and sends alerts.</p>
        </div>
        """, unsafe_allow_html=True)

    # -----------------------------------------
    # REPORT
    # -----------------------------------------
    elif menu == "➕ Report":

        st.header("Report Missing Person")

        name = st.text_input("Name")
        phone = st.text_input("Phone")
        email = st.text_input("Family Email")
        image = st.file_uploader("Upload Image")

        if st.button("Submit"):
            if name and phone and email and image:

                os.makedirs("data", exist_ok=True)
                path = f"data/{name}.jpg"

                with open(path, "wb") as f:
                    f.write(image.read())

                data = {
                    "Name": name,
                    "Phone": phone,
                    "Email": email,
                    "Image": path
                }

                file = "data.csv"

                if os.path.exists(file):
                    df = pd.read_csv(file)
                    df = pd.concat([df, pd.DataFrame([data])])
                else:
                    df = pd.DataFrame([data])

                df.to_csv(file, index=False)

                st.success("Saved Successfully")

            else:
                st.error("Fill all fields")

    # -----------------------------------------
    # VIEW RECORDS
    # -----------------------------------------
    elif menu == "📋 Records":

        st.header("Records")

        if os.path.exists("data.csv"):
            df = pd.read_csv("data.csv")
            st.dataframe(df)
        else:
            st.warning("No records")

    # -----------------------------------------
    # DETECTION (BASIC DEMO)
    # -----------------------------------------
    elif menu == "🎥 Detection":

        st.header("Detection")

        uploaded = st.file_uploader("Upload Person Image")

        if uploaded:

            file_bytes = uploaded.read()
            st.image(file_bytes)

            if os.path.exists("data.csv"):
                df = pd.read_csv("data.csv")

                for _, row in df.iterrows():
                    st.success(f"Possible Match Found: {row['Name']}")

                    send_email(
                        row["Email"],
                        "Missing Person Found",
                        f"{row['Name']} might be found."
                    )
            else:
                st.warning("No data available")
