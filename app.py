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
import av

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

with open("login_info.txt", "r") as f:
    lines = f.readlines()

names = eval(lines[0].split("=")[1].strip())
usernames = eval(lines[1].split("=")[1].strip())

file_path = Path(__file__).parent / "hashed_pw.pkl"
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

def send_email(to_email, subject, body):
    sender_email = st.secrets["EMAIL"]
    password = st.secrets["EMAIL_PASSWORD"]
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login(sender_email,password)
        smtp.send_message(msg)

if st.session_state.get("authentication_status"):

    authenticator.logout("Logout","sidebar")

    st.markdown(f"""
    <div class='card'>
        👤 Logged in as <b>{name}</b> | 🟢 System Active
    </div>
    """, unsafe_allow_html=True)

    menu = st.sidebar.radio("Navigation",["Dashboard","Report","Reports","Detection"])

# ---------------- DASHBOARD ----------------
    if menu == "Dashboard":

        st.markdown("""
        <div class='card'>
            <h3>📍 Real-time Missing Person Identification & Monitoring Dashboard</h3>
            <p>Centralized system for tracking, detection, and alerting</p>
        </div>
        """, unsafe_allow_html=True)

        total = 0
        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
            total = len(df)
        else:
            df = pd.DataFrame()

        col1,col2,col3 = st.columns(3)

        col1.markdown(f"<div class='card'><h1>{total}</h1><p>Total Cases</p></div>", unsafe_allow_html=True)
        col2.markdown("<div class='card'><h1>🟢</h1><p>Detection Active</p></div>", unsafe_allow_html=True)
        col3.markdown("<div class='card'><h1>📧</h1><p>Alert System</p></div>", unsafe_allow_html=True)

        st.markdown("<div class='card'><h3>📌 Recent Reports</h3></div>", unsafe_allow_html=True)

        if not df.empty:
            st.dataframe(df.tail(5))
        else:
            st.warning("No reports available")

        st.markdown("""
        <div class='card'>
        This system identifies missing persons using face detection and sends alerts to authorities.
        </div>
        """, unsafe_allow_html=True)

# ---------------- REPORT ----------------
    elif menu == "Report":

        st.markdown("<div class='card'><h3>➕ Report Missing Person</h3></div>", unsafe_allow_html=True)

        col1,col2 = st.columns([2,1])

        with col1:
            name = st.text_input("Name")
            phone = st.text_input("Phone")
            location = st.text_input("Location")
            admin_email = st.text_input("Admin Email")
            family_email = st.text_input("Family Email")

        with col2:
            image = st.file_uploader("Upload Image")

            if image:
                img_bytes = np.asarray(bytearray(image.read()), dtype=np.uint8)
                img = cv2.imdecode(img_bytes,1)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img,(150,150))
                _,buffer = cv2.imencode('.jpg',img)
                img_str = base64.b64encode(buffer).decode()

                st.markdown(f"""
                <div style="display:flex;justify-content:center;">
                <img src="data:image/jpeg;base64,{img_str}"
                style="border-radius:50%; width:150px; height:150px;">
                </div>
                """, unsafe_allow_html=True)

        if st.button("Submit"):
            if image:
                os.makedirs("data",exist_ok=True)
                path=f"data/{name}.jpg"

                with open(path,"wb") as f:
                    f.write(image.getbuffer())

                data={
                    "Name":name,
                    "Image Path":path,
                    "Phone":phone,
                    "Location":location,
                    "Admin Email":admin_email,
                    "Family Email":family_email
                }

                if os.path.exists("missing_data.csv"):
                    df=pd.read_csv("missing_data.csv")
                    df=pd.concat([df,pd.DataFrame([data])])
                else:
                    df=pd.DataFrame([data])

                df.to_csv("missing_data.csv",index=False)
                st.success("Saved")

# ---------------- REPORTS ----------------
    elif menu == "Reports":

        st.markdown("<div class='card'><h3>📋 Reports</h3></div>", unsafe_allow_html=True)

        if os.path.exists("missing_data.csv"):
            df=pd.read_csv("missing_data.csv")
            st.dataframe(df)

            col1,col2 = st.columns(2)

            with col1:
                if st.button("🗑️ Clear All Reports"):
                    os.remove("missing_data.csv")
                    st.success("All reports cleared")
                    st.rerun()

            with col2:
                st.info("This will permanently delete all data")

        else:
            st.warning("No reports available")

# ---------------- DETECTION ----------------
    elif menu == "Detection":

        st.markdown("<div class='card'><h3>🎥 Live Detection</h3></div>", unsafe_allow_html=True)

        def match_faces(a,b):
            a=cv2.resize(a,(100,100))
            b=cv2.resize(b,(100,100))
            return np.mean((a-b)**2)<2000

        if os.path.exists("missing_data.csv"):
            df=pd.read_csv("missing_data.csv")
        else:
            df=None

        class Cam(VideoTransformerBase):
            def transform(self,frame):
                img=frame.to_ndarray(format="bgr24")
                gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
                face=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
                faces=face.detectMultiScale(gray,1.3,5)

                if df is not None:
                    for (x,y,w,h) in faces:
                        f=img[y:y+h,x:x+w]
                        for _,r in df.iterrows():
                            db=cv2.imread(r["Image Path"])
                            if db is not None and match_faces(f,db):
                                cv2.putText(img,r["Name"],(x,y-10),1,1,(0,255,0),2)
                                send_email(r["Admin Email"],"Alert",r["Name"])
                                break
                        cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
                return img

        webrtc_streamer(key="cam",video_transformer_factory=Cam)
