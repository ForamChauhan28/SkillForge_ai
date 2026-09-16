from flask import Blueprint, jsonify, session, request
from services.auth_service import login_required
from models.roadmap import toggle_node_completion, get_latest_roadmap, get_progress, get_roadmap_nodes
from services.progress_service import calculate_progress, get_skill_summary
import json


api_bp = Blueprint('api', __name__)


def serialize_node(node):
    """Convert a node dict to JSON-serializable format."""
    if not node:
        return None
    result = {}
    for key, val in node.items():
        if hasattr(val, 'isoformat'):
            result[key] = val.isoformat() if val else None
        elif isinstance(val, bytes):
            result[key] = bool(int.from_bytes(val, 'big')) if val else False
        elif isinstance(val, bool):
            result[key] = val
        else:
            result[key] = val
    return result


@api_bp.route('/toggle-node/<int:node_id>', methods=['POST'])
@login_required
def toggle_node(node_id):
    """Toggle completion status of a roadmap node."""
    try:
        updated_node = toggle_node_completion(node_id)
        if updated_node:
            return jsonify({
                'success': True,
                'node': serialize_node(updated_node)
            })
        else:
            return jsonify({'success': False, 'error': 'Node not found'}), 404
    except Exception as e:
        print(f"Toggle node error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/progress', methods=['GET'])
@login_required
def get_progress_data():
    """Get progress data for the current user."""
    try:
        user_id = session['user_id']
        progress = calculate_progress(user_id)
        return jsonify(progress)
    except Exception as e:
        print(f"Progress error: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/skills-summary', methods=['GET'])
@login_required
def get_skills_data():
    """Get skill summary for the current user."""
    try:
        user_id = session['user_id']
        skills = get_skill_summary(user_id)
        return jsonify(skills)
    except Exception as e:
        print(f"Skills summary error: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/roadmap-data', methods=['GET'])
@login_required
def get_roadmap_data():
    """Get full roadmap data with nodes and progress."""
    try:
        user_id = session['user_id']
        roadmap = get_latest_roadmap(user_id)

        if not roadmap:
            return jsonify({'error': 'No roadmap found'}), 404

        nodes = get_roadmap_nodes(roadmap['roadmap_id'])
        progress = get_progress(roadmap['roadmap_id'])

        # Parse JSON fields if they're strings
        raw_json = roadmap.get('raw_json', {})
        if isinstance(raw_json, str):
            try:
                raw_json = json.loads(raw_json)
            except (json.JSONDecodeError, TypeError):
                raw_json = {}

        # Serialize nodes (datetime/bytes safety)
        serialized_nodes = [serialize_node(n) for n in nodes]

        return jsonify({
            'roadmap': raw_json,
            'nodes': serialized_nodes,
            'progress': progress,
            'roadmap_id': roadmap['roadmap_id']
        })

    except Exception as e:
        print(f"Roadmap data error: {e}")
        return jsonify({'error': str(e)}), 500
