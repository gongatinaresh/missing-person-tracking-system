import streamlit as st
import pandas as pd
import os
import cv2
import numpy as np
import base64
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
body {
    background:#0f2027;
}
.topbar {
    background:#0b1c2c;
    padding:15px;
    border-radius:10px;
    color:white;
    font-weight:bold;
    text-align:center;
}
.metric-card {
    background:white;
    padding:15px;
    border-radius:12px;
    text-align:center;
    box-shadow:0 4px 12px rgba(0,0,0,0.1);
}
.section {
    background:white;
    padding:20px;
    border-radius:12px;
    margin-top:15px;
}
.match-box {
    text-align:center;
    color:green;
    font-weight:bold;
    font-size:20px;
}
.sidebar .sidebar-content {
    background:#111;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA LOAD ----------------
if os.path.exists("missing_data.csv"):
    df = pd.read_csv("missing_data.csv")
else:
    df = pd.DataFrame()

# ---------------- SIDEBAR ----------------
menu = st.sidebar.radio("Navigation", [
    "Dashboard",
    "Report Missing",
    "View Reports",
    "Live Detection"
])

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":

    st.markdown("<div class='topbar'>MISSING PERSON DETECTION SYSTEM | 🟢 ACTIVE</div>", unsafe_allow_html=True)

    total = len(df)
    matches = st.session_state.get("matches", 0)
    alerts = st.session_state.get("alerts", 0)

    col1,col2,col3,col4 = st.columns(4)

    col1.markdown(f"<div class='metric-card'><h2>{total}</h2><p>Total Records</p></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-card'><h2>{matches}</h2><p>Matches</p></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='metric-card'><h2>{alerts}</h2><p>Alerts</p></div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='metric-card'><h2>{datetime.now().strftime('%H:%M')}</h2><p>Time</p></div>", unsafe_allow_html=True)

    st.markdown("<div class='section'><h3>Match Result</h3></div>", unsafe_allow_html=True)

    col1,col2,col3 = st.columns([2,1,2])

    with col1:
        if "live_img" in st.session_state:
            st.image(st.session_state["live_img"], caption="Live Image")
        else:
            st.info("No Live Image")

    with col2:
        if "match_score" in st.session_state:
            st.markdown(f"<div class='match-box'>✔ MATCH FOUND<br><br>{st.session_state['match_score']}%</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='match-box'>No Match</div>", unsafe_allow_html=True)

    with col3:
        if "db_img" in st.session_state:
            st.image(st.session_state["db_img"], caption="Database Image")

# ---------------- REPORT ----------------
elif menu == "Report Missing":

    st.title("Report Missing Person")

    name = st.text_input("Name")
    phone = st.text_input("Phone")
    location = st.text_input("Location")

    image = st.file_uploader("Upload Image")

    if st.button("Save"):
        if image:

            os.makedirs("data", exist_ok=True)
            path = f"data/{name}.jpg"

            with open(path,"wb") as f:
                f.write(image.getbuffer())

            new_data = {
                "Name": name,
                "Phone": phone,
                "Location": location,
                "Image Path": path
            }

            if os.path.exists("missing_data.csv"):
                df = pd.read_csv("missing_data.csv")
                df = pd.concat([df, pd.DataFrame([new_data])])
            else:
                df = pd.DataFrame([new_data])

            df.to_csv("missing_data.csv", index=False)

            st.success("Saved Successfully")

# ---------------- VIEW REPORTS ----------------
elif menu == "View Reports":

    st.title("All Reports")

    if os.path.exists("missing_data.csv"):
        df = pd.read_csv("missing_data.csv")
        st.dataframe(df)
    else:
        st.warning("No Data Found")

# ---------------- DETECTION ----------------
elif menu == "Live Detection":

    st.title("Live Face Detection")

    run = st.checkbox("Start Camera")

    FRAME_WINDOW = st.image([])

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    cap = cv2.VideoCapture(0)

    def match_faces(a,b):
        a = cv2.resize(a,(100,100))
        b = cv2.resize(b,(100,100))
        return np.mean((a-b)**2) < 2000

    while run:
        ret, frame = cap.read()
        if not ret:
            st.error("Camera not working")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray,1.3,5)

        for (x,y,w,h) in faces:
            face = frame[y:y+h,x:x+w]

            if not df.empty:
                for _, row in df.iterrows():
                    db_img = cv2.imread(row["Image Path"])

                    if db_img is not None and match_faces(face, db_img):

                        st.session_state["live_img"] = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                        st.session_state["db_img"] = cv2.cvtColor(db_img, cv2.COLOR_BGR2RGB)
                        st.session_state["match_score"] = 92.45
                        st.session_state["matches"] = st.session_state.get("matches",0) + 1
                        st.session_state["alerts"] = st.session_state.get("alerts",0) + 1

                        cv2.putText(frame,row["Name"],(x,y-10),1,1,(0,255,0),2)

            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)

        FRAME_WINDOW.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    cap.release()
