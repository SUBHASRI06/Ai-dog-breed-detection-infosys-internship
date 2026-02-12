import streamlit as st
from PIL import Image
import base64
import os
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.xception import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
import google.generativeai as genai
import sqlite3
import traceback
import io
from datetime import datetime


st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet" />
<style>
span[translate="no"] {
  font-family: 'Material Symbols Rounded' !important;
}
.stButton > button {
  background: linear-gradient(180deg, #06402B, #096C6C);
  color: white;
  border-radius: 12px;
  padding: 8px 16px;
  font-weight: bold;
  border: none;
}
.stButton > button:hover {
  background-color: #256c36;
  color: #fff;
}
.active-btn {
  background-color: #256c36 !important;
  color: white !important;
  font-weight: bold !important;
  border-radius: 12px !important;
}
.default-avatar { 
  width:120px; height: 120px; border-radius: 50%; background:#777; 
  display:flex; align-items:center; justify-content:center; margin:0 auto 12px auto; color:white; font-size:48px; 
}
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'show_history' not in st.session_state:
        st.session_state.show_history = False
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None


init_session_state()


st.set_page_config(layout="centered", initial_sidebar_state="expanded")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def add_bg_from_local(image_file):
    if not os.path.exists(image_file):
        return False
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(2,8,24,0.68), rgba(2,8,24,0.68)),
                                  url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return True


add_bg_from_local(r"C:\Users\SUBHASRI\OneDrive\Desktop\milestone 3\dog background 3.jpg")


# Database Init and Helpers
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first TEXT NOT NULL,
            last TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_path TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS predictions_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            breed TEXT NOT NULL,
            confidence REAL NOT NULL,
            datetime TEXT NOT NULL,
            img_path TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


init_db()


