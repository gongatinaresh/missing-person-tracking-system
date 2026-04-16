import streamlit as st
import pandas as pd
import os
import cv2
import numpy as np
import smtplib
from email.message import EmailMessage

# -----------------------------------------
# CONFIG
# -----------------------------------------
st.set_page_config(page_title="Missing Person Detection", layout="wide")

# -----------------------------------------
# UI STYLE
# -----------------------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
}
.card {
    background: rgba(255,255,255,0.1);
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

st.title("🧭 Missing Person Detection System")

# -----------------------------------------
# EMAIL
# -----------------------------------------
def send_email(to_email, subject, body):
    try:
        sender = st.secrets["EMAIL"]
        password = st.secrets["EMAIL_PASSWORD"]

        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)

    except:
        pass

# -----------------------------------------
# DATABASE FILE
# -----------------------------------------
DATA_FILE = "data.csv"
os.makedirs("faces", exist_ok=True)

# -----------------------------------------
# FACE DETECTOR
# -----------------------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# -----------------------------------------
# MENU
# -----------------------------------------
menu = st.sidebar.radio("Menu", ["➕ Report", "📋 View", "🎥 Detection"])

# -----------------------------------------
# REPORT
# -----------------------------------------
if menu == "➕ Report":

    st.markdown('<div class="card">', unsafe_allow_html=True)

    name = st.text_input("Name")
    email = st.text_input("Email")
    image = st.file_uploader("Upload Face Image")

    if st.button("Submit"):

        if name and email and image:

            file_path = f"faces/{name}.jpg"

            with open(file_path, "wb") as f:
                f.write(image.read())

            data = {"Name": name, "Email": email, "Image": file_path}

            if os.path.exists(DATA_FILE):
                df = pd.read_csv(DATA_FILE)
                df = pd.concat([df, pd.DataFrame([data])])
            else:
                df = pd.DataFrame([data])

            df.to_csv(DATA_FILE, index=False)

            st.success("Saved Successfully")

        else:
            st.error("Fill all fields")

    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------
# VIEW
# -----------------------------------------
elif menu == "📋 View":

    st.markdown('<div class="card">', unsafe_allow_html=True)

    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        st.dataframe(df)

        if st.button("🗑 Clear Reports"):
            os.remove(DATA_FILE)
            st.success("Cleared")
            st.rerun()

    else:
        st.warning("No Data")

    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------
# TRAIN MODEL
# -----------------------------------------
def train_model():

    faces = []
    labels = []
    label_map = {}

    if not os.path.exists(DATA_FILE):
        return None, None

    df = pd.read_csv(DATA_FILE)

    for i, row in df.iterrows():
        img = cv2.imread(row["Image"])
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces_detected = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces_detected:
            face = gray[y:y+h, x:x+w]
            faces.append(face)
            labels.append(i)
            label_map[i] = row["Name"]

    if len(faces) == 0:
        return None, None

    model = cv2.face.LBPHFaceRecognizer_create()
    model.train(faces, np.array(labels))

    return model, label_map

# -----------------------------------------
# DETECTION
# -----------------------------------------
elif menu == "🎥 Detection":

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("📷 Live Face Detection")

    model, label_map = train_model()

    if model is None:
        st.warning("No trained data available")
    else:

        run = st.checkbox("Start Camera")

        if run:
            cap = cv2.VideoCapture(0)
            frame_window = st.image([])

            detected = set()

            df = pd.read_csv(DATA_FILE)

            while run:
                ret, frame = cap.read()
                if not ret:
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces_detected = face_cascade.detectMultiScale(gray, 1.3, 5)

                for (x, y, w, h) in faces_detected:
                    face = gray[y:y+h, x:x+w]

                    label, confidence = model.predict(face)

                    if confidence < 70:
                        name = label_map[label]

                        cv2.putText(frame, name, (x, y-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

                        if name not in detected:
                            detected.add(name)

                            st.success(f"🎉 Match Found: {name}")

                            email = df[df["Name"] == name]["Email"].values[0]

                            send_email(
                                email,
                                "Person Found",
                                f"{name} has been detected"
                            )

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_window.image(frame)

            cap.release()

    st.markdown('</div>', unsafe_allow_html=True)
