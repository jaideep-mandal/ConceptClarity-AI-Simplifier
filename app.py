import streamlit as st
from streamlit_option_menu import option_menu
import requests
import time
import base64

# Connection to your FastAPI Backend
BACKEND_URL = "http://127.0.0.1:8000"

# --- SCIENTIFIC BACKGROUND GENERATOR ---
def get_scientific_bg():
    return """
    <style>
    .stApp {
        background-color: #06141B;
    }
    </style>
    """

st.markdown(get_scientific_bg(), unsafe_allow_html=True)

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'page' not in st.session_state:
    st.session_state['page'] = "Home"
if 'search_performed' not in st.session_state:
    st.session_state['search_performed'] = False
if 'last_explanation' not in st.session_state:
    st.session_state['last_explanation'] = ""

# --- CSS Styling ---
st.markdown("""
<style>
    /* 1. Global Background and Text */
    .stApp {
        background-color: #06141B;
        color: #CCD0CF;
    }
    
    /* 2. Input Fields Styling */
    div[data-baseweb="input"] {
        border: 2px solid #253745 !important;
        border-radius: 8px;
        background-color: #9BA6A8 !important;
    }
    
    div[data-baseweb="input"] > div {
        background-color: #9BA6A8 !important;
    }
    
    input {
        color: #06141B !important;
        background-color: #9BA6A8 !important;
    }

    /* 3. Password Field Styling */
    div[data-baseweb="input"]:has(input[type="password"]) {
        display: flex !important;
        align-items: center !important;
        background-color: #9BA6A8 !important;
    }

    div[data-baseweb="input"]:has(input[type="password"]) div[role="button"] {
        border-left: 1px solid #253745 !important;
        padding-left: 10px;
        margin-left: 10px;
        display: flex !important;
        align-items: center !important;
        height: 100% !important;
        background-color: #9BA6A8 !important;
    }
    
    div[data-baseweb="input"]:has(input[type="password"]) svg {
        fill: #06141B !important;
        color: #06141B !important;
    }

    /* Sidebar Toggle */
    button[kind="header"] {
        color: white !important;
        background-color: rgba(0, 0, 0, 0.3) !important;
        border-radius: 50% !important;
    }
    
    button[kind="header"]:hover {
        color: #9BA6A8 !important;
        background-color: rgba(0, 0, 0, 0.5) !important;
    }


    /* 4. Title Box / Header */
    .title-box { 
        text-align: center; 
        margin-bottom: 20px; 
        position: sticky;
        top: 0;
        background-color: rgba(6, 20, 27, 0.8);
        backdrop-filter: blur(10px);
        z-index: 999;
        padding: 15px 0;
        color: #9BA6A8;
    }

    /* 5. Buttons Styling */
    .stButton>button {
        background-color: #253745 !important;
        color: #CCD0CF !important;
        border-radius: 20px !important;
        border: none !important;
        padding: 0.5rem 2rem !important;
        font-weight: bold !important;
    }
    
    .stButton>button:hover {
        background-color: #4A5C6A !important;
        color: #CCD0CF !important;
    }

    /* 6. Cards / Containers */
    div.stAlert {
        background-color: #11212D !important;
        color: #CCD0CF !important;
        border: 1px solid #253745 !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown("""<div class="title-box"><h1>Concept Clarity</h1></div>""", unsafe_allow_html=True)

    # --- Sidebar Logic ---
    with st.sidebar:
        if st.session_state['logged_in']:
            menu = ["Home", "Logout"]
            icons = ["house", "box-arrow-right"]
        else:
            menu = ["Home", "Login", "SignUp"]
            icons = ["house", "person", "person-plus"]

        try: def_idx = menu.index(st.session_state['page'])
        except: def_idx = 0

        choice = option_menu("Menu", menu, icons=icons, default_index=def_idx, 
            styles={
                "container": {"background-color": "#11212D"},
                "nav-link": {"color": "#CCD0CF", "--hover-color": "#253745"},
                "nav-link-selected": {"background-color": "#4A5C6A", "color": "#CCD0CF"}
            })

        if choice != st.session_state['page']:
            st.session_state['page'] = choice
            st.rerun()

    # --- Page 1: Home ---
    if st.session_state['page'] == "Home":
        st.markdown("""<div class="title-box"><h3>Simplifying Science for Everyone</h3></div>""", unsafe_allow_html=True)
        if st.session_state['logged_in']:
            st.write(f"Welcome back, **{st.session_state['username']}**!")

        search_term = st.text_input("Enter a scientific term to get a simplified explanation.")

        if st.button("Explain"):
            if search_term:
                st.session_state['search_performed'] = True

                # --- NEW: Call Groq Backend ---
                with st.spinner("Asking AI..."):
                    try:
                        resp = requests.post(f"{BACKEND_URL}/explain", json={"term": search_term})
                        if resp.status_code == 200:
                            st.session_state['last_explanation'] = resp.json()['explanation']
                        else:
                            st.error("Error generating explanation.")
                    except requests.exceptions.RequestException:
                        st.error("Backend offline. Is FastAPI running?")
            else:
                st.warning("Please enter a term.")

        # Display Result
        if st.session_state['last_explanation']:
            st.success(st.session_state['last_explanation'])

        # Guest Nudge
        if not st.session_state['logged_in'] and st.session_state['search_performed']:
            st.info("Want to save your search history?")
            if st.button("Login to Save"):
                st.session_state['page'] = "Login"
                st.rerun()

    # --- Page 2: Login ---
    elif st.session_state['page'] == "Login":
        st.markdown("""<div class="title-box"><h3>Login</h3></div>""", unsafe_allow_html=True)
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            with st.spinner("Logging in..."):
                try:
                    resp = requests.post(f"{BACKEND_URL}/login", json={"email": email, "password": password})
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = data['username']
                        st.session_state['page'] = "Home"
                        st.success("Logged in successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                except requests.exceptions.RequestException:
                    st.error("Backend offline.")

    # --- Page 3: SignUp ---
    elif st.session_state['page'] == "SignUp":
        st.markdown("""<div class="title-box"><h3>Create Account</h3></div>""", unsafe_allow_html=True)
        new_user = st.text_input("Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            with st.spinner("Creating account..."):
                try:
                    resp = requests.post(f"{BACKEND_URL}/register", 
                                        json={"username": new_user, "email": new_email, "password": new_password})
                    if resp.status_code == 200:
                        st.success("Account created! Please log in.")
                        time.sleep(1)
                        st.session_state['page'] = "Login"
                        st.rerun()
                    else:
                        st.error("Registration failed. Email might already exist.")
                except requests.exceptions.RequestException:
                    st.error("Backend offline.")

    # --- Logout ---
    elif st.session_state['page'] == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.session_state['page'] = "Home"
        st.rerun()

if __name__ == "__main__":
    main()