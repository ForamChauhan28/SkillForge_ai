import json
from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
from services.auth_service import login_required
from services.progress_service import calculate_progress, get_skill_summary
from services.ai_engine import generate_skill_gap_analysis
from models.roadmap import get_latest_roadmap
from models.profile import get_profile


analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/analytics')
@login_required
def analytics_view():
    """Display progress analytics dashboard."""
    user_id = session['user_id']

    # Get profile and roadmap
    profile = get_profile(user_id)
    roadmap = get_latest_roadmap(user_id)

    if not roadmap:
        flash('Generate a roadmap first to see your analytics.', 'warning')
        return redirect(url_for('dashboard.dashboard'))

    # Calculate progress
    progress = calculate_progress(user_id)
    skill_summary = get_skill_summary(user_id)

    # Parse dream job from profile
    dream_job = profile.get('dream_job', 'Not set') if profile else 'Not set'

    # Count skills
    skills_text = profile.get('extracted_skills', '') if profile else ''
    skills_count = len([s for s in skills_text.split(',') if s.strip()]) if skills_text else 0

    # Estimated weeks from roadmap
    raw_json = roadmap.get('raw_json', '{}')
    if isinstance(raw_json, str):
        try:
            raw_json = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            raw_json = {}
    est_weeks = raw_json.get('roadmap', {}).get('estimated_weeks', 'N/A') if raw_json else 'N/A'

    # Count completed phases
    phase_progress = progress.get('phase_progress', [])
    completed_phases = sum(1 for p in phase_progress if p.get('percentage', 0) == 100)

    return render_template('analytics.html',
                           profile=profile,
                           roadmap=roadmap,
                           progress=progress,
                           skill_summary=skill_summary,
                           dream_job=dream_job,
                           skills_count=skills_count,
                           est_weeks=est_weeks,
                           completed_phases=completed_phases,
                           total_phases=len(phase_progress))


@analytics_bp.route('/api/skill-gap')
@login_required
def skill_gap_data():
    """Generate skill gap analysis for radar chart."""
    user_id = session['user_id']
    profile = get_profile(user_id)

    if not profile or not profile.get('extracted_skills') or not profile.get('dream_job'):
        return jsonify({'error': 'Need skills and dream job to generate gap analysis'}), 400

    result = generate_skill_gap_analysis(profile['extracted_skills'], profile['dream_job'])
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to generate skill gap analysis'}), 500
