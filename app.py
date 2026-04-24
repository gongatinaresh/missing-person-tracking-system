import streamlit as st
import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import pandas as pd
import os
import cv2
import numpy as np
import base64
import smtplib
from email.message import EmailMessage
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

st.set_page_config(layout="wide")

# ---------- UI ----------
st.markdown("""
<style>
.block-container {padding-top: 1rem;}
.element-container:empty {display:none;}
.stApp {
    background: linear-gradient(135deg, #0f2027,#203a43,#2c5364);
}
.card {
    padding:18px;
    border-radius:14px;
    background:rgba(255,255,255,0.08);
    backdrop-filter:blur(12px);
    margin-bottom:10px;
}
h1,h2,h3 {color:white;text-align:center;}
.stButton>button {
    background:linear-gradient(90deg,#00c6ff,#0072ff);
    color:white;
    border-radius:10px;
    height:42px;
    width:100%;
}
</style>
""", unsafe_allow_html=True)

# ---------- LOGIN DATA ----------
with open("login_info.txt") as f:
    lines = f.readlines()

names = eval(lines[0].split("=")[1])
usernames = eval(lines[1].split("=")[1])

file_path = Path("hashed_pw.pkl")
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

credentials = {
    "usernames": {
        usernames[i]: {"name": names[i], "password": hashed_passwords[i]}
        for i in range(len(usernames))
    }
}

authenticator = stauth.Authenticate(credentials, "app", "key", 30)

# ---------- PREMIUM LOGIN UI ----------
# ---------- SESSION INIT ----------
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = False


# ---------- LOGIN PAGE ----------
if not st.session_state["authentication_status"]:

    st.markdown("""
    <style>

    .stApp {
        background: url("https://i.ibb.co/8gZz0qj/background.jpg") no-repeat center center fixed;
        background-size: cover;
    }

    [data-testid="stAppViewContainer"] {
        background: rgba(0,0,0,0.75);
    }

    header {visibility: hidden;}

    .main-title {
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        color: white;
        margin-top: 40px;
    }

    .login-box {
        width: 360px;
        margin: 80px auto;
        padding: 25px;
        border-radius: 15px;
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(12px);
        text-align: center;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.8);
    }

    .stTextInput input {
        border-radius: 10px;
        padding: 10px;
        background: white;
    }

    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 42px;
        background: linear-gradient(90deg,#00c6ff,#0072ff);
        color: white;
        font-weight: bold;
        border: none;
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>🔍 Missing Person Tracking System</div>", unsafe_allow_html=True)

    st.markdown("<div class='login-box'>", unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        # 🔑 CHANGE THIS CREDENTIAL
        if username == "admin" and password == "1234":
            st.session_state["authentication_status"] = True
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Username or Password")

    st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ---------- AFTER LOGIN ----------
st.success(f"Welcome {name}")

# ---------- EMAIL ----------
def send_email(to_email, name, location, phone, image_path):
    try:
        sender = st.secrets["EMAIL"]
        password = st.secrets["EMAIL_PASSWORD"]

        msg = EmailMessage()
        msg["Subject"] = "🚨 Missing Person Detected"
        msg["From"] = sender
        msg["To"] = to_email

        msg.set_content(f"""
ALERT: Missing Person Detected

Name: {name}
Location: {location}
Phone: {phone}
""")

        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="image", subtype="jpeg", filename="live.jpg")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)

    except Exception as e:
        print("Email Error:", e)

# ---------- MAIN ----------
if st.session_state.get("authentication_status"):

    authenticator.logout("Logout","sidebar")

    menu = st.sidebar.radio("Navigation",["Dashboard","Report","Reports","Detection"])

    # KEEP ALL YOUR ORIGINAL CODE BELOW (UNCHANGED)
