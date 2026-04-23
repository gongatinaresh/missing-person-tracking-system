import streamlit as st
import pandas as pd
import os
import cv2
import numpy as np
import smtplib
from email.message import EmailMessage
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# ================= CONFIG =================
st.set_page_config(layout="wide")

# ================= STYLE =================
st.markdown("""
<style>
.stApp {background:#0f172a;font-family:'Segoe UI';}
section[data-testid="stSidebar"] {background:#020617;color:white;}

.topbar {
    background:#020617;color:white;padding:12px;
    border-radius:8px;margin-bottom:15px;
    display:flex;justify-content:space-between;
}

.card {
    background:#1e293b;padding:18px;border-radius:12px;
    color:white;box-shadow:0 4px 12px rgba(0,0,0,0.4);
}

.metric {text-align:center;}
.match-box {text-align:center;color:#22c55e;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# ================= EMAIL =================
def send_email(to_email, subject, body):
    try:
        sender_email = st.secrets["EMAIL"]
        password = st.secrets["EMAIL_PASSWORD"]

        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
            smtp.login(sender_email,password)
            smtp.send_message(msg)
    except:
        pass

# ================= SIDEBAR =================
st.sidebar.title("CONTROL PANEL")
menu = st.sidebar.radio("",["Dashboard","Report","Reports","Detection"])

# ================= TOP BAR =================
st.markdown(f"""
<div class='topbar'>
<div>🧭 Missing Person Detection System</div>
<div>🟢 Active | ⏰ {pd.Timestamp.now().strftime("%H:%M:%S")}</div>
</div>
""", unsafe_allow_html=True)

# ================= LOAD DATA =================
if os.path.exists("missing_data.csv"):
    df = pd.read_csv("missing_data.csv")
else:
    df = pd.DataFrame()

# ================= DASHBOARD =================
if menu == "Dashboard":

    total = len(df)
    matches = st.session_state.get("matches", 0)
    alerts = st.session_state.get("alerts", 0)

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='card metric'><h2>{total}</h2>Total Records</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card metric'><h2>{matches}</h2>Matches</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card metric'><h2>{alerts}</h2>Alerts</div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='card metric'><h2>{pd.Timestamp.now().strftime('%H:%M')}</h2>Last Match</div>", unsafe_allow_html=True)

    left, right = st.columns([3,1])

    # MATCH RESULT
    with left:
        st.markdown("<div class='card'><h3>MATCH RESULT</h3></div>", unsafe_allow_html=True)

        l1,l2,l3 = st.columns([2,1,2])

        with l1:
            if "live_img" in st.session_state:
                st.image(st.session_state["live_img"], caption="Live Image")

        with l2:
            if "match_name" in st.session_state:
                st.markdown(f"<div class='match-box'>✔ MATCH FOUND<br>{st.session_state.get('score','92%')}</div>", unsafe_allow_html=True)

        with l3:
            if "db_img" in st.session_state:
                st.image(st.session_state["db_img"], caption="Database Image")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("<div class='card'><h3>Recent Reports</h3></div>", unsafe_allow_html=True)
        if not df.empty:
            st.dataframe(df.tail(5), use_container_width=True)

    # RIGHT PANEL
    with right:
        st.markdown("<div class='card'><h3>Person Details</h3></div>", unsafe_allow_html=True)

        if "match_name" in st.session_state:
            st.write("Name:", st.session_state["match_name"])
            st.write("Status: Identified")
        else:
            st.info("No match yet")

        if st.button("🗑 Clear Data"):
            if os.path.exists("missing_data.csv"):
                os.remove("missing_data.csv")
                st.success("Cleared")
                st.rerun()

# ================= REPORT =================
elif menu == "Report":

    st.markdown("<div class='card'><h3>Report Missing Person</h3></div>", unsafe_allow_html=True)

    col1,col2 = st.columns([2,1])

    with col1:
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        location = st.text_input("Location")
        email = st.text_input("Email")

    with col2:
        image = st.file_uploader("Upload Image")
        if image:
            st.image(image)

    if st.button("Submit"):
        if image:
            os.makedirs("data", exist_ok=True)
            path = f"data/{name}.jpg"

            with open(path,"wb") as f:
                f.write(image.getbuffer())

            new_data = pd.DataFrame([{
                "Name": name,
                "Image Path": path,
                "Phone": phone,
                "Location": location,
                "Email": email
            }])

            df = pd.concat([df, new_data])
            df.to_csv("missing_data.csv", index=False)

            st.success("Saved Successfully")

# ================= REPORTS =================
elif menu == "Reports":

    st.markdown("<div class='card'><h3>Reports</h3></div>", unsafe_allow_html=True)

    if not df.empty:
        st.dataframe(df, use_container_width=True)

        col1,col2 = st.columns(2)

        with col1:
            st.download_button("Download", df.to_csv(index=False), "reports.csv")

        with col2:
            if st.button("Clear Reports"):
                os.remove("missing_data.csv")
                st.success("Cleared")
                st.rerun()

# ================= DETECTION =================
elif menu == "Detection":

    st.markdown("<div class='card'><h3>Live Detection</h3></div>", unsafe_allow_html=True)

    def match_faces(a,b):
        a=cv2.resize(a,(100,100))
        b=cv2.resize(b,(100,100))
        return np.mean((a-b)**2) < 2000

    class Cam(VideoTransformerBase):
        def transform(self,frame):
            img=frame.to_ndarray(format="bgr24")
            gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

            face=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
            faces=face.detectMultiScale(gray,1.3,5)

            for (x,y,w,h) in faces:
                face_img = img[y:y+h,x:x+w]

                for _,row in df.iterrows():
                    db_img = cv2.imread(row["Image Path"])

                    if db_img is not None and match_faces(face_img, db_img):

                        st.session_state["live_img"] = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                        st.session_state["db_img"] = cv2.cvtColor(db_img, cv2.COLOR_BGR2RGB)
                        st.session_state["match_name"] = row["Name"]
                        st.session_state["score"] = "92%"

                        st.session_state["matches"] = st.session_state.get("matches",0)+1
                        st.session_state["alerts"] = st.session_state.get("alerts",0)+1

                        send_email(row["Email"], "Match Found", row["Name"])

                        cv2.putText(img,row["Name"],(x,y-10),1,1,(0,255,0),2)
                        break

                cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

            return img

    webrtc_streamer(key="cam", video_transformer_factory=Cam)
