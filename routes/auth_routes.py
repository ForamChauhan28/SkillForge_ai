from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, current_app
from models.user import create_user, get_user_by_email, verify_password, create_or_get_google_user
from services.ai_engine import get_trending_roles, get_demo_roadmaps, get_demo_roadmap_detail

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    """Public landing page with demo roadmaps and trending roles."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    trending_roles = get_trending_roles()
    demo_roadmaps = get_demo_roadmaps()
    return render_template('landing.html', hide_nav=True, trending_roles=trending_roles, demo_roadmaps=demo_roadmaps)

@auth_bp.route('/login/google')
def login_google():
    if not current_app.config.get('GOOGLE_CLIENT_ID'):
        if current_app.config.get('DEBUG'):
            # Mock Google Login for local development UI
            return render_template('mock_google.html')
                
        flash('Google Login is not configured yet. Please configure OAuth Client ID.', 'warning')
        return redirect(url_for('auth.login'))
        
    redirect_uri = url_for('auth.auth_google', _external=True)
    return current_app.oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/login/google/mock')
def login_google_mock():
    if not current_app.config.get('DEBUG'):
        abort(404)

    # Only allow mock login from localhost for security
    if request.host.split(':')[0] not in ('localhost', '127.0.0.1'):
        abort(404)
        
    mock_name = request.args.get('name', 'Demo User')
    mock_email = request.args.get('email', 'demo_user@gmail.com')
    mock_google_id = f"mock_google_id_{mock_email}"
    
    user_id = create_or_get_google_user(mock_name, mock_email, mock_google_id)
    if user_id:
        session['user_id'] = user_id
        session['user_name'] = mock_name
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard.dashboard'))
    else:
        flash('Failed to create mock user account.', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/login/google/callback')
def auth_google():
    try:
        token = current_app.oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if user_info:
            email = user_info['email']
            name = user_info.get('name', email.split('@')[0])
            google_id = user_info['sub']
            
            user_id = create_or_get_google_user(name, email, google_id)
            if user_id:
                session['user_id'] = user_id
                session['user_name'] = name
                flash('Successfully logged in with Google!', 'success')
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('Failed to create user account.', 'danger')
                return redirect(url_for('auth.login'))
    except Exception as e:
        print(f"OAuth error: {e}")
        flash('Google login failed or was cancelled.', 'danger')
        
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('login.html', hide_nav=True)

        user = get_user_by_email(email)

        if user and verify_password(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html', hide_nav=True)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([name, email, password, confirm_password]):
            flash('Please fill out all fields.', 'danger')
            return render_template('register.html', hide_nav=True)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', hide_nav=True)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html', hide_nav=True)

        user_id = create_user(name, email, password)
        if user_id:
            session['user_id'] = user_id
            session['user_name'] = name
            flash('Registration successful! Welcome to SkillForge AI.', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Email already registered or an error occurred.', 'danger')

    return render_template('register.html', hide_nav=True)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.index'))


@auth_bp.route('/demo-roadmap/<slug>')
def demo_roadmap(slug):
    """Public demo roadmap — no login required."""
    roadmap_data = get_demo_roadmap_detail(slug)
    if not roadmap_data:
        abort(404)
    return render_template('demo_roadmap.html', roadmap=roadmap_data, hide_nav=True)
