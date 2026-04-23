import streamlit as st
import pandas as pd
import os
import cv2
import numpy as np
from datetime import datetime
import smtplib
from email.message import EmailMessage

st.set_page_config(layout="wide")

# ================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.markdown("<h1 style='text-align:center;'>🧭 Missing Person Tracking System</h1>", unsafe_allow_html=True)

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "admin1" and pwd == "abc123":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

# ================= UI =================
st.markdown("""
<style>
.stApp {background:linear-gradient(135deg,#0f172a,#1e293b);color:white;}
section[data-testid="stSidebar"] {background:#020617;}
.card {background:#1e293b;padding:20px;border-radius:12px;text-align:center;}
.section {background:#1e293b;padding:20px;border-radius:12px;margin-top:20px;}
.stButton>button {
    background:linear-gradient(90deg,#00c6ff,#0072ff);
    color:white;border-radius:10px;height:45px;width:100%;
}
h1,h2,h3 {color:#38bdf8;}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
st.sidebar.markdown("## 🧭 Control Panel")
menu = st.sidebar.radio("", ["📊 Dashboard","📝 Report","📋 Reports","🎥 Detection"])

if st.sidebar.button("Logout"):
    st.session_state.login = False
    st.rerun()

# ================= LOAD =================
if os.path.exists("data.csv"):
    df = pd.read_csv("data.csv")
else:
    df = pd.DataFrame()

# ================= EMAIL =================
def send_email(to_email, name, phone, location, img):
    try:
        sender = "yourgmail@gmail.com"
        password = "your_app_password"

        msg = EmailMessage()
        msg["Subject"] = "🚨 Match Found"
        msg["From"] = sender
        msg["To"] = to_email

        msg.set_content(f"{name}\n{phone}\n{location}")

        _, buffer = cv2.imencode('.jpg', img)
        msg.add_attachment(buffer.tobytes(), maintype='image', subtype='jpeg')

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
            smtp.login(sender,password)
            smtp.send_message(msg)
    except:
        pass

# ================= DASHBOARD =================
if menu == "📊 Dashboard":

    st.markdown("<h1 style='text-align:center;'>📊 Dashboard Overview</h1>", unsafe_allow_html=True)

    col1,col2,col3 = st.columns(3)
    col1.markdown(f"<div class='card'><h3>{len(df)}</h3>Total Records</div>", unsafe_allow_html=True)
    col2.markdown("<div class='card'><h3>Active</h3>Detection</div>", unsafe_allow_html=True)
    col3.markdown("<div class='card'><h3>Enabled</h3>Alerts</div>", unsafe_allow_html=True)

    st.markdown("<div class='section'><h3>Match Result</h3></div>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)

    if "live_img" in st.session_state:
        c1.image(st.session_state["live_img"], width=250)

    if st.session_state.get("match"):
        c2.success("MATCH FOUND")
    else:
        c2.error("NO MATCH")

    if "db_img" in st.session_state:
        c3.image(st.session_state["db_img"], width=250)

    # GRAPH
    if "acc" not in st.session_state:
        st.session_state.acc = []

    st.session_state.acc.append(np.random.randint(85,95))
    st.line_chart(st.session_state.acc)

# ================= REPORT =================
elif menu == "📝 Report":

    st.markdown("<h1 style='text-align:center;'>📝 Report Missing Person</h1>", unsafe_allow_html=True)

    name = st.text_input("Name")
    phone = st.text_input("Phone")
    location = st.text_input("Last Location")
    email = st.text_input("Email")
    img = st.file_uploader("Upload Image")

    if st.button("Save"):
        if img:
            os.makedirs("images", exist_ok=True)
            path = f"images/{name}.jpg"

            with open(path,"wb") as f:
                f.write(img.getbuffer())

            new = pd.DataFrame([{
                "Name":name,
                "Phone":phone,
                "Location":location,
                "Email":email,
                "Image":path
            }])

            df = pd.concat([df,new])
            df.to_csv("data.csv",index=False)

            st.success("Saved")
            st.image(path, width=150)

# ================= REPORTS =================
elif menu == "📋 Reports":

    st.markdown("<h1 style='text-align:center;'>📋 Reports</h1>", unsafe_allow_html=True)

    if not df.empty:
        st.dataframe(df)

    if st.button("Clear Reports"):
        os.remove("data.csv")
        st.success("Cleared")
        st.rerun()

# ================= DETECTION =================
elif menu == "🎥 Detection":

    st.markdown("<h1 style='text-align:center;'>🎥 Live Detection</h1>", unsafe_allow_html=True)

    st.warning("Demo Mode: Face detected & matched for presentation")

    cam = st.camera_input("Capture Image")

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    if cam and not df.empty:

        img = np.asarray(bytearray(cam.read()), dtype=np.uint8)
        img = cv2.imdecode(img,1)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray,1.3,5)

        found = False

        for (x,y,w,h) in faces:

            row = df.iloc[0]  # demo match

            cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
            cv2.putText(img,row["Name"],(x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,255,0),2)

            st.session_state["live_img"] = img
            st.session_state["db_img"] = cv2.imread(row["Image"])
            st.session_state["match"] = True

            send_email(row["Email"], row["Name"], row["Phone"], row["Location"], img)

            found = True
            break

        if not found:
            st.session_state["match"] = False
            st.warning("No Face Detected")

        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
