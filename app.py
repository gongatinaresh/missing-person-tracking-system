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

# ---------------- UI STYLE ----------------
st.set_page_config(layout="wide")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f2027,#203a43,#2c5364);
}
.card {
    padding:15px;
    border-radius:12px;
    background:rgba(255,255,255,0.08);
    margin-bottom:10px;
}
h1,h2,h3 {color:white;text-align:center;}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
with open("login_info.txt", "r") as f:
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

name, auth_status, username = authenticator.login("Login", "main")

if auth_status:
    st.success(f"Welcome {name}")
elif auth_status is False:
    st.error("Invalid credentials")
else:
    st.stop()

authenticator.logout("Logout", "sidebar")

# ---------------- EMAIL FUNCTION ----------------
def send_email(to_email, subject, body):
    try:
        sender = st.secrets["EMAIL"]
        password = st.secrets["EMAIL_PASSWORD"]

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

# ---------------- SIDEBAR ----------------
menu = st.sidebar.radio("Navigation", ["Dashboard", "Report", "Reports", "Detection"])

# ================= DASHBOARD =================
if menu == "Dashboard":

    st.markdown("<div class='card'><h3>Dashboard</h3></div>", unsafe_allow_html=True)

    if os.path.exists("missing_data.csv"):
        df = pd.read_csv("missing_data.csv")
        total = len(df)
    else:
        df = pd.DataFrame()
        total = 0

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Cases", total)
    col2.metric("System Status", "Active")
    col3.metric("Alerts", "Enabled")

    if not df.empty:
        st.dataframe(df.tail(5))
    else:
        st.warning("No data available")

# ================= REPORT =================
elif menu == "Report":

    st.markdown("<div class='card'><h3>Report Missing Person</h3></div>", unsafe_allow_html=True)

    name = st.text_input("Name")
    phone = st.text_input("Phone")
    location = st.text_input("Location")
    email = st.text_input("Email")

    image = st.file_uploader("Upload Image")

    if image:
        st.image(image)

    if st.button("Save"):
        if image:
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
            st.success("Saved Successfully")

# ================= REPORTS =================
elif menu == "Reports":

    st.markdown("<div class='card'><h3>All Reports</h3></div>", unsafe_allow_html=True)

    if os.path.exists("missing_data.csv"):
        df = pd.read_csv("missing_data.csv")
        st.dataframe(df)

# ================= DETECTION =================
elif menu == "Detection":

    st.markdown("<div class='card'><h3>Live Detection</h3></div>", unsafe_allow_html=True)

    def match_faces(a, b):
        a = cv2.resize(a, (100,100))
        b = cv2.resize(b, (100,100))
        score = np.mean((a - b) ** 2)
        return score, score < 2000

    if os.path.exists("missing_data.csv"):
        df = pd.read_csv("missing_data.csv")
    else:
        df = None

    FRAME = st.empty()
    RESULT = st.empty()

    cap = cv2.VideoCapture(0)

    if st.button("Start Detection"):

        sent = False

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            match_img = None
            match_name = None

            if df is not None:
                for (x,y,w,h) in faces:
                    face = frame[y:y+h, x:x+w]

                    for _, row in df.iterrows():
                        db = cv2.imread(row["Image Path"])

                        if db is not None:
                            score, matched = match_faces(face, db)

                            if matched:
                                match_img = db
                                match_name = row["Name"]

                                cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                                cv2.putText(frame, match_name,(x,y-10),1,1,(0,255,0),2)

                                if not sent:
                                    send_email(row["Email"], "Match Found", f"{match_name} detected")
                                    sent = True
                                break

            FRAME.image(frame, channels="BGR")

            with RESULT.container():
                c1, c2 = st.columns(2)

                with c1:
                    st.image(frame, channels="BGR", caption="Live Image")

                with c2:
                    if match_img is not None:
                        st.image(match_img, channels="BGR", caption="Matched Image")
                        st.success(f"Match Found: {match_name}")
                    else:
                        st.warning("No Match")

    cap.release()
