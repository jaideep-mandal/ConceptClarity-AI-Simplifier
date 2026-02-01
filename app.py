import streamlit as st
from streamlit_option_menu import option_menu
import requests
import time
from streamlit_mic_recorder import mic_recorder
import io
import json

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
if 'last_result' not in st.session_state:
    st.session_state['last_result'] = None 
if 'last_search_term' not in st.session_state:
    st.session_state['last_search_term'] = ""

# Initialize complexity_pref to "Basic" by default for Guests
if 'complexity_pref' not in st.session_state or st.session_state['complexity_pref'] is None:
    st.session_state['complexity_pref'] = "Basic"
    
# History State
if 'history_list' not in st.session_state:
    st.session_state['history_list'] = []
if 'history_offset' not in st.session_state:
    st.session_state['history_offset'] = 0

# --- CSS Styling ---
st.markdown("""
<style>
    /* 1. Global Background and Text */
    .stApp {
        background-color: #06141B;
        color: #CCD0CF;
    }
    
    /* 2. Unified Input Fields Styling */
    div[data-baseweb="input"], 
    div[data-baseweb="input"] > div,
    input {
        background-color: #9BA6A8 !important;
        color: #06141B !important;
        border-radius: 8px;
    }
    
    div[data-baseweb="input"] {
        border: 2px solid #253745 !important;
    }

    /* 3. Password Field & Eye Icon */
    div[data-baseweb="input"]:has(input[type="password"]) div[role="button"] {
        border-left: 1px solid #253745 !important;
        padding-left: 10px;
        background-color: transparent !important;
    }
    div[data-baseweb="input"] svg {
        fill: #06141B !important;
    }

    /* 4. Sidebar Toggle Button */
    button[kind="header"] {
        color: white !important;
        background-color: rgba(0, 0, 0, 0.3) !important;
        border-radius: 50% !important;
    }
    button[kind="header"]:hover {
        color: #9BA6A8 !important;
        background-color: rgba(0, 0, 0, 0.5) !important;
    }

    /* 5. Sticky Header (App Name) */
    .title-box { 
        text-align: center; 
        margin-bottom: 20px; 
        padding: 15px 0;
        color: #9BA6A8;
        background-color: rgba(6, 20, 27, 0.9);
        border-bottom: 1px solid #253745;
    }

    /* 6. Standard Buttons */
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

    /* 7. Alerts & Expanders */
    div.stAlert, .streamlit-expanderHeader {
        background-color: #11212D !important;
        color: #CCD0CF !important;
        border: 1px solid #253745 !important;
    }
    .streamlit-expanderContent {
        background-color: #06141B !important;
        color: #CCD0CF !important;
        border: 1px solid #253745 !important;
        border-top: none !important;
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
    .user-card h4 { margin: 0; color: #CCD0CF; font-size: 16px; }
    .user-card p { margin: 5px 0 0 0; color: #9BA6A8; font-size: 12px; }

    /* 9. Mic Icon Layout Alignment */
    div[data-testid="stColumn"] {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    div[data-testid="stColumn"]:nth-of-type(2) > div > div > div {
        transform: translateY(0px);
    }
            
    /* 10. REFINED MIC ICON STYLING */
    div[data-testid="stColumn"]:nth-of-type(2) iframe {
        filter: invert(1) hue-rotate(180deg) brightness(1.2) !important;
        width: 42px !important;
        height: 42px !important;
        margin: auto !important;
        display: block !important;
        border-radius: 8px !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* 11. Custom Radio Button Styling */
    div[role="radiogroup"] {
        display: flex;
        justify-content: center;
        gap: 20px;
        background-color: #11212D;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 1px solid #253745;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper: Update Preference ---
def update_pref_in_db():
    if st.session_state['logged_in'] and st.session_state['complexity_pref']:
        try:
            requests.post(f"{BACKEND_URL}/update_preference", json={
                "username": st.session_state['username'],
                "complexity": st.session_state['complexity_pref']
            })
        except:
            pass

def main():
    # --- APP NAME ---
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
        if st.session_state['logged_in']:
            st.markdown(f"<div style='text-align: center; margin-bottom: 10px;'>Welcome back, <b>{st.session_state['username']}</b>!</div>", unsafe_allow_html=True)

        # --- Search Interface ---
        st.write("Enter a scientific term to get a simplified explanation.")
        
        col1, col2 = st.columns([6, 1], vertical_alignment="center") 

        with col1:
            search_term = st.text_input("Search", key="last_search_term", label_visibility="collapsed")

        with col2:
            audio_data = mic_recorder(
                start_prompt="🎙️", 
                stop_prompt="🟥", 
                just_once=True,
                key='recorder'
            )

        # --- Complexity Toggle ---
        options = ["Basic", "Intermediate", "Advanced"]
        current_pref = st.session_state.get('complexity_pref', 'Basic')
        if current_pref not in options: current_pref = "Basic"
        default_ix = options.index(current_pref)
        
        selected_complexity = st.radio(
            "Select Detail Level:", 
            options, 
            index=default_ix,
            horizontal=True,
            key="complexity_radio",
            on_change=lambda: st.session_state.update({'complexity_pref': st.session_state.complexity_radio}) or update_pref_in_db()
        )
        st.session_state['complexity_pref'] = selected_complexity

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
        explain_clicked = st.button("Explain")
        
        should_explain = explain_clicked or (st.session_state['search_performed'] and search_term)

        if should_explain:
            if not search_term:
                st.warning("Please enter a term.")
            else:
                st.session_state['search_performed'] = False 
                current_complexity = st.session_state.get('complexity_pref', 'Basic')

                with st.spinner(f"Explaining '{search_term}' ({current_complexity} Mode)..."):
                    try:
                        resp = requests.post(f"{BACKEND_URL}/explain", json={
                            "term": search_term, 
                            "complexity": current_complexity
                        })
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            
                            # Store complexity used in the result object
                            data['complexity'] = current_complexity
                            st.session_state['last_result'] = data
                            
                            if st.session_state['logged_in']:
                                try:
                                    requests.post(f"{BACKEND_URL}/save_history", json={
                                        "username": st.session_state['username'],
                                        "term": data['term'],
                                        "category": data['category'],
                                        "explanation": data['explanation'],
                                        "extra_content": data['extra_content'],
                                        "complexity_used": current_complexity,
                                        "related_terms": data['related_terms']
                                    })
                                except:
                                    pass
                        
                        elif resp.status_code == 400:
                            st.session_state['last_result'] = None
                            error_msg = resp.json().get('detail', "Invalid term.")
                            st.warning(f"⚠️ {error_msg}")
                        else:
                            st.error("Error generating explanation.")
                            
                    except requests.exceptions.RequestException:
                        st.error("Backend offline.")

        # --- 3. Display Result ---
        if st.session_state['last_result']:
            res = st.session_state['last_result']
            
            st.markdown("---")
            st.markdown(f"## 🧬 **{res['term']}**")
            st.caption(f"**Category:** {res['category']}")
            
            st.write(f"### 📖 Explanation")
            st.write(res['explanation'])
            
            # Use the stored complexity from the result to determine the title style
            result_mode = res.get('complexity', 'Basic')
            
            if result_mode == "Basic":
                st.info(f"**📚 Story Time:**\n\n{res['extra_content']}")
            elif result_mode == "Intermediate":
                st.success(f"**🌍 Real World Scenario:**\n\n{res['extra_content']}")

            # --- RELATED TERMS ---
            st.write("### 🔗 Related Terms")
            cols = st.columns(len(res['related_terms']))
            
            def update_search(t):
                st.session_state['last_search_term'] = t
                st.session_state['search_performed'] = False
                st.session_state['last_result'] = None
            
            for idx, term in enumerate(res['related_terms']):
                cols[idx].button(
                    term, 
                    key=f"rel_{term}", 
                    on_click=update_search, 
                    args=(term,)
                )

        # Guest Nudge
        if not st.session_state['logged_in'] and st.session_state['last_result']:
             st.info("Want to save your preferences and history?")
             if st.button("Login to Save"):
                st.session_state['page'] = "Login"
                st.rerun()

    # --- Page 2: History ---
    elif st.session_state['page'] == "History":
        st.markdown("<h3>My Learning History</h3>", unsafe_allow_html=True)
        
        if not st.session_state['history_list']:
             try:
                resp = requests.get(f"{BACKEND_URL}/get_history/{st.session_state['username']}?offset=0&limit=10")
                if resp.status_code == 200:
                    st.session_state['history_list'] = resp.json()
                    st.session_state['history_offset'] = 10
             except:
                 st.error("Backend offline.")

        if st.session_state['history_list']:
            for item in st.session_state['history_list']:
                icon = "🟢" if item.get('complexity_used') == "Basic" else "MF" 
                if item.get('complexity_used') == "Intermediate": icon = "🔵"
                if item.get('complexity_used') == "Advanced": icon = "🔴"

                with st.expander(f"{icon} **{item['term']}** ({item.get('category', 'General')}) - {item['timestamp']}"):
                    st.write(f"**Explanation:** {item['explanation']}")
                    st.info(f"**Context:** {item.get('extra_content', 'N/A')}")
                    if item.get('related_terms'):
                        st.caption(f"Related: {', '.join(item['related_terms'])}")
            
            if st.button("Load More"):
                try:
                    offset = st.session_state['history_offset']
                    resp = requests.get(f"{BACKEND_URL}/get_history/{st.session_state['username']}?offset={offset}&limit=10")
                    if resp.status_code == 200:
                        new_items = resp.json()
                        if new_items:
                            st.session_state['history_list'].extend(new_items)
                            st.session_state['history_offset'] += 10
                            st.rerun()
                        else:
                            st.warning("No more history to load.")
                except:
                    pass
        else:
            st.info("No history found.")

    # --- Page 3: Login ---
    elif st.session_state['page'] == "Login":
        st.markdown("<h3>Login</h3>", unsafe_allow_html=True)
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            with st.spinner("Logging in..."):
                try:
                    guest_pref_to_save = st.session_state.get('complexity_pref', 'Basic')
                    resp = requests.post(f"{BACKEND_URL}/login", json={"email": email, "password": password})
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = data['username']
                        st.session_state['email'] = email
                        
                        # 1. Save Preference
                        st.session_state['complexity_pref'] = guest_pref_to_save
                        update_pref_in_db() 
                        
                        # 2. SAVE GUEST HISTORY (NEW FIX)
                        if st.session_state.get('last_result'):
                            try:
                                res = st.session_state['last_result']
                                requests.post(f"{BACKEND_URL}/save_history", json={
                                    "username": data['username'],
                                    "term": res['term'],
                                    "category": res['category'],
                                    "explanation": res['explanation'],
                                    "extra_content": res['extra_content'],
                                    "complexity_used": res.get('complexity', 'Basic'),
                                    "related_terms": res['related_terms']
                                })
                            except:
                                pass # Silent fail if history save has issues

                        st.session_state['page'] = "Home"
                        st.success("Logged in successfully! History & Preferences saved.")
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
        st.markdown("<h3>Create Account</h3>", unsafe_allow_html=True)
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
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()