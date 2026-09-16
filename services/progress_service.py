import json
from models.roadmap import get_latest_roadmap, get_roadmap_nodes, get_progress, _to_bool
from models.profile import get_profile


def calculate_progress(user_id):
    """Calculate detailed progress for a user's latest roadmap."""
    roadmap = get_latest_roadmap(user_id)
    if not roadmap:
        return {
            'total_nodes': 0,
            'completed_nodes': 0,
            'percentage': 0,
            'phase_progress': [],
            'completed_list': []
        }

    nodes = get_roadmap_nodes(roadmap['roadmap_id'])

    total_nodes = len(nodes)
    completed_nodes = sum(1 for node in nodes if _to_bool(node.get('is_completed')))
    percentage = int((completed_nodes / total_nodes * 100)) if total_nodes > 0 else 0

    # Phase-by-phase progress
    phases = {}
    for node in nodes:
        phase_id = node['phase_id']
        if phase_id not in phases:
            phases[phase_id] = {
                'phase_id': phase_id,
                'title': f"Phase {phase_id}",
                'total': 0,
                'completed': 0
            }

        phases[phase_id]['total'] += 1
        if _to_bool(node.get('is_completed')):
            phases[phase_id]['completed'] += 1

    # Try to get phase titles from roadmap data
    raw_json = roadmap.get('raw_json', {})
    if isinstance(raw_json, str):
        try:
            raw_json = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            raw_json = {}

    roadmap_data = raw_json.get('roadmap', {}) if raw_json else {}
    roadmap_phases = roadmap_data.get('phases', [])

    for rp in roadmap_phases:
        pid = rp.get('phase_id')
        if pid and pid in phases:
            phases[pid]['title'] = rp.get('title', f"Phase {pid}")

    phase_progress = []
    for phase_id, data in sorted(phases.items()):
        data['percentage'] = int((data['completed'] / data['total'] * 100)) if data['total'] > 0 else 0
        phase_progress.append(data)

    # List of completed nodes (for timeline)
    completed_list = [
        {
            'topic_name': n['topic_name'],
            'completed_at': str(n.get('completed_at', '')) if n.get('completed_at') else None
        }
        for n in nodes if _to_bool(n.get('is_completed'))
    ]

    return {
        'total_nodes': total_nodes,
        'completed_nodes': completed_nodes,
        'percentage': percentage,
        'phase_progress': phase_progress,
        'completed_list': completed_list
    }


def get_skill_summary(user_id):
    """Get a structured skill summary for the user."""
    profile = get_profile(user_id)
    if not profile or not profile.get('extracted_skills'):
        return {'skills': []}

    skills_text = profile['extracted_skills']

    # Skills might be stored as JSON or comma-separated
    try:
        skills_data = json.loads(skills_text)
        # If it's a dict with categories, flatten to a list
        if isinstance(skills_data, dict):
            all_skills = []
            for key, val in skills_data.items():
                if isinstance(val, list):
                    all_skills.extend(val)
            return {'skills': all_skills, 'categories': skills_data}
        elif isinstance(skills_data, list):
            return {'skills': skills_data}
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: comma-separated string
    skills = [s.strip() for s in skills_text.split(',') if s.strip()]
    return {'skills': skills}
