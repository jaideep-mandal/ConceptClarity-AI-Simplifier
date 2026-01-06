import streamlit as st
import requests
import time

# Connection to your FastAPI Backend
BACKEND_URL = "http://127.0.0.1:8000"

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'page' not in st.session_state:
    st.session_state['page'] = "Login"  # Default start page

def main():
    st.title("Concept Clarity")

    # --- Sidebar Logic (Updated for Navigation) ---
    # We calculate 'index' so the sidebar automatically highlights the current page
    if st.session_state['logged_in']:
        menu = ["Home", "Logout"]
        # If we are on Home, highlight index 0
        index = 0 if st.session_state['page'] == "Home" else 0
    else:
        menu = ["Login", "SignUp"]
        # If we are on Login, highlight index 0. If SignUp, highlight index 1.
        if st.session_state['page'] == "Login":
            index = 0
        elif st.session_state['page'] == "SignUp":
            index = 1
        else:
            index = 0
    
    # Create the sidebar
    choice = st.sidebar.selectbox("Menu", menu, index=index)
    
    # Sync manual sidebar selection with session state
    # This handles when a user clicks the sidebar directly instead of our buttons
    if not st.session_state['logged_in']:
         if choice == "Login" and st.session_state['page'] != "Login":
             st.session_state['page'] = "Login"
             st.rerun()
         elif choice == "SignUp" and st.session_state['page'] != "SignUp":
             st.session_state['page'] = "SignUp"
             st.rerun()

    # --- Page 1: Home (Only accessible if logged in) ---
    if choice == "Home":
        if st.session_state['logged_in']:
            st.subheader("Simplifying Science for Everyone")
            st.write(f"Welcome back, **{st.session_state['username']}**!")
            
            # The Search Bar
            search_term = st.text_input("Enter a scientific term to explain:")
            if st.button("Explain"):
                if search_term:
                    st.info(f"Searching explanation for: '{search_term}'... (AI Integration coming in Module 2)")
                else:
                    st.warning("Please enter a term.")
        else:
            st.warning("Access Denied. Please Login first.")
            st.session_state['page'] = "Login"
            st.rerun()

    # --- Page 2: Login ---
    elif choice == "Login":
        st.subheader("Login")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type='password')
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
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
    elif choice == "SignUp":
        st.subheader("Create New Account")
        
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
    elif choice == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.session_state['page'] = "Login"
        st.rerun()

if __name__ == '__main__':
    main()