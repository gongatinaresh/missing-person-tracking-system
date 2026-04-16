import streamlit as st
import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import pandas as pd
import os
import cv2
import smtplib
from email.message import EmailMessage

# -----------------------------------------
# PAGE CONFIG
# -----------------------------------------
st.set_page_config(page_title="Missing Persons Tracking System", layout="wide")

# -----------------------------------------
# UI STYLE (GLASS + GRADIENT)
# -----------------------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
}

.glass {
    background: rgba(255, 255, 255, 0.1);
    padding: 30px;
    border-radius: 15px;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.card {
    background: rgba(255,255,255,0.1);
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 15px;
}

input {
    background-color: rgba(255,255,255,0.2) !important;
    color: white !important;
}

button {
    background: linear-gradient(90deg, #ff6a00, #ee0979);
    color: white;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------
# TITLE
# -----------------------------------------
st.title("🧭 Missing Persons Tracking System")

# -----------------------------------------
# LOAD LOGIN DATA
# -----------------------------------------
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

# -----------------------------------------
# LOGIN UI (CENTERED)
# -----------------------------------------
col1, col2, col3 = st.columns([1,2,1])

with col2:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    authenticator.login("Login", "main")
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------
# EMAIL FUNCTION
# -----------------------------------------
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

# -----------------------------------------
# AFTER LOGIN
# -----------------------------------------
if st.session_state.get("authentication_status"):

    st.sidebar.title("👤 Dashboard")
    st.sidebar.markdown(f"### {st.session_state['name']}")
    authenticator.logout("Logout", "sidebar")

    menu = st.sidebar.radio(
        "Navigation",
        ["🏠 Home", "➕ Report Missing Person", "📋 View Reports", "🎥 Live Detection"]
    )

    # -----------------------------------------
    # HOME
    # -----------------------------------------
    if menu == "🏠 Home":
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("Welcome")
        st.write("AI-Based Missing Person Detection System")
        st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------------------
    # REPORT
    # -----------------------------------------
    elif menu == "➕ Report Missing Person":
        st.markdown('<div class="card">', unsafe_allow_html=True)

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

        st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------------------
    # VIEW REPORTS
    # -----------------------------------------
    elif menu == "📋 View Reports":
        st.markdown('<div class="card">', unsafe_allow_html=True)

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")
            st.dataframe(df)

        else:
            st.warning("No data available")

        st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------------------
    # LIVE DETECTION (DEMO)
    # -----------------------------------------
    elif menu == "🎥 Live Detection":
        st.markdown('<div class="card">', unsafe_allow_html=True)

        st.info("Demo detection (simulated)")

        if os.path.exists("missing_data.csv"):
            df = pd.read_csv("missing_data.csv")

            for _, row in df.iterrows():
                st.success(f"Detected: {row['Name']}")

                subject = f"Alert: {row['Name']} Detected"
                body = f"{row['Name']} may be found at {row['Location']}"

                send_email(row["Family Email"], subject, body)

        else:
            st.warning("No data available")

        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------
# LOGIN FAIL
# -----------------------------------------
elif st.session_state.get("authentication_status") is False:
    st.error("Invalid Username or Password")

else:
    st.info("Please login")
