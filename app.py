import streamlit as st
import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import pandas as pd
import os
import cv2

# Email
import smtplib
from email.message import EmailMessage

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

        # attach image
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
# LIVE DETECTION (SIMPLIFIED)
# -------------------------------------------------
    elif menu == "Live Detection":

        st.header("🎥 Live Detection (Demo Version)")

        if os.path.exists("missing_data.csv"):

            df = pd.read_csv("missing_data.csv")

            detected_names = set()

            # simulate detection
            for _, row in df.iterrows():

                try:
                    name = row.get("Name")

                    if name not in detected_names:
                        detected_names.add(name)

                        st.success(f"🎉 Detected: {name}")

                        subject = f"🔍 AI Alert: {name} Detected"

                        body = f"""
Live Camera Detection Alert

Name: {name}
Location: {row.get("Location")}
Phone: {row.get("Phone Number")}
"""

                        # send emails
                        if row.get("Admin Email"):
                            send_email(row.get("Admin Email"), subject, body)

                        if row.get("Family Email"):
                            send_email(row.get("Family Email"), subject, body)

                except Exception as e:
                    st.error(f"Error: {e}")

        else:
            st.warning("No data available")


# -------------------------------------------------
# LOGIN FAIL
# -------------------------------------------------
elif st.session_state.get("authentication_status") is False:
    st.error("Username/password incorrect")

else:
    st.warning("Please login")
