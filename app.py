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
# --- FIX: Initialize the widget key to match the variable ---
if 'search_widget' not in st.session_state:
    st.session_state['search_widget'] = ""

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
        background: radial-gradient(circle at top right, #0D2029, #06141B);
        color: #E0E4E3;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* 2. Unified Input Fields Styling - Glassmorphism */
    div[data-baseweb="input"] {
        background-color: rgba(155, 166, 168, 0.1) !important;
        border: 1px solid rgba(37, 55, 69, 0.5) !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
        backdrop-filter: blur(5px);
    }

    div[data-baseweb="input"]:focus-within {
        border-color: #4A5C6A !important;
        box-shadow: 0 0 0 2px rgba(74, 92, 106, 0.2);
    }

    input {
        background-color: transparent !important;
        color: #E0E4E3 !important;
        padding: 12px !important;
    }

    /* 3. Password Field & Eye Icon */
    div[data-baseweb="input"]:has(input[type="password"]) div[role="button"] {
        border-left: 1px solid rgba(37, 55, 69, 0.5) !important;
        padding-left: 10px;
        background-color: transparent !important;
    }
    div[data-baseweb="input"] svg {
        fill: #9BA6A8 !important;
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
        margin-bottom: 30px; 
        padding: 20px 0;
        color: #9BA6A8;
        background: rgba(6, 20, 27, 0.7);
        backdrop-filter: blur(15px);
        border-bottom: 1px solid rgba(37, 55, 69, 0.3);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }

    .title-box h1 {
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(90deg, #9BA6A8, #CCD0CF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* 12. Standard Buttons & Related Terms - Modern Pill Style */
    .stButton>button {
        background: linear-gradient(135deg, #253745 0%, #11212D 100%) !important;
        color: #CCD0CF !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 0.4rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        letter-spacing: 0.3px;
        font-size: 0.85rem !important;
        width: auto !important;
        min-width: fit-content !important;
        white-space: nowrap !important;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        background: linear-gradient(135deg, #4A5C6A 0%, #253745 100%) !important;
    }

    /* 7. Alerts & Cards */
    div.stAlert, .streamlit-expanderHeader, .user-card {
        background: rgba(17, 33, 45, 0.4) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(37, 55, 69, 0.3) !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    }
    .streamlit-expanderContent {
        background-color: rgba(6, 20, 27, 0.4) !important;
        color: #CCD0CF !important;
        border: 1px solid rgba(37, 55, 69, 0.3) !important;
        border-top: none !important;
        border-radius: 0 0 16px 16px !important;
    }

    /* 8. User Profile Sidebar Card */
    .user-card {
        background: rgba(17, 33, 45, 0.4) !important;
        padding: 15px;
        border-radius: 16px;
        border: 1px solid rgba(37, 55, 69, 0.3);
        margin-top: 20px;
        text-align: center;
        backdrop-filter: blur(10px);
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
        width: 41px !important;
        height: 38px !important;
        margin: auto !important;
        display: block !important;
        border-radius: 8px !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        transition: none !important;
    }
    div[data-testid="stColumn"]:nth-of-type(2) iframe:focus,
    div[data-testid="stColumn"]:nth-of-type(2) iframe:active,
    div[data-testid="stColumn"]:nth-of-type(2) iframe:hover {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* 11. Custom Radio Button Styling - Modern Segmented Control */
    div[role="radiogroup"] {
        background-color: rgba(17, 33, 45, 0.6);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(37, 55, 69, 0.4);
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 15px;
    }

    /* 12. Flexbox for Related Terms (Dynamic Wrap) */
    .related-terms-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
        justify-content: flex-start;
    }

    /* Target the streamlit button container inside our flex wrapper */
    .related-terms-container div[data-testid="stButton"] {
        width: fit-content !important;
        margin-bottom: 8px;
    }

    /* Target button itself to ensure it doesn't stretch */
    .related-terms-container button {
        width: auto !important;
        min-width: fit-content !important;
        padding: 6px 18px !important;
    }

    /* 13. Sidebar Option Menu Styling */
    .nav-link {
        border-radius: 10px !important;
        margin: 4px 0 !important;
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

# --- FIX: New Callback Function to Sync Input ---
def update_search_box():
    # Sync the widget's value to our main state variable
    st.session_state['last_search_term'] = st.session_state.search_widget

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

        # STEP 1: Handle Microphone FIRST (Must be before Text Input to avoid crash)
        with col2:
            audio_data = mic_recorder(
                start_prompt="🎙️", 
                stop_prompt="🟥", 
                just_once=True,
                key='recorder'
            )
            
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
                                # Update the main variable
                                st.session_state['last_search_term'] = transcribed_text
                                # Force-update the widget state
                                st.session_state['search_widget'] = transcribed_text 
                                
                                # FIX: Set to False so it updates the text BUT DOES NOT auto-explain
                                st.session_state['search_performed'] = False 
                                
                                st.rerun() 
                        else:
                            st.error("Audio error.")
                    except Exception as e:
                        st.error(f"Error: {e}")

        # STEP 2: Draw Text Input SECOND
        with col1:
            st.text_input(
                "Search", 
                # value=st.session_state['last_search_term'], <--- REMOVED TO FIX WARNING
                key="search_widget",          
                on_change=update_search_box,  
                label_visibility="collapsed"
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
        
        # --- FIX: Define search_term variable (Required because we removed 'value=' from the widget)
        search_term = st.session_state['last_search_term']

        # Note: We removed "# 1. Handle Audio Input" from here because 
        # it is now handled correctly inside the 'col2' block above.

        # 2. Explain Trigger
        st.write("") 
        explain_clicked = st.button("Explain")
        
        # Now 'search_term' is defined, so this line works perfectly
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

            # --- Feedback Logic Helper ---
            # We construct a unique key to store the Feedback ID for this specific search result
            # e.g., "fb_id_gravity_Basic"
            current_fb_id_key = f"fb_id_{res['term']}_{res.get('complexity', 'Basic')}"

            def send_feedback_to_api(rating_val, comment_text=""):
                # Prepare payload
                fb_user = st.session_state['username'] if st.session_state['logged_in'] else "Guest"
                
                # Check if we already have an ID for this session (meaning we are updating)
                existing_id = st.session_state.get(current_fb_id_key, None)
                
                payload = {
                    "id": existing_id, # If None, backend creates new. If exists, backend updates.
                    "username": fb_user,
                    "term": res['term'],
                    "complexity": res.get('complexity', 'Basic'),
                    "category": res.get('category', 'General'),
                    "explanation": res['explanation'],
                    "extra_content": res['extra_content'],
                    "rating": rating_val,
                    "comment": comment_text
                }

                try:
                    resp = requests.post(f"{BACKEND_URL}/submit_feedback", json=payload)
                    if resp.status_code == 200:
                        # Save the ID returned by backend so next time we update this same row
                        new_id = resp.json().get('id')
                        st.session_state[current_fb_id_key] = new_id
                        return True
                    else:
                        st.error(f"Error: {resp.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")
                return False
            
            if result_mode == "Basic":
                st.info(f"**📚 Story Time:**\n\n{res['extra_content']}")
            elif result_mode == "Intermediate":
                st.success(f"**🌍 Real World Scenario:**\n\n{res['extra_content']}")

            # --- NEW: Customer Feedback Section (Disappearing Form) ---
            
            # 1. Create unique keys for this specific search result
            current_fb_id_key = f"fb_id_{res['term']}_{res.get('complexity', 'Basic')}"
            fb_submitted_key = f"fb_done_{res['term']}_{res.get('complexity', 'Basic')}"

            # 2. Helper to send data (Inserts or Updates based on ID)
            def send_feedback_to_api(rating_val, comment_text=""):
                fb_user = st.session_state['username'] if st.session_state['logged_in'] else "Guest"
                existing_id = st.session_state.get(current_fb_id_key, None)
                
                payload = {
                    "id": existing_id, 
                    "username": fb_user,
                    "term": res['term'],
                    "complexity": res.get('complexity', 'Basic'),
                    "category": res.get('category', 'General'),
                    "explanation": res['explanation'],
                    "extra_content": res['extra_content'],
                    "rating": rating_val,
                    "comment": comment_text
                }

                try:
                    resp = requests.post(f"{BACKEND_URL}/submit_feedback", json=payload)
                    if resp.status_code == 200:
                        new_id = resp.json().get('id')
                        st.session_state[current_fb_id_key] = new_id
                        return True
                    else:
                        st.error(f"Error: {resp.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")
                return False

            # 3. LOGIC: If submitted, show "Thanks". If not, show Form.
            if st.session_state.get(fb_submitted_key, False):
                 # --- VIEW A: SUCCESS MESSAGE ---
                 st.success("✅ **Thanks for your feedback!**")
                 
            else:
                # --- VIEW B: FEEDBACK FORM ---
                with st.expander("Rate this explanation", expanded=True):
                    fb_col1, fb_col2 = st.columns([3, 1], vertical_alignment="bottom")
                    
                    with fb_col1:
                        # STAR RATING (Immediate Save)
                        star_key = f"star_widget_{res['term']}"
                        
                        def on_star_change():
                            val = st.session_state[star_key]
                            if val is not None:
                                send_feedback_to_api(val + 1, "") 
                                st.toast("Rating saved! ⭐") 

                        st.feedback("stars", key=star_key, on_change=on_star_change)
                        
                        # COMMENT BOX
                        fb_comment = st.text_input(
                            "Comment (Optional)", 
                            placeholder="Tell us more...", 
                            key=f"comment_{res['term']}"
                        )
                    
                    with fb_col2:
                        # SUBMIT BUTTON (Finalize & Close)
                        if st.button("Submit Comment", key=f"btn_fb_{res['term']}"):
                            current_stars = st.session_state.get(star_key)
                            rating_to_send = (current_stars + 1) if current_stars is not None else 5
                            
                            if send_feedback_to_api(rating_to_send, fb_comment):
                                # Mark as done so the form disappears
                                st.session_state[fb_submitted_key] = True
                                st.rerun()

            # --- RELATED TERMS (Optimized Flow) ---
            st.write("### 🔗 Related Terms")

            if res['related_terms']:
                def update_search(t):
                    st.session_state['last_search_term'] = t
                    st.session_state['search_widget'] = t 
                    st.session_state['search_performed'] = False
                    st.session_state['last_result'] = None

                # Create a horizontal flow of buttons that wrap naturally
                st.markdown('<div class="related-terms-container">', unsafe_allow_html=True)
                
                # Using st.button with use_container_width=False and CSS flex container
                # is the most robust way to handle varying lengths in Streamlit
                # We wrap each button in a div to control its flex behavior
                for term in res['related_terms']:
                    st.button(
                        term, 
                        key=f"rel_{term}", 
                        on_click=update_search, 
                        args=(term,),
                        use_container_width=False
                    )
                st.markdown('</div>', unsafe_allow_html=True)

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