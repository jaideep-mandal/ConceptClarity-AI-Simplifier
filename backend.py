from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import hashlib
import os
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime

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
    # User Table
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, email TEXT, password TEXT)')
    # History Table (New)
    c.execute('''
        CREATE TABLE IF NOT EXISTS search_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            term TEXT,
            explanation TEXT,
            timestamp TEXT
        )
    ''')
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

# New Model for Saving History
class HistoryRequest(BaseModel):
    username: str
    term: str
    explanation: str

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

# --- Voice Endpoint (Strict English) ---
@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # Send audio file to Groq Whisper
        transcription = client.audio.transcriptions.create(
            file=(file.filename, file.file.read()), # Send the file bytes
            model="whisper-large-v3",
            response_format="json",
            language="en",  # <--- FORCE English output
            prompt="Scientific terms in English." # <--- Context hint to reduce hallucinations
        )
        return {"text": transcription.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- AI Endpoint ---
@app.post("/explain")
def explain_term(request: ExplainRequest):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are a strict science tutor. 
                    1. First, check if the user's input is a valid scientific concept (Physics, Chemistry, Biology, Math, Computer Science, Astronomy, etc.).
                    2. If it is NOT a scientific term (e.g., a celebrity, movie, food, or random nonsense), output EXACTLY and ONLY the string: 'INVALID_TERM'.
                    3. If it IS scientific, explain it simply and clearly for a student in under 3 sentences.
                    """
                },
                {
                    "role": "user",
                    "content": request.term,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        
        response_text = chat_completion.choices[0].message.content.strip()

        # Check if AI rejected the term
        if "INVALID_TERM" in response_text:
            raise HTTPException(status_code=400, detail="This doesn't seem to be a scientific term. Please try again!")
        
        return {"explanation": response_text}

    except HTTPException as he:
        raise he # Re-raise known HTTP errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- NEW: History Endpoints ---

@app.post("/save_history")
def save_history(entry: HistoryRequest):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO search_history(username, term, explanation, timestamp) VALUES (?,?,?,?)',
              (entry.username, entry.term, entry.explanation, timestamp))
    conn.commit()
    conn.close()
    return {"message": "History saved"}

@app.get("/get_history/{username}")
def get_history(username: str):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Get last 10 searches, newest first
    c.execute('SELECT term, explanation, timestamp FROM search_history WHERE username = ? ORDER BY id DESC LIMIT 10', (username,))
    data = c.fetchall()
    conn.close()
    
    # Convert list of tuples to list of dictionaries
    history_list = [{"term": row[0], "explanation": row[1], "timestamp": row[2]} for row in data]
    return history_list