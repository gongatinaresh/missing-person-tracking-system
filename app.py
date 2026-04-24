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

# ---------- LOGIN ----------
with open("login_info.txt") as f:
    lines = f.readlines()

names = eval(lines[0].split("=")[1])
usernames = eval(lines[1].split("=")[1])

with open("hashed_pw.pkl", "rb") as f:
    hashed_passwords = pickle.load(f)

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

name, auth_status, username = authenticator.login("Login", "main")

# ---------- LOGIN UI ----------
if auth_status is False:
    st.error("Invalid credentials")
    st.stop()

elif auth_status is None:
    st.title("🔍 Missing Person Tracking System")
    st.warning("Please login")
    st.stop()

# ---------- AFTER LOGIN ----------
authenticator.logout("Logout", "sidebar")

menu = st.sidebar.radio("Navigation", ["Dashboard", "Report", "Reports", "Detection"])

# ---------- EMAIL ----------
def send_email(to_email, name, location, phone, image_path):
    sender = st.secrets["EMAIL"]
    password = st.secrets["EMAIL_PASSWORD"]

    msg = EmailMessage()
    msg["Subject"] = "🚨 Missing Person Detected"
    msg["From"] = sender
    msg["To"] = to_email

    msg.set_content(f"""
ALERT: Missing Person Found

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

# ---------- DASHBOARD ----------
if menu == "Dashboard":

    st.title("📊 Dashboard")

    if os.path.exists("missing_data.csv"):
        df = pd.read_csv("missing_data.csv")
    else:
        df = pd.DataFrame()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Records", len(df))
    col2.metric("Detection", "Active")
    col3.metric("Alerts", "Enabled")

    st.subheader("Live Detection Result")

    col1, col2 = st.columns(2)

    if os.path.exists("temp/live.jpg"):
        col1.image("temp/live.jpg", caption="Live Image")

    if os.path.exists("temp/match.jpg"):
        col2.image("temp/match.jpg", caption="Database Image")

    st.subheader("Accuracy Graph")
    st.line_chart(pd.DataFrame({"Accuracy": [60,70,75,80,85,90]}))

# ---------- REPORT ----------
elif menu == "Report":

    st.title("Report Missing Person")

    name = st.text_input("Name")
    phone = st.text_input("Phone")
    location = st.text_input("Last Seen Location")

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

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
            df = pd.concat([df, pd.DataFrame([data])])
        else:
            df = pd.DataFrame([data])

        df.to_csv("missing_data.csv", index=False)
        st.success("Report Saved")

# ---------- REPORTS ----------
elif menu == "Reports":

    st.title("All Reports")

    if os.path.exists("missing_data.csv"):
        df = pd.read_csv("missing_data.csv")
        st.dataframe(df)

        if st.button("Clear All"):
            os.remove("missing_data.csv")
            st.success("Deleted")
            st.rerun()
    else:
        st.warning("No data")

# ---------- DETECTION ----------
elif menu == "Detection":

    st.title("Live Detection")

    if not os.path.exists("missing_data.csv"):
        st.warning("No data available")
    else:
        df = pd.read_csv("missing_data.csv")

        known, names, emails = [], [], []

        for _, r in df.iterrows():
            img = cv2.imread(r["Image Path"])
            if img is not None:
                known.append(cv2.resize(img,(100,100)))
                names.append(r["Name"])
                emails.append(r["Admin Email"])

        os.makedirs("temp", exist_ok=True)
        sent = set()

        def match(a,b):
            return np.mean((a-b)**2) < 800

        class Cam(VideoTransformerBase):
            def transform(self,frame):
                img = frame.to_ndarray(format="bgr24")
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                face = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
                faces = face.detectMultiScale(gray,1.3,5)

                for (x,y,w,h) in faces:
                    f = cv2.resize(img[y:y+h,x:x+w],(100,100))
                    cv2.imwrite("temp/live.jpg", img)

                    for i, db in enumerate(known):
                        if match(f, db):
                            cv2.imwrite("temp/match.jpg", db)
                            st.session_state["status"] = f"MATCH FOUND: {names[i]}"

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

                    cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

                return img

        webrtc_streamer(key="cam", video_transformer_factory=Cam)
