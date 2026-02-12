import streamlit as st
import sqlite3
import os

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
