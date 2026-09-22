import bcrypt
from models.db import get_connection

def create_user(name, email, password):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return None # Email already exists
            
        # Hash password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        # Insert user
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        user_id = cursor.lastrowid
        
        # Create empty profile
        cursor.execute("INSERT INTO user_profiles (user_id) VALUES (%s)", (user_id,))
        
        conn.commit()
        return user_id
    except Exception as e:
        print(f"Error creating user: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()

def get_user_by_email(email):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    finally:
        if conn:
            cursor.close()
            conn.close()

def get_user_by_id(user_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        if conn:
            cursor.close()
            conn.close()

def verify_password(stored_hash, password):
    if not stored_hash: # OAuth user
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except Exception:
        return False

def create_or_get_google_user(name, email, google_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        # Check if user already exists by email
        cursor.execute("SELECT user_id, oauth_provider, oauth_id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # If exists but no oauth_id, update it to link google
            if not existing_user['oauth_id']:
                update_cursor = conn.cursor()
                update_cursor.execute("UPDATE users SET oauth_provider = 'google', oauth_id = %s WHERE email = %s", (google_id, email))
                conn.commit()
            return existing_user['user_id']
            
        # Create new user
        insert_cursor = conn.cursor()
        insert_cursor.execute(
            "INSERT INTO users (name, email, oauth_provider, oauth_id) VALUES (%s, %s, 'google', %s)",
            (name, email, google_id)
        )
        user_id = insert_cursor.lastrowid
        
        # Create empty profile
        insert_cursor.execute("INSERT INTO user_profiles (user_id) VALUES (%s)", (user_id,))
        conn.commit()
        
        return user_id
    except Exception as e:
        print(f"Error creating Google user: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()
