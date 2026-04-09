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
# Page Config
# -------------------------------------------------
st.set_page_config(page_title="Missing Persons Tracking System")

# -------------------------------------------------
# Title
# -------------------------------------------------
st.title("🧭 Missing Persons Tracking System")

# -------------------------------------------------
# Load Login Info
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

authenticator = stauth.Authenticate(
    credentials,
    "missing_person_app",
    "abcdef",
    cookie_expiry_days=30
)

# 🔥 FIXED HERE
authenticator.login("Login", "sidebar")

# -------------------------------------------------
# Email Function
# -------------------------------------------------
def send_email(to_email, subject, body):
    try:
        sender_email = st.secrets["EMAIL"]
        app_password = st.secrets["EMAIL_PASSWORD"]

        msg = EmailMessage()
        msg.set_content(body)

        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)

        return True

    except Exception as e:
        st.error(f"Email failed: {e}")
        return False


# -------------------------------------------------
# AFTER LOGIN
# -------------------------------------------------
if st.session_state.get("authentication_status"):

    st.success(f"Welcome {st.session_state['name']}")
    authenticator.logout("Logout", "sidebar")

    menu = st.selectbox(
        "Select Option",
        ["Report Missing Person", "View Reports", "Live Detection"]
    )

# -------------------------------------------------
# REPORT
# -------------------------------------------------
    if menu == "Report Missing Person":

        st.header("➕ Report Missing Person")

        name = st.text_input("Name")
        image = st.file_uploader("Upload Image")
        phone = st.text_input("Phone Number")
        age = st.number_input("Age", min_value=1)
        admin_email = st.text_input("Admin Email")
        family_email = st.text_input("Family Email")
        location = st.text_input("Location")

        if st.button("Submit"):

            if all([name, image, phone, age, admin_email, family_email, location]):

                os.makedirs("data", exist_ok=True)
                file_path = f"data/{name}.jpg"

                with open(file_path, "wb") as f:
                    f.write(image.read())

                data = {
                    "Name": name,
                    "Image Path": file_path,
                    "Phone Number": phone,
                    "Location": location,
                    "Admin Email": admin_email,
                    "Family Email": family_email
                }

                csv_file = "missing_data.csv"

                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
                else:
                    df = pd.DataFrame([data])

                df.to_csv(csv_file, index=False)

                st.success("Saved Successfully ✅")

            else:
                st.error("Fill all fields")

# -------------------------------------------------
# VIEW REPORTS
# -------------------------------------------------
    elif menu == "View Reports":

        st.header("📋 Reports")

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
            st.dataframe(df)

            if st.button("Clear Reports"):
                os.remove("missing_data.csv")
                st.success("Cleared ✅")

        else:
            st.warning("No data")

# -------------------------------------------------
# LIVE CAMERA + MATCHING
# -------------------------------------------------
    elif menu == "Live Detection":

        st.header("🎥 Live Camera Detection + Matching")

        # ---------- MATCH FUNCTION ----------
        def match_faces(img1, img2):
            try:
                img1 = cv2.resize(img1, (100, 100))
                img2 = cv2.resize(img2, (100, 100))
                diff = np.mean((img1 - img2) ** 2)
                return diff < 2000
            except:
                return False

        # ---------- LOAD DATA ----------
        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
        else:
            df = None

        # ---------- CAMERA CLASS ----------
        class VideoTransformer(VideoTransformerBase):
            def __init__(self):
                self.detected = set()

            def transform(self, frame):
                img = frame.to_ndarray(format="bgr24")

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                )

                faces = face_cascade.detectMultiScale(gray, 1.3, 5)

                if df is not None:
                    for (x, y, w, h) in faces:
                        face = img[y:y+h, x:x+w]

                        for _, row in df.iterrows():
                            try:
                                db_img = cv2.imread(row["Image Path"])

                                if db_img is not None and match_faces(face, db_img):

                                    name = row["Name"]

                                    if name not in self.detected:
                                        self.detected.add(name)

                                        subject = f"🚨 ALERT: {name} Detected"

                                        body = f"""
Match Found!

Name: {name}
Location: {row.get("Location")}
Phone: {row.get("Phone Number")}
"""

                                        if row.get("Admin Email"):
                                            send_email(row.get("Admin Email"), subject, body)

                                        if row.get("Family Email"):
                                            send_email(row.get("Family Email"), subject, body)

                                    cv2.putText(img, name, (x, y-10),
                                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

                                    break
                            except:
                                pass

                        cv2.rectangle(img, (x, y), (x+w, y+h), (0,255,0), 2)

                return img

        webrtc_streamer(
            key="camera",
            video_transformer_factory=VideoTransformer
        )

# -------------------------------------------------
# LOGIN FAIL
# -------------------------------------------------
elif st.session_state.get("authentication_status") is False:
    st.error("Username/password incorrect")

else:
    st.warning("Please login")
