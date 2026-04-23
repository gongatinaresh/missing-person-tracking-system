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

/* ✅ LOGIN FIX */
.login-box {
    width: 100%;
    max-width: 350px;
    margin: auto;
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
        usernames[i]: {"name": names[i], "password": hashed_passwords[i]}
        for i in range(len(usernames))
    }
}

authenticator = stauth.Authenticate(credentials, "app", "key", 30)

# ---------- LOGIN UI ----------
if not st.session_state.get("authentication_status"):

    st.markdown("""
    <h1 style='text-align:center;color:white;margin-top:40px;'>
    MISSING PERSON TRACKING SYSTEM
    </h1>
    """, unsafe_allow_html=True)

    # ✅ CENTER FIX
    col1, col2, col3 = st.columns([1,1.2,1])

    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)

        st.markdown("<div style='color:white;text-align:center;margin-bottom:10px;'>Admin Login</div>", unsafe_allow_html=True)

        name, auth_status, username = authenticator.login("Login","main")

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
"""
        msg.set_content(body)

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

    if menu == "Dashboard":

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
        else:
            df = pd.DataFrame()

        total = len(df)

        st.markdown("<div class='card'><h3>Dashboard</h3></div>", unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        c1.markdown(f"<div class='card'><h2>{total}</h2><p>Total</p></div>", unsafe_allow_html=True)
        c2.markdown("<div class='card'><h2>Active</h2></div>", unsafe_allow_html=True)
        c3.markdown("<div class='card'><h2>Alerts</h2></div>", unsafe_allow_html=True)

    elif menu == "Report":

        name = st.text_input("Name")
        phone = st.text_input("Phone")
        location = st.text_input("Location")
        admin_email = st.text_input("Admin Email")
        family_email = st.text_input("Family Email")
        image = st.file_uploader("Upload Image")

        if st.button("Submit") and image:
            os.makedirs("data", exist_ok=True)
            path = f"data/{name}.jpg"

            with open(path, "wb") as f:
                f.write(image.getbuffer())

            st.success("Saved")

    elif menu == "Reports":

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
            st.dataframe(df)

            if st.button("Clear All Reports"):
                os.remove("missing_data.csv")
                st.success("Cleared")

    elif menu == "Detection":

        st.subheader("Live Detection")

        webrtc_streamer(key="cam", video_transformer_factory=VideoTransformerBase)
