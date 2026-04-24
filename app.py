import streamlit as st
import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import pandas as pd
import os
import cv2
import numpy as np
import smtplib
from email.message import EmailMessage

st.set_page_config(layout="wide")

# ---------- UI ----------
st.markdown("""
<style>
.stApp {
    background: url("https://i.ibb.co/8gZz0qj/background.jpg") no-repeat center center fixed;
    background-size: cover;
}
[data-testid="stAppViewContainer"] {
    background: rgba(0,0,0,0.7);
}
.login-box {
    width: 350px;
    margin: auto;
    padding: 25px;
    border-radius: 15px;
    background: rgba(0,0,0,0.6);
    backdrop-filter: blur(10px);
    text-align: center;
}
div[data-baseweb="input"] > div {
    background-color: white !important;
}
div[data-baseweb="input"] input {
    color: black !important;
}
label {
    color: white !important;
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
auth_status = st.session_state.get("authentication_status")

if auth_status is None:

    st.markdown("""
    <style>
    .main-title {
        text-align:center;
        font-size:34px;
        font-weight:bold;
        color:white;
        margin-bottom:20px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>🔍 Missing Person Tracking System</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1.2,1])

    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)

        name, auth_status, username = authenticator.login(
            "Login",
            "main"
        )

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

elif auth_status is False:
    st.error("❌ Invalid Username or Password")
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

    authenticator.logout("Logout", "sidebar")

    menu = st.sidebar.radio("Navigation", ["Dashboard", "Report", "Reports", "Detection"])

    # ---------- DASHBOARD ----------
    if menu == "Dashboard":

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
        else:
            df = pd.DataFrame()

        st.markdown("<h3 style='color:white;'>Dashboard</h3>", unsafe_allow_html=True)
        st.write("Total Records:", len(df))

    # ---------- REPORT ----------
    elif menu == "Report":

        name = st.text_input("Name")
        phone = st.text_input("Phone")
        location = st.text_input("Location")
        email = st.text_input("Email")
        image = st.file_uploader("Upload Image")

        if image:
            st.image(image)

        if st.button("Submit") and image:
            os.makedirs("data", exist_ok=True)
            path = f"data/{name}.jpg"

            with open(path, "wb") as f:
                f.write(image.getbuffer())

            data = {
                "Name": name,
                "Image Path": path,
                "Phone": phone,
                "Location": location,
                "Email": email
            }

            if os.path.exists("missing_data.csv"):
                df = pd.read_csv("missing_data.csv")
                df = pd.concat([df, pd.DataFrame([data])])
            else:
                df = pd.DataFrame([data])

            df.to_csv("missing_data.csv", index=False)
            st.success("Saved")

    # ---------- REPORTS ----------
    elif menu == "Reports":

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
            st.dataframe(df)
        else:
            st.warning("No data")

    # ---------- DETECTION ----------
    elif menu == "Detection":

        st.subheader("📷 Live Detection")

        cam = st.camera_input("Take Photo")

        if cam:
            st.image(cam)