def add_user(first, last, username, email, password, profile_path=None):
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO users (first, last, username, email, password, profile_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (first, last, username, email, password, profile_path))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def login_user(user_input, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        SELECT * FROM users
        WHERE (username=? OR email=?) AND password=?
    """, (user_input, user_input, password))
    user = c.fetchone()
    conn.close()
    return user


def update_user(user_id, first, last, username, email, password=None, profile_path=None):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    if password:
        c.execute("""
            UPDATE users
            SET first=?, last=?, username=?, email=?, password=?, profile_path=?
            WHERE id=?
        """, (first, last, username, email, password, profile_path, user_id))
    else:
        c.execute("""
            UPDATE users
            SET first=?, last=?, username=?, email=?, profile_path=?
            WHERE id=?
        """, (first, last, username, email, profile_path, user_id))
    conn.commit()
    conn.close()


def save_prediction_history(user_id, breed, confidence, datetime_str, img_bytes):
    os.makedirs("history_images", exist_ok=True)
    filename = f"history_images/{user_id}_{datetime_str.replace(' ', '_').replace(':','-')}.png"
    with open(filename, "wb") as f:
        f.write(img_bytes)
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO predictions_history (user_id, breed, confidence, datetime, img_path)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, breed, confidence, datetime_str, filename))
    conn.commit()
    conn.close()


def load_user_history(user_id):
    import os
    from datetime import datetime
    import sqlite3

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id=?", (user_id,))
    user_row = c.fetchone()
    username = user_row[0] if user_row else f"user_{user_id}"
    c.execute("""
        SELECT breed, confidence, datetime, img_path
        FROM predictions_history
        WHERE user_id=?
        ORDER BY datetime DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    history = []
    for breed, confidence, datetime_str, img_path in rows:
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                img_bytes = f.read()
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            formatted_time = dt.strftime("%I:%M %p")
            history.append({
                "user": username,
                "breed": breed,
                "confidence": f"{confidence:.2f}",
                "datetime": formatted_time,
                "img_bytes": img_bytes
            })
    return history



# The login/signup, profile, and sidebar functions.

def login_signup_page():
    st.markdown("""
    <style>
    .auth-card {
        max-width: 480px;
        margin: 60px auto;
        padding: 36px;
        border-radius: 22px;
        background: rgba(8,22,44,0.64);
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 40px rgba(3,10,30,0.68);
        border: 1px solid rgba(77,166,255,0.06);
    }
    .auth-title {
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        color: #CFFFDC;
        margin-bottom: 20px;
        text-shadow: 0 3px 8px rgba(0,0,0,0.5);
    }
    .switch-link {
        text-align: center;
        margin-top: 16px;
        color: #CFFFDC;
    }
    .switch-link button {
        background: none !important;
        color: #4da6ff !important;
        border: none !important;
        font-size: 15px !important;
        text-decoration: underline;
        cursor: pointer;
    }
    .stTextInput>div>div>input {
        background-color: #f0fff4;
        border: 2px solid #2E6F40;
        border-radius: 10px;
        padding: 6px;
        color: black !important;
        font-weight: 500 !important;
    }
    .stButton>button {
        background: linear-gradient(180deg, #06402B, #096C6C);
        color: white;
        border-radius: 12px;
        padding: 8px 16px;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #256c36;
        color: #fff;
    }
    </style>
    """, unsafe_allow_html=True)
    if st.session_state.page == "signup":
        st.markdown('<div class="auth-title">🐾 Create a New Account</div>', unsafe_allow_html=True)
        first = st.text_input("First Name").strip()
        last = st.text_input("Last Name").strip()
        username = st.text_input("Username").strip()
        email = st.text_input("Email").strip()
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        profile_pic = st.file_uploader("Upload Profile Picture (optional)", type=["jpg","jpeg","png"])
        profile_path = None
        if profile_pic:
            os.makedirs("profile_pics", exist_ok=True)
            profile_path = os.path.join("profile_pics", profile_pic.name)
            with open(profile_path, "wb") as f:
                f.write(profile_pic.getbuffer())
        if st.button("Signup"):
            if not (first and last and username and email and password):
                st.error("⚠️ All fields except profile picture are required.")
            elif password != confirm:
                st.error("⚠️ Passwords do not match.")
            else:
                success = add_user(first, last, username, email, password, profile_path)
                if success:
                    user = login_user(username, password)
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.session_state.history = load_user_history(user[0])
                    st.success(f"✅ Account created! Welcome {user[1]}")
                    st.session_state.page = "app"
                else:
                    st.error("⚠️ Username or Email already exists.")


        st.markdown('<div class="switch-link">Already have an account?', unsafe_allow_html=True)
        if st.button("Login"):
            st.session_state.page = "login"
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="auth-title">🔐 Login to Your Account</div>', unsafe_allow_html=True)
        user_input = st.text_input("Username or Email").strip()
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(user_input, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.history = load_user_history(user[0])
                st.success(f"Welcome {user[1]} 👋")
                st.session_state.page = "app"
            else:
                st.error("Invalid username/email or password.")


        st.markdown('<div class="switch-link">Don\'t have an account?', unsafe_allow_html=True)
        if st.button("Signup"):
            st.session_state.page = "signup"
        st.markdown('</div>', unsafe_allow_html=True)


def profile_page():
    user = st.session_state.get("user")
    if not user:
        st.error("No user in session.")
        return


    st.markdown("""
    <style>
    .profile-card {
        max-width: 720px;
        margin: 24px auto;
        padding: 22px;
        border-radius: 12px;
        background: rgba(8,22,44,0.64);
        box-shadow: 0 8px 30px rgba(0,0,0,0.45);
        border: 1px solid rgba(77,166,255,0.06);
    }
    .profile-title { text-align:center; color:#CFFFDC; font-size:22px; margin-bottom:8px; }
    </style>
    """, unsafe_allow_html=True)


    st.markdown('<div class="profile-title">👤 Edit Profile</div>', unsafe_allow_html=True)
    profile_path = user[6]
    if profile_path and os.path.exists(profile_path):
        st.image(profile_path, width=120)
    else:
        st.markdown(
            "<div style='width:120px;height:120px;border-radius:50%;background:#777;display:flex;align-items:center;justify-content:center;margin:0 auto 12px auto;color:#fff;font-size:48px;'>👤</div>",
            unsafe_allow_html=True,
        )
    first = st.text_input("First Name", value=user[1] or "")
    last = st.text_input("Last Name", value=user[2] or "")
    username = st.text_input("Username", value=user[3] or "")
    email = st.text_input("Email", value=user[4] or "")
    new_password = st.text_input("New Password (leave blank to keep current)", type="password")
    st.markdown("### 📷 Profile Picture")
    profile_pic = st.file_uploader("", type=["jpg", "jpeg", "png"])


    if st.button("💾 Save Changes", key="save_profile"):
        new_profile_path = profile_path
        if profile_pic:
            os.makedirs("profile_pics", exist_ok=True)
            new_profile_path = os.path.join("profile_pics", profile_pic.name)
            with open(new_profile_path, "wb") as f:
                f.write(profile_pic.getbuffer())
        pwd = new_password if new_password else None
        update_user(user_id=user[0], first=first, last=last, username=username, email=email, password=pwd, profile_path=new_profile_path)
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=?", (user[0],))
        updated_user = c.fetchone()
        conn.close()
        if updated_user:
            st.session_state.user = updated_user
            st.success("✅ Profile updated successfully!")
            if new_profile_path and os.path.exists(new_profile_path):
                st.image(new_profile_path, width=120)
        else:
            st.error("❌ Failed to reload updated profile.")


    if st.button("⬅ Back to App", key="back_from_profile"):
        st.session_state.page = "app"


def show_user_info_sidebar():
    user = st.session_state.get("user")
    if not user:
        return

    with st.sidebar:
        profile_path = user[6]
        if profile_path and os.path.exists(profile_path):
            st.image(profile_path, width=120)
        else:
            st.markdown("<div class='default-avatar'>👤</div>", unsafe_allow_html=True)

        st.title("👤 User Info")
        st.write(f"**Name:** {user[1]} {user[2]}")
        st.write(f"**Username:** {user[3]}")
        st.write(f"**Email:** {user[4]}")

        if st.button("👤 View Profile", key="view_profile_btn") or st.session_state.page == "profile":
            st.session_state.page = "profile"
            st.session_state.show_history = False
        if st.button("🚪 Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "login"
            st.session_state.history = []
            st.session_state.show_history = False
        if st.button("🕒 View History", key="view_history_btn") or st.session_state.show_history:
            st.session_state.show_history = True
            st.session_state.page = "app"
        if not (st.session_state.show_history or st.session_state.page == "profile"):
            st.session_state.page = "app"


@st.cache_resource
def load_dog_model():
    return load_model(r"C:\Users\SUBHASRI\OneDrive\Desktop\milestone 3\Xception_model.h5")


model = load_dog_model()
labels_df = pd.read_csv(r"C:\Users\SUBHASRI\OneDrive\Desktop\milestone 3\labels.csv")
class_names = sorted(labels_df["breed"].unique())


def preprocess_image(image):
    image = image.resize((350, 350))
    arr = img_to_array(image)
    arr = np.expand_dims(arr, axis=0)
    arr = preprocess_input(arr)
    return arr


genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])


@st.cache_resource
def load_gemini_model():
    return genai.GenerativeModel("models/gemini-2.5-flash")


gemini_model = load_gemini_model()


@st.cache_data(show_spinner=False, max_entries=100)
def get_breed_info_cached(breed_name):
    prompt = f"""
     For the dog breed '{breed_name}', provide exactly:
        - 2 plain factual sentences for ancestry (no numbering, labels, or formatting).
        - 2 plain factual sentences for purpose.
        - 2 plain factual sentences for migration.
     Do not write section labels, emoji, numbering, or bold at any position. Each sentence should be on a new line. If information is missing, write: Information not well documented.
     """

    response = gemini_model.generate_content(prompt)
    return response.text.strip()


# Main app
if not st.session_state.logged_in:
    login_signup_page()
else:
    show_user_info_sidebar()

    if st.session_state.show_history:
        st.markdown("## 🕒 Prediction History")
        if not st.session_state.history:
            st.info("No prediction history found.")
        else:
            for entry in st.session_state.history:
                col1, col2 = st.columns([1,3])
                with col1:
                    st.image(entry["img_bytes"], width=80)
                with col2:
                    st.markdown(f"""**User:** {entry['user']}  
**Breed:** {entry['breed']}  
**Confidence:** {entry['confidence']}%  
**Time:** {entry['datetime']}  
""")
                st.markdown("---")
        if st.button("⬅ Back to App"):
            st.session_state.show_history = False
        st.stop()

    if st.session_state.page == "profile":
        profile_page()
    else:
        st.markdown("""
            <style>
            * { font-family: "Times New Roman", Times, serif !important; }
            .app-container { display:flex; justify-content:center; align-items:flex-start; padding-top:40px; padding-bottom:40px; }
            .card { width:880px; max-width:94%; border-radius:22px; padding:44px; background: rgba(8,22,44,0.64); box-shadow: 0 10px 40px rgba(3,10,30,0.68); border: 1px solid rgba(77,166,255,0.06); backdrop-filter: blur(6px); }
            .title { text-align:center; font-size:60px; margin:0 0 6px 0; color:#CFFFDC; font-weight:700; text-shadow: 0 6px 20px rgba(34,95,165,0.35); }
            .subtitle { text-align:center; font-size:20px; margin:0 0 26px 0; color:#2E6F40; opacity:0.95; }
            .upload-card { border-radius:18px; padding:22px; background: linear-gradient(180deg, rgba(255,255,255,0.015), rgba(255,255,255,0.01)); border: 1px solid rgba(77,166,255,0.10); }
            .upload-inner { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:14px; padding:18px; border-radius:14px; border: 1px dashed rgba(77,166,255,0.18); background: rgba(255,255,255,0.008); min-height:120px; }
            .small-text { font-size:16px; color:#dfeeff; opacity:0.95; margin:0; }
            div.stButton > button:first-child { background: linear-gradient(180deg, #06402B, #096C6C) !important; color: white !important; padding: 12px 34px !important; border-radius: 12px !important; font-size:18px !important; font-weight:600 !important; box-shadow: 0 6px 18px rgba(36,135,255,0.28) !important; border: none !important; }
            .uploaded-label { text-align:center; font-size:20px; color:#e6eef9; margin-top:18px; opacity:0.95; }
            .stFileUploader { width: 100%; display:flex; justify-content:center; }
            .stElementContainer:has(.upload-inner:empty), .stElementContainer:has(.stMarkdownContainer:empty), .stMarkdown:has(.stMarkdownContainer:empty), .stElementContainer:has(.card:empty), .stElementContainer:has(.upload-card:empty), .stMarkdown:has(.card:empty), .stMarkdown:has(.upload-card:empty) { display: none !important; }
            @media (max-width:720px) { .title { font-size:36px; } .card { padding:20px; border-radius:14px; } }
            </style>""", unsafe_allow_html=True)

        st.markdown('<div class="app-container">', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="title">AI Model for Dog Breed Detection</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Upload a dog image to identify its breed</div>', unsafe_allow_html=True)
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        st.markdown('<div class="upload-inner">', unsafe_allow_html=True)

        file_obj = st.file_uploader(label="Browse image (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=False, label_visibility="collapsed", help="Select an image file, then click Upload.")
        st.markdown('<p class="small-text">Only JPG / PNG image files are allowed</p>', unsafe_allow_html=True)
        upload_pressed = st.button("Upload")

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="uploaded-label">Uploaded Image</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if upload_pressed:
            if file_obj is None:
                st.warning("Please select an image first using the Browse control above.")
            else:
                try:
                    img = Image.open(file_obj).convert("RGB")
                    st.image(img, use_container_width=True)

                    arr = preprocess_image(img)
                    with st.spinner("Predicting breed..."):
                        preds = model.predict(arr)

                    top3_idx = np.argsort(preds[0])[-3:][::-1]
                    top3_breeds = [class_names[i] for i in top3_idx]
                    top3_conf = [float(preds[0][i]) * 100 for i in top3_idx]

                    breed_info = get_breed_info_cached(top3_breeds[0])

                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, #06402B, #2a5298);
                                    padding:25px; border-radius:18px; text-align:center;
                                    box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-bottom:20px;">
                            <h2 style="color:#fff;">🐶 Predicted Breed</h2>
                            <h1 style="color:#ffdd57; font-size:32px; margin:10px 0;">
                                {top3_breeds[0]}
                            </h1>
                            <p style="color:#e6eef9; font-size:18px;">Confidence: {top3_conf[0]:.2f}%</p>
                        </div>
                        """, unsafe_allow_html=True)

                    lines = [line.strip() for line in breed_info.split('\n') if line.strip()]
                    ancestry = " ".join(lines[:2]) if len(lines) >= 2 else "Information not well documented"
                    purpose = " ".join(lines[2:4]) if len(lines) >= 4 else "Information not well documented"
                    migration = " ".join(lines[4:6]) if len(lines) >= 6 else "Information not well documented"


                    sections = {
                        "🧬 <b>Ancestry</b>": ancestry,
                        "🎯 <b>Purpose</b>": purpose,
                        "🌍 <b>Migration</b>": migration
                    }

                    formatted_info = ""
                    for title, content in sections.items():
                        formatted_info += f"<h4 style='color:#ffdd57;'>{title}</h4><p>{content}</p>"

                    st.markdown(f"""
<div style="background:#243447; border-radius:18px; padding:20px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); margin-top:25px;">
    <h3 style="color:#9bbcff; text-align:center; margin-bottom:15px;">
        📜 Breed Background
    </h3>
    <h4 style='color:#ffdd57; margin:16px 0 2px;'>🧬 Ancestry</h4>
    <p style="color:#f0f6ff; margin-bottom:14px;">{ancestry}</p>
    <h4 style='color:#ffdd57; margin:16px 0 2px;'>🎯 Purpose</h4>
    <p style="color:#f0f6ff; margin-bottom:14px;">{purpose}</p>
    <h4 style='color:#ffdd57; margin:16px 0 2px;'>🌍 Migration</h4>
    <p style="color:#f0f6ff;">{migration}</p>
</div>
""", unsafe_allow_html=True)


                    st.markdown("### 🔝 Top 3 Predictions")
                    cols = st.columns(3)
                    for i, col in enumerate(cols):
                        col.markdown(
                            f"""
                            <div style="background: linear-gradient(135deg, #4e54c8, #8f94fb);
                                        padding:18px; border-radius:15px; text-align:center;
                                        box-shadow: 0 4px 10px rgba(0,0,0,0.25); margin-top:10px;">
                                <h4 style="color:#fff; margin-bottom:10px;">{top3_breeds[i]}</h4>
                                <p style="color:#ffdd57; font-size:16px;">{top3_conf[i]:.2f}%</p>
                            </div>
                            """, unsafe_allow_html=True)

                    buffered = io.BytesIO()
                    img.save(buffered, format="PNG")
                    img_bytes = buffered.getvalue()
                    datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    save_prediction_history(
                        user_id=st.session_state.user[0],
                        breed=top3_breeds[0],
                        confidence=top3_conf[0],
                        datetime_str=datetime_str,
                        img_bytes=img_bytes
                    )
                    st.session_state.history = load_user_history(st.session_state.user[0])

                except Exception as e:
                    st.error(f"Error: {e}")
                    st.text("Full traceback (for debugging):")
                    st.text(traceback.format_exc())
