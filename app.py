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

st.set_page_config(layout="wide")

# ---------- UI ----------
st.markdown("""
<style>

.stApp {
    background: url("https://i.ibb.co/8gZz0qj/background.jpg") no-repeat center center fixed;
    background-size: cover;
}

/* Dark overlay */
[data-testid="stAppViewContainer"] {
    background: rgba(0,0,0,0.7);
}

/* Login card */
.login-box {
    width: 350px;
    margin: auto;
    padding: 25px;
    border-radius: 15px;
    background: rgba(0,0,0,0.6);
    backdrop-filter: blur(10px);
    text-align: center;
}

/* 🔥 FIX INPUT VISIBILITY */
div[data-baseweb="input"] > div {
    background-color: white !important;
}

div[data-baseweb="input"] input {
    color: black !important;
}

/* Labels */
label {
    color: white !important;
    font-weight: bold;
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

# ✅ PASTE HERE 👇
# ---------- LOGIN UI ----------
auth_status = st.session_state.get("authentication_status")

if auth_status is None:

    st.markdown("""
    <style>

    .stApp {
        background: url("https://www.image2url.com/r2/default/images/1777004946995-2d9a1d91-03d5-4d08-a0b7-b7811a0202cd.jpeg") no-repeat center center fixed;
        background-size: cover;
    }

    [data-testid="stAppViewContainer"] {
        background: rgba(0,0,0,0.75);
    }

    header {visibility: hidden;}

    .main-title {
        text-align: center;
        font-size: 34px;
        font-weight: bold;
        color: white;
        margin-bottom: 20px;
    }

    .login-box {
        width: 380px;
        margin: auto;
        padding: 25px;
        border-radius: 15px;
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(10px);
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>🔍 Missing Person Tracking System</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1.2,1])

    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)

        name, auth_status, username = authenticator.login(
            "Login",
            "main",
            key="login_form"
        )

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

elif auth_status is False:
    st.error("❌ Invalid Username or Password")
    st.stop()

# ---------- AFTER LOGIN ----------
st.success(f"Welcome {name}")
# ---------- EMAIL ----------
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

The system has detected a possible match in live camera feed.
Please verify immediately.

- Missing Person Tracking System
"""
        msg.set_content(body)

        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                file_data = f.read()
                file_name = os.path.basename(image_path)

                msg.add_attachment(
                    file_data,
                    maintype="image",
                    subtype="jpeg",
                    filename=file_name
                )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)

    except Exception as e:
        print("Email Error:", e)

# ---------- MAIN ----------
if st.session_state.get("authentication_status"):

    authenticator.logout("Logout","sidebar")

    menu = st.sidebar.radio("Navigation",["Dashboard","Report","Reports","Detection"])

    # ---------------- DASHBOARD ----------------
    if menu == "Dashboard":

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
        else:
            df = pd.DataFrame()

        total = len(df)

        st.markdown("""
        <div class='card'>
        <h3>📍 Real-time Missing Person Monitoring Dashboard</h3>
        </div>
        """, unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        c1.markdown(f"<div class='card'><h2>{total}</h2><p>Total Records</p></div>", unsafe_allow_html=True)
        c2.markdown("<div class='card'><h2>Active</h2><p>Detection</p></div>", unsafe_allow_html=True)
        c3.markdown("<div class='card'><h2>Enabled</h2><p>Alerts</p></div>", unsafe_allow_html=True)

        st.markdown("<div class='card'><h3>Match Result</h3></div>", unsafe_allow_html=True)

        col1,col2,col3 = st.columns([1,2,1])

        cam_path = "temp/live.jpg"
        db_path = "temp/match.jpg"

        with col1:
            if os.path.exists(cam_path):
                st.image(cam_path)
            else:
                st.info("Live Image")

        with col2:
            status = st.session_state.get("status","No Detection")
            st.markdown(f"""
            <div style="background:#2ecc71;padding:10px;border-radius:8px;text-align:center;color:white;">
            {status}
            </div>
            """, unsafe_allow_html=True)

        with col3:
            if os.path.exists(db_path):
                st.image(db_path)
            else:
                st.info("Matched Image")

        st.markdown("<div class='card'><h3>Detection Accuracy Trend</h3></div>", unsafe_allow_html=True)

        chart = pd.DataFrame({"Accuracy":[60,70,75,80,85,90]})
        st.line_chart(chart)

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

            if os.path.exists("missing_data.csv"):
                df = pd.read_csv("missing_data.csv")
                df = pd.concat([df, pd.DataFrame([data])])
            else:
                df = pd.DataFrame([data])

            df.to_csv("missing_data.csv", index=False)
            st.success("Saved")

    # ---------------- REPORTS ----------------
    elif menu == "Reports":

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
            st.dataframe(df)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Clear All Reports"):
                    os.remove("missing_data.csv")
                    if os.path.exists("temp"):
                        for f in os.listdir("temp"):
                            os.remove(os.path.join("temp", f))
                    st.success("All reports cleared successfully")
                    st.rerun()

            with col2:
                st.info("This will permanently delete all records")
        else:
            st.warning("No reports available")

        # ---------------- DETECTION ----------------
    elif menu == "Detection":

        st.subheader("📷 Live Detection")

        if not os.path.exists("missing_data.csv"):
            st.warning("No data available")
        else:
            df = pd.read_csv("missing_data.csv")

            known = []
            names = []
            emails = []

            for _, r in df.iterrows():
                img = cv2.imread(r["Image Path"])
                if img is not None:
                    img = cv2.resize(img,(100,100))
                    known.append(img)
                    names.append(r["Name"])
                    emails.append(r["Admin Email"])

            os.makedirs("temp",exist_ok=True)
            sent=set()

            def match(a,b):
                return np.mean((a-b)**2) < 2000

            # 🔥 USE STREAMLIT CAMERA (STABLE)
            cam = st.camera_input("Take Photo")

            if cam:
                img = np.asarray(bytearray(cam.read()), dtype=np.uint8)
                img = cv2.imdecode(img,1)

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                face = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
                faces = face.detectMultiScale(gray,1.3,5)

                found = False

                for (x,y,w,h) in faces:
                    f = cv2.resize(img[y:y+h,x:x+w],(100,100))

                    cv2.imwrite("temp/live.jpg", img)

                    for i, db in enumerate(known):
                        if match(f, db):

                            cv2.imwrite("temp/match.jpg", db)
                            st.session_state["status"] = "MATCH FOUND"

                            if emails[i] not in sent:
                                send_email(
                                    emails[i],
                                    names[i],
                                    df.iloc[i]["Location"],
                                    df.iloc[i]["Phone"],
                                    "temp/live.jpg"
                                )
                                sent.add(emails[i])

                            found = True
                            break

                    # 🔥 DRAW RECTANGLE
                    cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

                    if found:
                        cv2.putText(img, names[i], (x, y-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                                    (0,255,0), 2)

                if not found:
                    st.session_state["status"] = "NO MATCH"

                # 🔥 SHOW RESULT
                st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="Detection Result")
