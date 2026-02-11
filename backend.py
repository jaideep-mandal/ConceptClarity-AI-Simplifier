from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import sqlite3
import hashlib
import os
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Optional # Make sure to import Optional

# Load environment variables
load_dotenv()

app = FastAPI()

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Groq Client Setup ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing in .env file")

# --- NEW: Admin Environment Variables ---
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

client = Groq(api_key=GROQ_API_KEY)

# --- Database Setup & Migration ---
DB_NAME = "users.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_db():
    """
    Updates the database schema automatically without deleting data.
    Adds new columns for Milestone 3 features if they don't exist.
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Create tables if they don't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS userstable (
            username TEXT,
            email TEXT PRIMARY KEY,
            password TEXT,
            complexity_pref TEXT DEFAULT NULL 
        )
    ''')

    # --- NEW: Admin Table ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS admintable (
            username TEXT,
            email TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    # UPDATED: Seed an admin user using Environment Variables
    c.execute('SELECT COUNT(*) FROM admintable')
    if c.fetchone()[0] == 0:
        if ADMIN_EMAIL and ADMIN_PASSWORD:
            admin_hashed_pw = hashlib.sha256(str.encode(ADMIN_PASSWORD)).hexdigest()
            c.execute('INSERT INTO admintable (username, email, password) VALUES (?, ?, ?)',
                      ("AdminUser", ADMIN_EMAIL, admin_hashed_pw))
            print("Admin account seeded from environment variables.")
        else:
            print("Warning: Admin credentials not found in .env file.")
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            term TEXT,
            category TEXT,
            explanation TEXT,
            extra_content TEXT,
            complexity_used TEXT,
            related_terms TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- NEW: Feedback Table with ALL fields ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            term TEXT,
            complexity TEXT,
            category TEXT,         -- New
            explanation TEXT,      -- New
            extra_content TEXT,    -- New
            rating INTEGER,
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Check and Add Missing Columns for Existing Tables (Migration Logic)
    
    # Check 'userstable' for 'complexity_pref'
    c.execute("PRAGMA table_info(userstable)")
    columns = [info[1] for info in c.fetchall()]
    if 'complexity_pref' not in columns:
        print("Migrating: Adding 'complexity_pref' to userstable...")
        c.execute("ALTER TABLE userstable ADD COLUMN complexity_pref TEXT DEFAULT NULL")

    conn.commit()
    conn.close()

# Run migration on startup
migrate_db()

# --- Utility Functions ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# --- Pydantic Models ---
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ExplainRequest(BaseModel):
    term: str
    complexity: str  # 'Basic', 'Intermediate', 'Advanced'

class HistoryRequest(BaseModel):
    username: str
    term: str
    category: str
    explanation: str
    extra_content: str
    complexity_used: str
    related_terms: list 

class PreferenceRequest(BaseModel):
    username: str
    complexity: str

# --- NEW: Feedback Model ---
class FeedbackRequest(BaseModel):
    id: Optional[int] = None  # If provided, we UPDATE. If None, we INSERT.
    username: str
    term: str
    complexity: str
    category: str       # New
    explanation: str    # New
    extra_content: str  # New
    rating: int
    comment: Optional[str] = ""

# --- Auth Endpoints ---
@app.post("/register")
def register_user(user: UserRegister):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM userstable WHERE email = ?', (user.email,))
        if c.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_pw = make_hashes(user.password)
        # Default complexity is NULL until they choose
        c.execute('INSERT INTO userstable(username, email, password, complexity_pref) VALUES (?,?,?,?)', 
                  (user.username, user.email, hashed_pw, None))
        conn.commit()
        return {"message": "User registered successfully"}
    finally:
        conn.close()

@app.post("/login")
def login_user(user: UserLogin):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        hashed_pw = make_hashes(user.password)
        
        # 1. Check userstable
        c.execute('SELECT * FROM userstable WHERE email = ?', (user.email,))
        data = c.fetchone()
        
        if data and data['password'] == hashed_pw:
            return {
                "username": data['username'],
                "email": data['email'],
                "complexity_pref": data['complexity_pref'],
                "role": "user"
            }
        
        # 2. Check admintable
        c.execute('SELECT * FROM admintable WHERE email = ?', (user.email,))
        admin_data = c.fetchone()
        
        if admin_data and admin_data['password'] == hashed_pw:
            return {
                "username": admin_data['username'],
                "email": admin_data['email'],
                "role": "admin"
            }
        
        raise HTTPException(status_code=401, detail="Invalid email or password")
    finally:
        conn.close()

@app.post("/update_preference")
def update_preference(req: PreferenceRequest):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('UPDATE userstable SET complexity_pref = ? WHERE username = ?', (req.complexity, req.username))
        conn.commit()
        return {"message": "Preference updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- AI Logic Endpoints ---

@app.post("/explain")
def explain_term(request: ExplainRequest):
    term = request.term
    complexity = request.complexity

    # 1. Select the Persona based on Complexity
    if complexity == "Basic":
        system_prompt = """
        You are a creative science storyteller for beginners.
        1. Check if the term is scientific. If NOT, return {"error": "INVALID_TERM"}.
        2. If YES, return a JSON object with:
           - "term": The term itself.
           - "category": (e.g., Physics, Biology).
           - "explanation": Simple, easy to understand (max 2 sentences).
           - "extra_content": A short, engaging story with characters (like 'Raju' or 'Professor X') to explain the concept.
           - "related_terms": A list of 3 simple related terms.
        """
    elif complexity == "Intermediate":
        system_prompt = """
        You are a practical science tutor.
        1. Check if the term is scientific. If NOT, return {"error": "INVALID_TERM"}.
        2. If YES, return a JSON object with:
           - "term": The term.
           - "category": Field of science.
           - "explanation": Detailed standard definition.
           - "extra_content": A concrete Real-World Scenario or application of this term.
           - "related_terms": A list of 3 related terms.
        """
    else: # Advanced
        system_prompt = """
        You are a Research Professor.
        1. Check if the term is scientific. If NOT, return {"error": "INVALID_TERM"}.
        2. If YES, return a JSON object with:
           - "term": The term.
           - "category": specific academic field.
           - "explanation": In-depth, technical, academic explanation suitable for a researcher.
           - "extra_content": "Academic Analysis provided." (or similar brief confirmation).
           - "related_terms": A list of 3 advanced related terms.
        """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt + " \n IMPORTANT: OUTPUT MUST BE VALID JSON ONLY."},
                {"role": "user", "content": f"Explain: {term}"}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        response_content = chat_completion.choices[0].message.content
        data = json.loads(response_content)

        if "error" in data and data["error"] == "INVALID_TERM":
             raise HTTPException(status_code=400, detail="This doesn't seem to be a scientific term.")
             
        return data

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI output error (Invalid JSON). Try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        transcription = client.audio.transcriptions.create(
            file=(file.filename, file.file.read()),
            model="whisper-large-v3",
            response_format="json",
            language="en",
            prompt="Scientific terms in English."
        )
        return {"text": transcription.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Feedback Endpoint (Smart Update) ---
@app.post("/submit_feedback")
def submit_feedback(req: FeedbackRequest):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Scenario 1: Update existing feedback (User added a comment to an existing rating)
        if req.id:
            c.execute('''
                UPDATE feedback 
                SET rating = ?, comment = ? 
                WHERE id = ?
            ''', (req.rating, req.comment, req.id))
            conn.commit()
            return {"message": "Feedback updated", "id": req.id}
        
        # Scenario 2: Create new feedback (User just clicked a star)
        else:
            c.execute('''
                INSERT INTO feedback (username, term, complexity, category, explanation, extra_content, rating, comment) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (req.username, req.term, req.complexity, req.category, req.explanation, req.extra_content, req.rating, req.comment))
            conn.commit()
            return {"message": "Feedback saved", "id": c.lastrowid} # Return ID so frontend can update later
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- History Endpoints ---

@app.post("/save_history")
def save_history(req: HistoryRequest):
    conn = get_db_connection()
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        related_terms_str = json.dumps(req.related_terms)
        
        c.execute('''
            INSERT INTO history (username, term, category, explanation, extra_content, complexity_used, related_terms, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (req.username, req.term, req.category, req.explanation, req.extra_content, req.complexity_used, related_terms_str, timestamp))
        conn.commit()
        return {"message": "History saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- Admin Analytics Endpoints ---
@app.get("/admin/stats")
def get_admin_stats():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT COUNT(*) FROM userstable')
        total_users = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM history')
        total_searches = c.fetchone()[0]
        
        # Calculate Real Average Rating
        c.execute('SELECT AVG(rating) FROM feedback')
        avg_rating = c.fetchone()[0]
        # Handle case where there is no feedback yet
        avg_rating = round(avg_rating, 1) if avg_rating else 0.0
        
        return {
            "total_users": total_users,
            "total_searches": total_searches,
            "avg_rating": avg_rating
        }
    finally:
        conn.close()
@app.get("/admin/trends")
def get_admin_trends():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Most searched terms
        c.execute('''
            SELECT term, COUNT(*) as count 
            FROM history 
            GROUP BY term 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        top_terms = [{"term": row[0], "count": row[1]} for row in c.fetchall()]
        
        # Complexity distribution
        c.execute('''
            SELECT complexity_used, COUNT(*) as count 
            FROM history 
            GROUP BY complexity_used
        ''')
        complexity_dist = {row[0]: row[1] for row in c.fetchall()}
        
        return {
            "top_terms": top_terms,
            "complexity_distribution": complexity_dist
        }
    finally:
        conn.close()
@app.get("/admin/users")
def get_admin_users():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # List users with their search counts
        c.execute('''
            SELECT u.username, u.email, COUNT(h.id) as search_count
            FROM userstable u
            LEFT JOIN history h ON u.username = h.username
            GROUP BY u.username, u.email
        ''')
        users = [{"username": row[0], "email": row[1], "search_count": row[2]} for row in c.fetchall()]
        return users
    finally:
        conn.close()

# Updated for Pagination: Accepts offset and limit
@app.get("/get_history/{username}")
def get_history(username: str, offset: int = 0, limit: int = 10):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # SQL supports pagination now
        c.execute('SELECT * FROM history WHERE username = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?', (username, limit, offset))
        rows = c.fetchall()
        
        history_data = []
        for row in rows:
            item = dict(row)
            if item['related_terms']:
                try:
                    item['related_terms'] = json.loads(item['related_terms'])
                except:
                    item['related_terms'] = []
            history_data.append(item)
            
        return history_data
    finally:
        conn.close()

# --- Admin Role Management Endpoints ---

@app.get("/admin/list")
def list_admins():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT username, email FROM admintable')
        return [{"username": row[0], "email": row[1]} for row in c.fetchall()]
    finally:
        conn.close()

@app.post("/admin/add")
def add_new_admin(req: UserRegister): # Reuse UserRegister model
    conn = get_db_connection()
    c = conn.cursor()
    try:
        hashed_pw = hashlib.sha256(str.encode(req.password)).hexdigest()
        c.execute('INSERT INTO admintable (username, email, password) VALUES (?, ?, ?)',
                  (req.username, req.email, hashed_pw))
        conn.commit()
        return {"message": "Admin added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Admin already exists or invalid data.")
    finally:
        conn.close()

@app.delete("/admin/delete/{email}")
def delete_admin(email: str):
    # Security: Prevent deleting the seed admin from .env
    if email == os.getenv("ADMIN_EMAIL"):
        raise HTTPException(status_code=403, detail="The primary seed admin cannot be deleted.")
        
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('DELETE FROM admintable WHERE email = ?', (email,))
        conn.commit()
        return {"message": "Admin deleted"}
    finally:
        conn.close()

@app.get("/admin/is_super/{email}")
def check_is_super_admin(email: str):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Get the email of the very first admin (ordered by hidden rowid)
        c.execute('SELECT email FROM admintable ORDER BY rowid ASC LIMIT 1')
        first_admin = c.fetchone()
        
        if first_admin and first_admin[0] == email:
            return {"is_super": True}
        return {"is_super": False}
    finally:
        conn.close()