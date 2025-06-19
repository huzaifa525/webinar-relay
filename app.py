"""
Ratlam Relay Centre - Webinar Access Portal

A Flask web application that provides authorized access to webinar streams
for registered ITS members. Features include user authentication via ITS ID,
session management, and an admin panel for managing authorized users.

Author: Huzaifa
Date: June 18, 2025
Version: 1.0.0
"""

from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify, send_file
import json
import os
from datetime import datetime, timedelta
import hashlib
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = 'Huzaifa53'

# File paths for data storage
ITS_FILE = 'its_ids.json'
SESSIONS_FILE = 'active_sessions.json'
ADMIN_FILE = 'admin_credentials.json'
WEBINAR_SETTINGS_FILE = 'webinar_settings.json'

# Admin credentials (you can modify these)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'Huzaifa5253@'  # Change this in production

def init_files():
    """Initialize data files if they don't exist"""
    if not os.path.exists(ITS_FILE):
        with open(ITS_FILE, 'w') as f:
            json.dump([], f)
    
    if not os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'w') as f:
            json.dump({}, f)
    
    if not os.path.exists(ADMIN_FILE):
        admin_hash = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
        with open(ADMIN_FILE, 'w') as f:
            json.dump({'username': ADMIN_USERNAME, 'password_hash': admin_hash}, f)
            
    if not os.path.exists(WEBINAR_SETTINGS_FILE):
        default_settings = {
            "embed_url": "https://www.youtube.com/embed/GXRL7PcPbOA?autoplay=1&mute=1&controls=0&modestbranding=1&rel=0&showinfo=0&iv_load_policy=3&fs=0&disablekb=1&cc_load_policy=0&playsinline=1&loop=1&enablejsapi=1",
            "webinar_title": "Ashara Mubaraka 1447 - Ratlam Relay",
            "webinar_description": "Welcome to the live relay of Ashara Mubaraka 1447. This stream is authorized for ITS members only. Please do not share this link with others.",
            "webinar_date": "June 18-27, 2025",
            "webinar_time": "7:30 AM - 12:30 PM IST",
            "webinar_speaker": "His Holiness Dr. Syedna Mufaddal Saifuddin (TUS)",
            "no_webinar": False
        }
        with open(WEBINAR_SETTINGS_FILE, 'w') as f:
            json.dump(default_settings, f, indent=2)

def load_its_ids():
    """Load ITS IDs from file"""
    try:
        with open(ITS_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_its_ids(its_ids):
    """Save ITS IDs to file"""
    with open(ITS_FILE, 'w') as f:
        json.dump(list(its_ids), f, indent=2)

def load_sessions():
    """Load active sessions from file"""
    try:
        with open(SESSIONS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_sessions(sessions):
    """Save active sessions to file"""
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f, indent=2)

def cleanup_expired_sessions():
    """Remove expired sessions"""
    sessions = load_sessions()
    current_time = datetime.now()
    
    expired_sessions = []
    for session_id, session_data in sessions.items():
        session_time = datetime.fromisoformat(session_data['login_time'])
        if current_time - session_time > timedelta(hours=24):  # 24 hour session timeout
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del sessions[session_id]
    
    save_sessions(sessions)

def is_its_logged_in(its_id):
    """Check if ITS ID already has an active session"""
    cleanup_expired_sessions()
    sessions = load_sessions()
    
    for session_data in sessions.values():
        if session_data['its_id'] == str(its_id):
            return True
    return False

def create_session(its_id):
    """Create a new session for ITS ID"""
    sessions = load_sessions()
    session_token = secrets.token_urlsafe(32)
    
    sessions[session_token] = {
        'its_id': str(its_id),
        'login_time': datetime.now().isoformat()
    }
    
    save_sessions(sessions)
    return session_token

def verify_session(session_token):
    """Verify if session token is valid"""
    cleanup_expired_sessions()
    sessions = load_sessions()
    return session_token in sessions

def logout_session(session_token):
    """Remove session"""
    sessions = load_sessions()
    if session_token in sessions:
        del sessions[session_token]
        save_sessions(sessions)

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Login page template
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ratlam Relay Centre - Login</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --brand-primary: #0a3da0;
            --brand-primary-light: #1c54c5;
            --brand-primary-dark: #082c71;
            --brand-secondary: #a08c3a;
            --accent-gold: #d4af37;
            --accent-gold-light: #f0cc50;
            --accent-gold-dark: #b39128;
            --bg-dark: #090d1b;
            --bg-surface: #0f1428;
            --bg-surface-light: #1a233f;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --text-tertiary: rgba(255, 255, 255, 0.65);
            --surface-1: rgba(255, 255, 255, 0.04);
            --surface-2: rgba(255, 255, 255, 0.07);
            --surface-3: rgba(255, 255, 255, 0.12);
            --gold-overlay: rgba(212, 175, 55, 0.08);
            --gradient-brand: linear-gradient(135deg, var(--brand-primary), var(--brand-primary-light));
            --gradient-gold: linear-gradient(135deg, var(--accent-gold), var(--brand-secondary));
            --gradient-surface: linear-gradient(120deg, var(--bg-surface), rgba(23, 32, 62, 0.85));
            --gradient-glass: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.15);
            --shadow-md: 0 8px 28px rgba(0, 0, 0, 0.2);
            --shadow-lg: 0 16px 50px rgba(0, 0, 0, 0.3);
            --shadow-brand: 0 8px 30px rgba(10, 61, 160, 0.3);
            --shadow-gold: 0 6px 25px rgba(212, 175, 55, 0.15);
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
            --radius-xl: 24px;
            --radius-full: 999px;
            --transition-fast: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-normal: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-slow: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: url('/background.svg') center/cover no-repeat fixed;
            min-height: 100vh;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow-x: hidden;
        }

        .noise-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            opacity: 0.15;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 600 600' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
            pointer-events: none;
        }

        .gradient-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -3;
            background: radial-gradient(circle at 15% 15%, rgba(10, 61, 160, 0.3), transparent 40%),
                        radial-gradient(circle at 85% 85%, rgba(212, 175, 55, 0.2), transparent 40%),
                        radial-gradient(circle at 50% 50%, rgba(9, 13, 27, 0.8), rgba(9, 13, 27, 0.9) 80%);
            pointer-events: none;
        }

        .login-container {
            background: var(--gradient-glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: var(--radius-xl);
            padding: 3rem 2.5rem;
            width: 100%;
            max-width: 420px;
            box-shadow: var(--shadow-lg);
            border: 1px solid rgba(212, 175, 55, 0.2);
            position: relative;
            overflow: hidden;
            animation: slideUp 0.6s ease forwards;
        }

        .login-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, var(--gold-overlay), transparent);
            opacity: 0.3;
            z-index: -1;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .login-header {
            text-align: center;
            margin-bottom: 2.5rem;
        }

        .logo-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .logo-icon {
            width: 60px;
            height: 60px;
            border-radius: var(--radius-md);
            background: var(--gradient-brand);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: white;
            font-family: 'Montserrat', sans-serif;
            font-size: 2rem;
            box-shadow: var(--shadow-brand);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .logo-text {
            text-align: left;
        }

        .logo-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Montserrat', sans-serif;
            letter-spacing: -0.02em;
            text-transform: uppercase;
        }

        .logo-subtitle {
            font-size: 0.9rem;
            color: var(--accent-gold);
            font-weight: 500;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .login-title {
            font-size: 2rem;
            font-weight: 700;
            background: var(--gradient-gold);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: 'Montserrat', sans-serif;
            margin-bottom: 0.5rem;
        }

        .login-subtitle {
            color: var(--text-secondary);
            font-size: 1rem;
            font-weight: 400;
        }

        .login-form {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .input-group {
            position: relative;
        }

        .input-label {
            display: block;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .input-field {
            width: 100%;
            padding: 1rem 1.25rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: var(--radius-md);
            color: var(--text-primary);
            font-size: 1.1rem;
            font-weight: 500;
            transition: var(--transition-normal);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .input-field:focus {
            outline: none;
            border-color: var(--accent-gold);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
        }

        .input-field::placeholder {
            color: var(--text-tertiary);
            font-weight: 400;
        }

        .login-button {
            background: var(--gradient-brand);
            color: white;
            border: none;
            padding: 1.25rem 2rem;
            border-radius: var(--radius-md);
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition-normal);
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: var(--shadow-brand);
            border: 1px solid rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
        }

        .login-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), transparent);
            opacity: 0;
            transition: var(--transition-normal);
        }

        .login-button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg), 0 12px 40px rgba(10, 61, 160, 0.4);
        }

        .login-button:hover::before {
            opacity: 1;
        }

        .login-button:active {
            transform: translateY(0);
        }

        .error-message {
            background: rgba(220, 53, 69, 0.1);
            color: #ff6b7a;
            padding: 1rem;
            border-radius: var(--radius-md);
            font-size: 0.9rem;
            font-weight: 500;
            border: 1px solid rgba(220, 53, 69, 0.2);
            text-align: center;
            margin-bottom: 1rem;
            animation: shake 0.5s ease-in-out;
        }

        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }

        .admin-link {
            text-align: center;
            margin-top: 2rem;
        }

        .admin-link a {
            color: var(--accent-gold);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: var(--transition-normal);
        }

        .admin-link a:hover {
            color: var(--accent-gold-light);
            text-decoration: underline;
        }

        @media (max-width: 480px) {
            .login-container {
                margin: 1rem;
                padding: 2rem 1.5rem;
            }

            .logo-container {
                flex-direction: column;
                gap: 1rem;
            }

            .logo-text {
                text-align: center;
            }

            .logo-title {
                font-size: 1.3rem;
            }

            .login-title {
                font-size: 1.8rem;
            }
        }
    </style>
