import streamlit as st
import pandas as pd
import os
import cv2
import numpy as np
import smtplib
from email.message import EmailMessage
from datetime import datetime

st.set_page_config(layout="wide")

# ================= LOGIN =================
USERNAME = "naresh"
PASSWORD = "1234"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.markdown("<h2 style='text-align:center;'>🔐 Login</h2>", unsafe_allow_html=True)
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == USERNAME and pwd == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ================= UI =================
st.markdown("""
<style>
body {background-color:#0f172a;}
.card {
    background:#1e293b;
    padding:18px;
    border-radius:12px;
    text-align:center;
    color:white;
}
.section {
    background:#1e293b;
    padding:20px;
    border-radius:12px;
    margin-top:20px;
    color:white;
}
.metric {font-size:28px;font-weight:bold;}
.label {color:#94a3b8;font-size:14px;}
</style>
""", unsafe_allow_html=True)

# ================= EMAIL =================
def send_email(to_email, name):
    try:
        sender = st.secrets["EMAIL"]
        password = st.secrets["EMAIL_PASSWORD"]

        msg = EmailMessage()
        msg.set_content(f"Match found for {name}")
        msg["Subject"] = "Alert"
        msg["From"] = sender
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
            smtp.login(sender,password)
            smtp.send_message(msg)
    except:
        pass

# ================= LOAD DATA =================
if os.path.exists("missing_data.csv"):
    df = pd.read_csv("missing_data.csv")
else:
    df = pd.DataFrame()

# ================= SIDEBAR =================
menu = st.sidebar.radio("Menu",["Dashboard","Report","Reports","Detection"])

st.sidebar.write("👤 Logged in: naresh")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ================= DASHBOARD =================
if menu == "Dashboard":

    total = len(df)

    col1,col2,col3 = st.columns(3)
    col1.markdown(f"<div class='card'><div class='metric'>{total}</div><div class='label'>Total Records</div></div>", unsafe_allow_html=True)
    col2.markdown("<div class='card'><div class='metric'>Active</div><div class='label'>Detection</div></div>", unsafe_allow_html=True)
    col3.markdown("<div class='card'><div class='metric'>Enabled</div><div class='label'>Alerts</div></div>", unsafe_allow_html=True)

    # MATCH RESULT
    st.markdown("<div class='section'><h3>Match Result</h3></div>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)

    with c1:
        if "live_img" in st.session_state:
            st.image(st.session_state["live_img"], caption="Live Image")

    with c2:
        if st.session_state.get("match"):
            st.markdown("<h2 style='color:lightgreen;text-align:center;'>MATCH FOUND</h2>", unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='color:red;text-align:center;'>NO MATCH</h2>", unsafe_allow_html=True)

        if "time" in st.session_state:
            st.write(f"Time: {st.session_state['time']}")

    with c3:
        if "db_img" in st.session_state:
            st.image(st.session_state["db_img"], caption="Database Image")

    st.markdown("<div class='section'><h3>Recent Reports</h3></div>", unsafe_allow_html=True)

    if not df.empty:
        st.dataframe(df.tail(5))

# ================= REPORT =================
elif menu == "Report":

    name = st.text_input("Name")
    phone = st.text_input("Phone")
    location = st.text_input("Location")
    email = st.text_input("Email")
    image = st.file_uploader("Upload Image")

    if st.button("Submit"):
        if image:
            os.makedirs("data", exist_ok=True)
            path = f"data/{name}.jpg"

            with open(path,"wb") as f:
                f.write(image.getbuffer())

            new_data = pd.DataFrame([{
                "Name": name,
                "Image Path": path,
                "Phone": phone,
                "Location": location,
                "Email": email
            }])

            df = pd.concat([df, new_data])
            df.to_csv("missing_data.csv", index=False)

            st.success("Saved")

# ================= REPORTS =================
elif menu == "Reports":

    if not df.empty:
        st.dataframe(df)

    if st.button("Clear Reports"):
        if os.path.exists("missing_data.csv"):
            os.remove("missing_data.csv")
            st.success("Cleared")
            st.rerun()

# ================= DETECTION =================
elif menu == "Detection":

    cam = st.camera_input("Capture")

    def match_faces(a,b):
        a = cv2.resize(a,(100,100))
        b = cv2.resize(b,(100,100))
        return np.mean((a-b)**2) < 2000

    if cam and not df.empty:

        img = np.asarray(bytearray(cam.read()), dtype=np.uint8)
        img = cv2.imdecode(img,1)

        st.session_state["live_img"] = img
        st.session_state["time"] = datetime.now().strftime("%H:%M:%S")

        found = False

        for _,row in df.iterrows():
            db = cv2.imread(row["Image Path"])

            if db is not None and match_faces(img, db):
                st.session_state["db_img"] = db
                st.session_state["match"] = True
                found = True

                send_email(row["Email"], row["Name"])
                break

        if not found:
            st.session_state["match"] = False
