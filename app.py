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
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

st.set_page_config(layout="wide")

# ---------- UI ----------
st.markdown("""
<style>
.block-container {padding-top: 1rem;}
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
        usernames[i]: {"name": names[i], "password": hashed_passwords[i]}
        for i in range(len(usernames))
    }
}

authenticator = stauth.Authenticate(credentials, "app", "key", 30)

# ---------- TITLE ----------
st.markdown("<h1 style='text-align:center;'>🔍 Missing Person Tracking System</h1>", unsafe_allow_html=True)

# ---------- LOGIN BOX ----------
col1, col2, col3 = st.columns([1.5,1,1.5])
with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    name, auth_status, username = authenticator.login("Login", "main")
    st.markdown("</div>", unsafe_allow_html=True)

if auth_status:
    st.success(f"Welcome {name}")
elif auth_status is False:
    st.error("Invalid credentials")
    st.stop()
else:
    st.warning("Please login")
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

        msg.set_content(f"""
Missing Person Detected

Name: {name}
Location: {location}
Phone: {phone}
""")

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="image",
                    subtype="jpeg",
                    filename="live.jpg"
                )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)

    except Exception as e:
        st.error(f"Email Error: {e}")

# ---------- MAIN ----------
authenticator.logout("Logout", "sidebar")
menu = st.sidebar.radio("Navigation", ["Dashboard", "Report", "Reports", "Detection"])

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":

    df = pd.read_csv("missing_data.csv") if os.path.exists("missing_data.csv") else pd.DataFrame()
    total = len(df)

    st.markdown("<div class='card'><h3>📍 Dashboard</h3></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='card'><h2>{total}</h2><p>Total Records</p></div>", unsafe_allow_html=True)
    c2.markdown("<div class='card'><h2>Active</h2></div>", unsafe_allow_html=True)
    c3.markdown("<div class='card'><h2>Alerts</h2></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if os.path.exists("temp/live.jpg"):
            st.image("temp/live.jpg")
        else:
            st.info("Live Image")

    with col2:
        st.success(st.session_state.get("status", "No Detection"))

    with col3:
        if os.path.exists("temp/match.jpg"):
            st.image("temp/match.jpg")
        else:
            st.info("Matched Image")

    st.line_chart(pd.DataFrame({"Accuracy": [60,70,75,80,85,90]}))

# ---------------- REPORT ----------------
elif menu == "Report":

    name = st.text_input("Name")
    phone = st.text_input("Phone")
    location = st.text_input("Location")
    admin_email = st.text_input("Admin Email")
    family_email = st.text_input("Family Email")
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
            "Admin Email": admin_email,
            "Family Email": family_email
        }

        df = pd.read_csv("missing_data.csv") if os.path.exists("missing_data.csv") else pd.DataFrame()
        df = pd.concat([df, pd.DataFrame([data])])
        df.to_csv("missing_data.csv", index=False)

        st.success("Saved")

# ---------------- REPORTS ----------------
elif menu == "Reports":

    if os.path.exists("missing_data.csv"):
        df = pd.read_csv("missing_data.csv")
        st.dataframe(df)

        if st.button("Clear All"):
            os.remove("missing_data.csv")
            st.rerun()
    else:
        st.warning("No reports")

# ---------------- DETECTION ----------------
elif menu == "Detection":

    st.subheader("Live Detection")

    if not os.path.exists("missing_data.csv"):
        st.warning("No data available")
    else:
        df = pd.read_csv("missing_data.csv")

        known, names, emails = [], [], []

        for _, r in df.iterrows():
            img = cv2.imread(r["Image Path"])
            if img is not None:
                known.append(cv2.resize(img, (100,100)))
                names.append(r["Name"])
                emails.append(r["Admin Email"])

        os.makedirs("temp", exist_ok=True)
        sent = set()

        def match(a, b):
            return np.mean((a - b) ** 2) < 6000

        class Cam(VideoTransformerBase):
            def transform(self, frame):
                img = frame.to_ndarray(format="bgr24")
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)

                faces = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                ).detectMultiScale(gray, 1.1, 4)

                for (x, y, w, h) in faces:

                    cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)

                    f = cv2.resize(img[y:y+h, x:x+w], (100,100))
                    matched = False

                    for i, db in enumerate(known):

                        if match(f, db):

                            matched = True

                            cv2.imwrite("temp/live.jpg", img)
                            cv2.imwrite("temp/match.jpg", db)

                            st.session_state["status"] = f"MATCH FOUND: {names[i]}"

                            cv2.putText(img, names[i], (x, y-10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

                            if emails[i] not in sent:
                                send_email(
                                    emails[i],
                                    names[i],
                                    df.iloc[i]["Location"],
                                    df.iloc[i]["Phone"],
                                    "temp/live.jpg"
                                )
                                sent.add(emails[i])

                            break

                    if not matched:
                        cv2.putText(img, "Unknown", (x, y-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

                        st.session_state["status"] = "Face Detected (No Match)"

                return img

        webrtc_streamer(
            key="cam",
            video_transformer_factory=Cam,
            media_stream_constraints={"video": True},
            async_processing=True
        )
