import streamlit as st
import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import pandas as pd
import os
import cv2
import numpy as np

# Email
import smtplib
from email.message import EmailMessage

# Camera
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import av

# -------------------------------------------------
# UI STYLE (PREMIUM)
# -------------------------------------------------
st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}

h1, h2, h3, h4 {
    text-align: center;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    border-radius: 10px;
    height: 45px;
    font-weight: bold;
    box-shadow: 0 0 10px #00c6ff;
}

/* Cards */
.card {
    padding: 20px;
    border-radius: 15px;
    background: rgba(255,255,255,0.05);
    text-align: center;
}

/* Hide Streamlit menu */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# TITLE
# -------------------------------------------------
st.markdown("<h1>🧭 Missing Persons Tracking System</h1>", unsafe_allow_html=True)

# -------------------------------------------------
# LOGIN SYSTEM
# -------------------------------------------------
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

# CENTER LOGIN
col1, col2, col3 = st.columns([1,2,1])
with col2:
    name, auth_status, username = authenticator.login("Login", "main")

if auth_status:
    st.success(f"Welcome {name}")

elif auth_status is False:
    st.error("Invalid credentials")

else:
    st.warning("Please login")

# -------------------------------------------------
# EMAIL FUNCTION
# -------------------------------------------------
def send_email(to_email, subject, body):
    sender_email = st.secrets["EMAIL"]
    password = st.secrets["EMAIL_PASSWORD"]

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, password)
        smtp.send_message(msg)

# -------------------------------------------------
# MAIN APP
# -------------------------------------------------
if st.session_state.get("authentication_status"):

    authenticator.logout("Logout", "sidebar")

    menu = st.sidebar.radio("Navigation", ["Dashboard","Report","Reports","Detection"])

# ---------------- DASHBOARD ----------------
    if menu == "Dashboard":

        st.subheader("📊 Dashboard")

        total = 0
        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
            total = len(df)

        col1, col2, col3 = st.columns(3)

        col1.markdown(f"<div class='card'>👥<h2>{total}</h2>Total Missing</div>", unsafe_allow_html=True)
        col2.markdown("<div class='card'>📋<h2>Reports</h2></div>", unsafe_allow_html=True)
        col3.markdown("<div class='card'>🚨<h2>Alerts</h2></div>", unsafe_allow_html=True)

# ---------------- REPORT ----------------
    elif menu == "Report":

        st.subheader("➕ Report Missing Person")

        name = st.text_input("Name")
        image = st.file_uploader("Upload Image")
        phone = st.text_input("Phone")
        location = st.text_input("Location")
        admin_email = st.text_input("Admin Email")
        family_email = st.text_input("Family Email")

        if image:
            st.image(image)

        if st.button("Submit"):
            os.makedirs("data", exist_ok=True)
            path = f"data/{name}.jpg"

            with open(path, "wb") as f:
                f.write(image.read())

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
            st.success("Saved Successfully")

# ---------------- REPORTS ----------------
    elif menu == "Reports":

        st.subheader("📋 Reports")

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
            st.dataframe(df)

            if st.button("Clear"):
                os.remove("missing_data.csv")
                st.success("Cleared")

# ---------------- DETECTION ----------------
    elif menu == "Detection":

        st.subheader("🎥 Live Detection")

        def match_faces(a,b):
            a=cv2.resize(a,(100,100))
            b=cv2.resize(b,(100,100))
            return np.mean((a-b)**2)<2000

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
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

# -------------------------------------------------
# FOOTER
# -------------------------------------------------
st.markdown("""
<div style='text-align:center;margin-top:20px'>
<p style='color:gray'>Created by</p>
<h4>Gongati Naresh</h4>
</div>
""", unsafe_allow_html=True)
