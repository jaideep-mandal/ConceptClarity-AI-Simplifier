from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import hashlib
import os
from groq import Groq
from dotenv import load_dotenv

# 1. Load the hidden API key from .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# 2. Check if key exists
if not api_key:
    raise ValueError("API Key not found! Make sure you have a .env file with GROQ_API_KEY.")

# 3. Initialize Groq
client = Groq(api_key=api_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, email TEXT, password TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- Models ---
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ExplainRequest(BaseModel):
    term: str

# --- Helpers ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- Routes ---
@app.post("/register")
def register_user(user: UserRegister):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM userstable WHERE email = ?', (user.email,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = make_hashes(user.password)
    c.execute('INSERT INTO userstable(username, email, password) VALUES (?,?,?)', 
              (user.username, user.email, hashed_pw))
    conn.commit()
    conn.close()
    return {"message": "User registered successfully"}

@app.post("/login")
def login_user(user: UserLogin):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_pw = make_hashes(user.password)
    c.execute('SELECT * FROM userstable WHERE email = ? AND password = ?', 
              (user.email, hashed_pw))
    data = c.fetchone()
    conn.close()
    
    if data:
        return {"message": "Login successful", "username": data[0]}
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")

# --- AI Endpoint ---
@app.post("/explain")
def explain_term(request: ExplainRequest):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert science tutor. Explain the following scientific term simply and clearly for a student. Keep it concise (under 3 sentences)."
                },
                {
                    "role": "user",
                    "content": request.term,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        return {"explanation": chat_completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))