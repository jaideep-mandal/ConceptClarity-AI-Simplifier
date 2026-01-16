import streamlit as st
from streamlit_option_menu import option_menu
import requests
import time
import base64

# Connection to your FastAPI Backend
BACKEND_URL = "http://127.0.0.1:8000"

# --- SCIENTIFIC BACKGROUND GENERATOR ---
def get_scientific_bg():
    # This SVG defines the Atoms, DNA, and Flask icons
    svg_bg = """
    <svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <g fill="none" stroke="#CBD5E1" stroke-width="1.5" opacity="0.6">
            <circle cx="40" cy="40" r="10"/>
            <ellipse cx="40" cy="40" rx="25" ry="8" transform="rotate(45 40 40)"/>
            <ellipse cx="40" cy="40" rx="25" ry="8" transform="rotate(-45 40 40)"/>
            <path d="M140,130 L150,160 H130 L140,130 V115 H145 V130"/>
            <path d="M30,140 Q40,150 50,140 T70,140 T90,140"/>
            <path d="M30,150 Q40,140 50,150 T70,150 T90,150"/>
            <circle cx="150" cy="40" r="15"/>
            <path d="M150,55 L150,70"/>
        </g>
    </svg>
    """
    b64_bg = base64.b64encode(svg_bg.encode("utf-8")).decode("utf-8")
    
    return f"""
    <style>
    .stApp {{
        background-color: #F8FAFC;
        background-image: url("data:image/svg+xml;base64,{b64_bg}");
        background-size: 150px 150px;
        background-repeat: repeat;
        background-attachment: fixed;
    }}
    </style>
    """

st.markdown(get_scientific_bg(), unsafe_allow_html=True)

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'page' not in st.session_state:
    st.session_state['page'] = "Home"  # Default start page

if 'search_performed' not in st.session_state:
    st.session_state['search_performed'] = False

# Custom CSS for Password Field and Layout
st.markdown("""
<style>
    /* Force Light Theme */
    [data-testid="stAppViewContainer"] {
        background-color: transparent;
        color: black;
    }
    
    /* Blue Border Container around all input fields */
    div[data-baseweb="input"] {
        border: 2px solid #007bff !important;
        border-radius: 4px;
    }
    /* Grey Partition Line separating the eye icon in password fields */
    div[data-baseweb="input"]:has(input[type="password"]) div[role="button"] {
        border-left: 1px solid #ccc !important;
        padding-left: 10px;
        margin-left: 10px;
    }

    /* Shorter and Centered Input Fields */
    .shorter-input {
        max-width: 400px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Centered Title and Subheader for all pages
    st.markdown("""
        <div style="text-align: center;">
            <h1>Concept Clarity</h1>
        </div>
    """, unsafe_allow_html=True)

    # --- Sidebar Logic with streamlit-option-menu ---
    with st.sidebar:
        if st.session_state['logged_in']:
            menu_options = ["Home", "Logout"]
            menu_icons = ["house", "box-arrow-right"]
        else:
            menu_options = ["Home", "Login", "SignUp"]
            menu_icons = ["house", "person", "person-plus"]
        
        # Calculate index for option_menu
        try:
            default_index = menu_options.index(st.session_state['page'])
        except ValueError:
            default_index = 0

        choice = option_menu(
            "Menu", 
            menu_options,
            icons=menu_icons, 
            menu_icon="cast", 
            default_index=default_index,
            styles={
                "container": {"padding": "5!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "25px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#02ab21"},
            }
        )
        
        # Update session state based on menu selection
        if choice != st.session_state['page']:
            st.session_state['page'] = choice
            st.rerun()

    # --- Page 1: Home ---
    if st.session_state['page'] == "Home":
        st.markdown("""
            <div style="text-align: center;">
                <h3>Simplifying Science for Everyone</h3>
            </div>
        """, unsafe_allow_html=True)
        if st.session_state['logged_in']:
            st.write(f"Welcome back, **{st.session_state['username']}**!")
        
        # The Search Bar
        search_term = st.text_input("Enter a scientific term to get a simplified explanation.")
        if st.button("Explain"):
            if search_term:
                st.session_state['search_performed'] = True
                st.info(f"AI explanation for {search_term}...")
            else:
                st.warning("Please enter a term.")
        
        # Condition for Non-Logged In Users - Only after search
        if not st.session_state['logged_in'] and st.session_state['search_performed']:
            st.info("Want to save your search history?")
            if st.button("Login to Save"):
                st.session_state['page'] = "Login"
                st.rerun()

    # --- Page 2: Login ---
    elif st.session_state['page'] == "Login":
        st.markdown("""
            <div style="text-align: center;">
                <h3>Login</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Centering and shortening login form
        _, col, _ = st.columns([1, 2, 1])
        with col:
            email = st.text_input("Email")
            password = st.text_input("Password", type='password')
            
            if st.button("Login"):
                try:
                    payload = {"email": email, "password": password}
                    response = requests.post(f"{BACKEND_URL}/login", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = data['username']
                        st.session_state['page'] = "Home"
                        
                        st.success(f"Login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid Email or Password")
                
                # CHANGE: Specific exception handling
                except requests.exceptions.RequestException:
                    st.error("Could not connect to backend. Is FastAPI running?")

            # --- NEW: Create Account Redirect ---
            st.markdown("---")
            st.write("Don't have an account?")
            if st.button("Create New Account"):
                st.session_state['page'] = "SignUp"
                st.rerun()

    # --- Page 3: SignUp ---
    elif st.session_state['page'] == "SignUp":
        st.markdown("""
            <div style="text-align: center;">
                <h3>Create New Account</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Centering and shortening signup form
        _, col, _ = st.columns([1, 2, 1])
        with col:
            new_user = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type='password')

            if st.button("Register"):
                try:
                    payload = {"username": new_user, "email": new_email, "password": new_password}
                    response = requests.post(f"{BACKEND_URL}/register", json=payload)
                    
                    if response.status_code == 200:
                        st.success("Account created! Redirecting to Login...")
                        time.sleep(1)
                        st.session_state['page'] = "Login"
                        # Rerun acts like a 'stop', so we don't need code after it
                        st.rerun()
                    else:
                        st.error(response.json().get('detail', 'Registration failed'))
                
                # CHANGE: Only catch connection errors, let the Rerun exception pass through
                except requests.exceptions.RequestException:
                    st.error("Could not connect to backend. Is FastAPI running?")

            # Option to go back to Login
            st.markdown("---") 
            if st.button("Back to Login"):
                st.session_state['page'] = "Login"
                st.rerun()

    # --- Page 4: Logout ---
    elif st.session_state['page'] == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.session_state['page'] = "Login"
        st.rerun()

if __name__ == '__main__':
    main()