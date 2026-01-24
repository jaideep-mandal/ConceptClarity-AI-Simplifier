import streamlit as st
from streamlit_option_menu import option_menu
import requests
import time
from streamlit_mic_recorder import mic_recorder
import io

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
if 'email' not in st.session_state:
    st.session_state['email'] = "" 
if 'page' not in st.session_state:
    st.session_state['page'] = "Home"
if 'search_performed' not in st.session_state:
    st.session_state['search_performed'] = False
if 'last_explanation' not in st.session_state:
    st.session_state['last_explanation'] = ""
if 'last_search_term' not in st.session_state:
    st.session_state['last_search_term'] = ""

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
    
    /* 7. Expander Styling (For History) */
    .streamlit-expanderHeader {
        background-color: #11212D !important;
        color: #CCD0CF !important;
        border: 1px solid #253745 !important;
    }
    .streamlit-expanderContent {
        background-color: #06141B !important;
        color: #CCD0CF !important;
        border-bottom: 1px solid #253745 !important;
        border-left: 1px solid #253745 !important;
        border-right: 1px solid #253745 !important;
    }

    /* 8. User Profile Sidebar Card */
    .user-card {
        background-color: #11212D;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #253745;
        margin-top: 20px;
        text-align: center;
    }
    .user-card h4 {
        margin: 0;
        color: #CCD0CF;
        font-size: 16px;
    }
    .user-card p {
        margin: 5px 0 0 0;
        color: #9BA6A8;
        font-size: 12px;
    }

    /* 9. General Column Center Alignment */
    div[data-testid="stColumn"] {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* 10. Force Circle Shape on White Icon */
    div[data-testid="stColumn"]:nth-of-type(2) iframe {
        /* Invert colors to make it white */
        filter: invert(1) hue-rotate(180deg) brightness(1.2) !important;
        
        /* Force the container into a circle so corners don't stick out */
        border-radius: 8px !important;
        
        /* Tweak size to fit the button tightly */
        width: 40px !important;
        height: 38px !important;
        
        /* Center it in the column */
        margin: auto !important;
        display: block !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown("""<div class="title-box"><h1>Concept Clarity</h1></div>""", unsafe_allow_html=True)

    # --- Sidebar Logic ---
    with st.sidebar:
        if st.session_state['logged_in']:
            menu = ["Home", "History", "Logout"]
            icons = ["house", "clock-history", "box-arrow-right"]
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
        
        # User Profile Section
        if st.session_state['logged_in']:
            st.markdown("---")
            st.markdown(f"""
                <div class="user-card">
                    <h4>👤 {st.session_state['username']}</h4>
                    <p>{st.session_state.get('email', 'User')}</p>
                </div>
            """, unsafe_allow_html=True)

        if choice != st.session_state['page']:
            st.session_state['page'] = choice
            st.rerun()

    # --- Page 1: Home ---
    if st.session_state['page'] == "Home":
        st.markdown("""<div class="title-box"><h3>Simplifying Science for Everyone</h3></div>""", unsafe_allow_html=True)
        
        # --- 1. WELCOME MESSAGE (RESTORED) ---
        if st.session_state['logged_in']:
            st.write(f"Welcome back, **{st.session_state['username']}**!")
            st.write("") # Spacer

        # --- Search Interface (Side-by-Side) ---
        # Changed vertical_alignment to "center" for perfect alignment
        st.write("Enter a scientific term to get a simplified explanation.")
        col1, col2 = st.columns([6, 1], vertical_alignment="center") 

        with col1:
            default_val = st.session_state.get('last_search_term', "")
            search_term = st.text_input("Search", value=default_val, label_visibility="collapsed")

        with col2:
            # Mic Recorder Button
            audio_data = mic_recorder(
                start_prompt="🎙️", 
                stop_prompt="🟥", 
                just_once=True,
                key='recorder'
            )

        # --- Logic Handling ---
        
        # 1. Handle Audio Input
        if audio_data:
            with st.spinner("Processing voice..."):
                try:
                    audio_bytes = audio_data['bytes']
                    audio_file = io.BytesIO(audio_bytes)
                    audio_file.name = "audio.wav"
                    
                    files = {"file": ("audio.wav", audio_file, "audio/wav")}
                    
                    resp = requests.post(f"{BACKEND_URL}/transcribe", files=files)
                    if resp.status_code == 200:
                        transcribed_text = resp.json()['text']
                        if transcribed_text != st.session_state.get('last_search_term', ""):
                            st.session_state['last_search_term'] = transcribed_text
                            st.session_state['search_performed'] = True
                            st.rerun() 
                    else:
                        st.error("Audio error.")
                except Exception as e:
                    st.error(f"Error: {e}")

        # 2. Explain Trigger
        st.write("") 
        
        should_explain = st.button("Explain") or (st.session_state['search_performed'] and search_term)

        if should_explain:
            if search_term:
                st.session_state['search_performed'] = False 

                with st.spinner(f"Explaining '{search_term}'..."):
                    try:
                        resp = requests.post(f"{BACKEND_URL}/explain", json={"term": search_term})
                        
                        if resp.status_code == 200:
                            explanation = resp.json()['explanation']
                            st.session_state['last_explanation'] = explanation
                            st.session_state['last_search_term'] = search_term 
                            
                            if st.session_state['logged_in']:
                                try:
                                    requests.post(f"{BACKEND_URL}/save_history", json={
                                        "username": st.session_state['username'],
                                        "term": search_term,
                                        "explanation": explanation
                                    })
                                except:
                                    pass
                        
                        elif resp.status_code == 400:
                            st.session_state['last_explanation'] = ""
                            error_msg = resp.json().get('detail', "Invalid term.")
                            st.warning(f"⚠️ {error_msg}")
                        else:
                            st.error("Error generating explanation.")
                            
                    except requests.exceptions.RequestException:
                        st.error("Backend offline.")
            else:
                st.warning("Please enter a term.")

        # Display Result
        if st.session_state['last_explanation']:
            st.success(st.session_state['last_explanation'])

        # Guest Nudge
        if not st.session_state['logged_in'] and st.session_state['last_explanation']:
             st.info("Want to save your search history?")
             if st.button("Login to Save"):
                st.session_state['page'] = "Login"
                st.rerun()

    # --- Page 2: History ---
    elif st.session_state['page'] == "History":
        st.markdown("""<div class="title-box"><h3>My Learning History</h3></div>""", unsafe_allow_html=True)
        try:
            resp = requests.get(f"{BACKEND_URL}/get_history/{st.session_state['username']}")
            if resp.status_code == 200:
                history_data = resp.json()
                if history_data:
                    for item in history_data:
                        with st.expander(f"**{item['term']}** - {item['timestamp']}"):
                            st.write(item['explanation'])
                else:
                    st.info("No history found.")
            else:
                st.error("Failed to load history.")
        except:
            st.error("Backend offline.")

    # --- Page 3: Login ---
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
                        st.session_state['email'] = email
                        
                        if st.session_state['last_search_term'] and st.session_state['last_explanation']:
                            try:
                                requests.post(f"{BACKEND_URL}/save_history", json={
                                    "username": st.session_state['username'],
                                    "term": st.session_state['last_search_term'],
                                    "explanation": st.session_state['last_explanation']
                                })
                            except:
                                pass 
                        
                        st.session_state['page'] = "Home"
                        st.success("Logged in successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                except requests.exceptions.RequestException:
                    st.error("Backend offline.")

        st.markdown("---")
        if st.button("Create New Account"):
            st.session_state['page'] = "SignUp"
            st.rerun()

    # --- Page 4: SignUp ---
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
        st.session_state['email'] = "" 
        st.session_state['last_search_term'] = "" 
        st.session_state['last_explanation'] = ""
        st.session_state['page'] = "Home"
        st.rerun()

if __name__ == "__main__":
    main()