</head>
<body>
    <div class="noise-bg"></div>
    <div class="gradient-bg"></div>

    <div class="login-container">
        <div class="login-header">
            <div class="logo-container">
                <div class="logo-icon">R</div>
                <div class="logo-text">
                    <div class="logo-title">Ratlam Relay Centre</div>
                    <div class="logo-subtitle">Ashara 1447</div>
                </div>
            </div>
            <h1 class="login-title">Access Portal</h1>
            <p class="login-subtitle">Enter your ITS ID to join the webinar</p>
        </div>

        {% if error %}
        <div class="error-message">
            {{ error }}
        </div>
        {% endif %}

        <form class="login-form" method="POST">
            <div class="input-group">
                <label class="input-label" for="its_id">ITS ID</label>
                <input 
                    type="text" 
                    id="its_id" 
                    name="its_id" 
                    class="input-field" 
                    placeholder="Enter your 8-digit ITS ID"
                    maxlength="8"
                    pattern="[0-9]{8}"
                    required
                >
            </div>
            <button type="submit" class="login-button">Access Webinar</button>
        </form>

        <div class="admin-link">
            <a href="{{ url_for('admin_login') }}">Admin Panel</a>
        </div>
    </div>

    <script>
        // Auto-format ITS ID input
        document.getElementById('its_id').addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 8) {
                this.value = this.value.slice(0, 8);
            }
        });

        // Disable right-click and dev tools
        document.addEventListener('contextmenu', e => e.preventDefault());
        document.addEventListener('keydown', function(e) {
            if (e.key === 'F12' || 
                (e.ctrlKey && e.shiftKey && e.key === 'I') ||
                (e.ctrlKey && e.shiftKey && e.key === 'J') ||
                (e.ctrlKey && e.key === 'U')) {
                e.preventDefault();
                return false;
            }
        });
    </script>
</body>
</html>
'''

# Admin login template
ADMIN_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Ratlam Relay Centre</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --brand-primary: #0a3da0;
            --brand-primary-light: #1c54c5;
            --brand-primary-dark: #082c71;
            --brand-secondary: #a08c3a;
            --accent-gold: #d4af37;
            --accent-gold-light: #f0cc50;
            --accent-gold-dark: #b39128;
            --bg-dark: #090d1b;
            --bg-surface: #0f1428;
            --bg-surface-light: #1a233f;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --text-tertiary: rgba(255, 255, 255, 0.65);
            --surface-1: rgba(255, 255, 255, 0.04);
            --surface-2: rgba(255, 255, 255, 0.07);
            --surface-3: rgba(255, 255, 255, 0.12);
            --gold-overlay: rgba(212, 175, 55, 0.08);
            --gradient-brand: linear-gradient(135deg, var(--brand-primary), var(--brand-primary-light));
            --gradient-gold: linear-gradient(135deg, var(--accent-gold), var(--brand-secondary));
            --gradient-surface: linear-gradient(120deg, var(--bg-surface), rgba(23, 32, 62, 0.85));
            --gradient-glass: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.15);
            --shadow-md: 0 8px 28px rgba(0, 0, 0, 0.2);
            --shadow-lg: 0 16px 50px rgba(0, 0, 0, 0.3);
            --shadow-brand: 0 8px 30px rgba(10, 61, 160, 0.3);
            --shadow-gold: 0 6px 25px rgba(212, 175, 55, 0.15);
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
            --radius-xl: 24px;
            --radius-full: 999px;
            --transition-fast: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-normal: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-slow: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: var(--bg-dark);
            min-height: 100vh;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .admin-container {
            background: var(--gradient-glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: var(--radius-xl);
            padding: 3rem 2.5rem;
            width: 100%;
            max-width: 420px;
            box-shadow: var(--shadow-lg);
            border: 1px solid rgba(212, 175, 55, 0.2);
            position: relative;
            overflow: hidden;
        }

        .admin-header {
            text-align: center;
            margin-bottom: 2.5rem;
        }

        .admin-title {
            font-size: 2rem;
            font-weight: 700;
            background: var(--gradient-gold);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: 'Montserrat', sans-serif;
            margin-bottom: 0.5rem;
        }

        .admin-subtitle {
            color: var(--text-secondary);
            font-size: 1rem;
            font-weight: 400;
        }

        .login-form {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .input-group {
            position: relative;
        }

        .input-label {
            display: block;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .input-field {
            width: 100%;
            padding: 1rem 1.25rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: var(--radius-md);
            color: var(--text-primary);
            font-size: 1.1rem;
            font-weight: 500;
            transition: var(--transition-normal);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .input-field:focus {
            outline: none;
            border-color: var(--accent-gold);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
        }

        .login-button {
            background: var(--gradient-brand);
            color: white;
            border: none;
            padding: 1.25rem 2rem;
            border-radius: var(--radius-md);
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition-normal);
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: var(--shadow-brand);
        }

        .login-button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg), 0 12px 40px rgba(10, 61, 160, 0.4);
        }

        .error-message {
            background: rgba(220, 53, 69, 0.1);
            color: #ff6b7a;
            padding: 1rem;
            border-radius: var(--radius-md);
            font-size: 0.9rem;
            font-weight: 500;
            border: 1px solid rgba(220, 53, 69, 0.2);
            text-align: center;
            margin-bottom: 1rem;
        }

        .back-link {
            text-align: center;
            margin-top: 2rem;
        }

        .back-link a {
            color: var(--accent-gold);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: var(--transition-normal);
        }

        .back-link a:hover {
            color: var(--accent-gold-light);
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="admin-container">
        <div class="admin-header">
            <h1 class="admin-title">Admin Panel</h1>
            <p class="admin-subtitle">Administrative Access Required</p>
        </div>

        {% if error %}
        <div class="error-message">
            {{ error }}
        </div>
        {% endif %}

        <form class="login-form" method="POST">
            <div class="input-group">
                <label class="input-label" for="username">Username</label>
                <input type="text" id="username" name="username" class="input-field" required>
            </div>
            <div class="input-group">
                <label class="input-label" for="password">Password</label>
                <input type="password" id="password" name="password" class="input-field" required>
            </div>
            <button type="submit" class="login-button">Login</button>
        </form>        <div class="back-link">
            <a href="{{ url_for('index') }}">← Back to User Login</a>
        </div>
    </div>
</body>
</html>
'''

