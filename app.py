import streamlit as st
import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import pandas as pd
import os
import cv2
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
# LOAD USERS
# -------------------------------------------------
def load_users():
    if os.path.exists("login_info.txt"):
        with open("login_info.txt", "r") as f:
            lines = f.readlines()
            names = eval(lines[0].split("=")[1].strip())
            usernames = eval(lines[1].split("=")[1].strip())
    else:
        names, usernames = [], []

    if os.path.exists("hashed_pw.pkl"):
        with open("hashed_pw.pkl", "rb") as file:
            hashed_passwords = pickle.load(file)
    else:
        hashed_passwords = []

    return names, usernames, hashed_passwords


def save_users(names, usernames, hashed_passwords):
    with open("login_info.txt", "w") as f:
        f.write(f"names={names}\n")
        f.write(f"usernames={usernames}\n")

    with open("hashed_pw.pkl", "wb") as file:
        pickle.dump(hashed_passwords, file)


names, usernames, hashed_passwords = load_users()

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

# -------------------------------------------------
# LOGIN / REGISTER
# -------------------------------------------------
menu_auth = st.radio("Select Option", ["Login", "Register"])

if menu_auth == "Login":
    name, authentication_status, username = authenticator.login("Login", "main")

elif menu_auth == "Register":
    st.subheader("📝 Register")

    new_name = st.text_input("Name")
    new_username = st.text_input("Username")
    new_password = st.text_input("Password", type="password")

    if st.button("Register"):
        if new_name and new_username and new_password:

            if new_username in usernames:
                st.error("Username already exists")
            else:
                hashed = stauth.Hasher([new_password]).generate()[0]

                names.append(new_name)
                usernames.append(new_username)
                hashed_passwords.append(hashed)

                save_users(names, usernames, hashed_passwords)

                st.success("Registered successfully! Go to Login")

        else:
            st.error("Fill all fields")

    authentication_status = None


# -------------------------------------------------
# LOGIN STATUS
# -------------------------------------------------
if authentication_status:
    st.success(f"Welcome {name}")
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

        person_name = st.text_input("Name")
        image = st.file_uploader("Upload Image")
        phone = st.text_input("Phone Number")
        age = st.number_input("Age", min_value=1)
        admin_email = st.text_input("Admin Email")
        family_email = st.text_input("Family Email")
        location = st.text_input("Location")

        if st.button("Submit"):

            if all([person_name, image, phone, age, admin_email, family_email, location]):

                os.makedirs("data", exist_ok=True)
                file_path = f"data/{person_name}.jpg"

                with open(file_path, "wb") as f:
                    f.write(image.read())

                data = {
                    "Name": person_name,
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
# EMAIL FUNCTION
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

        except:
            st.warning("Email not configured")

# -------------------------------------------------
# LIVE DETECTION
# -------------------------------------------------
    elif menu == "Live Detection":

        st.header("🎥 Live Detection (Demo)")

        if os.path.exists("missing_data.csv"):

            df = pd.read_csv("missing_data.csv")
            detected = set()

            for _, row in df.iterrows():
                name = row.get("Name")

                if name not in detected:
                    detected.add(name)

                    st.success(f"🎉 Detected: {name}")

                    subject = f"{name} Detected"
                    body = f"""
Name: {name}
Location: {row.get("Location")}
Phone: {row.get("Phone Number")}
"""

                    send_email(row.get("Admin Email"), subject, body)
                    send_email(row.get("Family Email"), subject, body)

        else:
            st.warning("No data")

# -------------------------------------------------
# LOGIN FAIL
# -------------------------------------------------
elif authentication_status is False:
    st.error("Username/password incorrect")

else:
    st.warning("Please login or register")

# -------------------------------------------------
# CREATED BY FOOTER
# -------------------------------------------------
st.markdown("---")

st.markdown(
    """
    <div style="
        display:flex;
        align-items:center;
        justify-content:center;
        gap:15px;
        margin-top:20px;
    ">
        <img src="C:\Users\lovel\Downloads\pho.jpeg"
             style="
                width:60px;
                height:60px;
                border-radius:50%;
                border:2px solid white;
                object-fit:cover;
             ">

        <div style="text-align:left;">
            <p style="margin:0; font-size:14px; color:gray;">Created by</p>
            <h4 style="margin:0; color:white;">Gongati Naresh</h4>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
