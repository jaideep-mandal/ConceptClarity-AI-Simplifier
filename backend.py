# backend.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import hashlib

app = FastAPI()

# --- Database Setup (Step 1 requirement) ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Create table with columns for username, email, and password
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, email TEXT, password TEXT)')
    conn.commit()
    conn.close()

init_db()  # Run this immediately when server starts

# --- Data Models ---
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# --- Security Helper ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- Routes ---

# Step 2: Signup Endpoint
@app.post("/register")
def register_user(user: UserRegister):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Check if email already exists
    c.execute('SELECT * FROM userstable WHERE email = ?', (user.email,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Save new user
    hashed_pw = make_hashes(user.password)
    c.execute('INSERT INTO userstable(username, email, password) VALUES (?,?,?)', 
              (user.username, user.email, hashed_pw))
    conn.commit()
    conn.close()
    return {"message": "User registered successfully"}

# Step 3: Login Endpoint
@app.post("/login")
def login_user(user: UserLogin):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_pw = make_hashes(user.password)
    
    # Check credentials
    c.execute('SELECT * FROM userstable WHERE email = ? AND password = ?', 
              (user.email, hashed_pw))
    data = c.fetchone()
    conn.close()
    
    if data:
        # Return success and the username (data[0] is username)
        return {"message": "Login successful", "username": data[0]}
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")