# Admin dashboard template
ADMIN_DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - Ratlam Relay Centre</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --brand-primary: #0a3da0;
            --brand-primary-light: #1c54c5;
            --brand-primary-dark: #082c71;
            --brand-secondary: #a08c3a;
            --accent-gold: #d4af37;
            --accent-gold-light: #f0cc50;
            --accent-gold-dark: #b39128;
            --bg-dark: #090d1b;
            --bg-surface: #0f1428;
            --bg-surface-light: #1a233f;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --text-tertiary: rgba(255, 255, 255, 0.65);
            --surface-1: rgba(255, 255, 255, 0.04);
            --surface-2: rgba(255, 255, 255, 0.07);
            --surface-3: rgba(255, 255, 255, 0.12);
            --gold-overlay: rgba(212, 175, 55, 0.08);
            --gradient-brand: linear-gradient(135deg, var(--brand-primary), var(--brand-primary-light));
            --gradient-gold: linear-gradient(135deg, var(--accent-gold), var(--brand-secondary));
            --gradient-surface: linear-gradient(120deg, var(--bg-surface), rgba(23, 32, 62, 0.85));
            --gradient-glass: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.15);
            --shadow-md: 0 8px 28px rgba(0, 0, 0, 0.2);
            --shadow-lg: 0 16px 50px rgba(0, 0, 0, 0.3);
            --shadow-brand: 0 8px 30px rgba(10, 61, 160, 0.3);
            --shadow-gold: 0 6px 25px rgba(212, 175, 55, 0.15);
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
            --radius-xl: 24px;
            --radius-full: 999px;
            --transition-fast: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-normal: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-slow: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: var(--bg-dark);
            min-height: 100vh;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .header {
            background: var(--gradient-glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid rgba(212, 175, 55, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .logo-icon {
            width: 45px;
            height: 45px;
            border-radius: var(--radius-md);
            background: var(--gradient-brand);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: white;
            font-family: 'Montserrat', sans-serif;
            font-size: 1.5rem;
        }

        .logo-text h1 {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Montserrat', sans-serif;
        }

        .logo-text p {
            font-size: 0.8rem;
            color: var(--accent-gold);
            font-weight: 500;
            text-transform: uppercase;
        }

        .logout-btn {
            background: rgba(220, 53, 69, 0.1);
            color: #ff6b7a;
            border: 1px solid rgba(220, 53, 69, 0.2);
            padding: 0.75rem 1.5rem;
            border-radius: var(--radius-md);
            text-decoration: none;
            font-weight: 600;
            transition: var(--transition-normal);
        }

        .logout-btn:hover {
            background: rgba(220, 53, 69, 0.2);
            border-color: rgba(220, 53, 69, 0.4);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .card {
            background: var(--gradient-glass);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border-radius: var(--radius-lg);
            padding: 2rem;
            border: 1px solid rgba(212, 175, 55, 0.2);
            box-shadow: var(--shadow-md);
        }

        .card-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1.5rem;
            font-family: 'Montserrat', sans-serif;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--gradient-surface);
            padding: 1.5rem;
            border-radius: var(--radius-md);
            text-align: center;
            border: 1px solid rgba(212, 175, 55, 0.1);
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--accent-gold);
            font-family: 'Montserrat', sans-serif;
        }

        .stat-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-label {
            display: block;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .form-input, .form-textarea {
            width: 100%;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: var(--radius-md);
            color: var(--text-primary);
            font-size: 1rem;
            transition: var(--transition-normal);
        }

        .form-input:focus, .form-textarea:focus {
            outline: none;
            border-color: var(--accent-gold);
            background: rgba(255, 255, 255, 0.08);
        }

        .form-textarea {
            min-height: 120px;
            resize: vertical;
        }

        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: var(--radius-md);
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition-normal);
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .btn-primary {
            background: var(--gradient-brand);
            color: white;
            box-shadow: var(--shadow-brand);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(10, 61, 160, 0.4);
        }

        .btn-success {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
        }

        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(16, 185, 129, 0.4);
        }

        .btn-danger {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.3);
        }

        .btn-danger:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(239, 68, 68, 0.4);
        }

        .btn-sm {
            padding: 0.6rem 1.2rem;
            font-size: 0.9rem;
        }

        .success-message {
            background: rgba(16, 185, 129, 0.1);
            color: #34d399;
            padding: 1rem;
            border-radius: var(--radius-md);
            font-size: 0.9rem;
            font-weight: 500;
            border: 1px solid rgba(16, 185, 129, 0.2);
            text-align: center;
            margin-bottom: 1rem;
        }

        .error-message {
            background: rgba(220, 53, 69, 0.1);
            color: #ff6b7a;
            padding: 1rem;
            border-radius: var(--radius-md);
            font-size: 0.9rem;
            font-weight: 500;
            border: 1px solid rgba(220, 53, 69, 0.2);
            text-align: center;
            margin-bottom: 1rem;
        }

        .its-list {
            max-height: 400px;
            overflow-y: auto;
            background: rgba(255, 255, 255, 0.03);
            border-radius: var(--radius-md);
            border: 1px solid rgba(212, 175, 55, 0.1);
            padding: 1rem;
            margin-bottom: 1.5rem;
        }

        .its-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: var(--radius-sm);
            margin-bottom: 0.5rem;
        }

        .its-item:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .its-badge {
            background: rgba(212, 175, 55, 0.1);
            color: var(--accent-gold);
            padding: 0.3rem 0.7rem;
            border-radius: var(--radius-full);
            font-weight: 600;
            font-size: 0.9rem;
        }

        .active-session {
            position: relative;
        }

        .active-session::after {
            content: '';
            position: absolute;
            top: 50%;
            right: -15px;
            transform: translateY(-50%);
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 10px #10b981;
        }

        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: 1fr 1fr;
            }
            
            .container {
                padding: 1rem;
            }
            
            .header {
                padding: 1rem;
                flex-direction: column;
                gap: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-container">
            <div class="logo-icon">R</div>
            <div class="logo-text">
                <h1>Admin Dashboard</h1>
                <p>Ratlam Relay Centre</p>
            </div>
        </div>
        <a href="{{ url_for('admin_logout') }}" class="logout-btn">Logout</a>
    </div>

    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_its }}</div>
                <div class="stat-label">Total ITS IDs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.active_sessions }}</div>
                <div class="stat-label">Active Sessions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_sessions }}</div>
                <div class="stat-label">Total Sessions</div>
            </div>
        </div>        <div class="dashboard-grid">
            <div class="card">
                <h2 class="card-title">Webinar Settings</h2>
                
                {% if message and message_type == 'success' %}
                <div class="success-message">
                    {{ message }}
                </div>
                {% endif %}
                
                {% if message and message_type == 'error' %}
                <div class="error-message">
                    {{ message }}
                </div>
                {% endif %}
                
                <form method="POST" action="{{ url_for('admin_update_webinar_settings') }}">
                    <div class="form-group">
                        <label for="embed_url">YouTube Embed URL</label>
                        <input type="text" id="embed_url" name="embed_url" class="form-input" 
                               value="{{ settings.embed_url if settings else '' }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="webinar_title">Webinar Title</label>
                        <input type="text" id="webinar_title" name="webinar_title" class="form-input" 
                               value="{{ settings.webinar_title if settings else '' }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="webinar_description">Webinar Description</label>
                        <textarea id="webinar_description" name="webinar_description" class="form-textarea" 
                                 required>{{ settings.webinar_description if settings else '' }}</textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="webinar_date">Webinar Date</label>
                        <input type="text" id="webinar_date" name="webinar_date" class="form-input" 
                               value="{{ settings.webinar_date if settings else '' }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="webinar_time">Webinar Time</label>
                        <input type="text" id="webinar_time" name="webinar_time" class="form-input" 
                               value="{{ settings.webinar_time if settings else '' }}" required>
                    </div>
                      <div class="form-group">
                        <label for="webinar_speaker">Speaker Name</label>
                        <input type="text" id="webinar_speaker" name="webinar_speaker" class="form-input" 
                               value="{{ settings.webinar_speaker if settings else '' }}" required>
                    </div>
                    
                    <div class="form-group" style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
                        <label for="no_webinar" style="display: flex; align-items: center; gap: 1rem; cursor: pointer;">
                            <input type="checkbox" id="no_webinar" name="no_webinar" {% if settings.no_webinar %}checked{% endif %} 
                                   style="width: 1.2rem; height: 1.2rem; cursor: pointer;">
                            <span style="font-weight: 600; color: var(--text-primary);">No Webinar Available</span>
                        </label>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">Update Webinar Settings</button>
                </form>
            </div>
            
            <div class="card">
                <h2 class="card-title">Add ITS IDs</h2>
                
                {% if message and message_type == 'success' %}
                <div class="success-message">
                    {{ message }}
                </div>
                {% endif %}
                
                {% if message and message_type == 'error' %}
                <div class="error-message">
                    {{ message }}
                </div>
                {% endif %}

                <form method="POST" action="{{ url_for('admin_add_its') }}">
                    <div class="form-group">
                        <label class="form-label" for="single_its">Single ITS ID</label>
                        <input type="text" id="single_its" name="single_its" class="form-input" 
                               placeholder="Enter 8-digit ITS ID" maxlength="8" pattern="[0-9]{8}">
                    </div>
                    <button type="submit" class="btn btn-primary">Add Single ITS</button>
                </form>

                <hr style="margin: 2rem 0; border: none; border-top: 1px solid rgba(212, 175, 55, 0.2);">

                <form method="POST" action="{{ url_for('admin_add_bulk_its') }}">
                    <div class="form-group">
                        <label class="form-label" for="bulk_its">Bulk ITS IDs</label>
                        <textarea id="bulk_its" name="bulk_its" class="form-textarea" 
                                  placeholder="Enter multiple ITS IDs (one per line or comma-separated)"></textarea>
                    </div>
                    <button type="submit" class="btn btn-success">Add Bulk ITS</button>
                </form>
            </div>

            <div class="card">
                <h2 class="card-title">Manage ITS IDs ({{ stats.total_its }} total)</h2>
                
                <div style="margin-bottom: 1rem;">
                    <form method="POST" action="{{ url_for('admin_clear_sessions') }}" style="display: inline;">
                        <button type="submit" class="btn btn-danger btn-sm" 
                                onclick="return confirm('Clear all active sessions?')">
                            Clear All Sessions
                        </button>
                    </form>
                    <form method="POST" action="{{ url_for('admin_delete_all_its') }}" style="display: inline; margin-left: 0.5rem;">
                        <button type="submit" class="btn btn-danger btn-sm" 
                                onclick="return confirm('Delete all ITS IDs? This cannot be undone.')">
                            Delete All ITS IDs
                        </button>
                    </form>
                </div>
                
                {% if its_ids %}
                <div class="its-list">
                    {% for its_id in its_ids %}
                    <div class="its-item">
                        <div class="its-badge {% if its_id in sessions_status %}active-session{% endif %}">
                            {{ its_id }}
                        </div>
                        <form method="POST" action="{{ url_for('admin_delete_its') }}">
                            <input type="hidden" name="its_id" value="{{ its_id }}">
                            <button type="submit" class="btn btn-danger btn-sm" 
                                    onclick="return confirm('Delete this ITS ID?')">
                                Delete
                            </button>
                        </form>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="error-message">
                    No ITS IDs added yet.
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
'''


# Webinar template
WEBINAR_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ratlam Relay Centre - {{ webinar_title }}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            /* Premium color system */
            --brand-primary: #0a3da0;
            --brand-primary-light: #1c54c5;
            --brand-primary-dark: #082c71;
            --brand-secondary: #a08c3a;
            --accent-gold: #d4af37;
            --accent-gold-light: #f0cc50;
            --accent-gold-dark: #b39128;
            --bg-dark: #090d1b;
            --bg-surface: #0f1428;
            --bg-surface-light: #1a233f;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --text-tertiary: rgba(255, 255, 255, 0.65);
            --surface-1: rgba(255, 255, 255, 0.04);
            --surface-2: rgba(255, 255, 255, 0.07);
            --surface-3: rgba(255, 255, 255, 0.12);
            --gold-overlay: rgba(212, 175, 55, 0.08);
            
            /* Gradients */
            --gradient-brand: linear-gradient(135deg, var(--brand-primary), var(--brand-primary-light));
            --gradient-gold: linear-gradient(135deg, var(--accent-gold), var(--brand-secondary));
            --gradient-surface: linear-gradient(120deg, var(--bg-surface), rgba(23, 32, 62, 0.85));
            --gradient-glass: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            --gradient-dark: linear-gradient(145deg, var(--bg-surface), var(--bg-dark));
            
            /* Shadows */
            --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.15);
            --shadow-md: 0 8px 28px rgba(0, 0, 0, 0.2);
            --shadow-lg: 0 16px 50px rgba(0, 0, 0, 0.3);
            --shadow-brand: 0 8px 30px rgba(10, 61, 160, 0.3);
            --shadow-gold: 0 6px 25px rgba(212, 175, 55, 0.15);
            
            /* Border Radius */
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
            --radius-xl: 24px;
            --radius-full: 999px;
            
            /* Transitions */
            --transition-fast: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-normal: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-slow: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-bounce: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: url('/background.svg') center/cover no-repeat fixed;
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            position: relative;
        }

        /* Background Effects */
        .noise-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            opacity: 0.15;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 600 600' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
            pointer-events: none;
        }

        .gradient-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -3;
            background: radial-gradient(circle at 15% 15%, rgba(10, 61, 160, 0.3), transparent 40%),
                        radial-gradient(circle at 85% 85%, rgba(212, 175, 55, 0.2), transparent 40%),
                        radial-gradient(circle at 50% 50%, rgba(9, 13, 27, 0.8), rgba(9, 13, 27, 0.9) 80%);
            pointer-events: none;
        }

        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            pointer-events: none;
        }

        .particle {
            position: absolute;
            width: 2px;
            height: 2px;
            background: var(--accent-gold);
            border-radius: 50%;
            opacity: 0.3;
            animation: float 20s infinite linear;
        }

        @keyframes float {
            0% {
                transform: translateY(100vh) translateX(0px);
                opacity: 0;
            }
            10% {
                opacity: 0.3;
            }
            90% {
                opacity: 0.3;
            }
            100% {
                transform: translateY(-100px) translateX(100px);
                opacity: 0;
            }
        }

        /* Header */
        .header {
            background: rgba(9, 13, 27, 0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 1.5rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid rgba(212, 175, 55, 0.2);
            box-shadow: var(--shadow-lg);
            position: relative;
            z-index: 100;
        }

        .logo-wrapper {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .logo-icon {
            width: 50px;
            height: 50px;
            border-radius: var(--radius-md);
            background: var(--gradient-brand);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: white;
            font-family: 'Montserrat', sans-serif;
            font-size: 1.8rem;
            box-shadow: var(--shadow-brand);
            border: 1px solid rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
        }

        .logo-icon::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), transparent);
            z-index: 0;
        }

        .logo-text {
            display: flex;
            flex-direction: column;
        }

        .logo-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Montserrat', sans-serif;
            letter-spacing: -0.02em;
            text-transform: uppercase;
        }

        .logo-subtitle {
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .user-id {
            background: var(--gold-overlay);
            padding: 0.5rem 1rem;
            border-radius: var(--radius-full);
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--accent-gold);
            border: 1px solid rgba(212, 175, 55, 0.3);
        }

        .logout-btn {
            background: var(--surface-2);
            color: var(--text-primary);
            padding: 0.5rem 1.2rem;
            border-radius: var(--radius-full);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: var(--transition-normal);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .logout-btn:hover {
            background: var(--surface-3);
            transform: translateY(-2px);
        }

        /* Container */
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 3rem 2rem;
            position: relative;
            z-index: 10;
        }

        /* Webinar Info */
        .webinar-info {
            text-align: center;
            margin-bottom: 3rem;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--gold-overlay);
            padding: 0.5rem 1rem;
            border-radius: var(--radius-full);
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--accent-gold);
            margin-bottom: 1.5rem;
            border: 1px solid rgba(212, 175, 55, 0.3);
        }

        .badge-icon {
            width: 8px;
            height: 8px;
            background: var(--accent-gold);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(212, 175, 55, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(212, 175, 55, 0); }
        }

        .webinar-title {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: var(--gradient-gold);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-fill-color: transparent;
            line-height: 1.1;
            font-family: 'Montserrat', sans-serif;
            letter-spacing: -0.02em;
        }

        .webinar-subtitle {
            font-size: 1.2rem;
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 2rem;
        }

        .speaker-info {
            display: flex;
            align-items: center;
            gap: 1.5rem;
            background: var(--surface-1);
            border-radius: var(--radius-lg);
            padding: 2rem;
            max-width: 500px;
            margin: 0 auto;
            border: 1px solid rgba(212, 175, 55, 0.1);
            position: relative;
            overflow: hidden;
        }

        .speaker-info::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, var(--gold-overlay), transparent);
            opacity: 0.3;
            z-index: -1;
        }

        .speaker-avatar {
            width: 60px;
            height: 60px;
            background: var(--gradient-brand);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            font-weight: bold;
            color: white;
            box-shadow: var(--shadow-brand);
            border: 2px solid rgba(212, 175, 55, 0.3);
            position: relative;
            overflow: hidden;
        }

        .speaker-avatar::after {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), transparent);
            z-index: 1;
        }

        .speaker-details {
            text-align: left;
        }

        .speaker-name {
            font-weight: 700;
            font-size: 1.2rem;
            color: var(--text-primary);
            margin-bottom: 0.2rem;
            font-family: 'Montserrat', sans-serif;
        }

        .speaker-title {
            opacity: 0.9;
            font-size: 0.9rem;
            color: var(--accent-gold);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Video Container */
        .video-container {
            position: relative;
            width: 100%;
            max-width: 1400px;
            margin: 0 auto;
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-lg), 0 20px 80px rgba(10, 61, 160, 0.15);
            background: var(--bg-surface);
            border: 1px solid rgba(212, 175, 55, 0.2);
            transform: translateZ(0);
            transition: var(--transition-normal);
            animation: fadeIn 1s ease forwards;
            isolation: isolate;
        }

        .video-container::before {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: var(--radius-lg);
            padding: 2px;
            background: linear-gradient(135deg, var(--accent-gold), var(--brand-primary-light), var(--accent-gold));
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            mask-composite: exclude;
            opacity: 0.4;
            transition: var(--transition-normal);
            z-index: 1;
            pointer-events: none;
        }

        .video-container:hover::before {
            opacity: 0.8;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .video-wrapper {
            position: relative;
            padding-bottom: 56.25%; /* 16:9 aspect ratio */
            height: 0;
        }

        .video-frame {
            position: absolute;
            top: -50px;
            left: -50px;
            width: calc(100% + 100px);
            height: calc(100% + 100px);
            border: none;
        }

        .video-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(0deg, rgba(9, 13, 27, 0.6) 0%, transparent 15%, transparent 85%, rgba(9, 13, 27, 0.6) 100%);
            pointer-events: none;
            z-index: 5;
        }

        .youtube-brand-blocker {
            position: absolute;
            bottom: 8px;
            right: 8px;
            width: 65px;
            height: 25px;
            background: var(--bg-dark);
            z-index: 6;
            pointer-events: none;
        }

        .video-click-layer {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 10;
            cursor: pointer;
        }

        /* Video Controls */
        .custom-play-button {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 100px;
            height: 100px;
            background: rgba(9, 13, 27, 0.8);
            border-radius: var(--radius-full);
            display: none;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 15;
            transition: var(--transition-bounce);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(212, 175, 55, 0.3);
            box-shadow: var(--shadow-lg), 0 0 40px rgba(212, 175, 55, 0.15);
            overflow: hidden;
        }

        .custom-play-button::before {
            content: "";
            position: absolute;
            inset: 0;
            background: var(--gradient-gold);
            opacity: 0;
            transition: var(--transition-normal);
            z-index: -1;
        }

        .custom-play-button:hover {
            transform: translate(-50%, -50%) scale(1.1);
            box-shadow: var(--shadow-lg), 0 0 50px rgba(212, 175, 55, 0.3);
            border-color: var(--accent-gold);
        }

        .custom-play-button:hover::before {
            opacity: 0.15;
        }

        .play-icon {
            position: relative;
            width: 0;
            height: 0;
            border-left: 30px solid white;
            border-top: 20px solid transparent;
            border-bottom: 20px solid transparent;
            margin-left: 10px;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
            z-index: 2;
        }

        .volume-control, .fullscreen-control {
            position: absolute;
            bottom: 25px;
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(9, 13, 27, 0.8);
            padding: 12px 20px;
            border-radius: var(--radius-full);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            z-index: 15;
            border: 1px solid rgba(212, 175, 55, 0.2);
            box-shadow: var(--shadow-md);
            transition: var(--transition-normal);
            overflow: hidden;
        }

        .volume-control {
            right: 25px;
        }

        .fullscreen-control {
            left: 25px;
        }

        .volume-control::before, .fullscreen-control::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.1), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .volume-control:hover, .fullscreen-control:hover {
            background: rgba(9, 13, 27, 0.9);
            box-shadow: var(--shadow-lg), 0 5px 20px rgba(212, 175, 55, 0.1);
            border-color: var(--accent-gold);
        }

        .volume-control:hover::before, .fullscreen-control:hover::before {
            opacity: 1;
        }

        .control-button {
            width: 45px;
            height: 45px;
            background: none;
            border: none;
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            border-radius: var(--radius-full);
            transition: var(--transition-normal);
            position: relative;
            z-index: 2;
        }

        .control-button:hover {
            background: rgba(212, 175, 55, 0.15);
            color: var(--accent-gold);
            transform: scale(1.08);
        }

        /* Loading Overlay */
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: var(--bg-dark);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            z-index: 20;
            transition: opacity 0.5s ease;
        }

        .loading-spinner {
            position: relative;
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
        }

        .loading-spinner::before,
        .loading-spinner::after {
            content: '';
            position: absolute;
            border-radius: 50%;
        }

        .loading-spinner::before {
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, transparent, var(--accent-gold));
            animation: spin 2s linear infinite;
        }

        .loading-spinner::after {
            width: 85%;
            height: 85%;
            background: var(--bg-dark);
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }

        .loading-text {
            font-family: 'Montserrat', sans-serif;
            color: var(--accent-gold);
            font-size: 1rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1; }
            100% { opacity: 0.6; }
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Mobile Responsiveness */
        @media (max-width: 768px) {
            .header {
                padding: 1.2rem 1rem;
            }

            .logo-title {
                font-size: 1.2rem;
            }

            .logo-subtitle {
                font-size: 0.75rem;
            }

            .webinar-title {
                font-size: 2.5rem;
            }

            .webinar-subtitle {
                font-size: 1.1rem;
            }

            .container {
                padding: 2rem 1.25rem;
            }

            .speaker-info {
                flex-direction: column;
                gap: 1rem;
                padding: 1.5rem;
                text-align: center;
            }

            .speaker-details {
                text-align: center;
            }

            .volume-control {
                bottom: 20px;
                right: 20px;
                padding: 10px 15px;
            }

            .fullscreen-control {
                bottom: 20px;
                left: 20px;
                padding: 10px 15px;
            }

            .control-button {
                width: 40px;
                height: 40px;
                font-size: 1.1rem;
            }

            .custom-play-button {
                width: 85px;
                height: 85px;
            }

            .play-icon {
                border-left: 24px solid white;
                border-top: 16px solid transparent;
                border-bottom: 16px solid transparent;
            }
        }

        @media (max-width: 480px) {
            .logo-title {
                font-size: 1rem;
            }

            .logo-icon {
                width: 36px;
                height: 36px;
                font-size: 1.3rem;
            }

            .webinar-title {
                font-size: 2rem;
            }

            .webinar-subtitle {
                font-size: 1rem;
            }

            .speaker-info {
                padding: 1.25rem;
                gap: 0.8rem;
            }

            .speaker-avatar {
                width: 50px;
                height: 50px;
                font-size: 1.5rem;
            }

            .speaker-name {
                font-size: 1.1rem;
            }

            .speaker-title {
                font-size: 0.8rem;
            }

            .volume-control, .fullscreen-control {
                padding: 8px 12px;
            }

            .control-button {
                width: 35px;
                height: 35px;
                font-size: 1rem;
            }

            .custom-play-button {
                width: 70px;
                height: 70px;
            }

            .play-icon {
                border-left: 20px solid white;
                border-top: 14px solid transparent;
                border-bottom: 14px solid transparent;
            }
        }
    </style>
</head>
<body>
    <div class="noise-bg"></div>
    <div class="gradient-bg"></div>
    <div class="particles" id="particles"></div>

    <header class="header">
        <div class="logo-wrapper">
            <div class="logo-icon">R</div>
            <div class="logo-text">
                <div class="logo-title">Ratlam Relay Centre</div>
                <div class="logo-subtitle">Ashara 1447 Webinar Series</div>
            </div>
        </div>
        <div class="user-info">
            <div class="user-id">ITS ID: {{ its_id }}</div>
            <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
        </div>
    </header>

    <div class="container">
        <div class="webinar-info">
            <div class="badge">
                <div class="badge-icon"></div>
                <span>Exclusive Access</span>
            </div>
            <h1 class="webinar-title">{{ webinar_title }}</h1>
            <p class="webinar-subtitle">{{ webinar_description }}</p>
            <div class="speaker-info">
                <div class="speaker-avatar">{{ webinar_speaker[:2] }}</div>
                <div class="speaker-details">
                    <div class="speaker-name">{{ webinar_speaker }}</div>
                    <div class="speaker-title"></div>
                </div>
            </div>
        </div>

        <div class="video-container">
            <div class="video-wrapper">
                <div class="loading-overlay" id="loadingOverlay">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Connecting to live stream...</div>
                </div>
                <iframe 
                    class="video-frame" 
                    id="videoFrame"
                    src="{{ embed_url }}"
                    allow="autoplay; encrypted-media"
                    allowfullscreen>
                </iframe>
                <div class="video-overlay"></div>
                <div class="youtube-brand-blocker"></div>
                <div class="video-click-layer" id="videoClickLayer"></div>
                <div class="custom-play-button" id="playButton">
                    <div class="play-icon"></div>
                </div>
                <div class="volume-control">
                    <button class="control-button" id="volumeButton">🔇</button>
                </div>
                <div class="fullscreen-control">
                    <button class="control-button" id="fullscreenButton">⛶</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Create floating particles
        function createParticles() {
            const particlesContainer = document.getElementById('particles');
            const particleCount = 50;

            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.animationDuration = (Math.random() * 15 + 10) + 's';
                particle.style.animationDelay = Math.random() * 5 + 's';
                particlesContainer.appendChild(particle);
            }
        }

        // Parallax effect for background
        document.addEventListener('mousemove', function(e) {
            const moveX = (e.clientX - window.innerWidth / 2) * 0.01;
            const moveY = (e.clientY - window.innerHeight / 2) * 0.01;
            document.querySelector('.gradient-bg').style.transform = `translate(${moveX}px, ${moveY}px)`;
        });

        // Initialize particles
        createParticles();

        // Hide loading overlay after iframe loads
        document.getElementById('videoFrame').addEventListener('load', function() {
            setTimeout(() => {
                document.getElementById('loadingOverlay').style.opacity = '0';
                setTimeout(() => {
                    document.getElementById('loadingOverlay').style.display = 'none';
                }, 500);
            }, 1000);
        });

        // Simple play/pause and mute functionality
        let isPlaying = true; // Start as playing since autoplay is on
        let isMuted = true; // Start muted for autoplay compliance
        let isFullscreen = false;

        // Video click to pause/play
        document.getElementById('videoClickLayer').addEventListener('click', function() {
            const playButton = document.getElementById('playButton');
            const iframe = document.getElementById('videoFrame');
            
            if (isPlaying) {
                // Pause video and show play button
                playButton.style.display = 'flex';
                isPlaying = false;
                iframe.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
            } else {
                // Play video and hide play button
                playButton.style.display = 'none';
                isPlaying = true;
                iframe.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}', '*');
            }
        });

        // Play button click
        document.getElementById('playButton').addEventListener('click', function(e) {
            e.stopPropagation();
            this.style.display = 'none';
            isPlaying = true;
            const iframe = document.getElementById('videoFrame');
            iframe.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}', '*');
        });

        // Volume toggle
        document.getElementById('volumeButton').addEventListener('click', function(e) {
            e.stopPropagation();
            const iframe = document.getElementById('videoFrame');
            if (isMuted) {
                this.textContent = '🔊';
                isMuted = false;
                iframe.contentWindow.postMessage('{"event":"command","func":"unMute","args":""}', '*');
            } else {
                this.textContent = '🔇';
                isMuted = true;
                iframe.contentWindow.postMessage('{"event":"command","func":"mute","args":""}', '*');
            }
        });

        // Fullscreen toggle
        document.getElementById('fullscreenButton').addEventListener('click', function(e) {
            e.stopPropagation();
            const videoContainer = document.querySelector('.video-container');
            
            if (!isFullscreen) {
                // Enter fullscreen
                if (videoContainer.requestFullscreen) {
                    videoContainer.requestFullscreen();
                } else if (videoContainer.webkitRequestFullscreen) {
                    videoContainer.webkitRequestFullscreen();
                } else if (videoContainer.mozRequestFullScreen) {
                    videoContainer.mozRequestFullScreen();
                } else if (videoContainer.msRequestFullscreen) {
                    videoContainer.msRequestFullscreen();
                }
                this.textContent = '⛉';
                isFullscreen = true;
            } else {
                // Exit fullscreen
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                } else if (document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                }
                this.textContent = '⛶';
                isFullscreen = false;
            }
        });

        // Listen for fullscreen change events
        document.addEventListener('fullscreenchange', handleFullscreenChange);
        document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.addEventListener('mozfullscreenchange', handleFullscreenChange);
        document.addEventListener('MSFullscreenChange', handleFullscreenChange);

        function handleFullscreenChange() {
            const fullscreenButton = document.getElementById('fullscreenButton');
            if (document.fullscreenElement || document.webkitFullscreenElement || 
                document.mozFullScreenElement || document.msFullscreenElement) {
                fullscreenButton.textContent = '⛉';
                isFullscreen = true;
            } else {
                fullscreenButton.textContent = '⛶';
                isFullscreen = false;
            }
        }

        // Disable developer tools shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.key === 'F12' || 
                (e.ctrlKey && e.shiftKey && e.key === 'I') ||
                (e.ctrlKey && e.shiftKey && e.key === 'J') ||
                (e.ctrlKey && e.key === 'U')) {
                e.preventDefault();
                return false;
            }
        });

        // Disable right-click on the entire page
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
        });
    </script>
</body>
</html>
'''
html_code = '''
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ratlam Relay Centre - Ashara 1447 Webinar Series</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap">
    <style>
        :root {
            --bg-dark: #090D1B; 
            --bg-surface: #0A0E1B;
            --text-primary: #FFFFFF;
            --text-secondary: #B0B3C6;
            --text-tertiary: #7A7D8F;
            --accent-gold: #D4AF37;
            --gradient-brand: linear-gradient(135deg, #D4AF37, #FF6B7A);
            --gradient-glass: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
            --brand-primary-light: #FF6B7A;
            --radius-md: 8px;
            --radius-lg: 12px;
        }
        body {
            margin: 0;
            font-family: 'Montserrat', sans-serif;
        }
        .logo-container {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .logo-icon {
            width: 45px;
            height: 45px;
            border-radius: var(--radius-md);
            background: var(--gradient-brand);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: white;
            font-family: 'Montserrat', sans-serif;
            font-size: 1.5rem;
        }

        .logo-text h1 {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Montserrat', sans-serif;
        }

        .logo-text p {
            font-size: 0.8rem;
            color: var(--accent-gold);
            font-weight: 500;
            text-transform: uppercase;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .its-id-badge {
            background: rgba(212, 175, 55, 0.1);
            border: 1px solid rgba(212, 175, 55, 0.3);
            color: var(--accent-gold);
            padding: 0.5rem 1rem;
            border-radius: var(--radius-full);
            font-weight: 600;
            font-size: 0.9rem;
        }

        .logout-btn {
            background: rgba(220, 53, 69, 0.1);
            color: #ff6b7a;
            border: 1px solid rgba(220, 53, 69, 0.2);
            padding: 0.5rem 1rem;
            border-radius: var(--radius-md);
            text-decoration: none;
            font-weight: 600;
            transition: var(--transition-normal);
            font-size: 0.9rem;
        }

        .logout-btn:hover {
            background: rgba(220, 53, 69, 0.2);
            border-color: rgba(220, 53, 69, 0.4);
        }

        .main-content {
            padding-top: 6rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding-bottom: 3rem;
        }

        .video-container {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-lg);
            position: relative;
            aspect-ratio: 16/9;
            background: black;
        }

        .video-iframe {
            width: 100%;
            height: 100%;
            border: none;
        }

        .webinar-info {
            max-width: 1200px;
            margin: 2rem auto 0;
            padding: 2rem;
            background: var(--gradient-glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: var(--radius-lg);
            border: 1px solid rgba(212, 175, 55, 0.2);
        }

        .webinar-title {
            font-size: 1.8rem;
            font-weight: 700;
            font-family: 'Montserrat', sans-serif;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .webinar-description {
            color: var(--text-secondary);
            line-height: 1.6;
            font-size: 1rem;
        }

        .webinar-meta {
            display: flex;
            gap: 2rem;
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .meta-item {
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
        }

        .meta-label {
            font-size: 0.8rem;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }

        .meta-value {
            font-size: 1rem;
            color: var(--accent-gold);
            font-weight: 600;
        }

        @media (max-width: 768px) {
            .header {
                padding: 1rem;
            }
            
            .webinar-info {
                padding: 1.5rem;
                margin: 1.5rem 1rem 0;
            }
            
            .webinar-title {
                font-size: 1.5rem;
            }
            
            .video-container {
                margin: 0 1rem;
            }
            
            .webinar-meta {
                flex-direction: column;
                gap: 1rem;
            }
        }

        @media (max-width: 480px) {
            .header {
                flex-direction: column;
                padding: 1rem 1rem 1.5rem;
                gap: 1rem;
            }
            
            .user-info {
                flex-direction: column;
                gap: 1rem;
            }
            
            .main-content {
                padding-top: 9rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-container">
            <div class="logo-icon">R</div>
            <div class="logo-text">
                <h1>Ratlam Relay Centre</h1>
                <p>Ashara 1447</p>
            </div>
        </div>
        <div class="user-info">
            <div class="its-id-badge">ITS ID: {{ its_id }}</div>
            <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
        </div>
    </div>    <div class="main-content">
        <!-- Debug information (hidden by default) -->
        <div style="background: #333; color: white; padding: 10px; margin: 10px 0; display: none;">
            <p>Debug info:</p>
            <ul>
                <li>show_no_webinar: {{ show_no_webinar }}</li>
                <li>no_webinar (original): {{ no_webinar }}</li>
                <li>Current settings: {{ webinar_title }} / {{ webinar_date }}</li>
            </ul>
        </div>
        
        <!-- Using a string-based condition for better reliability -->
        {% if show_no_webinar == "yes" %}
        <div class="webinar-info" style="text-align: center; padding: 3rem; margin-top: 2rem;">
            <div style="margin-bottom: 2rem;">
                <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="var(--accent-gold)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin: 0 auto 1.5rem;">
                    <rect x="2" y="6" width="20" height="12" rx="2" ry="2"></rect>
                    <line x1="12" y1="12" x2="12" y2="12"></line>
                    <path d="M17 12H7"></path>
                </svg>
                <h2 class="webinar-title">No Webinar Available</h2>
            </div>
            <p class="webinar-description" style="font-size: 1.2rem; margin-bottom: 1.5rem;">
                There is currently no webinar scheduled at this time. Please check back later.
            </p>
            <div style="color: var(--accent-gold); font-weight: 500;">
                Thank you for your patience.
            </div>
        </div>
        {% else %}
        <div class="video-container">
            <iframe 
                class="video-iframe"
                src="{{ embed_url }}"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen>
            </iframe>
        </div>

        <div class="webinar-info">
            <h2 class="webinar-title">{{ webinar_title }}</h2>
            <p class="webinar-description">{{ webinar_description }}</p>
            
            <div class="webinar-meta">
                <div class="meta-item">
                    <span class="meta-label">Date</span>
                    <span class="meta-value">{{ webinar_date }}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Time</span>
                    <span class="meta-value">{{ webinar_time }}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Speaker</span>
                    <span class="meta-value">{{ webinar_speaker }}</span>
                </div>
            </div>
        </div>
        {% endif %}
    </div>

    <script>
        // Disable right-click and dev tools
        document.addEventListener('contextmenu', e => e.preventDefault());
        document.addEventListener('keydown', function(e) {
            if (e.key === 'F12' || 
                (e.ctrlKey && e.shiftKey && e.key === 'I') ||
                (e.ctrlKey && e.shiftKey && e.key === 'J') ||
                (e.ctrlKey && e.key === 'U')) {
                e.preventDefault();
                return false;
            }
        });
    </script>
</body>
</html>
'''


