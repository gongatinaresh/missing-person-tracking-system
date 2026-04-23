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

# ---------------- UI STYLE ----------------
st.markdown("""
<style>
.block-container {padding-top: 1rem;}
.element-container:empty {display:none;}
.stApp {
    background: linear-gradient(135deg, #0f2027,#203a43,#2c5364);
    font-family: 'Segoe UI';
}
.card {
    padding:20px;
    border-radius:16px;
    background:rgba(255,255,255,0.06);
    backdrop-filter:blur(15px);
    box-shadow:0 8px 25px rgba(0,0,0,0.4);
    margin-bottom:15px;
    transition:0.3s;
}
.card:hover {
    transform:scale(1.02);
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

# ---------------- LOGIN ----------------
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

# ---------------- EMAIL ----------------
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

# ---------------- MAIN ----------------
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

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
        else:
            df = pd.DataFrame()

        total = len(df)

        col1,col2,col3 = st.columns(3)
        col1.markdown(f"<div class='card'><h2>{total}</h2><p>Total Cases</p></div>", unsafe_allow_html=True)
        col2.markdown("<div class='card'><h2>🟢</h2><p>Detection Active</p></div>", unsafe_allow_html=True)
        col3.markdown("<div class='card'><h2>📧</h2><p>Alerts Enabled</p></div>", unsafe_allow_html=True)

        st.markdown("<div class='card'><h3>🔍 Match Result</h3></div>", unsafe_allow_html=True)

        c1,c2,c3 = st.columns([2,1,2])

        with c1:
            if "live_img" in st.session_state:
                st.image(st.session_state["live_img"], caption="Live Image")

        with c2:
            if "match_name" in st.session_state:
                st.markdown(f"""
                <div style='text-align:center;color:#00ff9f;font-size:20px'>
                ✔ MATCH FOUND <br><br>
                <b>{st.session_state["match_name"]}</b>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No match yet")

        with c3:
            if "db_img" in st.session_state:
                st.image(st.session_state["db_img"], caption="Matched Image")

        st.markdown("<div class='card'><h3>📋 Recent Reports</h3></div>", unsafe_allow_html=True)

        if not df.empty:
            st.dataframe(df.tail(5))

# ---------------- REPORT ----------------
    elif menu == "Report":

        st.markdown("<div class='card'><h3>➕ Report Missing Person</h3></div>", unsafe_allow_html=True)

        name = st.text_input("Name")
        phone = st.text_input("Phone")
        location = st.text_input("Location")
        admin_email = st.text_input("Admin Email")

        image = st.file_uploader("Upload Image")

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
                    "Admin Email":admin_email
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

        if os.path.exists("missing_data.csv"):
            df=pd.read_csv("missing_data.csv")
            st.dataframe(df)

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

                                st.session_state["live_img"] = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                                st.session_state["db_img"] = cv2.cvtColor(db, cv2.COLOR_BGR2RGB)
                                st.session_state["match_name"] = r["Name"]

                                cv2.putText(img,r["Name"],(x,y-10),1,1,(0,255,0),2)

                                if st.session_state.get("last_email") != r["Name"]:
                                    send_email(r["Admin Email"],"Match Found",r["Name"])
                                    st.session_state["last_email"] = r["Name"]

                                break

                        cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

                return img

        webrtc_streamer(key="cam",video_transformer_factory=Cam)
