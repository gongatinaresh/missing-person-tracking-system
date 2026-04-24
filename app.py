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
auth_status = st.session_state.get("authentication_status")

if auth_status is None:

    st.markdown("""
    <style>

    .stApp {
        background: url("https://www.image2url.com/r2/default/images/1777004946995-2d9a1d91-03d5-4d08-a0b7-b7811a0202cd.jpeg") no-repeat center center fixed;
        background-size: cover;
    }

    [data-testid="stAppViewContainer"] {
        background: rgba(0,0,0,0.75);
    }

    header {visibility: hidden;}

    /* ===== TITLE ===== */
    .main-title {
        text-align: center;
        font-size: 30px;
        font-weight: bold;
        color: white;
        margin-bottom: 20px;
    }

    /* ===== CENTER FIX ===== */
    .block-container {
        max-width: 400px;
        margin: auto;
    }

    /* ===== LOGIN CARD ===== */
    .login-box {
        padding: 20px;
        border-radius: 12px;
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(10px);
        text-align: center;
    }

    /* ===== INPUT CONTROL ===== */
    div[data-baseweb="input"] {
        width: 100% !important;
    }

    div[data-baseweb="input"] input {
        color: black !important;
    }

    /* ===== BUTTON ===== */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 40px;
        background: linear-gradient(90deg,#00c6ff,#0072ff);
        color: white;
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>🔍 Missing Person Tracking System</div>", unsafe_allow_html=True)

    st.markdown("<div class='login-box'>", unsafe_allow_html=True)

    name, auth_status, username = authenticator.login(
        "Login",
        "main",
        key="login_form"
    )

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