# API Health Check route
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/status')
def api_status():
    """API endpoint to check login status"""
    if 'session_token' not in request.cookies:
        return jsonify({'logged_in': False})
    
    session_token = request.cookies.get('session_token')
    if not verify_session(session_token):
        return jsonify({'logged_in': False})
    
    sessions = load_sessions()
    its_id = sessions[session_token]['its_id']
    login_time = sessions[session_token]['login_time']
    
    return jsonify({
        'logged_in': True,
        'its_id': its_id,
        'login_time': login_time
    })


# Main route for login
@app.route('/', methods=['GET', 'POST'])
def index():
    """Home page / login route"""
    # Initialize data files if they don't exist
    init_files()
    
    # Check if user is already logged in
    if 'session_token' in request.cookies:
        session_token = request.cookies.get('session_token')
        if verify_session(session_token):
            return redirect(url_for('webinar'))
    
    # Handle login form submission
    if request.method == 'POST':
        its_id = request.form.get('its_id', '').strip()
        
        # Validate ITS ID format
        if not its_id or len(its_id) != 8 or not its_id.isdigit():
            return render_template_string(LOGIN_TEMPLATE, error="Please enter a valid 8-digit ITS ID.")
        
        # Check if ITS ID is in the allowed list
        its_ids = load_its_ids()
        if its_id not in its_ids:
            return render_template_string(LOGIN_TEMPLATE, error="ITS ID not authorized. Please contact the administrator.")
        
        # Check if ITS ID is already logged in elsewhere
        if is_its_logged_in(its_id):
            return render_template_string(LOGIN_TEMPLATE, error="This ITS ID is already logged in on another device.")
        
        # Create session and set cookie
        session_token = create_session(its_id)
        response = redirect(url_for('webinar'))
        response.set_cookie('session_token', session_token, httponly=True, max_age=86400)  # 24 hour cookie
        
        return response
    
    # Display login page
    return render_template_string(LOGIN_TEMPLATE)

