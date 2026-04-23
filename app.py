import streamlit as st
import cv2
import numpy as np
import pandas as pd
import os
import base64
import smtplib
from email.message import EmailMessage
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

# ---------------- DARK UI ----------------
st.markdown("""
<style>
.stApp {
    background: #0e1117;
    color: white;
}
.sidebar .sidebar-content {
    background: #111827;
}
.card {
    background: #1f2937;
    padding: 20px;
    border-radius: 12px;
    margin: 10px;
    text-align: center;
}
.metric {
    font-size: 28px;
    font-weight: bold;
}
.title {
    font-size: 22px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.markdown("<h2 style='text-align:center'>🔐 Login</h2>", unsafe_allow_html=True)
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "admin" and pwd == "1234":
            st.session_state.login = True
        else:
            st.error("Invalid Login")
    st.stop()

# ---------------- EMAIL ----------------
def send_email(to_email, name):
    sender = "your_email@gmail.com"
    password = "your_app_password"

    msg = EmailMessage()
    msg["Subject"] = "Missing Person Found"
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(f"{name} has been detected.")

    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login(sender,password)
        smtp.send_message(msg)

# ---------------- SIDEBAR ----------------
menu = st.sidebar.radio("Menu",
["Dashboard","Report","Reports","Detection"])

# ---------------- LOAD DATA ----------------
if os.path.exists("data.csv"):
    df = pd.read_csv("data.csv")
else:
    df = pd.DataFrame()

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":

    st.title("📊 Missing Person Dashboard")

    col1,col2,col3,col4 = st.columns(4)

    col1.markdown(f"<div class='card'><div class='metric'>{len(df)}</div>Total Records</div>", unsafe_allow_html=True)
    col2.markdown("<div class='card'><div class='metric'>8</div>Matches Today</div>", unsafe_allow_html=True)
    col3.markdown("<div class='card'><div class='metric'>5</div>Alerts Sent</div>", unsafe_allow_html=True)
    col4.markdown("<div class='card'><div class='metric'>10:20 AM</div>Last Match</div>", unsafe_allow_html=True)

    st.subheader("📈 Accuracy Graph")
    chart_data = pd.DataFrame({
        "Accuracy":[70,75,80,85,88,90]
    })
    st.line_chart(chart_data)

    st.subheader("📋 Recent Reports")
    if not df.empty:
        st.dataframe(df.tail(5))
    else:
        st.warning("No data")

# ---------------- REPORT ----------------
elif menu == "Report":

    st.title("➕ Report Missing Person")

    name = st.text_input("Name")
    phone = st.text_input("Phone")
    location = st.text_input("Last Location")
    email = st.text_input("Email")

    img_file = st.file_uploader("Upload Image")

    if st.button("Submit"):
        if img_file:
            os.makedirs("images", exist_ok=True)
            path = f"images/{name}.jpg"
            with open(path,"wb") as f:
                f.write(img_file.getbuffer())

            data = {
                "Name":name,
                "Phone":phone,
                "Location":location,
                "Email":email,
                "Image":path
            }

            if os.path.exists("data.csv"):
                df = pd.read_csv("data.csv")
                df = pd.concat([df, pd.DataFrame([data])])
            else:
                df = pd.DataFrame([data])

            df.to_csv("data.csv", index=False)

            st.success("Saved Successfully")

            # PROFILE STYLE
            st.image(path, width=200)
            st.write(f"**Name:** {name}")
            st.write(f"**Phone:** {phone}")
            st.write(f"**Location:** {location}")

# ---------------- REPORTS ----------------
elif menu == "Reports":

    st.title("📋 Reports")

    if not df.empty:
        st.dataframe(df)

        if st.button("Clear Reports"):
            os.remove("data.csv")
            st.success("Cleared")
    else:
        st.warning("No Reports")

# ---------------- DETECTION ----------------
elif menu == "Detection":

    st.title("🎥 Live Detection")

    col1,col2 = st.columns(2)

    def match_faces(a,b):
        a = cv2.resize(a,(100,100))
        b = cv2.resize(b,(100,100))
        return np.mean((a-b)**2) < 2000

    class Cam(VideoTransformerBase):
        def transform(self,frame):
            img = frame.to_ndarray(format="bgr24")
            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            face = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
            faces = face.detectMultiScale(gray,1.3,5)

            if not df.empty:
                for (x,y,w,h) in faces:
                    f = img[y:y+h,x:x+w]

                    for _,r in df.iterrows():
                        db = cv2.imread(r["Image"])

                        if db is not None and match_faces(f,db):

                            # DRAW NAME
                            cv2.putText(img,r["Name"],(x,y-10),
                            cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,255,0),2)

                            # SHOW MATCH RESULT
                            col1.image(cv2.cvtColor(f,cv2.COLOR_BGR2RGB),
                            caption="Live Image",width=300)

                            col2.image(cv2.cvtColor(db,cv2.COLOR_BGR2RGB),
                            caption="Database Image",width=300)

                            # EMAIL
                            send_email(r["Email"], r["Name"])

                    cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

            return img

    webrtc_streamer(key="cam", video_transformer_factory=Cam)
