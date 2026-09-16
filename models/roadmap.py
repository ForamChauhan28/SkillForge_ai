import json
from models.db import get_connection


def _to_bool(val):
    """Safely convert MySQL boolean/bytes/int to Python bool."""
    if isinstance(val, bytes):
        return bool(int.from_bytes(val, 'big'))
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, bool):
        return val
    return False


def create_roadmap(user_id, raw_json, certifications_json, projects_json, interview_json):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()

        # Safely convert to JSON strings
        raw_str = json.dumps(raw_json) if raw_json else None
        cert_str = json.dumps(certifications_json) if certifications_json else None
        proj_str = json.dumps(projects_json) if projects_json else None
        intv_str = json.dumps(interview_json) if interview_json else None

        # Insert roadmap
        cursor.execute(
            """INSERT INTO roadmaps 
               (user_id, raw_json, certifications_json, projects_json, interview_json) 
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, raw_str, cert_str, proj_str, intv_str)
        )
        roadmap_id = cursor.lastrowid

        # Parse nodes and insert
        if raw_json and isinstance(raw_json, dict):
            roadmap_data = raw_json.get("roadmap", {})
            phases = roadmap_data.get("phases", [])

            for phase in phases:
                phase_id = phase.get("phase_id", 0)
                topics = phase.get("topics", [])
                for topic in topics:
                    if isinstance(topic, dict):
                        topic_name = topic.get("name", "")
                    else:
                        topic_name = str(topic)
                    if topic_name:
                        cursor.execute(
                            "INSERT INTO roadmap_nodes (roadmap_id, phase_id, topic_name, is_completed) VALUES (%s, %s, %s, %s)",
                            (roadmap_id, phase_id, topic_name, False)
                        )

        conn.commit()
        return roadmap_id
    except Exception as e:
        print(f"Error creating roadmap: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_latest_roadmap(user_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM roadmaps WHERE user_id = %s ORDER BY generated_at DESC LIMIT 1",
            (user_id,)
        )
        roadmap = cursor.fetchone()
        if roadmap:
            # Safely parse JSON fields — handle both string and already-parsed dict
            for field in ('raw_json', 'certifications_json', 'projects_json', 'interview_json'):
                val = roadmap.get(field)
                if isinstance(val, str):
                    try:
                        roadmap[field] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        roadmap[field] = {}
                elif val is None:
                    roadmap[field] = {}
        return roadmap
    except Exception as e:
        print(f"Error getting latest roadmap: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_roadmap_nodes(roadmap_id):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM roadmap_nodes WHERE roadmap_id = %s ORDER BY phase_id ASC, node_id ASC", (roadmap_id,))
        nodes = cursor.fetchall()
        # Normalize is_completed from MySQL bytes to Python bool
        for node in nodes:
            node['is_completed'] = _to_bool(node.get('is_completed'))
        return nodes
    except Exception as e:
        print(f"Error getting roadmap nodes: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()


def toggle_node_completion(node_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)

        # Get current state
        cursor.execute("SELECT is_completed FROM roadmap_nodes WHERE node_id = %s", (node_id,))
        row = cursor.fetchone()
        if not row:
            return None

        current = _to_bool(row['is_completed'])
        new_state = not current

        # Update state
        if new_state:
            cursor.execute(
                "UPDATE roadmap_nodes SET is_completed = %s, completed_at = CURRENT_TIMESTAMP WHERE node_id = %s",
                (True, node_id)
            )
        else:
            cursor.execute(
                "UPDATE roadmap_nodes SET is_completed = %s, completed_at = NULL WHERE node_id = %s",
                (False, node_id)
            )
        conn.commit()

        # Return updated node
        cursor.execute("SELECT * FROM roadmap_nodes WHERE node_id = %s", (node_id,))
        updated = cursor.fetchone()
        if updated:
            updated['is_completed'] = _to_bool(updated.get('is_completed'))
        return updated
    except Exception as e:
        print(f"Error toggling node: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_progress(roadmap_id):
    conn = get_connection()
    if not conn:
        return {"total_nodes": 0, "completed_nodes": 0, "percentage": 0}
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed FROM roadmap_nodes WHERE roadmap_id = %s",
            (roadmap_id,)
        )
        row = cursor.fetchone()
        total = row['total'] or 0
        completed = int(row['completed'] or 0)
        percentage = int((completed / total * 100)) if total > 0 else 0

        return {
            "total_nodes": total,
            "completed_nodes": completed,
            "percentage": percentage
        }
    except Exception as e:
        print(f"Error getting progress: {e}")
        return {"total_nodes": 0, "completed_nodes": 0, "percentage": 0}
    finally:
        if conn:
            cursor.close()
            conn.close()