# No Webinar Template
NO_WEBINAR_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ratlam Relay Centre - No Webinar Available</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            /* Premium color system */
            --brand-primary: #0a3da0;
            --brand-primary-light: #1c54c5;
            --brand-primary-dark: #082c71;
            --brand-secondary: #a08c3a;
            --accent-gold: #d4af37;
            --accent-gold-light: #f0cc50;
            --accent-gold-dark: #b39128;
            --bg-dark: #090d1b;
            --bg-surface: #0f1428;
            --bg-surface-light: #1a233f;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --text-tertiary: rgba(255, 255, 255, 0.65);
            --surface-1: rgba(255, 255, 255, 0.04);
            --surface-2: rgba(255, 255, 255, 0.07);
            --surface-3: rgba(255, 255, 255, 0.12);
            --gold-overlay: rgba(212, 175, 55, 0.08);
            
            /* Gradients */
            --gradient-brand: linear-gradient(135deg, var(--brand-primary), var(--brand-primary-light));
            --gradient-gold: linear-gradient(135deg, var(--accent-gold), var(--brand-secondary));
            --gradient-surface: linear-gradient(120deg, var(--bg-surface), rgba(23, 32, 62, 0.85));
            --gradient-glass: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            --gradient-dark: linear-gradient(145deg, var(--bg-surface), var(--bg-dark));
            
            /* Shadows */
            --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.15);
            --shadow-md: 0 8px 28px rgba(0, 0, 0, 0.2);
            --shadow-lg: 0 16px 50px rgba(0, 0, 0, 0.3);
            --shadow-brand: 0 8px 30px rgba(10, 61, 160, 0.3);
            --shadow-gold: 0 6px 25px rgba(212, 175, 55, 0.15);
            
            /* Border Radius */
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
            --radius-xl: 24px;
            --radius-full: 999px;
            
            /* Transitions */
            --transition-fast: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-normal: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-slow: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
            --transition-bounce: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: url('/background.svg') center/cover no-repeat fixed;
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            position: relative;
        }

        /* Background Effects */
        .noise-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            opacity: 0.15;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 600 600' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
            pointer-events: none;
        }

        .gradient-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -3;
            background: radial-gradient(circle at 15% 15%, rgba(10, 61, 160, 0.3), transparent 40%),
                        radial-gradient(circle at 85% 85%, rgba(212, 175, 55, 0.2), transparent 40%),
                        radial-gradient(circle at 50% 50%, rgba(9, 13, 27, 0.8), rgba(9, 13, 27, 0.9) 80%);
            pointer-events: none;
        }

        /* Header */
        .header {
            background: rgba(9, 13, 27, 0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 1.5rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid rgba(212, 175, 55, 0.2);
            box-shadow: var(--shadow-lg);
            position: relative;
            z-index: 100;
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .logo-icon {
            width: 50px;
            height: 50px;
            border-radius: var(--radius-md);
            background: var(--gradient-brand);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: white;
            font-family: 'Montserrat', sans-serif;
            font-size: 1.8rem;
            box-shadow: var(--shadow-brand);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .logo-text h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Montserrat', sans-serif;
            letter-spacing: -0.02em;
        }

        .logo-text p {
            font-size: 0.9rem;
            color: var(--accent-gold);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .its-id-badge {
            background: rgba(10, 61, 160, 0.2);
            padding: 0.5rem 1rem;
            border-radius: var(--radius-full);
            font-size: 0.9rem;
            color: var(--text-primary);
            font-weight: 500;
            border: 1px solid rgba(10, 61, 160, 0.3);
        }

        .logout-btn {
            background: rgba(212, 175, 55, 0.1);
            color: var(--accent-gold);
            padding: 0.5rem 1.25rem;
            border-radius: var(--radius-full);
            text-decoration: none;
            font-weight: 600;
            transition: var(--transition-normal);
            border: 1px solid rgba(212, 175, 55, 0.2);
        }

        .logout-btn:hover {
            background: rgba(212, 175, 55, 0.15);
            border-color: rgba(212, 175, 55, 0.3);
            transform: translateY(-2px);
        }

        .main-content {
            padding: 3rem 2rem;
            max-width: 1000px;
            margin: 0 auto;
        }

        .no-webinar-message {
            background: var(--gradient-glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: var(--radius-xl);
            padding: 3.5rem;
            border: 1px solid rgba(212, 175, 55, 0.2);
            text-align: center;
            box-shadow: var(--shadow-lg);
            animation: fadeIn 1s ease forwards;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .no-webinar-icon {
            width: 100px;
            height: 100px;
            margin: 0 auto 2rem;
            color: var(--accent-gold);
            opacity: 0.9;
        }

        .no-webinar-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: var(--gradient-gold);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: 'Montserrat', sans-serif;
            margin-bottom: 1.5rem;
        }

        .no-webinar-description {
            font-size: 1.2rem;
            line-height: 1.7;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            max-width: 700px;
            margin-left: auto;
            margin-right: auto;
        }

        .status-badge {
            display: inline-block;
            background: rgba(212, 175, 55, 0.1);
            color: var(--accent-gold);
            padding: 0.5rem 1.25rem;
            border-radius: var(--radius-full);
            font-weight: 600;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(212, 175, 55, 0.2);
        }

        @media (max-width: 768px) {
            .header {
                padding: 1.2rem 1rem;
                flex-direction: column;
                gap: 1rem;
            }

            .user-info {
                flex-direction: column;
                gap: 1rem;
            }

            .main-content {
                padding: 2rem 1rem;
            }

            .no-webinar-message {
                padding: 2rem 1.5rem;
            }

            .no-webinar-title {
                font-size: 1.8rem;
            }

            .no-webinar-description {
                font-size: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="noise-bg"></div>
    <div class="gradient-bg"></div>

    <div class="header">
        <div class="logo-container">
            <div class="logo-icon">R</div>
            <div class="logo-text">
                <h1>Ratlam Relay Centre</h1>
                <p>Ashara 1447</p>
            </div>
        </div>
        <div class="user-info">
            <div class="its-id-badge">ITS ID: {{ its_id }}</div>
            <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
        </div>
    </div>

    <div class="main-content">
        <div class="no-webinar-message">
            <svg class="no-webinar-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="6" width="20" height="12" rx="2" ry="2"></rect>
                <line x1="7" y1="12" x2="17" y2="12"></line>
            </svg>
            
            <div class="status-badge">Status: Offline</div>
            
            <h1 class="no-webinar-title">No Webinar Available</h1>
            
            <p class="no-webinar-description">
                There is currently no webinar scheduled at this time. The webinar stream is temporarily offline. 
                Please check back later for updates. Thank you for your patience.
            </p>
        </div>
    </div>

    <script>
        // Disable right-click and dev tools
        document.addEventListener('contextmenu', e => e.preventDefault());
        document.addEventListener('keydown', function(e) {
            if (e.key === 'F12' || 
                (e.ctrlKey && e.shiftKey && e.key === 'I') ||
                (e.ctrlKey && e.shiftKey && e.key === 'J') ||
                (e.ctrlKey && e.key === 'U')) {
                e.preventDefault();
                return false;
            }
        });
    </script>
</body>
</html>
'''

@app.route('/webinar')
def webinar():
    """Webinar page - requires valid session"""
    # Check if user is logged in
    if 'session_token' not in request.cookies:
        return redirect(url_for('index'))
    
    session_token = request.cookies.get('session_token')
    if not verify_session(session_token):
        response = redirect(url_for('index'))
        response.delete_cookie('session_token')
        return response
    
    # Get user's ITS ID from session
    sessions = load_sessions()
    its_id = sessions[session_token]['its_id']
    
    # Get webinar settings directly from file for maximum reliability
    try:
        with open(WEBINAR_SETTINGS_FILE, 'r') as f:
            webinar_data = json.load(f)
            print(f"Raw webinar data from file: {webinar_data}")
            
            # Direct check for the no_webinar key
            if 'no_webinar' in webinar_data and webinar_data['no_webinar'] == True:
                # Render the "No Webinar" template directly
                return render_template_string(NO_WEBINAR_TEMPLATE, its_id=its_id)
            else:
                # Render normal webinar template
                return render_template_string(WEBINAR_TEMPLATE, its_id=its_id, **webinar_data)
    except Exception as e:
        print(f"Error loading webinar settings: {e}")
        # Fallback to default settings
        default_settings = {
            "embed_url": "https://www.youtube.com/embed/GXRL7PcPbOA?autoplay=1&mute=1&controls=0&modestbranding=1&rel=0&showinfo=0&iv_load_policy=3&fs=0&disablekb=1&cc_load_policy=0&playsinline=1&loop=1&enablejsapi=1",
            "webinar_title": "Ashara Mubaraka 1447 - Ratlam Relay",
            "webinar_description": "Welcome to the live relay of Ashara Mubaraka 1447. This stream is authorized for ITS members only. Please do not share this link with others.",
            "webinar_date": "June 18-27, 2025",
            "webinar_time": "7:30 AM - 12:30 PM IST",
            "webinar_speaker": "His Holiness Dr. Syedna Mufaddal Saifuddin (TUS)"
        }
        return render_template_string(WEBINAR_TEMPLATE, its_id=its_id, **default_settings)

@app.route('/logout')
def logout():
    """Logout route - clear session"""
    if 'session_token' in request.cookies:
        session_token = request.cookies.get('session_token')
        logout_session(session_token)
    
    response = redirect(url_for('index'))
    response.delete_cookie('session_token')
    return response

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login route"""
    # Check if admin is already logged in
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    
    # Handle login form submission
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Load admin credentials
        try:
            with open(ADMIN_FILE, 'r') as f:
                admin_data = json.load(f)
        except:
            return render_template_string(ADMIN_LOGIN_TEMPLATE, error="Admin credentials not configured.")
        
        # Verify credentials
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if username == admin_data['username'] and password_hash == admin_data['password_hash']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template_string(ADMIN_LOGIN_TEMPLATE, error="Invalid username or password.")
    
    # Display login page
    return render_template_string(ADMIN_LOGIN_TEMPLATE)

@app.route('/admin/logout')
def admin_logout():
    """Admin logout route"""
    if 'admin_logged_in' in session:
        session.pop('admin_logged_in')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard route"""    # Load data
    its_ids = set(load_its_ids())
    sessions = load_sessions()
    
    # Get active sessions by ITS ID
    sessions_status = set()
    for session_data in sessions.values():
        sessions_status.add(session_data['its_id'])
    
    # Get webinar settings
    webinar_settings = load_webinar_settings()
    
    # Prepare stats
    stats = {
        'total_its': len(its_ids),
        'active_sessions': len(sessions),
        'total_sessions': len(sessions)
    }
    
    message = request.args.get('message', '')
    message_type = request.args.get('type', 'success')
    
    print(f"Admin dashboard - Stats: {stats}")
    
    return render_template_string(ADMIN_DASHBOARD_TEMPLATE, 
                               stats=stats,
                               its_ids=sorted(its_ids),
                               sessions_status=sessions_status,
                               message=message,
                               message_type=message_type,
                               settings=webinar_settings)

@app.route('/admin/add_its', methods=['POST'])
def admin_add_its():
    """Add a single ITS ID"""
    its_id = request.form.get('single_its', '').strip()
    
    if not its_id or len(its_id) != 8 or not its_id.isdigit():
        print(f"Invalid ITS ID: {its_id}")
        return redirect(url_for('admin_dashboard') + '?message=Invalid ITS ID format&type=error')
    
    its_ids = load_its_ids()
    
    if its_id in its_ids:
        print(f"ITS ID already exists: {its_id}")
        return redirect(url_for('admin_dashboard') + '?message=ITS ID already exists&type=error')
    
    its_ids.add(its_id)
    save_its_ids(its_ids)
    
    print(f"Added ITS ID: {its_id}")
    return redirect(url_for('admin_dashboard') + '?message=ITS ID added successfully&type=success')
@app.route('/admin/add_bulk_its', methods=['POST'])
def admin_add_bulk_its():
    """Add multiple ITS IDs from a textarea"""
    bulk_its = request.form.get('bulk_its', '').strip()
    
    if not bulk_its:
        print("No ITS IDs provided")
        return redirect(url_for('admin_dashboard') + '?message=No ITS IDs provided&type=error')
    
    its_ids = load_its_ids()
    new_ids = set()
    
    # Split by lines or commas and validate each ID
    for line in bulk_its.splitlines():
        for its_id in line.split(','):
            its_id = its_id.strip()
            if len(its_id) == 8 and its_id.isdigit() and its_id not in its_ids:
                new_ids.add(its_id)
    
    if not new_ids:
        print("No valid ITS IDs to add")
        return redirect(url_for('admin_dashboard') + '?message=No valid ITS IDs to add&type=error')
    
    its_ids.update(new_ids)
    save_its_ids(its_ids)
    
    print(f"Added {len(new_ids)} ITS IDs: {new_ids}")
    return redirect(url_for('admin_dashboard') + '?message=ITS IDs added successfully&type=success')
@app.route('/admin/delete_its', methods=['POST'])
def admin_delete_its():
    """Delete a specific ITS ID"""
    its_id = request.form.get('its_id', '').strip()
    
    if not its_id or len(its_id) != 8 or not its_id.isdigit():
        print(f"Invalid ITS ID for deletion: {its_id}")
        return redirect(url_for('admin_dashboard') + '?message=Invalid ITS ID format&type=error')
    
    its_ids = load_its_ids()
    
    if its_id not in its_ids:
        print(f"ITS ID not found for deletion: {its_id}")
        return redirect(url_for('admin_dashboard') + '?message=ITS ID not found&type=error')
    
    its_ids.remove(its_id)
    save_its_ids(its_ids)
    
    print(f"Deleted ITS ID: {its_id}")
    return redirect(url_for('admin_dashboard') + '?message=ITS ID deleted successfully&type=success')
@app.route('/admin/delete_all_its', methods=['POST'])
def admin_delete_all_its():
    """Delete all ITS IDs"""
    its_ids = load_its_ids()
    
    if not its_ids:
        print("No ITS IDs to delete")
        return redirect(url_for('admin_dashboard') + '?message=No ITS IDs to delete&type=error')
    
    its_ids.clear()
    save_its_ids(its_ids)
    print("Deleted all ITS IDs")
    return redirect(url_for('admin_dashboard') + '?message=All ITS IDs deleted successfully&type=success')
@app.route('/admin/clear_sessions', methods=['POST'])
def admin_clear_sessions():
    """Clear all active sessions"""
    sessions = load_sessions()
    
    if not sessions:
        print("No active sessions to clear")
        return redirect(url_for('admin_dashboard') + '?message=No active sessions to clear&type=error')
    
    sessions.clear()
    save_sessions(sessions)    
    print("Cleared all active sessions")
    return redirect(url_for('admin_dashboard') + '?message=All active sessions cleared successfully&type=success')

@app.route('/admin/update_webinar_settings', methods=['POST'])
def admin_update_webinar_settings():
    """Update webinar settings"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        # Load current settings
        with open(WEBINAR_SETTINGS_FILE, 'r') as f:
            current_settings = json.load(f)
        
        # Update with form data
        current_settings['embed_url'] = request.form.get('embed_url', current_settings.get('embed_url', ''))
        current_settings['webinar_title'] = request.form.get('webinar_title', current_settings.get('webinar_title', ''))
        current_settings['webinar_description'] = request.form.get('webinar_description', current_settings.get('webinar_description', ''))
        current_settings['webinar_date'] = request.form.get('webinar_date', current_settings.get('webinar_date', ''))
        current_settings['webinar_time'] = request.form.get('webinar_time', current_settings.get('webinar_time', ''))
        current_settings['webinar_speaker'] = request.form.get('webinar_speaker', current_settings.get('webinar_speaker', ''))
        
        # Simple checkbox handling
        current_settings['no_webinar'] = 'no_webinar' in request.form
        
        # Add a timestamp
        current_settings['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
          # Write directly to the file
        with open(WEBINAR_SETTINGS_FILE, 'w') as f:
            json.dump(current_settings, f, indent=2)
        
        print(f"Updated webinar settings: {current_settings}")
        return redirect(url_for('admin_dashboard') + f'?message=Webinar settings updated successfully. No webinar: {current_settings["no_webinar"]}&type=success')
    
    except Exception as e:
        print(f"Error updating webinar settings: {e}")
        return redirect(url_for('admin_dashboard') + f'?message=Error updating settings: {str(e)}&type=error')

@app.route('/admin')
def admin_index():
    """Redirect to admin login or dashboard"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

def load_webinar_settings():
    """Load webinar settings from file"""
    try:
        with open(WEBINAR_SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            
            # Explicitly handle the no_webinar flag
            if 'no_webinar' not in settings:
                settings['no_webinar'] = False
            else:
                # Convert to a proper boolean
                if isinstance(settings['no_webinar'], str):
                    settings['no_webinar'] = settings['no_webinar'].lower() in ('true', 'yes', 'y', '1')
                else:
                    settings['no_webinar'] = bool(settings['no_webinar'])
                    
            print(f"Loaded no_webinar value: {settings['no_webinar']} (type: {type(settings['no_webinar'])})")
            return settings
    except Exception as e:
        print(f"Error loading webinar settings: {e}")
        # Return default settings if file doesn't exist or can't be read
        return {
            "embed_url": "https://www.youtube.com/embed/GXRL7PcPbOA?autoplay=1&mute=1&controls=0&modestbranding=1&rel=0&showinfo=0&iv_load_policy=3&fs=0&disablekb=1&cc_load_policy=0&playsinline=1&loop=1&enablejsapi=1",
            "webinar_title": "Ashara Mubaraka 1447 - Ratlam Relay",
            "webinar_description": "Welcome to the live relay of Ashara Mubaraka 1447. This stream is authorized for ITS members only. Please do not share this link with others.",
            "webinar_date": "June 18-27, 2025",
            "webinar_time": "7:30 AM - 12:30 PM IST",
            "webinar_speaker": "His Holiness Dr. Syedna Mufaddal Saifuddin (TUS)",
            "no_webinar": False
        }

def save_webinar_settings(settings):
    """Save webinar settings to file"""
    with open(WEBINAR_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

# Start the server if this file is run directly
if __name__ == '__main__':
    # Initialize data files
    init_files()
    # Start Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)