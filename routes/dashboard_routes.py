import os
import json
from flask import Blueprint, render_template, request, session, jsonify, current_app, make_response
from werkzeug.utils import secure_filename
from services.auth_service import login_required
from models.profile import get_profile, update_skills, update_dream_job, update_ats_score
from models.roadmap import get_latest_roadmap, get_progress
from models.user import get_user_by_id
from services import resume_parser
from services import ai_engine


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page."""
    user_id = session.get('user_id')
    user_name = session.get('user_name', 'User')

    profile = get_profile(user_id)
    roadmap = get_latest_roadmap(user_id)

    progress = None
    if roadmap:
        progress = get_progress(roadmap['roadmap_id'])

    # Parse ATS score if available
    ats_score = None
    if profile and profile.get('ats_score_json'):
        try:
            ats_score = json.loads(profile['ats_score_json']) if isinstance(profile['ats_score_json'], str) else profile['ats_score_json']
        except (json.JSONDecodeError, TypeError):
            pass

    return render_template('dashboard.html',
                           user_name=user_name,
                           profile=profile,
                           roadmap=roadmap,
                           progress=progress,
                           ats_score=ats_score)


@dashboard_bp.route('/api/upload-resume', methods=['POST'])
@login_required
def upload_resume():
    """Handle resume PDF upload, extract text and skills via AI."""
    user_id = session.get('user_id')

    if 'resume' not in request.files:
        return jsonify({'success': False, 'error': 'No resume file provided'}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'Only PDF files are supported'}), 400

    try:
        filename = f"{user_id}_{secure_filename(file.filename)}"
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)

        file.save(filepath)

        # Extract text from PDF
        text = resume_parser.extract_text_from_pdf(filepath)
        if not text or len(text.strip()) < 20:
            return jsonify({'success': False, 'error': 'Could not extract text from PDF. Please try a different file.'}), 400

        # Extract skills using AI
        skills = ai_engine.extract_skills(text)

        if not skills:
            return jsonify({'success': False, 'error': 'AI could not extract skills. The AI service may be temporarily unavailable — please try again in a moment.'}), 500

        # Format skills as comma-separated string from all categories
        all_skills = []
        if isinstance(skills, dict):
            for category, category_skills in skills.items():
                if isinstance(category_skills, list):
                    all_skills.extend(category_skills)
        elif isinstance(skills, list):
            all_skills = skills
        else:
            all_skills = str(skills).split(',')

        skills_str = ', '.join([s.strip() for s in all_skills if s.strip()])

        # Save skills AND resume text
        update_skills(user_id, skills_str, filename, resume_text=text)

        # Auto-generate ATS score
        profile = get_profile(user_id)
        dream_job = profile.get('dream_job', '') if profile else ''
        ats_result = ai_engine.score_resume_ats(text, dream_job)
        if ats_result:
            update_ats_score(user_id, ats_result)

        return jsonify({
            'success': True,
            'skills': skills,
            'skills_str': skills_str,
            'ats_score': ats_result,
            'message': 'Skills extracted successfully!'
        })
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/ats-score', methods=['POST'])
@login_required
def get_ats_score():
    """Re-generate ATS score for existing resume."""
    user_id = session.get('user_id')
    profile = get_profile(user_id)

    if not profile or not profile.get('resume_text'):
        return jsonify({'success': False, 'error': 'No resume uploaded yet'}), 400

    dream_job = profile.get('dream_job', '')
    ats_result = ai_engine.score_resume_ats(profile['resume_text'], dream_job)

    if ats_result:
        update_ats_score(user_id, ats_result)
        return jsonify({'success': True, 'ats_score': ats_result})
    else:
        return jsonify({'success': False, 'error': 'Failed to score resume'}), 500


@dashboard_bp.route('/api/set-dream-job', methods=['POST'])
@login_required
def set_dream_job():
    """Update the user's dream job."""
    user_id = session.get('user_id')
    data = request.json

    dream_job = data.get('dream_job', '').strip()
    if not dream_job:
        return jsonify({'success': False, 'error': 'Dream job is required'}), 400

    try:
        update_dream_job(user_id, dream_job)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/api/download-report')
@login_required
def download_report():
    """Generate and download a career readiness report."""
    from services.report_generator import generate_report_html
    from services.progress_service import calculate_progress

    user_id = session.get('user_id')
    user = get_user_by_id(user_id)
    profile = get_profile(user_id)
    roadmap = get_latest_roadmap(user_id)
    progress = calculate_progress(user_id)

    html = generate_report_html(user, profile, roadmap, progress, None, None)

    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=SkillForge_Career_Report.html'
    return response
