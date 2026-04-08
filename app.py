import streamlit as st
import pandas as pd
import os
import smtplib
from email.message import EmailMessage

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Missing Persons Tracking System")
st.title("🧭 Missing Persons Tracking System")

# -------------------------------------------------
# USER FILE
# -------------------------------------------------
USER_FILE = "users.csv"

if os.path.exists(USER_FILE):
    users = pd.read_csv(USER_FILE)
else:
    users = pd.DataFrame(columns=["username", "password"])

# -------------------------------------------------
# LOGIN / REGISTER MENU
# -------------------------------------------------
menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

# ---------------- REGISTER ----------------
if menu == "Register":
    st.subheader("Create Account")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        if username in users["username"].values:
            st.error("Username already exists")
        else:
            new_user = pd.DataFrame([[username, password]],
                                    columns=["username", "password"])
            users = pd.concat([users, new_user], ignore_index=True)
            users.to_csv(USER_FILE, index=False)
            st.success("Account created successfully ✅")

# ---------------- LOGIN ----------------
elif menu == "Login":
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = users[(users["username"] == username) & (users["password"] == password)]

        if not user.empty:
            st.session_state["user"] = username
            st.success("Login successful 🎉")
        else:
            st.error("Invalid credentials")

# -------------------------------------------------
# EMAIL FUNCTION
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
# AFTER LOGIN
# -------------------------------------------------
if "user" in st.session_state:

    st.success(f"Welcome {st.session_state['user']}")

    menu = st.selectbox(
        "Select Option",
        ["Report Missing Person", "View Reports", "Live Detection"]
    )

# ---------------- REPORT ----------------
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

# ---------------- VIEW ----------------
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

# ---------------- DETECTION ----------------
    elif menu == "Live Detection":

        st.header("🎥 Live Detection")

        if os.path.exists("missing_data.csv"):

            df = pd.read_csv("missing_data.csv")

            detected_names = set()

            for _, row in df.iterrows():

                try:
                    name = row.get("Name")

                    if name not in detected_names:
                        detected_names.add(name)

                        st.success(f"🎉 Detected: {name}")

                        subject = f"🔍 AI Alert: {name} Detected"

                        body = f"""
Live Detection Alert

Name: {name}
Location: {row.get("Location")}
Phone: {row.get("Phone Number")}
"""

                        if row.get("Admin Email"):
                            send_email(row.get("Admin Email"), subject, body)

                        if row.get("Family Email"):
                            send_email(row.get("Family Email"), subject, body)

                except Exception as e:
                    st.error(f"Error: {e}")

        else:
            st.warning("No data available")

else:
    st.warning("Please login or register")
