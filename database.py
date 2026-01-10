import sqlite3
import hashlib
from datetime import datetime
import os

DB_NAME = "resume_analyzer.db"

def get_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Analysis history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            match_score INTEGER NOT NULL,
            job_title TEXT,
            analysis_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(username, email, password):
    """Create a new user account."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def verify_user(username, password):
    """Verify user credentials and return user_id if valid."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        cursor.execute('''
            SELECT id FROM users
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
    except Exception as e:
        print(f"Error verifying user: {e}")
        return None

def save_analysis(user_id, filename, match_score, job_title, analysis_data):
    """Save an analysis result to the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analysis_history (user_id, filename, match_score, job_title, analysis_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, filename, match_score, job_title, analysis_data))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving analysis: {e}")
        return False

def get_user_history(user_id, limit=10):
    """Retrieve analysis history for a user."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, created_at, filename, match_score, job_title
            FROM analysis_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    except Exception as e:
        print(f"Error retrieving history: {e}")
        return []

def get_user_stats(user_id):
    """Get statistics for a user's analyses."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_analyses,
                AVG(match_score) as avg_score,
                MAX(match_score) as best_score,
                MIN(match_score) as lowest_score
            FROM analysis_history
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total_analyses': result[0] if result else 0,
            'avg_score': result[1] if result else 0,
            'best_score': result[2] if result else 0,
            'lowest_score': result[3] if result else 0
        }
    except Exception as e:
        print(f"Error retrieving stats: {e}")
        return None

def delete_analysis(user_id, analysis_id):
    """Delete a single analysis entry for a user."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            DELETE FROM analysis_history
            WHERE id = ? AND user_id = ?
            ''',
            (analysis_id, user_id)
        )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting analysis: {e}")
        return False
