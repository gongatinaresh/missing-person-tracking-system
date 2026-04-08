import os
import pandas as pd
from send_email import send_email

def save_admin_data(image_file, name, age, contact, family_email, location, admin_email):
    # Ensure save folder exists
    save_dir = os.path.join("data", "admin_data", "missing_images")
    os.makedirs(save_dir, exist_ok=True)

    # Save uploaded image
    img_path = os.path.join(save_dir, image_file.name)
    with open(img_path, "wb") as f:
        f.write(image_file.getbuffer())

    # Path to CSV
    csv_path = os.path.join("data", "admin_data", "missing_data.csv")

    # ✅ Use one consistent schema
    new_entry = {
        "Name": name or "",
        "Age": age or "",
        "Contact Number": contact or "",
        "Family Email": family_email or "",
        "Location": location or "",
        "Admin Email": admin_email or "",
        "Image Path": img_path,
        "Reported At": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Append or create CSV
    if os.path.isfile(csv_path):
        df = pd.read_csv(csv_path, dtype=str)

        # Drop duplicate columns if any
        df = df.loc[:, ~df.columns.duplicated()]

        # Ensure schema is correct
        df = df.reindex(columns=new_entry.keys(), fill_value="")

        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    else:
        df = pd.DataFrame([new_entry])

    df.to_csv(csv_path, index=False)

    # ✅ Send email automatically to Family Email
    if family_email:
        try:
            send_email(
                name=name,
                age=age,
                contact_number=contact,
                recipient_email=family_email,
                location=location,
                img_path=img_path
            )
            print(f"✅ Email sent successfully to {family_email}")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")

    # ✅ Also notify Admin Email if provided
    if admin_email:
        try:
            send_email(
                name=name,
                age=age,
                contact_number=contact,
                recipient_email=admin_email,
                location=location,
                img_path=img_path
            )
            print(f"✅ Email sent successfully to {admin_email}")
        except Exception as e:
            print(f"❌ Failed to send admin email: {e}")

    return img_path
