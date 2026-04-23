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

# ---------- UI ----------
st.set_page_config(layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1rem;}
.element-container:empty {display:none;}
.stApp {
    background: linear-gradient(135deg, #0f2027,#203a43,#2c5364);
    font-family: 'Segoe UI';
}
.card {
    padding:18px;
    border-radius:14px;
    background:rgba(255,255,255,0.08);
    backdrop-filter:blur(12px);
    box-shadow:0 6px 20px rgba(0,0,0,0.3);
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
section[data-testid="stSidebar"] {
    background: rgba(0,0,0,0.5);
}
#MainMenu,footer {visibility:hidden;}
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

col1,col2,col3 = st.columns([1,2,1])
with col2:
    st.markdown("<div class='card'><h3>🧭 Missing Persons Tracking System</h3></div>", unsafe_allow_html=True)
    name, auth_status, username = authenticator.login("Login","main")

if auth_status:
    st.success(f"Welcome {name}")
elif auth_status is False:
    st.error("Invalid credentials")
else:
    st.warning("Please login")

# ---------- EMAIL ----------
def send_email(to_email, subject, body):
    try:
        sender = st.secrets["EMAIL"]
        password = st.secrets["EMAIL_PASSWORD"]

        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
            smtp.login(sender,password)
            smtp.send_message(msg)
    except:
        pass

# ---------- MAIN ----------
if st.session_state.get("authentication_status"):

    authenticator.logout("Logout","sidebar")

    st.markdown(f"<div class='card'>👤 Logged in as <b>{name}</b></div>", unsafe_allow_html=True)

    menu = st.sidebar.radio("Navigation",["Dashboard","Report","Reports","Detection"])

# ---------- DASHBOARD ----------
    if menu == "Dashboard":

        total = 0
        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
            total = len(df)
        else:
            df = pd.DataFrame()

        col1,col2,col3 = st.columns(3)

        col1.metric("Total Cases", total)
        col2.metric("Detection", "Active")
        col3.metric("Alert System", "ON")

# ---------- REPORT ----------
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

            if st.button("Clear Reports"):
                os.remove("missing_data.csv")
                st.success("Cleared")

# ---------- DETECTION ----------
    elif menu == "Detection":

        st.subheader("Live Detection")

        if not os.path.exists("missing_data.csv"):
            st.warning("No data available")
        else:
            df = pd.read_csv("missing_data.csv")

            known_faces = []
            names = []
            emails = []

            for _, r in df.iterrows():
                img = cv2.imread(r["Image Path"])
                if img is not None:
                    img = cv2.resize(img,(100,100))
                    known_faces.append(img)
                    names.append(r["Name"])
                    emails.append(r["Admin Email"])

            sent = set()

            def match(a,b):
                return np.mean((a-b)**2) < 2000

            class Cam(VideoTransformerBase):
                def transform(self, frame):
                    img = frame.to_ndarray(format="bgr24")
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                    face = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
                    faces = face.detectMultiScale(gray,1.3,5)

                    for (x,y,w,h) in faces:
                        f = cv2.resize(img[y:y+h,x:x+w],(100,100))

                        for i, db in enumerate(known_faces):
                            if match(f, db):

                                cv2.putText(img, names[i], (x,y-10), 1,1,(0,255,0),2)

                                if emails[i] not in sent:
                                    send_email(emails[i], "Alert", names[i])
                                    sent.add(emails[i])

                                break

                        cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

                    return img

            webrtc_streamer(key="cam", video_transformer_factory=Cam)
