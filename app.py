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

# ---------------- UI CONFIG ----------------
st.set_page_config(page_title="Missing Person System", layout="wide")

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
    st.stop()
else:
    st.stop()

authenticator.logout("Logout", "sidebar")

# ---------------- EMAIL ----------------
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

    st.markdown("<div class='card'><h3>📊 Dashboard</h3></div>", unsafe_allow_html=True)

    if os.path.exists("missing_data.csv"):
        df = pd.read_csv("missing_data.csv")
        total = len(df)
    else:
        df = pd.DataFrame()
        total = 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Cases", total)
    c2.metric("System Status", "Active")
    c3.metric("Alerts", "Enabled")

    st.markdown("<div class='card'><h3>Recent Reports</h3></div>", unsafe_allow_html=True)

    if not df.empty:
        st.dataframe(df.tail(5))
    else:
        st.warning("No data available")

# ================= REPORT =================
elif menu == "Report":

    st.markdown("<div class='card'><h3>➕ Report Missing Person</h3></div>", unsafe_allow_html=True)

    name = st.text_input("Name")
    phone = st.text_input("Phone")
    location = st.text_input("Location")
    email = st.text_input("Email")

    image = st.file_uploader("Upload Image")

    if image:
        st.image(image, caption="Preview")

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

    st.markdown("<div class='card'><h3>📋 All Reports</h3></div>", unsafe_allow_html=True)

    if os.path.exists("missing_data.csv"):
        df = pd.read_csv("missing_data.csv")
        st.dataframe(df)

# ================= DETECTION =================
elif menu == "Detection":

    st.markdown("<div class='card'><h3>🎯 Detection</h3></div>", unsafe_allow_html=True)

    def match_faces(a, b):
        a = cv2.resize(a, (100,100))
        b = cv2.resize(b, (100,100))
        score = np.mean((a - b) ** 2)
        return score, score < 2000

    if os.path.exists("missing_data.csv"):
        df = pd.read_csv("missing_data.csv")
    else:
        df = None

    uploaded = st.file_uploader("Upload Image for Detection")

    if uploaded:
        img_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
        frame = cv2.imdecode(img_bytes, 1)

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        match_img = None
        match_name = None
        match_score = None

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
                            match_score = score

                            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                            cv2.putText(frame, match_name,(x,y-10),
                                        cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,255,0),2)
                            break

        col1, col2 = st.columns(2)

        with col1:
            st.image(frame, channels="BGR", caption="Live Image")

        with col2:
            if match_img is not None:
                st.image(match_img, channels="BGR", caption="Matched Image")
                st.success(f"✔ Match Found: {match_name}")
                st.write(f"Similarity Score: {round(match_score,2)}")

                if st.button("Send Alert"):
                    send_email(row["Email"], "Match Found", f"{match_name} detected")
                    st.success("Email Sent")
            else:
                st.warning("❌ No Match Found")
