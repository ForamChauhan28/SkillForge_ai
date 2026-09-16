from models.db import get_connection


def get_profile(user_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        if conn:
            cursor.close()
            conn.close()


def update_skills(user_id, skills_text, resume_filename=None, resume_text=None):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_profiles SET extracted_skills = %s, resume_filename = %s, resume_text = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
            (skills_text, resume_filename, resume_text, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating skills: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()


def update_dream_job(user_id, dream_job):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_profiles SET dream_job = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
            (dream_job, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating dream job: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()


def update_ats_score(user_id, ats_score_json):
    """Store the ATS score JSON in the user profile."""
    import json
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        score_str = json.dumps(ats_score_json) if isinstance(ats_score_json, dict) else ats_score_json
        cursor.execute(
            "UPDATE user_profiles SET ats_score_json = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
            (score_str, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating ATS score: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()
