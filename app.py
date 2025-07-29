"""
Ratlam Relay Centre - Webinar Access Portal (Enhanced Version)

A Flask web application that provides authorized access to webinar streams
for registered ITS members. Features include user authentication via ITS ID,
session management, IP geolocation, and an admin panel for managing authorized users.

Author: Huzaifa (Enhanced)
Date: July 29, 2025
Version: 3.0.0 - Enhanced with IP Geolocation
"""

from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify, send_file
import json
import os
from datetime import datetime, timedelta
import hashlib
import secrets
from functools import wraps
import requests
import ipaddress

app = Flask(__name__)
app.secret_key = 'Huzaifa53'

# File paths for data storage
ITS_FILE = 'its_ids.json'
SESSIONS_FILE = 'active_sessions.json'
ADMIN_FILE = 'admin_credentials.json'
WEBINAR_SETTINGS_FILE = 'webinar_settings.json'
GEO_SETTINGS_FILE = 'geo_settings.json'

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
    
    if not os.path.exists(GEO_SETTINGS_FILE):
        default_geo_settings = {
            "geo_blocking_enabled": False,
            "allowed_countries": ["IN", "US", "GB", "CA", "AU"],  # Default allowed countries
            "blocked_message": "Access is restricted from your location. Please contact the administrator.",
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(GEO_SETTINGS_FILE, 'w') as f:
            json.dump(default_geo_settings, f, indent=2)
            
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

def get_client_ip():
    """Get the real client IP address"""
    # Check for forwarded headers first
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def get_location_from_ip(ip_address):
    """Get location information from IP address using ipapi.co"""
    try:
        # Skip local/private IPs
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            if ip_obj.is_private or ip_obj.is_loopback:
                return {
                    'country_code': 'IN',  # Default to India for local IPs
                    'country': 'India',
                    'city': 'Local',
                    'region': 'Local',
                    'ip': ip_address
                }
        except:
            pass
        
        # Use ipapi.co for geolocation (free service)
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'country_code': data.get('country_code', ''),
                'country': data.get('country_name', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'ip': ip_address
            }
    except Exception as e:
        print(f"Geolocation error: {e}")
    
    # Fallback if geolocation fails
    return {
        'country_code': 'IN',  # Default to India
        'country': 'India',
        'city': 'Unknown',
        'region': 'Unknown',
        'ip': ip_address
    }

def is_country_allowed(country_code):
    """Check if the country is in the allowed list"""
    try:
        with open(GEO_SETTINGS_FILE, 'r') as f:
            geo_settings = json.load(f)
            
        if not geo_settings.get('geo_blocking_enabled', False):
            return True, None
            
        allowed_countries = geo_settings.get('allowed_countries', [])
        if country_code in allowed_countries:
            return True, None
        else:
            return False, geo_settings.get('blocked_message', 'Access restricted from your location.')
    except:
        return True, None  # Allow if settings can't be loaded

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

def create_session(its_id, location_info=None):
    """Create a new session for ITS ID"""
    sessions = load_sessions()
    session_token = secrets.token_urlsafe(32)
    
    session_data = {
        'its_id': str(its_id),
        'login_time': datetime.now().isoformat(),
        'ip_address': location_info.get('ip', '') if location_info else '',
        'country': location_info.get('country', '') if location_info else '',
        'city': location_info.get('city', '') if location_info else ''
    }
    
    sessions[session_token] = session_data
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

def load_geo_settings():
    """Load geo settings from file"""
    try:
        with open(GEO_SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "geo_blocking_enabled": False,
            "allowed_countries": ["IN", "US", "GB", "CA", "AU"],
            "blocked_message": "Access is restricted from your location.",
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def save_geo_settings(settings):
    """Save geo settings to file"""
    with open(GEO_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

# Login page template (keeping your original design)
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
            --accent-gold: #d4af37;
            --bg-dark: #090d1b;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --gradient-brand: linear-gradient(135deg, var(--brand-primary), var(--brand-primary-light));
            --gradient-gold: linear-gradient(135deg, var(--accent-gold), #a08c3a);
            --gradient-glass: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            --shadow-lg: 0 16px 50px rgba(0, 0, 0, 0.3);
            --radius-md: 10px;
            --radius-xl: 24px;
            --transition-normal: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: url('https://www.ratlamrelaycentre.co.in/jameafront.svg') center/cover no-repeat fixed;
            min-height: 100vh;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow-x: hidden;
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
        }

        .login-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(10, 61, 160, 0.4);
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
            --accent-gold: #d4af37;
            --bg-dark: #090d1b;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --gradient-brand: linear-gradient(135deg, var(--brand-primary), var(--brand-primary-light));
            --gradient-gold: linear-gradient(135deg, var(--accent-gold), #a08c3a);
            --gradient-glass: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            --shadow-lg: 0 16px 50px rgba(0, 0, 0, 0.3);
            --radius-md: 10px;
            --radius-xl: 24px;
            --radius-full: 999px;
            --transition-normal: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
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
        }

        .login-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(10, 61, 160, 0.4);
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
        </form>

        <div class="back-link">
            <a href="{{ url_for('index') }}">← Back to User Login</a>
        </div>
    </div>
</body>
</html>
'''

# Enhanced Admin dashboard template with geolocation features
ADMIN_DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - Ratlam Relay Centre</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --brand-primary: #0a3da0;
            --accent-gold: #d4af37;
            --bg-dark: #090d1b;
            --bg-surface: #0f1428;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --gradient-brand: linear-gradient(135deg, var(--brand-primary), #1c54c5);
            --gradient-glass: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            --shadow-lg: 0 16px 50px rgba(0, 0, 0, 0.3);
            --radius-md: 10px;
            --radius-lg: 16px;
            --radius-full: 999px;
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
        }

        .header {
            background: var(--gradient-glass);
            backdrop-filter: blur(20px);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid rgba(212, 175, 55, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .card {
            background: var(--gradient-glass);
            backdrop-filter: blur(15px);
            border-radius: var(--radius-lg);
            padding: 2rem;
            border: 1px solid rgba(212, 175, 55, 0.2);
            box-shadow: var(--shadow-lg);
        }

        .card-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1.5rem;
            font-family: 'Montserrat', sans-serif;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: linear-gradient(135deg, var(--bg-surface), rgba(23, 32, 62, 0.85));
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

        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: var(--radius-md);
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background: var(--gradient-brand);
            color: white;
        }

        .btn-success {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }

        .btn-danger {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
        }

        .btn-sm {
            padding: 0.6rem 1.2rem;
            font-size: 0.9rem;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }

        .form-input, .form-textarea, .form-select {
            width: 100%;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: var(--radius-md);
            color: var(--text-primary);
            font-size: 1rem;
            margin-bottom: 1rem;
        }

        .form-input:focus, .form-textarea:focus, .form-select:focus {
            outline: none;
            border-color: var(--accent-gold);
            background: rgba(255, 255, 255, 0.08);
        }

        .form-textarea {
            min-height: 120px;
            resize: vertical;
        }

        .success-message {
            background: rgba(16, 185, 129, 0.1);
            color: #34d399;
            padding: 1rem;
            border-radius: var(--radius-md);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .error-message {
            background: rgba(220, 53, 69, 0.1);
            color: #ff6b7a;
            padding: 1rem;
            border-radius: var(--radius-md);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
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
            border-radius: 8px;
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

        .country-list {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .country-tag {
            background: rgba(212, 175, 55, 0.1);
            color: var(--accent-gold);
            padding: 0.3rem 0.8rem;
            border-radius: var(--radius-full);
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }

        .country-tag .remove-btn {
            background: none;
            border: none;
            color: #ff6b7a;
            cursor: pointer;
            padding: 0;
            width: 16px;
            height: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .sessions-table {
            overflow-x: auto;
        }

        .sessions-table table {
            width: 100%;
            border-collapse: collapse;
        }

        .sessions-table th,
        .sessions-table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .sessions-table th {
            background: rgba(255, 255, 255, 0.05);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.05em;
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
        <div>
            <h1><i class="fas fa-cogs"></i> Admin Dashboard</h1>
            <p style="color: var(--text-secondary);">Ratlam Relay Centre Management</p>
        </div>
        <a href="{{ url_for('admin_logout') }}" style="color: #ff6b7a; text-decoration: none; display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas fa-sign-out-alt"></i> Logout
        </a>
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
            <div class="stat-card">
                <div class="stat-number">{{ stats.countries_count }}</div>
                <div class="stat-label">Countries Allowed</div>
            </div>
        </div>

        {% if message and message_type == 'success' %}
        <div class="success-message">
            <i class="fas fa-check-circle"></i>
            {{ message }}
        </div>
        {% endif %}
        
        {% if message and message_type == 'error' %}
        <div class="error-message">
            <i class="fas fa-exclamation-circle"></i>
            {{ message }}
        </div>
        {% endif %}

        <div class="dashboard-grid">
            <div class="card">
                <h2 class="card-title">
                    <i class="fas fa-video"></i>
                    Webinar Settings
                </h2>
                <form method="POST" action="{{ url_for('admin_update_webinar_settings') }}">
                    <input type="text" name="embed_url" class="form-input" placeholder="YouTube Embed URL" value="{{ settings.embed_url if settings else '' }}" required>
                    <input type="text" name="webinar_title" class="form-input" placeholder="Webinar Title" value="{{ settings.webinar_title if settings else '' }}" required>
                    <textarea name="webinar_description" class="form-textarea" placeholder="Description" required>{{ settings.webinar_description if settings else '' }}</textarea>
                    <input type="text" name="webinar_date" class="form-input" placeholder="Date" value="{{ settings.webinar_date if settings else '' }}" required>
                    <input type="text" name="webinar_time" class="form-input" placeholder="Time" value="{{ settings.webinar_time if settings else '' }}" required>
                    <input type="text" name="webinar_speaker" class="form-input" placeholder="Speaker" value="{{ settings.webinar_speaker if settings else '' }}" required>
                    
                    <label style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; cursor: pointer;">
                        <input type="checkbox" name="no_webinar" {% if settings and settings.no_webinar %}checked{% endif %} style="width: 1.2rem; height: 1.2rem;">
                        <span>No Webinar Available</span>
                    </label>
                    
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i>
                        Update Settings
                    </button>
                </form>
            </div>

            <div class="card">
                <h2 class="card-title">
                    <i class="fas fa-globe"></i>
                    IP Geolocation Settings
                </h2>
                <form method="POST" action="{{ url_for('admin_update_geo_settings') }}">
                    <label style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; cursor: pointer;">
                        <input type="checkbox" name="geo_blocking_enabled" {% if geo_settings and geo_settings.geo_blocking_enabled %}checked{% endif %} style="width: 1.2rem; height: 1.2rem;">
                        <span><strong>Enable Geographic Blocking</strong></span>
                    </label>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Add Country (ISO Code):</label>
                        <div style="display: flex; gap: 0.5rem;">
                            <input type="text" id="new_country" placeholder="e.g., IN, US, GB" style="flex: 1; padding: 0.75rem; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(212, 175, 55, 0.2); border-radius: 8px; color: white;">
                            <button type="button" onclick="addCountry()" class="btn btn-success btn-sm">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="country-list" id="countryList">
                        {% if geo_settings and geo_settings.allowed_countries %}
                            {% for country in geo_settings.allowed_countries %}
                            <div class="country-tag">
                                {{ country }}
                                <button type="button" class="remove-btn" onclick="removeCountry('{{ country }}')">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                            {% endfor %}
                        {% endif %}
                    </div>
                    
                    <input type="hidden" name="allowed_countries" id="allowed_countries" value="{{ ','.join(geo_settings.allowed_countries) if geo_settings and geo_settings.allowed_countries else '' }}">
                    
                    <textarea name="blocked_message" class="form-textarea" placeholder="Message for blocked users">{{ geo_settings.blocked_message if geo_settings else 'Access is restricted from your location.' }}</textarea>
                    
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i>
                        Update Geo Settings
                    </button>
                </form>
            </div>

            <div class="card">
                <h2 class="card-title">
                    <i class="fas fa-user-plus"></i>
                    Add ITS IDs
                </h2>
                
                <form method="POST" action="{{ url_for('admin_add_its') }}">
                    <input type="text" name="single_its" class="form-input" placeholder="Enter 8-digit ITS ID" maxlength="8" pattern="[0-9]{8}">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-plus"></i>
                        Add Single ITS
                    </button>
                </form>

                <hr style="margin: 2rem 0; border: none; border-top: 1px solid rgba(212, 175, 55, 0.2);">

                <form method="POST" action="{{ url_for('admin_add_bulk_its') }}">
                    <textarea name="bulk_its" class="form-textarea" placeholder="Enter multiple ITS IDs (one per line or comma-separated)" rows="5"></textarea>
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-upload"></i>
                        Add Bulk ITS
                    </button>
                </form>
            </div>

            <div class="card">
                <h2 class="card-title">
                    <i class="fas fa-users"></i>
                    Manage ITS IDs ({{ stats.total_its }} total)
                </h2>
                
                <div style="margin-bottom: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    <form method="POST" action="{{ url_for('admin_clear_sessions') }}" style="display: inline;">
                        <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Clear all active sessions?')">
                            <i class="fas fa-trash"></i>
                            Clear All Sessions
                        </button>
                    </form>
                    <form method="POST" action="{{ url_for('admin_delete_all_its') }}" style="display: inline;">
                        <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Delete all ITS IDs? This cannot be undone.')">
                            <i class="fas fa-trash-alt"></i>
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
                            {% if its_id in sessions_status %}
                                <i class="fas fa-circle" style="color: #10b981; font-size: 0.6rem; margin-left: 0.5rem;"></i>
                            {% endif %}
                        </div>
                        <form method="POST" action="{{ url_for('admin_delete_its') }}">
                            <input type="hidden" name="its_id" value="{{ its_id }}">
                            <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Delete this ITS ID?')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </form>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="error-message">
                    <i class="fas fa-info-circle"></i>
                    No ITS IDs added yet.
                </div>
                {% endif %}
            </div>

            <div class="card">
                <h2 class="card-title">
                    <i class="fas fa-chart-line"></i>
                    Active Sessions
                </h2>
                
                {% if sessions_data %}
                <div class="sessions-table">
                    <table>
                        <thead>
                            <tr>
                                <th>ITS ID</th>
                                <th>Login Time</th>
                                <th>Country</th>
                                <th>IP Address</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for session in sessions_data %}
                            <tr>
                                <td>{{ session.its_id }}</td>
                                <td>{{ session.login_time_formatted }}</td>
                                <td>{{ session.country or 'Unknown' }}</td>
                                <td>{{ session.ip_address or 'Unknown' }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="error-message">
                    <i class="fas fa-info-circle"></i>
                    No active sessions.
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <script>
        let allowedCountries = [];
        
        // Initialize countries from server data
        {% if geo_settings and geo_settings.allowed_countries %}
        allowedCountries = {{ geo_settings.allowed_countries | tojson }};
        {% endif %}

        function addCountry() {
            const input = document.getElementById('new_country');
            const country = input.value.trim().toUpperCase();
            
            if (country && !allowedCountries.includes(country)) {
                allowedCountries.push(country);
                updateCountryDisplay();
                updateHiddenInput();
                input.value = '';
            }
        }

        function removeCountry(country) {
            allowedCountries = allowedCountries.filter(c => c !== country);
            updateCountryDisplay();
            updateHiddenInput();
        }

        function updateCountryDisplay() {
            const container = document.getElementById('countryList');
            container.innerHTML = '';
            
            allowedCountries.forEach(country => {
                const tag = document.createElement('div');
                tag.className = 'country-tag';
                tag.innerHTML = `
                    ${country}
                    <button type="button" class="remove-btn" onclick="removeCountry('${country}')">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                container.appendChild(tag);
            });
        }

        function updateHiddenInput() {
            document.getElementById('allowed_countries').value = allowedCountries.join(',');
        }

        // Allow Enter key to add country
        document.getElementById('new_country').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addCountry();
            }
        });
    </script>
</body>
</html>
'''

# Improved webinar template (using the one from your existing code)
WEBINAR_TEMPLATE_IMPROVED = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ webinar_title }} - Ratlam Relay Centre</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --brand-primary: #0a3da0;
            --accent-gold: #d4af37;
            --bg-dark: #090d1b;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --gradient-brand: linear-gradient(135deg, var(--brand-primary), #1c54c5);
            --gradient-glass: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            --shadow-lg: 0 16px 50px rgba(0, 0, 0, 0.3);
            --radius-lg: 16px;
            --radius-full: 999px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: url('https://www.ratlamrelaycentre.co.in/jameafront.svg') center/cover no-repeat fixed;
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            position: relative;
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

        .header {
            background: rgba(9, 13, 27, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 1rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid rgba(212, 175, 55, 0.2);
            box-shadow: var(--shadow-lg);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo-wrapper {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            width: 45px;
            height: 45px;
            border-radius: 10px;
            background: var(--gradient-brand);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: white;
            font-family: 'Montserrat', sans-serif;
            font-size: 1.6rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            flex-shrink: 0;
        }

        .logo-text {
            display: flex;
            flex-direction: column;
        }

        .logo-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Montserrat', sans-serif;
            letter-spacing: -0.02em;
            text-transform: uppercase;
            line-height: 1.1;
        }

        .logo-subtitle {
            font-size: 0.8rem;
            color: var(--accent-gold);
            font-weight: 500;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex-shrink: 0;
        }

        .user-id {
            background: rgba(212, 175, 55, 0.1);
            padding: 0.5rem 0.75rem;
            border-radius: var(--radius-full);
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--accent-gold);
            border: 1px solid rgba(212, 175, 55, 0.3);
            white-space: nowrap;
        }

        .logout-btn {
            background: rgba(255, 255, 255, 0.07);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: var(--radius-full);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
            white-space: nowrap;
        }

        .logout-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-1px);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 1.5rem 1rem;
            position: relative;
            z-index: 10;
        }

        .webinar-info {
            text-align: center;
            margin-bottom: 1.5rem;
            padding: 1rem;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(212, 175, 55, 0.1);
            padding: 0.4rem 0.8rem;
            border-radius: var(--radius-full);
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--accent-gold);
            margin-bottom: 1rem;
            border: 1px solid rgba(212, 175, 55, 0.3);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .badge-icon {
            width: 6px;
            height: 6px;
            background: var(--accent-gold);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 4px rgba(212, 175, 55, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(212, 175, 55, 0); }
        }

        .webinar-title {
            font-size: clamp(1.8rem, 5vw, 3rem);
            font-weight: 800;
            margin-bottom: 0.75rem;
            background: linear-gradient(135deg, var(--accent-gold), #a08c3a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.1;
            font-family: 'Montserrat', sans-serif;
            letter-spacing: -0.02em;
        }

        .webinar-subtitle {
            font-size: clamp(0.9rem, 2vw, 1.1rem);
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 1rem;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }

        .speaker-info {
            display: inline-flex;
            align-items: center;
            gap: 1rem;
            background: rgba(255, 255, 255, 0.04);
            border-radius: var(--radius-lg);
            padding: 1rem 1.5rem;
            border: 1px solid rgba(212, 175, 55, 0.1);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .speaker-avatar {
            width: 50px;
            height: 50px;
            background: var(--gradient-brand);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            font-weight: bold;
            color: white;
            border: 2px solid rgba(212, 175, 55, 0.3);
            flex-shrink: 0;
        }

        .speaker-details {
            text-align: left;
        }

        .speaker-name {
            font-weight: 700;
            font-size: 1rem;
            color: var(--text-primary);
            margin-bottom: 0.2rem;
            font-family: 'Montserrat', sans-serif;
        }

        .speaker-title {
            opacity: 0.9;
            font-size: 0.8rem;
            color: var(--accent-gold);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .video-container {
            position: relative;
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-lg);
            background: var(--bg-dark);
            border: 1px solid rgba(212, 175, 55, 0.2);
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

        .video-wrapper {
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
        }

        .video-frame {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: none;
        }

        @media (max-width: 768px) {
            .header {
                padding: 0.75rem 1rem;
                flex-wrap: wrap;
                gap: 0.5rem;
            }

            .logo-wrapper {
                gap: 0.5rem;
            }

            .logo-icon {
                width: 40px;
                height: 40px;
                font-size: 1.4rem;
            }

            .logo-title {
                font-size: 1.1rem;
            }

            .logo-subtitle {
                font-size: 0.7rem;
            }

            .user-info {
                gap: 0.5rem;
                flex-wrap: wrap;
            }

            .user-id, .logout-btn {
                font-size: 0.8rem;
                padding: 0.4rem 0.6rem;
            }

            .speaker-info {
                flex-direction: column;
                gap: 0.75rem;
                padding: 1rem;
                text-align: center;
            }

            .speaker-details {
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="gradient-bg"></div>

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
                    <div class="speaker-title">{{ webinar_date }} • {{ webinar_time }}</div>
                </div>
            </div>
        </div>

        <div class="video-container">
            <div class="video-wrapper">
                <iframe 
                    class="video-frame"
                    src="{{ embed_url }}"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen>
                </iframe>
            </div>
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

# No webinar template (keeping the existing one)
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
            --brand-primary: #0a3da0;
            --accent-gold: #d4af37;
            --bg-dark: #090d1b;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --gradient-brand: linear-gradient(135deg, var(--brand-primary), #1c54c5);
            --gradient-gold: linear-gradient(135deg, var(--accent-gold), #a08c3a);
            --gradient-glass: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            --shadow-lg: 0 16px 50px rgba(0, 0, 0, 0.3);
            --radius-md: 10px;
            --radius-lg: 16px;
            --radius-xl: 24px;
            --radius-full: 999px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: url('https://www.ratlamrelaycentre.co.in/jameafront.svg') center/cover no-repeat fixed;
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            position: relative;
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
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .logo-text h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Montserrat', sans-serif;
        }

        .logo-text p {
            font-size: 0.9rem;
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
            border: 1px solid rgba(212, 175, 55, 0.2);
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
            <div class="status-badge">Status: Offline</div>
            <h1 class="no-webinar-title">No Webinar Available</h1>
            <p class="no-webinar-description">
                There is currently no webinar scheduled at this time. The webinar stream is temporarily offline. 
                Please check back later for updates. Thank you for your patience.
            </p>
        </div>
    </div>

    <script>
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
        'version': '3.0.0'
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

# Main route for login with IP geolocation
@app.route('/', methods=['GET', 'POST'])
def index():
    """Home page / login route with IP geolocation"""
    init_files()
    
    # Get client IP and location
    client_ip = get_client_ip()
    location_info = get_location_from_ip(client_ip)
    
    # Check if country is allowed
    is_allowed, blocked_message = is_country_allowed(location_info.get('country_code', 'IN'))
    
    if not is_allowed:
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Access Restricted</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 2rem; background: #1a1a1a; color: white; }
                .container { max-width: 500px; margin: 0 auto; padding: 2rem; background: rgba(255,255,255,0.1); border-radius: 10px; }
                .error { color: #ff6b7a; margin-bottom: 1rem; }
                .location { color: #d4af37; font-size: 0.9rem; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🚫 Access Restricted</h2>
                <p class="error">{{ blocked_message }}</p>
                <p class="location">Your location: {{ location.city }}, {{ location.country }} ({{ location.ip }})</p>
                <p style="margin-top: 2rem; font-size: 0.9rem; color: #ccc;">
                    If you believe this is an error, please contact the administrator.
                </p>
            </div>
        </body>
        </html>
        ''', blocked_message=blocked_message, location=location_info)
    
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
        
        # Create session with location info and set cookie
        session_token = create_session(its_id, location_info)
        response = redirect(url_for('webinar'))
        response.set_cookie('session_token', session_token, httponly=True, max_age=86400)
        
        return response
    
    # Display login page
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/webinar')
def webinar():
    """Webinar page - requires valid session"""
    if 'session_token' not in request.cookies:
        return redirect(url_for('index'))
    
    session_token = request.cookies.get('session_token')
    if not verify_session(session_token):
        response = redirect(url_for('index'))
        response.delete_cookie('session_token')
        return response
    
    sessions = load_sessions()
    its_id = sessions[session_token]['its_id']
    
    try:
        with open(WEBINAR_SETTINGS_FILE, 'r') as f:
            webinar_data = json.load(f)
            
            if 'no_webinar' in webinar_data and webinar_data['no_webinar'] == True:
                return render_template_string(NO_WEBINAR_TEMPLATE, its_id=its_id)
            else:
                return render_template_string(WEBINAR_TEMPLATE_IMPROVED, its_id=its_id, **webinar_data)
    except Exception as e:
        print(f"Error loading webinar settings: {e}")
        default_settings = {
            "embed_url": "https://www.youtube.com/embed/GXRL7PcPbOA?autoplay=1&mute=1&controls=0&modestbranding=1&rel=0&showinfo=0&iv_load_policy=3&fs=0&disablekb=1&cc_load_policy=0&playsinline=1&loop=1&enablejsapi=1",
            "webinar_title": "Ashara Mubaraka 1447 - Ratlam Relay",
            "webinar_description": "Welcome to the live relay of Ashara Mubaraka 1447. This stream is authorized for ITS members only. Please do not share this link with others.",
            "webinar_date": "June 18-27, 2025",
            "webinar_time": "7:30 AM - 12:30 PM IST",
            "webinar_speaker": "His Holiness Dr. Syedna Mufaddal Saifuddin (TUS)"
        }
        return render_template_string(WEBINAR_TEMPLATE_IMPROVED, its_id=its_id, **default_settings)

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
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        try:
            with open(ADMIN_FILE, 'r') as f:
                admin_data = json.load(f)
        except:
            return render_template_string(ADMIN_LOGIN_TEMPLATE, error="Admin credentials not configured.")
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if username == admin_data['username'] and password_hash == admin_data['password_hash']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template_string(ADMIN_LOGIN_TEMPLATE, error="Invalid username or password.")
    
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
    """Enhanced admin dashboard route with geolocation features"""
    its_ids = set(load_its_ids())
    sessions = load_sessions()
    geo_settings = load_geo_settings()
    webinar_settings = load_webinar_settings()
    
    # Get active sessions by ITS ID
    sessions_status = set()
    sessions_data = []
    for session_data in sessions.values():
        sessions_status.add(session_data['its_id'])
        # Format session data for display
        login_time = datetime.fromisoformat(session_data['login_time'])
        sessions_data.append({
            'its_id': session_data['its_id'],
            'login_time_formatted': login_time.strftime('%Y-%m-%d %H:%M:%S'),
            'country': session_data.get('country', 'Unknown'),
            'city': session_data.get('city', 'Unknown'),
            'ip_address': session_data.get('ip_address', 'Unknown')
        })
    
    # Prepare stats
    stats = {
        'total_its': len(its_ids),
        'active_sessions': len(sessions),
        'total_sessions': len(sessions),
        'countries_count': len(geo_settings.get('allowed_countries', []))
    }
    
    message = request.args.get('message', '')
    message_type = request.args.get('type', 'success')
    
    return render_template_string(ADMIN_DASHBOARD_TEMPLATE, 
                               stats=stats,
                               its_ids=sorted(its_ids),
                               sessions_status=sessions_status,
                               sessions_data=sessions_data,
                               message=message,
                               message_type=message_type,
                               settings=webinar_settings,
                               geo_settings=geo_settings)

@app.route('/admin/add_its', methods=['POST'])
def admin_add_its():
    """Add a single ITS ID"""
    its_id = request.form.get('single_its', '').strip()
    
    if not its_id or len(its_id) != 8 or not its_id.isdigit():
        return redirect(url_for('admin_dashboard') + '?message=Invalid ITS ID format&type=error')
    
    its_ids = load_its_ids()
    
    if its_id in its_ids:
        return redirect(url_for('admin_dashboard') + '?message=ITS ID already exists&type=error')
    
    its_ids.add(its_id)
    save_its_ids(its_ids)
    
    return redirect(url_for('admin_dashboard') + '?message=ITS ID added successfully&type=success')

@app.route('/admin/add_bulk_its', methods=['POST'])
def admin_add_bulk_its():
    """Add multiple ITS IDs from a textarea"""
    bulk_its = request.form.get('bulk_its', '').strip()
    
    if not bulk_its:
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
        return redirect(url_for('admin_dashboard') + '?message=No valid ITS IDs to add&type=error')
    
    its_ids.update(new_ids)
    save_its_ids(its_ids)
    
    return redirect(url_for('admin_dashboard') + f'?message=Added {len(new_ids)} ITS IDs successfully&type=success')

@app.route('/admin/delete_its', methods=['POST'])
def admin_delete_its():
    """Delete a specific ITS ID"""
    its_id = request.form.get('its_id', '').strip()
    
    if not its_id or len(its_id) != 8 or not its_id.isdigit():
        return redirect(url_for('admin_dashboard') + '?message=Invalid ITS ID format&type=error')
    
    its_ids = load_its_ids()
    
    if its_id not in its_ids:
        return redirect(url_for('admin_dashboard') + '?message=ITS ID not found&type=error')
    
    its_ids.remove(its_id)
    save_its_ids(its_ids)
    
    return redirect(url_for('admin_dashboard') + '?message=ITS ID deleted successfully&type=success')

@app.route('/admin/delete_all_its', methods=['POST'])
def admin_delete_all_its():
    """Delete all ITS IDs"""
    its_ids = load_its_ids()
    
    if not its_ids:
        return redirect(url_for('admin_dashboard') + '?message=No ITS IDs to delete&type=error')
    
    its_ids.clear()
    save_its_ids(its_ids)
    
    return redirect(url_for('admin_dashboard') + '?message=All ITS IDs deleted successfully&type=success')

@app.route('/admin/clear_sessions', methods=['POST'])
def admin_clear_sessions():
    """Clear all active sessions"""
    sessions = load_sessions()
    
    if not sessions:
        return redirect(url_for('admin_dashboard') + '?message=No active sessions to clear&type=error')
    
    sessions.clear()
    save_sessions(sessions)
    
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
        
        return redirect(url_for('admin_dashboard') + '?message=Webinar settings updated successfully&type=success')
    
    except Exception as e:
        return redirect(url_for('admin_dashboard') + f'?message=Error updating settings: {str(e)}&type=error')

@app.route('/admin/update_geo_settings', methods=['POST'])
def admin_update_geo_settings():
    """Update geolocation settings"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        # Load current settings
        geo_settings = load_geo_settings()
        
        # Update settings
        geo_settings['geo_blocking_enabled'] = 'geo_blocking_enabled' in request.form
        geo_settings['blocked_message'] = request.form.get('blocked_message', geo_settings.get('blocked_message', ''))
        
        # Handle allowed countries
        allowed_countries_str = request.form.get('allowed_countries', '')
        if allowed_countries_str:
            geo_settings['allowed_countries'] = [country.strip().upper() for country in allowed_countries_str.split(',') if country.strip()]
        else:
            geo_settings['allowed_countries'] = []
        
        geo_settings['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save settings
        save_geo_settings(geo_settings)
        
        return redirect(url_for('admin_dashboard') + '?message=Geolocation settings updated successfully&type=success')
    
    except Exception as e:
        return redirect(url_for('admin_dashboard') + f'?message=Error updating geo settings: {str(e)}&type=error')

@app.route('/admin')
def admin_index():
    """Redirect to admin login or dashboard"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    # Initialize data files
    init_files()
    # Start Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)