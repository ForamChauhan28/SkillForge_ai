import json
from flask import Blueprint, render_template, session, request, jsonify, redirect, url_for, flash
from services.auth_service import login_required
from services.ai_engine import generate_roadmap, generate_certifications, generate_projects, generate_interview_prep, chat_about_topic
from models.profile import get_profile, update_dream_job
from models.roadmap import create_roadmap, get_latest_roadmap, get_roadmap_nodes, get_progress


roadmap_bp = Blueprint('roadmap', __name__)


@roadmap_bp.route('/api/generate-roadmap', methods=['POST'])
@login_required
def generate_roadmap_route():
    """Trigger the full AI pipeline: roadmap + certifications + projects + interview prep."""
    user_id = session['user_id']

    try:
        data = request.get_json(silent=True) or {}
        dream_job = data.get('dream_job', '').strip()

        # Fallback: if dream_job not in body, read from profile
        if not dream_job:
            profile = get_profile(user_id)
            dream_job = (profile.get('dream_job', '') if profile else '').strip()

        if not dream_job:
            return jsonify({'success': False, 'error': 'Please enter your dream job'}), 400

        # Get user's extracted skills
        profile = get_profile(user_id)
        if not profile or not profile.get('extracted_skills'):
            return jsonify({'success': False, 'error': 'Please upload your resume first'}), 400

        extracted_skills = profile['extracted_skills']

        # Update dream job in profile
        update_dream_job(user_id, dream_job)

        # ── Step 1: Generate Learning Roadmap (chained LLM calls) ──
        print(f"[Roadmap] Step 1: Generating roadmap for '{dream_job}'...")
        roadmap_result = generate_roadmap(extracted_skills, dream_job)
        if not roadmap_result:
            return jsonify({'success': False, 'error': 'AI failed to generate roadmap. Please try again.'}), 500
        print(f"[Roadmap] Step 1 complete. Keys: {list(roadmap_result.keys()) if isinstance(roadmap_result, dict) else 'N/A'}")

        # ── Step 2: Generate Certifications ──
        print("[Roadmap] Step 2: Generating certifications...")
        cert_result = generate_certifications(roadmap_result, dream_job)

        # ── Step 3: Generate Portfolio Projects ──
        print("[Roadmap] Step 3: Generating projects...")
        projects_result = generate_projects(extracted_skills, dream_job)

        # ── Step 4: Generate Interview Prep ──
        print("[Roadmap] Step 4: Generating interview prep...")
        interview_result = generate_interview_prep(dream_job)

        # ── Store everything in database ──
        print("[Roadmap] Saving to database...")
        roadmap_id = create_roadmap(
            user_id=user_id,
            raw_json=roadmap_result,
            certifications_json=cert_result,
            projects_json=projects_result,
            interview_json=interview_result
        )

        if roadmap_id:
            print(f"[Roadmap] SUCCESS! Roadmap ID: {roadmap_id}")
            return jsonify({'success': True, 'roadmap_id': roadmap_id})
        else:
            return jsonify({'success': False, 'error': 'Failed to save roadmap to database'}), 500

    except Exception as e:
        import traceback
        print(f"[Roadmap] EXCEPTION: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@roadmap_bp.route('/roadmap')
@login_required
def roadmap_view():
    """Display the interactive roadmap visualization."""
    user_id = session['user_id']
    roadmap = get_latest_roadmap(user_id)

    if not roadmap:
        flash('Generate a roadmap first from your dashboard.', 'warning')
        return redirect(url_for('dashboard.dashboard'))

    # Get nodes and progress
    nodes = get_roadmap_nodes(roadmap['roadmap_id'])
    progress = get_progress(roadmap['roadmap_id'])

    # Parse raw_json if it's a string
    raw_json = roadmap.get('raw_json', {})
    if isinstance(raw_json, str):
        try:
            raw_json = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            raw_json = {}

    # Serialize nodes for safe JSON embedding in template
    serialized_nodes = []
    for node in nodes:
        sn = {}
        for key, val in node.items():
            if hasattr(val, 'isoformat'):
                sn[key] = val.isoformat() if val else None
            elif isinstance(val, bytes):
                sn[key] = bool(int.from_bytes(val, 'big')) if val else False
            elif isinstance(val, bool):
                sn[key] = val
            else:
                sn[key] = val
        serialized_nodes.append(sn)

    return render_template('roadmap.html',
                           roadmap=roadmap,
                           raw_json=raw_json,
                           nodes=serialized_nodes,
                           progress=progress)


@roadmap_bp.route('/projects')
@login_required
def projects_view():
    """Display tiered portfolio project suggestions."""
    user_id = session['user_id']
    roadmap = get_latest_roadmap(user_id)

    if not roadmap:
        flash('Generate a roadmap first from your dashboard.', 'warning')
        return redirect(url_for('dashboard.dashboard'))

    # Parse projects JSON
    projects_data = roadmap.get('projects_json', '{}')
    if isinstance(projects_data, str):
        try:
            projects_data = json.loads(projects_data)
        except (json.JSONDecodeError, TypeError):
            projects_data = {}

    projects = projects_data.get('projects', [])

    # Categorize by tier
    beginner = [p for p in projects if p.get('tier', '').lower() == 'beginner']
    intermediate = [p for p in projects if p.get('tier', '').lower() == 'intermediate']
    advanced = [p for p in projects if p.get('tier', '').lower() == 'advanced']

    return render_template('projects.html',
                           projects=projects,
                           beginner=beginner,
                           intermediate=intermediate,
                           advanced=advanced)


@roadmap_bp.route('/interview')
@login_required
def interview_view():
    """Display interview preparation questions and answers."""
    user_id = session['user_id']
    roadmap = get_latest_roadmap(user_id)

    if not roadmap:
        flash('Generate a roadmap first from your dashboard.', 'warning')
        return redirect(url_for('dashboard.dashboard'))

    # Parse interview JSON
    interview_data = roadmap.get('interview_json', '{}')
    if isinstance(interview_data, str):
        try:
            interview_data = json.loads(interview_data)
        except (json.JSONDecodeError, TypeError):
            interview_data = {}

    questions = interview_data.get('questions', [])

    # Separate by type
    technical = [q for q in questions if q.get('type', '').lower() == 'technical']
    behavioral = [q for q in questions if q.get('type', '').lower() == 'behavioral']

    return render_template('interview.html',
                           questions=questions,
                           technical=technical,
                           behavioral=behavioral)


@roadmap_bp.route('/certifications')
@login_required
def certifications_view():
    """Display recommended certifications."""
    user_id = session['user_id']
    roadmap = get_latest_roadmap(user_id)

    if not roadmap:
        flash('Generate a roadmap first from your dashboard.', 'warning')
        return redirect(url_for('dashboard.dashboard'))

    # Parse certifications JSON
    cert_data = roadmap.get('certifications_json', '{}')
    if isinstance(cert_data, str):
        try:
            cert_data = json.loads(cert_data)
        except (json.JSONDecodeError, TypeError):
            cert_data = {}

    certifications = cert_data.get('certifications', [])
    
    beginner = [c for c in certifications if c.get('difficulty', '').lower() == 'beginner']
    intermediate = [c for c in certifications if c.get('difficulty', '').lower() == 'intermediate']
    advanced = [c for c in certifications if c.get('difficulty', '').lower() == 'advanced']

    return render_template('certifications.html',
                           certifications=certifications,
                           beginner=beginner,
                           intermediate=intermediate,
                           advanced=advanced)


@roadmap_bp.route('/api/chat-topic', methods=['POST'])
@login_required
def api_chat_topic():
    """Handle chat specific to a roadmap topic."""
    user_id = session['user_id']
    data = request.get_json()
    topic = data.get('topic', '').strip()
    message = data.get('message', '').strip()

    if not message or not topic:
        return jsonify({'success': False, 'error': 'Topic and message are required'}), 400

    # Build context from user profile
    profile = get_profile(user_id)
    
    context = {
        'skills': profile.get('extracted_skills', 'Not uploaded yet') if profile else 'Not uploaded yet',
        'dream_job': profile.get('dream_job', 'Not set') if profile else 'Not set'
    }

    ai_response = chat_about_topic(topic, message, context)

    return jsonify({
        'success': True,
        'response': ai_response
    })

