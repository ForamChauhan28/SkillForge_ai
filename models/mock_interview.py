import json
from models.db import get_connection


def create_session(user_id, role_title, target_company, round_type, total_questions):
    """Create a new mock interview session."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO mock_interviews 
               (user_id, role_title, target_company, round_type, total_questions)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, role_title, target_company or 'General', round_type, total_questions)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error creating mock interview session: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_session(session_id, user_id=None):
    """Get a mock interview session, optionally verifying user ownership."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        if user_id:
            cursor.execute(
                "SELECT * FROM mock_interviews WHERE session_id = %s AND user_id = %s",
                (session_id, user_id)
            )
        else:
            cursor.execute(
                "SELECT * FROM mock_interviews WHERE session_id = %s",
                (session_id,)
            )
        session = cursor.fetchone()
        if session and session.get('report_json'):
            val = session['report_json']
            if isinstance(val, str):
                try:
                    session['report_json'] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    session['report_json'] = {}
        return session
    except Exception as e:
        print(f"Error getting mock interview session: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


def save_question(session_id, question_index, question_text, category='general', difficulty='medium'):
    """Save a generated interview question."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO mock_interview_qa 
               (session_id, question_index, question_text, category, difficulty)
               VALUES (%s, %s, %s, %s, %s)""",
            (session_id, question_index, question_text, category, difficulty)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error saving question: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


def save_answer(session_id, question_index, user_answer, feedback_json, score):
    """Save user's answer and AI feedback for a question."""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        feedback_str = json.dumps(feedback_json) if isinstance(feedback_json, dict) else feedback_json
        cursor.execute(
            """UPDATE mock_interview_qa 
               SET user_answer = %s, feedback_json = %s, score = %s, answered_at = CURRENT_TIMESTAMP
               WHERE session_id = %s AND question_index = %s""",
            (user_answer, feedback_str, score, session_id, question_index)
        )
        # Update current question index in session
        cursor.execute(
            """UPDATE mock_interviews 
               SET current_question_index = %s WHERE session_id = %s""",
            (question_index + 1, session_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving answer: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()


def complete_session(session_id, overall_score, report_json):
    """Mark a session as completed and store the report."""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        report_str = json.dumps(report_json) if isinstance(report_json, dict) else report_json
        cursor.execute(
            """UPDATE mock_interviews 
               SET status = 'completed', overall_score = %s, report_json = %s, completed_at = CURRENT_TIMESTAMP
               WHERE session_id = %s""",
            (overall_score, report_str, session_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error completing session: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_session_questions(session_id):
    """Get all Q&A for a session."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM mock_interview_qa WHERE session_id = %s ORDER BY question_index ASC",
            (session_id,)
        )
        questions = cursor.fetchall()
        for q in questions:
            if q.get('feedback_json') and isinstance(q['feedback_json'], str):
                try:
                    q['feedback_json'] = json.loads(q['feedback_json'])
                except (json.JSONDecodeError, TypeError):
                    q['feedback_json'] = {}
        return questions
    except Exception as e:
        print(f"Error getting session questions: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_user_sessions(user_id, limit=10):
    """Get recent mock interview sessions for a user."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT session_id, role_title, target_company, round_type, total_questions,
                      status, overall_score, started_at, completed_at
               FROM mock_interviews 
               WHERE user_id = %s 
               ORDER BY started_at DESC 
               LIMIT %s""",
            (user_id, limit)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting user sessions: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()
