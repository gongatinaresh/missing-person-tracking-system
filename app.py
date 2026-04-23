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

# ---------- LOGIN ----------
with open("login_info.txt") as f:
    lines = f.readlines()

names = eval(lines[0].split("=")[1])
usernames = eval(lines[1].split("=")[1])

file_path = Path("hashed_pw.pkl")
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

credentials = {
    "usernames": {
        usernames[i]: {
            "name": names[i],
            "password": hashed_passwords[i]
        }
        for i in range(len(usernames))
    }
}

authenticator = stauth.Authenticate(credentials, "app", "key", 30)

# ---------- LOGIN UI ----------
if not st.session_state.get("authentication_status"):

    st.markdown("""
    <style>
    .stApp {
        background: url("https://images.unsplash.com/photo-1531297484001-80022131f5a1") no-repeat center center fixed;
        background-size: cover;
    }

    .overlay {
        position: fixed;
        top:0;
        left:0;
        width:100%;
        height:100%;
        background: rgba(0,0,0,0.6);
    }

    .login-box {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 350px;
        padding: 30px;
        border-radius: 15px;
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(10px);
        text-align: center;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.7);
    }

    .subtitle {
        color: #ccc;
        margin-bottom: 20px;
    }

    .stTextInput input {
        border-radius: 30px;
        padding: 10px;
        background: white;
    }

    .stButton>button {
        width: 100%;
        border-radius: 30px;
        height: 45px;
        background: linear-gradient(90deg,#00c6ff,#0072ff);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='overlay'></div>", unsafe_allow_html=True)

    st.markdown("""
    <h1 style='text-align:center;color:white;margin-top:40px;'>
    MISSING PERSON AND CRIMINAL IDENTIFICATION SYSTEM
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-box'>", unsafe_allow_html=True)

    st.markdown("<div class='subtitle'>Admin Login</div>", unsafe_allow_html=True)

    name, auth_status, username = authenticator.login("Login", "main")

    st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ---------- EMAIL ----------
def send_email(to_email, name, location, phone, image_path):
    try:
        sender = st.secrets["EMAIL"]
        password = st.secrets["EMAIL_PASSWORD"]

        msg = EmailMessage()
        msg["Subject"] = "🚨 Missing Person Detected"
        msg["From"] = sender
        msg["To"] = to_email

        body = f"""
ALERT: Missing Person Detected

Name: {name}
Last Seen Location: {location}
Contact Number: {phone}

The system has detected a possible match in live camera feed.
Please verify immediately.
"""
        msg.set_content(body)

        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="image",
                    subtype="jpeg",
                    filename=os.path.basename(image_path)
                )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)

    except Exception as e:
        print("Email Error:", e)

# ---------- MAIN ----------
if st.session_state.get("authentication_status"):

    authenticator.logout("Logout", "sidebar")

    menu = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Report", "Reports", "Detection"]
    )

    # DASHBOARD
    if menu == "Dashboard":
        st.markdown("<h2 style='color:white;'>Dashboard</h2>", unsafe_allow_html=True)

    # REPORT
    elif menu == "Report":
        st.markdown("<h2 style='color:white;'>Report</h2>", unsafe_allow_html=True)

    # REPORTS
    elif menu == "Reports":
        st.markdown("<h2 style='color:white;'>Reports</h2>", unsafe_allow_html=True)

    # DETECTION
    elif menu == "Detection":
        st.markdown("<h2 style='color:white;'>Detection</h2>", unsafe_allow_html=True)
