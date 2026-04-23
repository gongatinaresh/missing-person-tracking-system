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
.stApp {
    background: linear-gradient(135deg, #1e3c72, #2a5298);
    font-family: 'Segoe UI', sans-serif;
}
.login-box {
    background: rgba(255,255,255,0.1);
    padding: 30px;
    border-radius: 15px;
    backdrop-filter: blur(15px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    width: 350px;
    margin: auto;
    margin-top: 120px;
    text-align: center;
    color:white;
}
.card {
    padding:15px;
    border-radius:10px;
    background:rgba(255,255,255,0.1);
    margin:10px 0;
}
.stButton>button {
    background: linear-gradient(90deg,#00c6ff,#0072ff);
    color:white;
    border-radius:8px;
    height:40px;
    width:100%;
}
#MainMenu, footer {visibility: hidden;}
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
    st.markdown("<div class='login-box'><h2>🧭 Missing Persons Detection</h2></div>", unsafe_allow_html=True)
    name, auth_status, username = authenticator.login("Login","main")

col1,col2,col3 = st.columns([1,2,1])
with col2:
    if auth_status:
        st.success(f"Welcome {name}")
    elif auth_status is False:
        st.error("Invalid credentials")
    else:
        st.warning("Please login")

# ---------- EMAIL FUNCTION ----------
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

Please verify immediately.
"""
        msg.set_content(body)

        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="image", subtype="jpeg", filename="detected.jpg")

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
            smtp.login(sender,password)
            smtp.send_message(msg)
    except Exception as e:
        print("Email Error:", e)

# ---------- MAIN ----------
if st.session_state.get("authentication_status"):

    authenticator.logout("Logout","sidebar")

    menu = st.sidebar.radio("Navigation",["Dashboard","Report","Reports","Detection"])

# ---------- DASHBOARD ----------
    if menu == "Dashboard":

        df = pd.read_csv("missing_data.csv") if os.path.exists("missing_data.csv") else pd.DataFrame()
        st.metric("Total Cases", len(df))

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
            os.makedirs("data",exist_ok=True)
            path = f"data/{name}.jpg"

            with open(path,"wb") as f:
                f.write(image.getbuffer())

            data = {
                "Name":name,
                "Image Path":path,
                "Phone":phone,
                "Location":location,
                "Admin Email":admin_email,
                "Family Email":family_email
            }

            df = pd.read_csv("missing_data.csv") if os.path.exists("missing_data.csv") else pd.DataFrame()
            df = pd.concat([df,pd.DataFrame([data])])
            df.to_csv("missing_data.csv",index=False)

            st.success("Saved")

# ---------- REPORTS ----------
    elif menu == "Reports":

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
            st.dataframe(df)

            if st.button("🗑 Clear All Reports"):
                os.remove("missing_data.csv")
                st.success("All data cleared")
                st.rerun()
        else:
            st.warning("No reports available")

# ---------- DETECTION ----------
    elif menu == "Detection":

        if not os.path.exists("missing_data.csv"):
            st.warning("No data available")
        else:
            df = pd.read_csv("missing_data.csv")

            known, names, emails = [],[],[]

            for _,r in df.iterrows():
                img = cv2.imread(r["Image Path"])
                if img is not None:
                    known.append(cv2.resize(img,(100,100)))
                    names.append(r["Name"])
                    emails.append(r["Admin Email"])

            os.makedirs("temp",exist_ok=True)
            sent=set()

            def match(a,b):
                return np.mean((a-b)**2) < 2000

            class Cam(VideoTransformerBase):
                def transform(self,frame):
                    img = frame.to_ndarray(format="bgr24")
                    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

                    face = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
                    faces = face.detectMultiScale(gray,1.3,5)

                    for (x,y,w,h) in faces:
                        f = cv2.resize(img[y:y+h,x:x+w],(100,100))
                        cv2.imwrite("temp/live.jpg", img)

                        for i,db in enumerate(known):
                            if match(f,db):

                                send_email(
                                    emails[i],
                                    names[i],
                                    df.iloc[i]["Location"],
                                    df.iloc[i]["Phone"],
                                    "temp/live.jpg"
                                )

                                break

                        cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

                    return img

            webrtc_streamer(key="cam",video_transformer_factory=Cam)
