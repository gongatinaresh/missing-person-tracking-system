import streamlit as st
import pandas as pd
import os
import cv2
import numpy as np
import smtplib
from email.message import EmailMessage
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import pickle
from pathlib import Path
import streamlit_authenticator as stauth

# ================= CONFIG =================
st.set_page_config(layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.stApp {background:#0f172a;font-family:'Segoe UI';}
section[data-testid="stSidebar"] {background:#020617;color:white;}

.topbar {
    background:#020617;color:white;
    padding:12px;border-radius:8px;
    margin-bottom:15px;
    display:flex;justify-content:space-between;
}

.card {
    background:#1e293b;padding:18px;
    border-radius:12px;color:white;
    box-shadow:0 4px 12px rgba(0,0,0,0.4);
    margin-bottom:10px;
}

.metric {text-align:center;}
.match-box {text-align:center;color:#22c55e;font-weight:bold;font-size:20px;}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
with open("login_info.txt", "r") as f:
    lines = f.readlines()

names = eval(lines[0].split("=")[1].strip())
usernames = eval(lines[1].split("=")[1].strip())

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

if auth_status is False:
    st.error("Invalid Username or Password")
    st.stop()
elif auth_status is None:
    st.warning("Enter login details")
    st.stop()

# ================= AFTER LOGIN =================
if auth_status:

    authenticator.logout("Logout", "sidebar")

    st.success(f"Welcome {name}")

    # ================= EMAIL =================
    def send_email(to_email, subject, person_data, live_img):
        try:
            sender_email = st.secrets["EMAIL"]
            password = st.secrets["EMAIL_PASSWORD"]

            msg = EmailMessage()

            body = f"""
MATCH FOUND 🚨

Name: {person_data['Name']}
Phone: {person_data['Phone']}
Last Seen: {person_data['Location']}
            """

            msg.set_content(body)
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = to_email

            _, buffer = cv2.imencode(".jpg", live_img)
            msg.add_attachment(buffer.tobytes(),
                               maintype='image',
                               subtype='jpeg',
                               filename='detected.jpg')

            with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
                smtp.login(sender_email,password)
                smtp.send_message(msg)

        except Exception as e:
            print(e)

    # ================= LOAD DATA =================
    if os.path.exists("missing_data.csv"):
        df = pd.read_csv("missing_data.csv")
    else:
        df = pd.DataFrame()

    # ================= SIDEBAR =================
    menu = st.sidebar.radio("Menu",["Dashboard","Report","Reports","Detection"])

    # ================= TOPBAR =================
    st.markdown(f"""
    <div class='topbar'>
    Missing Person System | 🟢 Active | ⏰ {pd.Timestamp.now().strftime("%H:%M:%S")}
    </div>
    """, unsafe_allow_html=True)

    # ================= DASHBOARD =================
    if menu == "Dashboard":

        total = len(df)

        c1,c2,c3 = st.columns(3)
        c1.markdown(f"<div class='card metric'><h2>{total}</h2>Total</div>", unsafe_allow_html=True)
        c2.markdown("<div class='card metric'><h2>🟢</h2>Detection</div>", unsafe_allow_html=True)
        c3.markdown("<div class='card metric'><h2>📧</h2>Alerts</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'><h3>Match Result</h3></div>", unsafe_allow_html=True)

        col1,col2,col3 = st.columns([2,1,2])

        with col1:
            if "live_img" in st.session_state:
                st.image(st.session_state["live_img"])

        with col2:
            if "match_name" in st.session_state:
                st.markdown(f"<div class='match-box'>✔ {st.session_state['match_name']}</div>", unsafe_allow_html=True)

        with col3:
            if "db_img" in st.session_state:
                st.image(st.session_state["db_img"])

    # ================= REPORT =================
    elif menu == "Report":

        col1,col2 = st.columns([2,1])

        with col1:
            name_input = st.text_input("Name")
            phone = st.text_input("Phone")
            location = st.text_input("Location")
            email = st.text_input("Email")

        with col2:
            image = st.file_uploader("Upload Image")

        if st.button("Submit"):
            if image:
                os.makedirs("data",exist_ok=True)
                path=f"data/{name_input}.jpg"

                with open(path,"wb") as f:
                    f.write(image.getbuffer())

                new = pd.DataFrame([{
                    "Name":name_input,
                    "Image Path":path,
                    "Phone":phone,
                    "Location":location,
                    "Email":email
                }])

                df = pd.concat([df,new])
                df.to_csv("missing_data.csv",index=False)
                st.success("Saved")

    # ================= REPORTS =================
    elif menu == "Reports":

        if not df.empty:
            st.dataframe(df)

            col1,col2 = st.columns(2)

            with col1:
                st.download_button("Download", df.to_csv(index=False), "reports.csv")

            with col2:
                if st.button("Clear Reports"):
                    os.remove("missing_data.csv")
                    st.success("Cleared")
                    st.rerun()

    # ================= DETECTION =================
    elif menu == "Detection":

        def match_faces(a,b):
            a=cv2.resize(a,(100,100))
            b=cv2.resize(b,(100,100))
            return np.mean((a-b)**2)<2000

        class Cam(VideoTransformerBase):
            def transform(self,frame):
                img=frame.to_ndarray(format="bgr24")
                gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

                face=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
                faces=face.detectMultiScale(gray,1.3,5)

                for (x,y,w,h) in faces:
                    face_img = img[y:y+h,x:x+w]

                    for _,row in df.iterrows():
                        db_img = cv2.imread(row["Image Path"])

                        if db_img is not None and match_faces(face_img, db_img):

                            st.session_state["live_img"] = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                            st.session_state["db_img"] = cv2.cvtColor(db_img, cv2.COLOR_BGR2RGB)
                            st.session_state["match_name"] = row["Name"]

                            if st.session_state.get("last_email") != row["Name"]:
                                send_email(row["Email"], "Match Found", row, face_img)
                                st.session_state["last_email"] = row["Name"]

                            cv2.putText(img,row["Name"],(x,y-10),1,1,(0,255,0),2)
                            break

                    cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

                return img

        webrtc_streamer(key="cam", video_transformer_factory=Cam)

        # SHOW RESULT CENTER
        if "live_img" in st.session_state:

            st.markdown("## 🔍 Match Result")

            c1,c2,c3 = st.columns([2,1,2])

            with c1:
                st.image(st.session_state["live_img"])

            with c2:
                st.markdown(f"<div class='match-box'>✔ {st.session_state['match_name']}</div>", unsafe_allow_html=True)

            with c3:
                st.image(st.session_state["db_img"])
