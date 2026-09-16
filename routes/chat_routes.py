import json
from flask import Blueprint, render_template, session, request, jsonify
from services.auth_service import login_required
from services.ai_engine import chat_with_mentor
from models.profile import get_profile
from services.progress_service import calculate_progress


chat_bp = Blueprint('chat', __name__)

# In-memory chat history per session (resets on server restart)
chat_histories = {}


@chat_bp.route('/chat')
@login_required
def chat_view():
    """Render the AI Mentor chat page."""
    user_id = session['user_id']
    profile = get_profile(user_id)
    return render_template('chat.html', profile=profile)


@chat_bp.route('/api/chat', methods=['POST'])
@login_required
def send_message():
    """Handle a chat message and return AI mentor response."""
    user_id = session['user_id']
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'success': False, 'error': 'Message is required'}), 400

    # Build context from user profile
    profile = get_profile(user_id)
    progress = calculate_progress(user_id)

    context = {
        'skills': profile.get('extracted_skills', 'Not uploaded yet') if profile else 'Not uploaded yet',
        'dream_job': profile.get('dream_job', 'Not set') if profile else 'Not set',
        'progress': f"{progress.get('percentage', 0)}% complete ({progress.get('completed_nodes', 0)}/{progress.get('total_nodes', 0)} topics)",
        'history': chat_histories.get(user_id, []),
    }

    # Get AI response
    ai_response = chat_with_mentor(user_message, context)

    # Store in history
    if user_id not in chat_histories:
        chat_histories[user_id] = []
    chat_histories[user_id].append({'role': 'user', 'content': user_message})
    chat_histories[user_id].append({'role': 'assistant', 'content': ai_response})

    # Keep only last 20 messages
    if len(chat_histories[user_id]) > 20:
        chat_histories[user_id] = chat_histories[user_id][-20:]

    return jsonify({
        'success': True,
        'response': ai_response
    })


@chat_bp.route('/api/chat/clear', methods=['POST'])
@login_required
def clear_chat():
    """Clear chat history for current user."""
    user_id = session['user_id']
    chat_histories[user_id] = []
    return jsonify({'success': True})
