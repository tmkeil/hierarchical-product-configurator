"""
Seeding Script für Initial Admin User

Erstellt einen Admin Account beim ersten Deployment.
Admin muss nach erstem Login das Passwort ändern.

Usage:
    python database/seed_admin.py
"""

import sqlite3
import bcrypt
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "variantenbaum.db"

def create_users_table():
    """Erstellt users Tabelle falls nicht existent"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
            is_active BOOLEAN DEFAULT 1,
            must_change_password BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
    
    conn.commit()
    conn.close()
    print("✓ Users table created/verified")

def create_initial_admin():
    """Erstellt Initial-Admin wenn noch kein Admin existiert"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Prüfe ob Admin existiert
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    
    if admin_count > 0:
        print(f"✓ {admin_count} admin(s) already exist - skipping")
        conn.close()
        return
    
    # Initial-Credentials aus Environment Variables
    username = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
    email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@firma.com")
    password = os.getenv("INITIAL_ADMIN_PASSWORD", "ChangeMe123!")
    
    # Passwort hashen mit bcrypt
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, is_active, must_change_password)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, email, password_hash, "admin", 1, 1))
        
        conn.commit()
        print(f"""
✓ Initial admin created successfully!
  
  Username: {username}
  Password: {password}
  Email:    {email}
  
  ⚠️  WICHTIG: Admin muss nach erstem Login das Passwort ändern!
  ⚠️  SICHERHEIT: Lösche diese Credentials aus den Logs!
""")
    except sqlite3.IntegrityError as e:
        print(f"✗ Error creating admin: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== Seeding Initial Admin ===")
    create_users_table()
    create_initial_admin()
    print("=== Done ===")
