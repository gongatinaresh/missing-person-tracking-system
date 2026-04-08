import streamlit as st
import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import pandas as pd
import os
from utils import save_admin_data

import smtplib
from email.message import EmailMessage
import cv2


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

authenticator = stauth.Authenticate(credentials, "missing_persons_app", "abcdef", 30)
authenticator.login("Login", "main")


# -------------------------------------------------
# Email Function
# -------------------------------------------------
def send_email(to_email, subject, body, image_path=None):

    try:
        sender_email = st.secrets["EMAIL"]
        app_password = st.secrets["EMAIL_PASSWORD"]

        msg = EmailMessage()
        msg.set_content(body)

        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_email

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as img:
                msg.add_attachment(
                    img.read(),
                    maintype="image",
                    subtype="jpeg",
                    filename=os.path.basename(image_path)
                )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)

        return True

    except Exception as e:
        st.error(f"Email failed: {e}")
        return False


# -------------------------------------------------
# After Login
# -------------------------------------------------
if st.session_state.get("authentication_status"):

    st.success(f"Welcome {st.session_state['name']}")
    authenticator.logout("Logout", "sidebar")

    page = st.sidebar.radio(
        "Menu",
        ["Report Missing Person", "Reports from Users", "Live Camera Detection"]
    )


# -------------------------------------------------
# Report Missing Person
# -------------------------------------------------
    if page == "Report Missing Person":

        st.header("➕ Report Missing Person")

        person_name = st.text_input("Name")
        person_image = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
        contact_number = st.text_input("Phone Number")
        age = st.number_input("Age", min_value=1)
        admin_email = st.text_input("Admin Email")
        family_email = st.text_input("Family Email")
        location = st.text_input("Last Seen Location")

        if st.button("Submit Report"):

            if all([person_name, person_image, contact_number, age, admin_email, family_email, location]):

                img_path = save_admin_data(
                    person_image,
                    person_name,
                    age,
                    contact_number,
                    family_email,
                    location,
                    admin_email
                )

                st.image(img_path, caption="Saved Image")
                st.success("Missing person report saved")

            else:
                st.error("Please fill all fields")


# -------------------------------------------------
# Reports
# -------------------------------------------------
    elif page == "Reports from Users":

        st.header("📋 Reports")

        csv_path = os.path.join("data", "admin_data", "missing_data.csv")

        if os.path.isfile(csv_path):
            df = pd.read_csv(csv_path, dtype=str)
            st.dataframe(df)
        else:
            st.warning("No reports found")


# -------------------------------------------------
# LIVE CAMERA DETECTION (MAIN FEATURE 🚀)
# -------------------------------------------------
    elif page == "Live Camera Detection":

        st.header("📷 Live Camera Detection (CCTV Style)")

        run = st.checkbox("Start Camera")

        FRAME_WINDOW = st.image([])

        camera = cv2.VideoCapture(0)

        csv_path = os.path.join("data", "admin_data", "missing_data.csv")

        detected_names = set()

        if run:

            while True:
                ret, frame = camera.read()

                if not ret:
                    st.error("Camera not working")
                    break

                FRAME_WINDOW.image(frame, channels="BGR")

                temp_path = "live.jpg"
                cv2.imwrite(temp_path, frame)

                if os.path.isfile(csv_path):

                    df = pd.read_csv(csv_path, dtype=str)

                    for _, row in df.iterrows():

                        try:
                             name = row.get("Name")

                             if name not in detected_names:
                                detected_names.add(name)

                                st.success(f"🚨 Detected: {name}")

                                subject = f"🔎 AI Surveillance Alert: {name} Detected"

                                body = f"""
Live Camera Detection Alert

Name: {name}
Location: {row.get("Location")}
Phone: {row.get("Phone Number")}
"""

                                    send_email(row.get("Admin Email"), subject, body, temp_path)
                                    send_email(row.get("Family Email"), subject, body, temp_path)

                                cv2.putText(frame, name, (50, 50),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                                break

                        except:
                            pass


elif st.session_state.get("authentication_status") is False:
    st.error("Username/password incorrect")

else:
    st.warning("Please login")
