from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from models.user import get_user_by_id

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Return JSON for API/AJAX requests instead of redirecting
            if (request.path.startswith('/api/') or
                request.is_json or
                request.headers.get('Accept', '').startswith('application/json') or
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
                return jsonify({'success': False, 'error': 'Please log in first'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return get_user_by_id(session['user_id'])
    return None

