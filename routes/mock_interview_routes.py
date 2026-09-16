import json
from flask import Blueprint, render_template, session, request, jsonify
from services.auth_service import login_required
from services.ai_engine import generate_mock_questions, evaluate_mock_answer, generate_mock_interview_report
from models.mock_interview import (
    create_session, get_session, save_question, save_answer,
    complete_session, get_session_questions, get_user_sessions
)
from models.profile import get_profile


mock_interview_bp = Blueprint('mock_interview', __name__)


@mock_interview_bp.route('/interview/simulator')
@login_required
def simulator_view():
    """Render the mock interview simulator page."""
    user_id = session['user_id']
    profile = get_profile(user_id)
    past_sessions = get_user_sessions(user_id, limit=5)
    return render_template('mock_interview.html', profile=profile, past_sessions=past_sessions)


@mock_interview_bp.route('/api/mock-interview/start', methods=['POST'])
@login_required
def start_interview():
    """Initialize a new mock interview session and generate questions."""
    user_id = session['user_id']
    data = request.get_json()

    role = data.get('role', '').strip()
    company = data.get('company', 'General').strip()
    round_type = data.get('round_type', 'technical_r1').strip()
    num_questions = min(int(data.get('num_questions', 5)), 10)  # Cap at 10

    if not role:
        return jsonify({'success': False, 'error': 'Role title is required'}), 400

    # Get user skills for context
    profile = get_profile(user_id)
    user_skills = profile.get('extracted_skills', '') if profile else ''

    # Create database session
    session_id = create_session(user_id, role, company, round_type, num_questions)
    if not session_id:
        return jsonify({'success': False, 'error': 'Failed to create interview session'}), 500

    # Generate questions via AI
    questions = generate_mock_questions(role, company, round_type, user_skills, num_questions)

    if not questions:
        return jsonify({'success': False, 'error': 'Failed to generate interview questions. Please try again.'}), 500

    # Save all questions to DB
    for i, q in enumerate(questions):
        save_question(
            session_id,
            question_index=i,
            question_text=q.get('question', f'Question {i+1}'),
            category=q.get('category', 'general'),
            difficulty=q.get('difficulty', 'medium')
        )

    # Return first question
    first_q = questions[0] if questions else {}
    return jsonify({
        'success': True,
        'session_id': session_id,
        'total_questions': len(questions),
        'current_index': 0,
        'question': {
            'text': first_q.get('question', ''),
            'category': first_q.get('category', 'general'),
            'difficulty': first_q.get('difficulty', 'medium'),
            'time_limit': first_q.get('time_limit_seconds', 120),
        }
    })


@mock_interview_bp.route('/api/mock-interview/answer', methods=['POST'])
@login_required
def submit_answer():
    """Submit an answer, get AI feedback, and return the next question."""
    user_id = session['user_id']
    data = request.get_json()

    session_id = data.get('session_id')
    question_index = data.get('question_index', 0)
    user_answer = data.get('answer', '').strip()

    if not session_id:
        return jsonify({'success': False, 'error': 'Session ID is required'}), 400
    if not user_answer:
        return jsonify({'success': False, 'error': 'Please provide an answer'}), 400

    # Verify session belongs to user
    interview_session = get_session(session_id, user_id)
    if not interview_session:
        return jsonify({'success': False, 'error': 'Session not found'}), 404

    # Get all questions for this session
    all_questions = get_session_questions(session_id)
    if question_index >= len(all_questions):
        return jsonify({'success': False, 'error': 'Invalid question index'}), 400

    current_q = all_questions[question_index]

    # Build previous Q&A context for evaluation
    previous_qa = []
    for q in all_questions[:question_index]:
        if q.get('user_answer'):
            previous_qa.append({
                'question': q['question_text'],
                'answer': q['user_answer']
            })

    # Evaluate answer with AI
    feedback = evaluate_mock_answer(
        question=current_q['question_text'],
        user_answer=user_answer,
        category=current_q.get('category', 'general'),
        round_type=interview_session['round_type'],
        role=interview_session['role_title'],
        previous_qa=previous_qa
    )

    score = feedback.get('overall_score', 5.0)

    # Save to DB
    save_answer(session_id, question_index, user_answer, feedback, score)

    # Check if there are more questions
    next_index = question_index + 1
    is_last = next_index >= len(all_questions)

    response_data = {
        'success': True,
        'feedback': feedback,
        'score': score,
        'is_last_question': is_last,
        'current_index': question_index,
    }

    if not is_last:
        next_q = all_questions[next_index]
        response_data['next_question'] = {
            'text': next_q['question_text'],
            'category': next_q.get('category', 'general'),
            'difficulty': next_q.get('difficulty', 'medium'),
            'time_limit': 120,
            'index': next_index,
        }

    return jsonify(response_data)


@mock_interview_bp.route('/api/mock-interview/<int:session_id>/report', methods=['GET'])
@login_required
def get_report(session_id):
    """Generate or retrieve the post-interview report."""
    user_id = session['user_id']

    interview_session = get_session(session_id, user_id)
    if not interview_session:
        return jsonify({'success': False, 'error': 'Session not found'}), 404

    # If report already exists, return it
    if interview_session.get('report_json') and interview_session['status'] == 'completed':
        return jsonify({
            'success': True,
            'report': interview_session['report_json'],
            'overall_score': interview_session.get('overall_score', 0)
        })

    # Generate report
    all_questions = get_session_questions(session_id)

    qna_list = []
    for q in all_questions:
        qna_list.append({
            'question': q['question_text'],
            'category': q.get('category', 'general'),
            'difficulty': q.get('difficulty', 'medium'),
            'user_answer': q.get('user_answer', 'No answer provided'),
            'score': q.get('score', 0),
        })

    report = generate_mock_interview_report(
        role=interview_session['role_title'],
        round_type=interview_session['round_type'],
        company=interview_session.get('target_company', 'General'),
        qna_list=qna_list
    )

    overall_score = report.get('overall_score', 0)
    complete_session(session_id, overall_score, report)

    return jsonify({
        'success': True,
        'report': report,
        'overall_score': overall_score
    })


@mock_interview_bp.route('/api/mock-interview/history', methods=['GET'])
@login_required
def get_history():
    """Get user's mock interview history."""
    user_id = session['user_id']
    sessions = get_user_sessions(user_id, limit=10)
    
    # Convert datetime objects to strings for JSON serialization
    for s in sessions:
        if s.get('started_at'):
            s['started_at'] = s['started_at'].isoformat()
        if s.get('completed_at'):
            s['completed_at'] = s['completed_at'].isoformat()
    
    return jsonify({'success': True, 'sessions': sessions})
