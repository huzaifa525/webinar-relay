"""
Anjuman e Hakimi Najmi Mohallah Ratlam Live Portal

A Flask web application that provides authorized access to live streams
for registered ITS members. Features include user authentication via ITS ID,
session management, and an admin panel for managing authorized users.

Author: Huzaifa
Date: August 9, 2025
Version: 3.0.0 - PostgreSQL Database Integration
"""

from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify, send_file
import os
from datetime import datetime, timedelta
import hashlib
import secrets
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.secret_key = 'Huzaifa53'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bHaJHoNZuiNzjhOMRkiCwlsgvxsHyUxM@yamabiko.proxy.rlwy.net:37305/railway'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Admin credentials (you can modify these)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'Huzaifa5253@'  # Change this in production

# Database Models
class ItsID(db.Model):
    __tablename__ = 'its_ids'
    id = db.Column(db.String(8), primary_key=True)
    added_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<ItsID {self.id}>'

class ActiveSession(db.Model):
    __tablename__ = 'active_sessions'
    token = db.Column(db.String(64), primary_key=True)
    its_id = db.Column(db.String(8), db.ForeignKey('its_ids.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.now)
    last_activity = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Session {self.token} for {self.its_id}>'

class AdminCredential(db.Model):
    __tablename__ = 'admin_credentials'
    username = db.Column(db.String(50), primary_key=True)
    password_hash = db.Column(db.String(64), nullable=False)
    
    def __repr__(self):
        return f'<Admin {self.username}>'

class WebinarSetting(db.Model):
    __tablename__ = 'webinar_settings'
    id = db.Column(db.Integer, primary_key=True)
    youtube_video_id = db.Column(db.String(50), nullable=False)  # Just the YouTube video ID
    webinar_title = db.Column(db.String(200), nullable=False)
    webinar_description = db.Column(db.Text, nullable=True)
    webinar_date = db.Column(db.String(100), nullable=True)
    webinar_time = db.Column(db.String(100), nullable=True)
    webinar_speaker = db.Column(db.String(200), nullable=True)
    no_webinar = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<WebinarSettings {self.webinar_title}>'
        
    @property
    def embed_url(self):
        """Generate the full embed URL from the video ID"""
        return f"https://www.youtube.com/embed/{self.youtube_video_id}?autoplay=1&mute=1&controls=0&modestbranding=1&rel=0&showinfo=0&iv_load_policy=3&fs=0&disablekb=1&cc_load_policy=0&playsinline=1&loop=1&enablejsapi=1"

def init_database():
    """Initialize database tables and default data if they don't exist"""
    # Create tables if they don't exist
    db.create_all()
    
    # Check if admin exists, if not create default admin
    admin = AdminCredential.query.filter_by(username=ADMIN_USERNAME).first()
    if not admin:
        admin_hash = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
        admin = AdminCredential(username=ADMIN_USERNAME, password_hash=admin_hash)
        db.session.add(admin)
        db.session.commit()
    
    # Check if webinar settings exist, if not create default settings
    settings = WebinarSetting.query.first()
    if not settings:
        default_settings = WebinarSetting(
            youtube_video_id="GXRL7PcPbOA",  # Just the YouTube video ID
            webinar_title="Anjuman e Hakimi Najmi Mohallah Ratlam Live Portal",
            webinar_description="Welcome to the live portal of Anjuman e Hakimi Najmi Mohallah Ratlam. This stream is authorized for ITS members only. Please do not share this link with others.",
            webinar_date="August 9-15, 2025",
            webinar_time="7:30 AM - 12:30 PM IST",
            webinar_speaker="His Holiness Dr. Syedna Mufaddal Saifuddin (TUS)",
            no_webinar=False
        )
        db.session.add(default_settings)
        db.session.commit()

def load_its_ids():
    """Load ITS IDs from database"""
    try:
        its_ids = ItsID.query.all()
        return {its_id.id for its_id in its_ids}
    except Exception as e:
        print(f"Error loading ITS IDs: {e}")
        return set()

def save_its_id(its_id):
    """Save a new ITS ID to database"""
    try:
        # Check if ID already exists
        existing = ItsID.query.get(its_id)
        if not existing:
            new_id = ItsID(id=its_id)
            db.session.add(new_id)
            db.session.commit()
        return True
    except Exception as e:
        print(f"Error saving ITS ID: {e}")
        db.session.rollback()
        return False

def delete_its_id(its_id):
    """Delete an ITS ID from database"""
    try:
        existing = ItsID.query.get(its_id)
        if existing:
            db.session.delete(existing)
            db.session.commit()
        return True
    except Exception as e:
        print(f"Error deleting ITS ID: {e}")
        db.session.rollback()
        return False

def load_sessions():
    """Load active sessions from database as a dictionary"""
    try:
        sessions = {}
        active_sessions = ActiveSession.query.all()
        
        for session in active_sessions:
            sessions[session.token] = {
                'its_id': session.its_id,
                'login_time': session.login_time.isoformat(),
                'last_activity': session.last_activity.isoformat()
            }
        return sessions
    except Exception as e:
        print(f"Error loading sessions: {e}")
        return {}

def save_session(token, its_id, login_time, last_activity):
    """Save a session to database"""
    try:
        # Check if session already exists
        existing = ActiveSession.query.get(token)
        if existing:
            existing.last_activity = last_activity
            db.session.commit()
        else:
            new_session = ActiveSession(
                token=token,
                its_id=its_id,
                login_time=login_time,
                last_activity=last_activity
            )
            db.session.add(new_session)
            db.session.commit()
        return True
    except Exception as e:
        print(f"Error saving session: {e}")
        db.session.rollback()
        return False

def delete_session(token):
    """Delete a session from database"""
    try:
        session = ActiveSession.query.get(token)
        if session:
            db.session.delete(session)
            db.session.commit()
        return True
    except Exception as e:
        print(f"Error deleting session: {e}")
        db.session.rollback()
        return False

def cleanup_expired_sessions():
    """Remove expired or inactive sessions"""
    current_time = datetime.now()
    
    try:
        # Find sessions expired by total time (24 hours)
        expired_by_time = ActiveSession.query.filter(
            current_time - ActiveSession.login_time > timedelta(hours=24)
        ).all()
        
        # Find sessions expired by inactivity (30 minutes)
        expired_by_inactivity = ActiveSession.query.filter(
            current_time - ActiveSession.last_activity > timedelta(minutes=30)
        ).all()
        
        # Combine and delete all expired sessions
        expired_sessions = set(expired_by_time + expired_by_inactivity)
        
        for session in expired_sessions:
            db.session.delete(session)
            
        db.session.commit()
    except Exception as e:
        print(f"Error cleaning up sessions: {e}")
        db.session.rollback()

def is_its_logged_in(its_id):
    """Check if ITS ID already has an active session"""
    cleanup_expired_sessions()
    
    # Check if any active session exists for this ITS ID
    session_exists = ActiveSession.query.filter_by(its_id=str(its_id)).first() is not None
    return session_exists

def create_session(its_id):
    """Create a new session for ITS ID"""
    session_token = secrets.token_urlsafe(32)
    now = datetime.now()
    
    try:
        new_session = ActiveSession(
            token=session_token,
            its_id=str(its_id),
            login_time=now,
            last_activity=now
        )
        db.session.add(new_session)
        db.session.commit()
        return session_token
    except Exception as e:
        print(f"Error creating session: {e}")
        db.session.rollback()
        return None

def verify_session(session_token):
    """Verify if session token is valid and update last activity"""
    cleanup_expired_sessions()
    
    try:
        session = ActiveSession.query.get(session_token)
        if session:
            # Update last activity time
            session.last_activity = datetime.now()
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"Error verifying session: {e}")
        return False

def logout_session(session_token):
    """Remove session"""
    try:
        session = ActiveSession.query.get(session_token)
        if session:
            db.session.delete(session)
            db.session.commit()
        return True
    except Exception as e:
        print(f"Error logging out session: {e}")
        db.session.rollback()
        return False

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def load_webinar_settings():
    """Load webinar settings from database"""
    try:
        settings = WebinarSetting.query.first()
        if settings:
            return {
                "embed_url": settings.embed_url,  # Use the computed property for backward compatibility
                "youtube_video_id": settings.youtube_video_id,
                "webinar_title": settings.webinar_title,
                "webinar_description": settings.webinar_description,
                "webinar_date": settings.webinar_date,
                "webinar_time": settings.webinar_time,
                "webinar_speaker": settings.webinar_speaker,
                "no_webinar": settings.no_webinar
            }
        else:
            # Return default settings if nothing in database
            default_video_id = "GXRL7PcPbOA"
            return {
                "embed_url": f"https://www.youtube.com/embed/{default_video_id}?autoplay=1&mute=1&controls=0&modestbranding=1&rel=0&showinfo=0&iv_load_policy=3&fs=0&disablekb=1&cc_load_policy=0&playsinline=1&loop=1&enablejsapi=1",
                "youtube_video_id": default_video_id,
                "webinar_title": "Ashara Mubaraka 1447 - Ratlam Relay",
                "webinar_description": "Welcome to the live relay of Ashara Mubaraka 1447. This stream is authorized for ITS members only. Please do not share this link with others.",
                "webinar_date": "June 18-27, 2025",
                "webinar_time": "7:30 AM - 12:30 PM IST",
                "webinar_speaker": "His Holiness Dr. Syedna Mufaddal Saifuddin (TUS)",
                "no_webinar": False
            }
    except Exception as e:
        print(f"Error loading webinar settings: {e}")
        # Return default settings if there's an error
        default_video_id = "GXRL7PcPbOA"
        return {
            "embed_url": f"https://www.youtube.com/embed/{default_video_id}?autoplay=1&mute=1&controls=0&modestbranding=1&rel=0&showinfo=0&iv_load_policy=3&fs=0&disablekb=1&cc_load_policy=0&playsinline=1&loop=1&enablejsapi=1",
            "youtube_video_id": default_video_id,
            "webinar_title": "Ashara Mubaraka 1447 - Ratlam Relay",
            "webinar_description": "Welcome to the live relay of Ashara Mubaraka 1447. This stream is authorized for ITS members only. Please do not share this link with others.",
            "webinar_date": "June 18-27, 2025",
            "webinar_time": "7:30 AM - 12:30 PM IST",
            "webinar_speaker": "His Holiness Dr. Syedna Mufaddal Saifuddin (TUS)",
            "no_webinar": False
        }

def extract_youtube_id(url):
    """Extract YouTube video ID from various URL formats"""
    if not url:
        return ""
        
    # Check if it's already just a video ID (no slashes, simple string)
    if '/' not in url and '?' not in url and len(url) > 8 and len(url) < 20:
        return url
        
    # Extract from standard or embed URLs
    import re
    patterns = [
        r'(?:youtube\.com\/embed\/|youtube\.com\/watch\?v=|youtu\.be\/)([^?&\/]+)',  # Standard formats
        r'([^?&\/]{11})'  # Fallback for ID-only or other formats
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no match found, return empty string
    return ""

def save_webinar_settings(settings):
    """Save webinar settings to database"""
    try:
        webinar_settings = WebinarSetting.query.first()
        
        # If settings contains embed_url, extract the video ID from it
        video_id = ""
        if "embed_url" in settings:
            video_id = extract_youtube_id(settings["embed_url"])
        elif "youtube_video_id" in settings:
            video_id = settings["youtube_video_id"]
            
        # If settings exists, update it, otherwise create new
        if webinar_settings:
            webinar_settings.youtube_video_id = video_id
            webinar_settings.webinar_title = settings["webinar_title"]
            webinar_settings.webinar_description = settings["webinar_description"]
            webinar_settings.webinar_date = settings["webinar_date"]
            webinar_settings.webinar_time = settings["webinar_time"]
            webinar_settings.webinar_speaker = settings["webinar_speaker"]
            webinar_settings.no_webinar = settings["no_webinar"]
        else:
            webinar_settings = WebinarSetting(
                youtube_video_id=video_id,
                webinar_title=settings["webinar_title"],
                webinar_description=settings["webinar_description"],
                webinar_date=settings["webinar_date"],
                webinar_time=settings["webinar_time"],
                webinar_speaker=settings["webinar_speaker"],
                no_webinar=settings["no_webinar"]
            )
            db.session.add(webinar_settings)
            
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error saving webinar settings: {e}")
        db.session.rollback()
        return False

# Login page template (keeping original)
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anjuman e Hakimi Najmi Mohallah Ratlam Live Portal - Login</title>
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
            background: url('https://i.ibb.co/JWTvVh2f/background-1.png') center/cover no-repeat fixed;
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
            width: 80px;
            height: 80px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            box-shadow: var(--shadow-brand);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .logo-icon img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }

        .logo-text {
            text-align: left;
        }

        .logo-title {
            font-size: 1.3rem;
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
        }
            
        .footer {
            text-align: center;
            margin-top: 2rem;
            font-size: 0.85rem;
            color: var(--text-tertiary);
        }
            
        .footer .heart {
            color: #ff4d4d;
            display: inline-block;
            animation: heartbeat 1.5s ease infinite;
        }
            
        @keyframes heartbeat {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }
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
                <div class="logo-icon">
                    <img src="https://i.ibb.co/nqfBrMmC/logo-without-back.png" alt="Anjuman e Hakimi Logo">
                </div>
                <div class="logo-text">
                    <div class="logo-title">Anjuman e Hakimi</div>
                    <div class="logo-subtitle">Najmi Mohallah Ratlam</div>
                </div>
            </div>
            <h1 class="login-title">Live Portal</h1>
            <p class="login-subtitle">Enter your ITS ID for access</p>
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
        
        <div class="footer">
            Developed with <span class="heart">♥</span> by Huzefa Nalkheda wala
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

# Improved Webinar Template with better mobile support and fixed fullscreen
WEBINAR_TEMPLATE_IMPROVED = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>{{ webinar_title }} - Anjuman e Hakimi Najmi Mohallah Ratlam Live Portal</title>
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
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
            -webkit-tap-highlight-color: transparent;
        }

        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: url('https://i.ibb.co/JWTvVh2f/background-1.png') center/cover no-repeat fixed;
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            position: relative;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* Background Effects */
        .noise-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            opacity: 0.1;
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
            min-height: 70px;
        }

        .logo-wrapper {
            display: flex;
            align-items: center;
            gap: 0.75rem;
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
            font-size: 1.6rem;
            box-shadow: var(--shadow-brand);
            border: 1px solid rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
            flex-shrink: 0;
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
            background: var(--gold-overlay);
            padding: 0.5rem 0.75rem;
            border-radius: var(--radius-full);
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--accent-gold);
            border: 1px solid rgba(212, 175, 55, 0.3);
            white-space: nowrap;
        }

        .logout-btn {
            background: var(--surface-2);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: var(--radius-full);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            transition: var(--transition-normal);
            border: 1px solid rgba(255, 255, 255, 0.1);
            white-space: nowrap;
        }

        .logout-btn:hover {
            background: var(--surface-3);
            transform: translateY(-1px);
        }
        
        .logout-dropdown {
            position: relative;
            display: inline-block;
        }
        
        .dropdown-content {
            display: none;
            position: absolute;
            right: 0;
            top: calc(100% + 5px);
            min-width: 220px;
            background: var(--bg-surface-light);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-md);
            z-index: 100;
            border: 1px solid rgba(212, 175, 55, 0.1);
            overflow: hidden;
        }
        
        .dropdown-content a {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1rem;
            color: var(--text-primary);
            text-decoration: none;
            font-size: 0.9rem;
            transition: var(--transition-fast);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .dropdown-content a:last-child {
            border-bottom: none;
        }
        
        .dropdown-content a:hover {
            background: var(--surface-2);
        }
        
        .dropdown-content a i {
            color: var(--accent-gold);
            font-size: 0.9rem;
            width: 18px;
            text-align: center;
        }

        /* Container */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 1.5rem 1rem;
            position: relative;
            z-index: 10;
        }

        /* Webinar Info */
        .webinar-info {
            text-align: center;
            margin-bottom: 1.5rem;
            padding: 1rem;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--gold-overlay);
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
            background: var(--surface-1);
            border-radius: var(--radius-lg);
            padding: 1rem 1.5rem;
            border: 1px solid rgba(212, 175, 55, 0.1);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
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
            box-shadow: var(--shadow-brand);
            border: 2px solid rgba(212, 175, 55, 0.3);
            position: relative;
            overflow: hidden;
            flex-shrink: 0;
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

        /* Video Container */
        .video-container {
            position: relative;
            width: 100%;
            max-width: 1200px;
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
            opacity: 0.6;
        }

        .video-container.fullscreen {
            max-width: none;
            border-radius: 0;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 9999;
        }

        .video-container.fullscreen::before {
            border-radius: 0;
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

        .video-container.fullscreen .video-wrapper {
            padding-bottom: 0;
            height: 100vh;
        }

        .video-frame {
            position: absolute;
            top: -50px;
            left: -50px;
            width: calc(100% + 100px);
            height: calc(100% + 100px);
            border: none;
        }

        .video-container.fullscreen .video-frame {
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }

        .video-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(0deg, rgba(9, 13, 27, 0.4) 0%, transparent 15%, transparent 85%, rgba(9, 13, 27, 0.4) 100%);
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
            width: 80px;
            height: 80px;
            background: rgba(9, 13, 27, 0.9);
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
            border-left: 24px solid white;
            border-top: 16px solid transparent;
            border-bottom: 16px solid transparent;
            margin-left: 8px;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
            z-index: 2;
        }

        .control-group {
            position: absolute;
            bottom: 20px;
            left: 20px;
            right: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 15;
            pointer-events: none;
        }

        .control-section {
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(9, 13, 27, 0.9);
            padding: 12px 16px;
            border-radius: var(--radius-full);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(212, 175, 55, 0.2);
            box-shadow: var(--shadow-md);
            transition: var(--transition-normal);
            overflow: hidden;
            pointer-events: auto;
        }

        .control-section::before {
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

        .control-section:hover {
            background: rgba(9, 13, 27, 0.95);
            box-shadow: var(--shadow-lg), 0 5px 20px rgba(212, 175, 55, 0.1);
            border-color: var(--accent-gold);
        }

        .control-section:hover::before {
            opacity: 1;
        }

        .control-button {
            width: 44px;
            height: 44px;
            background: none;
            border: none;
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            border-radius: var(--radius-full);
            transition: var(--transition-normal);
            position: relative;
            z-index: 2;
        }

        .control-button:hover {
            background: rgba(212, 175, 55, 0.15);
            color: var(--accent-gold);
            transform: scale(1.05);
        }

        .control-button:active {
            transform: scale(0.95);
        }

        /* Font Awesome icon styling */
        .control-button i {
            font-size: 1.1rem;
            transition: var(--transition-normal);
        }

        .control-button:hover i {
            transform: scale(1.1);
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
            width: 60px;
            height: 60px;
            margin-bottom: 15px;
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
            font-size: 0.9rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            animation: pulse 1.5s infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Mobile Responsiveness */
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

            .container {
                padding: 1rem 0.75rem;
            }

            .webinar-info {
                padding: 0.75rem;
                margin-bottom: 1rem;
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

            .speaker-avatar {
                width: 45px;
                height: 45px;
                font-size: 1.2rem;
            }

            .control-group {
                bottom: 15px;
                left: 15px;
                right: 15px;
                flex-direction: column;
                gap: 10px;
            }

            .control-section {
                padding: 10px 14px;
                width: 100%;
                justify-content: center;
            }

            .control-button {
                width: 40px;
                height: 40px;
                font-size: 1rem;
            }

            .custom-play-button {
                width: 70px;
                height: 70px;
            }

            .play-icon {
                border-left: 20px solid white;
                border-top: 13px solid transparent;
                border-bottom: 13px solid transparent;
                margin-left: 6px;
            }
        }

        @media (max-width: 480px) {
            .header {
                flex-direction: column;
                padding: 0.75rem 1rem 1rem;
                gap: 0.75rem;
            }

            .user-info {
                order: -1;
                width: 100%;
                justify-content: center;
            }

            .logo-title {
                font-size: 1rem;
            }

            .logo-icon {
                width: 36px;
                height: 36px;
                font-size: 1.2rem;
            }

            .speaker-info {
                padding: 0.75rem;
                gap: 0.5rem;
            }

            .speaker-avatar {
                width: 40px;
                height: 40px;
                font-size: 1.1rem;
            }

            .speaker-name {
                font-size: 0.9rem;
            }

            .speaker-title {
                font-size: 0.7rem;
            }

            .control-section {
                padding: 8px 12px;
            }

            .control-button {
                width: 36px;
                height: 36px;
                font-size: 0.9rem;
            }

            .custom-play-button {
                width: 60px;
                height: 60px;
            }

            .play-icon {
                border-left: 16px solid white;
                border-top: 11px solid transparent;
                border-bottom: 11px solid transparent;
                margin-left: 4px;
            }
        }

        /* Landscape mode for mobile */
        @media (max-width: 768px) and (orientation: landscape) {
            .header {
                padding: 0.5rem 1rem;
            }

            .container {
                padding: 0.5rem;
            }

            .webinar-info {
                display: none;
            }

            .video-container {
                max-width: none;
                border-radius: var(--radius-sm);
            }

            .control-group {
                bottom: 10px;
                left: 10px;
                right: 10px;
            }
        }

        /* Fullscreen specific styles */
        .video-container.fullscreen .control-group {
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
        }

        @media (max-width: 768px) {
            .video-container.fullscreen .control-group {
                bottom: 15px;
                left: 15px;
                right: 15px;
            }
        }

        /* Hide scrollbars in fullscreen */
        .video-container.fullscreen {
            -ms-overflow-style: none;
            scrollbar-width: none;
        }

        .video-container.fullscreen::-webkit-scrollbar {
            display: none;
        }
    </style>
</head>
<body>
    <div class="noise-bg"></div>
    <div class="gradient-bg"></div>

    <header class="header" id="header">
        <div class="logo-wrapper">
            <div class="logo-icon">
                <img src="https://i.ibb.co/nqfBrMmC/logo-without-back.png" alt="Anjuman e Hakimi Logo">
            </div>
            <div class="logo-text">
                <div class="logo-title">Anjuman e Hakimi</div>
                <div class="logo-subtitle">Najmi Mohallah Ratlam Live Portal</div>
            </div>
        </div>
        <div class="user-info">
            <div class="user-id">ITS ID: {{ its_id }}</div>
            <div class="logout-dropdown">
                <a href="javascript:void(0)" class="logout-btn" onclick="toggleDropdown()">Session <i class="fas fa-angle-down"></i></a>
                <div class="dropdown-content" id="sessionDropdown">
                    <a href="{{ url_for('logout') }}"><i class="fas fa-sign-out-alt"></i> Logout this device</a>
                    <a href="{{ url_for('force_logout') }}" onclick="return confirm('This will log you out from ALL devices. Continue?');"><i class="fas fa-power-off"></i> Logout from all devices</a>
                </div>
            </div>
        </div>
    </header>

    <div class="container" id="container">
        <div class="webinar-info" id="webinarInfo">
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

        <div class="video-container" id="videoContainer">
            <div class="video-wrapper">
                <div class="loading-overlay" id="loadingOverlay">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Connecting to live stream...</div>
                </div>
                <iframe 
                    class="video-frame" 
                    id="videoFrame"
                    src="{{ embed_url }}"
                    allow="autoplay; encrypted-media; fullscreen"
                    allowfullscreen
                    playsinline>
                </iframe>
                <div class="video-overlay"></div>
                <div class="youtube-brand-blocker"></div>
                <div class="video-click-layer" id="videoClickLayer"></div>
                <div class="custom-play-button" id="playButton">
                    <div class="play-icon"></div>
                </div>
                <div class="control-group">
                    <div class="control-section">
                        <button class="control-button" id="volumeButton" title="Toggle Volume">
                            <i class="fas fa-volume-mute" id="volumeIcon"></i>
                        </button>
                    </div>
                    <div class="control-section">
                        <button class="control-button" id="fullscreenButton" title="Toggle Fullscreen">
                            <i class="fas fa-expand" id="fullscreenIcon"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Mobile optimization variables
        let isFullscreen = false;
        let isPlaying = true;
        let isMuted = true;
        let initialOrientation = window.orientation;

        // Wait for DOM to be fully loaded
        document.addEventListener('DOMContentLoaded', function() {
            // DOM elements
            const videoContainer = document.getElementById('videoContainer');
            const videoFrame = document.getElementById('videoFrame');
            const loadingOverlay = document.getElementById('loadingOverlay');
            const playButton = document.getElementById('playButton');
            const videoClickLayer = document.getElementById('videoClickLayer');
            const volumeButton = document.getElementById('volumeButton');
            const volumeIcon = document.getElementById('volumeIcon');
            const fullscreenButton = document.getElementById('fullscreenButton');
            const fullscreenIcon = document.getElementById('fullscreenIcon');
            const header = document.getElementById('header');
            const container = document.getElementById('container');
            const webinarInfo = document.getElementById('webinarInfo');

            // Debug logging
            console.log('Elements loaded:', {
                videoContainer: !!videoContainer,
                volumeButton: !!volumeButton,
                fullscreenButton: !!fullscreenButton,
                volumeIcon: !!volumeIcon,
                fullscreenIcon: !!fullscreenIcon
            });

            // Hide loading overlay after iframe loads
            if (videoFrame) {
                videoFrame.addEventListener('load', function() {
                    setTimeout(() => {
                        if (loadingOverlay) {
                            loadingOverlay.style.opacity = '0';
                            setTimeout(() => {
                                loadingOverlay.style.display = 'none';
                            }, 500);
                        }
                    }, 1000);
                });
            }

            // Video click to pause/play
            if (videoClickLayer) {
                videoClickLayer.addEventListener('click', function() {
                    console.log('Video clicked, isPlaying:', isPlaying);
                    if (isPlaying) {
                        // Pause video and show play button
                        if (playButton) playButton.style.display = 'flex';
                        isPlaying = false;
                        if (videoFrame) {
                            videoFrame.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
                        }
                    } else {
                        // Play video and hide play button
                        if (playButton) playButton.style.display = 'none';
                        isPlaying = true;
                        if (videoFrame) {
                            videoFrame.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}', '*');
                        }
                    }
                });
            }

            // Play button click
            if (playButton) {
                playButton.addEventListener('click', function(e) {
                    e.stopPropagation();
                    console.log('Play button clicked');
                    playButton.style.display = 'none';
                    isPlaying = true;
                    if (videoFrame) {
                        videoFrame.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}', '*');
                    }
                });
            }

            // Volume toggle
            if (volumeButton && volumeIcon) {
                volumeButton.addEventListener('click', function(e) {
                    e.stopPropagation();
                    console.log('Volume button clicked, isMuted:', isMuted);
                    
                    if (isMuted) {
                        volumeIcon.className = 'fas fa-volume-up';
                        volumeButton.title = 'Mute Volume';
                        isMuted = false;
                        if (videoFrame) {
                            videoFrame.contentWindow.postMessage('{"event":"command","func":"unMute","args":""}', '*');
                        }
                        console.log('Volume unmuted');
                    } else {
                        volumeIcon.className = 'fas fa-volume-mute';
                        volumeButton.title = 'Unmute Volume';
                        isMuted = true;
                        if (videoFrame) {
                            videoFrame.contentWindow.postMessage('{"event":"command","func":"mute","args":""}', '*');
                        }
                        console.log('Volume muted');
                    }
                });

                // Add visual feedback for touch
                volumeButton.addEventListener('touchstart', function() {
                    this.style.transform = 'scale(0.95)';
                }, { passive: true });
                
                volumeButton.addEventListener('touchend', function() {
                    this.style.transform = '';
                }, { passive: true });
            }

            // Improved fullscreen functionality
            function enterFullscreen() {
                console.log('Entering fullscreen');
                const requestFullscreen = videoContainer.requestFullscreen || 
                                        videoContainer.webkitRequestFullscreen || 
                                        videoContainer.mozRequestFullScreen || 
                                        videoContainer.msRequestFullscreen;
                
                if (requestFullscreen) {
                    requestFullscreen.call(videoContainer).then(() => {
                        console.log('Fullscreen entered successfully');
                        isFullscreen = true;
                        videoContainer.classList.add('fullscreen');
                        if (fullscreenIcon) fullscreenIcon.className = 'fas fa-compress';
                        if (fullscreenButton) fullscreenButton.title = 'Exit Fullscreen';
                        
                        // Hide header and webinar info in fullscreen
                        if (header) header.style.display = 'none';
                        if (webinarInfo) webinarInfo.style.display = 'none';
                        
                        // Force landscape on mobile if portrait
                        if (window.innerHeight > window.innerWidth && screen.orientation && screen.orientation.lock) {
                            screen.orientation.lock('landscape').catch(() => {
                                console.log('Could not lock orientation to landscape');
                            });
                        }
                    }).catch((err) => {
                        console.log('Fullscreen request failed:', err);
                    });
                } else {
                    console.log('Fullscreen API not supported');
                }
            }

            function exitFullscreen() {
                console.log('Exiting fullscreen');
                const exitFullscreen = document.exitFullscreen || 
                                      document.webkitExitFullscreen || 
                                      document.mozCancelFullScreen || 
                                      document.msExitFullscreen;
                
                if (exitFullscreen) {
                    exitFullscreen.call(document).then(() => {
                        console.log('Fullscreen exited successfully');
                        isFullscreen = false;
                        videoContainer.classList.remove('fullscreen');
                        if (fullscreenIcon) fullscreenIcon.className = 'fas fa-expand';
                        if (fullscreenButton) fullscreenButton.title = 'Enter Fullscreen';
                        
                        // Show header and webinar info
                        if (header) header.style.display = 'flex';
                        if (webinarInfo) webinarInfo.style.display = 'block';
                        
                        // Unlock orientation
                        if (screen.orientation && screen.orientation.unlock) {
                            screen.orientation.unlock();
                        }
                    }).catch((err) => {
                        console.log('Exit fullscreen failed:', err);
                    });
                } else {
                    console.log('Exit fullscreen API not supported');
                }
            }

            // Fullscreen toggle
            if (fullscreenButton) {
                fullscreenButton.addEventListener('click', function(e) {
                    e.stopPropagation();
                    console.log('Fullscreen button clicked, isFullscreen:', isFullscreen);
                    
                    if (!isFullscreen) {
                        enterFullscreen();
                    } else {
                        exitFullscreen();
                    }
                });

                // Add visual feedback for touch
                fullscreenButton.addEventListener('touchstart', function() {
                    this.style.transform = 'scale(0.95)';
                }, { passive: true });
                
                fullscreenButton.addEventListener('touchend', function() {
                    this.style.transform = '';
                }, { passive: true });
            }

            // Listen for fullscreen change events
            const fullscreenEvents = [
                'fullscreenchange',
                'webkitfullscreenchange', 
                'mozfullscreenchange',
                'MSFullscreenChange'
            ];

            fullscreenEvents.forEach(event => {
                document.addEventListener(event, handleFullscreenChange);
            });

            function handleFullscreenChange() {
                const fullscreenElement = document.fullscreenElement || 
                                        document.webkitFullscreenElement || 
                                        document.mozFullScreenElement || 
                                        document.msFullscreenElement;
                
                console.log('Fullscreen change detected:', !!fullscreenElement);
                
                if (fullscreenElement === videoContainer) {
                    // Entered fullscreen
                    isFullscreen = true;
                    videoContainer.classList.add('fullscreen');
                    if (fullscreenIcon) fullscreenIcon.className = 'fas fa-compress';
                    if (fullscreenButton) fullscreenButton.title = 'Exit Fullscreen';
                    if (header) header.style.display = 'none';
                    if (webinarInfo) webinarInfo.style.display = 'none';
                } else {
                    // Exited fullscreen
                    isFullscreen = false;
                    videoContainer.classList.remove('fullscreen');
                    if (fullscreenIcon) fullscreenIcon.className = 'fas fa-expand';
                    if (fullscreenButton) fullscreenButton.title = 'Enter Fullscreen';
                    if (header) header.style.display = 'flex';
                    if (webinarInfo) webinarInfo.style.display = 'block';
                    
                    // Unlock orientation
                    if (screen.orientation && screen.orientation.unlock) {
                        screen.orientation.unlock();
                    }
                }
            }

            // Handle orientation changes
            window.addEventListener('orientationchange', function() {
                setTimeout(() => {
                    // If in fullscreen and changed to portrait, suggest landscape
                    if (isFullscreen && window.innerHeight > window.innerWidth) {
                        if (screen.orientation && screen.orientation.lock) {
                            screen.orientation.lock('landscape').catch(() => {
                                console.log('Could not lock to landscape after orientation change');
                            });
                        }
                    }
                }, 100);
            });

            // Handle escape key for fullscreen exit
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && isFullscreen) {
                    exitFullscreen();
                }
                
                // Disable developer tools shortcuts
                if (e.key === 'F12' || 
                    (e.ctrlKey && e.shiftKey && e.key === 'I') ||
                    (e.ctrlKey && e.shiftKey && e.key === 'J') ||
                    (e.ctrlKey && e.key === 'U')) {
                    e.preventDefault();
                    return false;
                }
            });

            // Initialize proper iframe communication
            window.addEventListener('message', function(event) {
                if (event.origin !== 'https://www.youtube.com') return;
                
                try {
                    const data = JSON.parse(event.data);
                    if (data.event === 'video-progress') {
                        // Handle video progress if needed
                    }
                } catch (e) {
                    // Invalid JSON, ignore
                }
            });

            // Add smooth transitions for better UX
            if (videoContainer) {
                videoContainer.style.transition = 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)';
            }
            
            console.log('Ratlam Relay Centre - Video player initialized successfully');
        });

        // Prevent zoom on double tap for better mobile experience
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function(event) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);

        // Disable right-click
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
        });

        // Prevent scrolling when in fullscreen
        function preventScroll(e) {
            if (isFullscreen) {
                e.preventDefault();
            }
        }

        document.addEventListener('touchmove', preventScroll, { passive: false });
        document.addEventListener('wheel', preventScroll, { passive: false });

        // Performance optimization: Throttle resize events
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                // Handle any resize-specific logic here if needed
                if (isFullscreen) {
                    // Ensure fullscreen container maintains proper dimensions
                    const videoContainer = document.getElementById('videoContainer');
                    if (videoContainer) {
                        videoContainer.style.width = '100vw';
                        videoContainer.style.height = '100vh';
                    }
                }
            }, 150);
        });
    </script>
    
    <div style="position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(9, 13, 27, 0.8); backdrop-filter: blur(10px); padding: 10px; text-align: center; font-size: 0.85rem; color: rgba(255, 255, 255, 0.65); border-top: 1px solid rgba(212, 175, 55, 0.2);">
        Developed with <span style="color: #ff4d4d; display: inline-block; animation: heartbeat 1.5s ease infinite;">♥</span> by Huzefa Nalkheda wala
    </div>
    
    <style>
        @keyframes heartbeat {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }
    </style>
    
    <script>
        // Session management dropdown toggle
        function toggleDropdown() {
            const dropdown = document.getElementById('sessionDropdown');
            if (dropdown.style.display === 'block') {
                dropdown.style.display = 'none';
            } else {
                dropdown.style.display = 'block';
            }
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(event) {
            const dropdown = document.getElementById('sessionDropdown');
            const logoutBtn = document.querySelector('.logout-btn');
            
            if (!event.target.closest('.logout-dropdown') && dropdown.style.display === 'block') {
                dropdown.style.display = 'none';
            }
        });
        
        // Auto logout after inactivity (30 minutes)
        let inactivityTimer;
        const INACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 minutes in milliseconds
        
        function resetInactivityTimer() {
            clearTimeout(inactivityTimer);
            inactivityTimer = setTimeout(function() {
                alert("You've been inactive for 30 minutes. You will be logged out for security reasons.");
                window.location.href = "{{ url_for('logout') }}";
            }, INACTIVITY_TIMEOUT);
        }
        
        // Reset timer on user activity
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(function(event) {
            document.addEventListener(event, resetInactivityTimer, true);
        });
        
        // Start the timer
        resetInactivityTimer();
    </script>
</body>
</html>
'''

# No Webinar Template (keeping existing)
NO_WEBINAR_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anjuman e Hakimi Najmi Mohallah Ratlam Live Portal - No Stream Available</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --brand-primary: #0a3da0;
            --brand-primary-light: #1c54c5;
            --accent-gold: #d4af37;
            --bg-dark: #090d1b;
            --bg-surface: #0f1428;
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.85);
            --gradient-brand: linear-gradient(135deg, var(--brand-primary), var(--brand-primary-light));
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
            background: url('https://i.ibb.co/JWTvVh2f/background-1.png') center/cover no-repeat fixed;
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
            <div class="logo-icon">
                <img src="https://i.ibb.co/nqfBrMmC/logo-without-back.png" alt="Anjuman e Hakimi Logo">
            </div>
            <div class="logo-text">
                <h1>Anjuman e Hakimi</h1>
                <p>Najmi Mohallah Ratlam</p>
            </div>
        </div>
        <div class="user-info">
            <div class="its-id-badge">ITS ID: {{ its_id }}</div>
            <div class="logout-dropdown">
                <a href="javascript:void(0)" class="logout-btn" onclick="toggleDropdown()">Session <i class="fas fa-angle-down"></i></a>
                <div class="dropdown-content" id="sessionDropdown">
                    <a href="{{ url_for('logout') }}"><i class="fas fa-sign-out-alt"></i> Logout this device</a>
                    <a href="{{ url_for('force_logout') }}" onclick="return confirm('This will log you out from ALL devices. Continue?');"><i class="fas fa-power-off"></i> Logout from all devices</a>
                </div>
            </div>
        </div>
    </div>

    <div class="main-content">
        <div class="no-webinar-message">
            <div class="status-badge">Status: Offline</div>
            <h1 class="no-webinar-title">No Stream Available</h1>
            <p class="no-webinar-description">
                There is currently no live stream scheduled at this time. The stream is temporarily offline. 
                Please check back later for updates. Thank you for your patience.
            </p>
        </div>
    </div>

    <div style="position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(9, 13, 27, 0.8); backdrop-filter: blur(10px); padding: 10px; text-align: center; font-size: 0.85rem; color: rgba(255, 255, 255, 0.65); border-top: 1px solid rgba(212, 175, 55, 0.2);">
        Developed with <span style="color: #ff4d4d; display: inline-block; animation: heartbeat 1.5s ease infinite;">♥</span> by Huzefa Nalkheda wala
    </div>
    
    <style>
        @keyframes heartbeat {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }
        
        /* Session dropdown styles */
        .logout-dropdown {
            position: relative;
            display: inline-block;
        }
        
        .dropdown-content {
            display: none;
            position: absolute;
            right: 0;
            top: calc(100% + 5px);
            min-width: 220px;
            background: var(--bg-surface-light, #1a233f);
            border-radius: var(--radius-md, 10px);
            box-shadow: 0 8px 28px rgba(0, 0, 0, 0.2);
            z-index: 100;
            border: 1px solid rgba(212, 175, 55, 0.1);
            overflow: hidden;
        }
        
        .dropdown-content a {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1rem;
            color: white;
            text-decoration: none;
            font-size: 0.9rem;
            transition: all 0.2s ease;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .dropdown-content a:last-child {
            border-bottom: none;
        }
        
        .dropdown-content a:hover {
            background: rgba(255, 255, 255, 0.07);
        }
        
        .dropdown-content a i {
            color: #d4af37;
            font-size: 0.9rem;
            width: 18px;
            text-align: center;
        }
    </style>

    <script>
        // Session management dropdown toggle
        function toggleDropdown() {
            const dropdown = document.getElementById('sessionDropdown');
            if (dropdown.style.display === 'block') {
                dropdown.style.display = 'none';
            } else {
                dropdown.style.display = 'block';
            }
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(event) {
            const dropdown = document.getElementById('sessionDropdown');
            
            if (!event.target.closest('.logout-dropdown') && dropdown && dropdown.style.display === 'block') {
                dropdown.style.display = 'none';
            }
        });
        
        // Auto logout after inactivity (30 minutes)
        let inactivityTimer;
        const INACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 minutes in milliseconds
        
        function resetInactivityTimer() {
            clearTimeout(inactivityTimer);
            inactivityTimer = setTimeout(function() {
                alert("You've been inactive for 30 minutes. You will be logged out for security reasons.");
                window.location.href = "{{ url_for('logout') }}";
            }, INACTIVITY_TIMEOUT);
        }
        
        // Reset timer on user activity
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(function(event) {
            document.addEventListener(event, resetInactivityTimer, true);
        });
        
        // Start the timer
        resetInactivityTimer();
        
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

# Keep all existing admin templates the same...
ADMIN_LOGIN_TEMPLATE = '''<!-- Admin login template remains the same -->'''
ADMIN_DASHBOARD_TEMPLATE = '''<!-- Admin dashboard template remains the same -->'''

# API Health Check route
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
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
    init_database()
    
    if 'session_token' in request.cookies:
        session_token = request.cookies.get('session_token')
        if verify_session(session_token):
            return redirect(url_for('webinar'))
    
    if request.method == 'POST':
        its_id = request.form.get('its_id', '').strip()
        
        if not its_id or len(its_id) != 8 or not its_id.isdigit():
            return render_template_string(LOGIN_TEMPLATE, error="Please enter a valid 8-digit ITS ID.")
        
        its_ids = load_its_ids()
        if its_id not in its_ids:
            return render_template_string(LOGIN_TEMPLATE, error="ITS ID not authorized. Please contact the administrator.")
        
        if is_its_logged_in(its_id):
            return render_template_string(LOGIN_TEMPLATE, error="This ITS ID is already logged in on another device.")
        
        session_token = create_session(its_id)
        if not session_token:
            return render_template_string(LOGIN_TEMPLATE, error="An error occurred during login. Please try again.")
        
        response = redirect(url_for('webinar'))
        response.set_cookie('session_token', session_token, httponly=True, max_age=86400)
        
        return response
    
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
    
    # Get session from database
    try:
        session = ActiveSession.query.get(session_token)
        if not session:
            response = redirect(url_for('index'))
            response.delete_cookie('session_token')
            return response
        
        its_id = session.its_id
        webinar_data = load_webinar_settings()
        
        if webinar_data.get('no_webinar', False):
            return render_template_string(NO_WEBINAR_TEMPLATE, its_id=its_id, session_token=session_token)
        else:
            return render_template_string(WEBINAR_TEMPLATE_IMPROVED, its_id=its_id, session_token=session_token, **webinar_data)
    except Exception as e:
        print(f"Error in webinar route: {e}")
        response = redirect(url_for('index'))
        response.delete_cookie('session_token')
        return response

@app.route('/logout')
def logout():
    """Logout route - clear session"""
    if 'session_token' in request.cookies:
        session_token = request.cookies.get('session_token')
        logout_session(session_token)
    
    response = redirect(url_for('index'))
    response.delete_cookie('session_token')
    return response
    
@app.route('/force-logout')
def force_logout():
    """Force logout from all devices"""
    if 'session_token' in request.cookies:
        try:
            session_token = request.cookies.get('session_token')
            session = ActiveSession.query.get(session_token)
            
            if session:
                its_id = session.its_id
                # Find and delete all sessions for this ITS ID
                sessions_to_delete = ActiveSession.query.filter_by(its_id=its_id).all()
                
                for s in sessions_to_delete:
                    db.session.delete(s)
                
                db.session.commit()
        except Exception as e:
            print(f"Error in force logout: {e}")
            db.session.rollback()
    
    response = redirect(url_for('index'))
    response.delete_cookie('session_token')
    return response

# Admin login template
ADMIN_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Anjuman e Hakimi Najmi Mohallah Ratlam Live Portal</title>
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

# Admin dashboard template (complete version)
ADMIN_DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - Anjuman e Hakimi Najmi Mohallah Ratlam Live Portal</title>
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

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--gradient-glass);
            padding: 1.5rem;
            border-radius: var(--radius-lg);
            text-align: center;
            border: 1px solid rgba(212, 175, 55, 0.1);
            backdrop-filter: blur(15px);
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
            text-decoration: none;
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

        .form-input, .form-textarea {
            width: 100%;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: var(--radius-md);
            color: var(--text-primary);
            font-size: 1rem;
            margin-bottom: 1rem;
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
            position: relative;
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

        .action-buttons {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
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

            .action-buttons {
                flex-direction: column;
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
                    <input type="text" name="youtube_video_id" class="form-input" placeholder="YouTube Video ID (e.g., 2iq6zW8nv2E)" value="{{ settings.youtube_video_id if settings else '' }}" required>
                    <div class="form-helper" style="font-size: 0.8rem; color: #666; margin: -0.5rem 0 1rem 0;">
                        Enter only the video ID (e.g., 2iq6zW8nv2E), not the entire URL.
                    </div>
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
                
                <div class="action-buttons">
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
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for session in sessions_data %}
                            <tr>
                                <td>{{ session.its_id }}</td>
                                <td>{{ session.login_time_formatted }}</td>
                                <td>
                                    <form method="POST" action="{{ url_for('admin_kick_session') }}" style="display: inline;">
                                        <input type="hidden" name="session_token" value="{{ session.session_token }}">
                                        <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Kick this user?')">
                                            <i class="fas fa-user-times"></i>
                                        </button>
                                    </form>
                                </td>
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
    
    <div style="text-align: center; margin-top: 20px; padding: 10px; font-size: 0.85rem; color: rgba(255, 255, 255, 0.65);">
        Developed with <span style="color: #ff4d4d; display: inline-block; animation: heartbeat 1.5s ease infinite;">♥</span> by Huzefa Nalkheda wala
    </div>
    
    <style>
        @keyframes heartbeat {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }
    </style>
</body>
</html>
'''

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login route"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        try:
            admin = AdminCredential.query.filter_by(username=username).first()
            if not admin:
                return render_template_string(ADMIN_LOGIN_TEMPLATE, error="Invalid username or password.")
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash == admin.password_hash:
                session['admin_logged_in'] = True
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template_string(ADMIN_LOGIN_TEMPLATE, error="Invalid username or password.")
        except Exception as e:
            print(f"Error in admin login: {e}")
            return render_template_string(ADMIN_LOGIN_TEMPLATE, error="An error occurred during login. Please try again.")
    
    return render_template_string(ADMIN_LOGIN_TEMPLATE)

@app.route('/admin/logout')
def admin_logout():
    """Admin logout route"""
    if 'admin_logged_in' in session:
        session.pop('admin_logged_in')
    return redirect(url_for('admin_login'))

@app.route('/admin/add_its', methods=['POST'])
def admin_add_its():
    """Add a single ITS ID"""
    its_id = request.form.get('single_its', '').strip()
    
    if not its_id or len(its_id) != 8 or not its_id.isdigit():
        return redirect(url_for('admin_dashboard') + '?message=Invalid ITS ID format&type=error')
    
    try:
        # Check if ID already exists
        existing = ItsID.query.get(its_id)
        
        if existing:
            return redirect(url_for('admin_dashboard') + '?message=ITS ID already exists&type=error')
        
        # Add new ITS ID
        new_id = ItsID(id=its_id)
        db.session.add(new_id)
        db.session.commit()
        
        return redirect(url_for('admin_dashboard') + '?message=ITS ID added successfully&type=success')
    except Exception as e:
        db.session.rollback()
        print(f"Error adding ITS ID: {e}")
        return redirect(url_for('admin_dashboard') + f'?message=Error adding ITS ID: {str(e)}&type=error')

@app.route('/admin/update_webinar_settings', methods=['POST'])
def admin_update_webinar_settings():
    """Update webinar settings"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        # Get current settings from database
        settings = WebinarSetting.query.first()
        
        if not settings:
            settings = WebinarSetting()
            db.session.add(settings)
            
        # Update settings with form data
        video_id_or_url = request.form.get('youtube_video_id', '') or request.form.get('embed_url', '')
        settings.youtube_video_id = extract_youtube_id(video_id_or_url)
        settings.webinar_title = request.form.get('webinar_title', '')
        settings.webinar_description = request.form.get('webinar_description', '')
        settings.webinar_date = request.form.get('webinar_date', '')
        settings.webinar_time = request.form.get('webinar_time', '')
        settings.webinar_speaker = request.form.get('webinar_speaker', '')
        settings.no_webinar = 'no_webinar' in request.form
        
        db.session.commit()
        
        return redirect(url_for('admin_dashboard') + '?message=Webinar settings updated successfully&type=success')
    
    except Exception as e:
        db.session.rollback()
        print(f"Error updating webinar settings: {e}")
        return redirect(url_for('admin_dashboard') + f'?message=Error updating settings: {str(e)}&type=error')

@app.route('/admin')
def admin_index():
    """Redirect to admin login or dashboard"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Enhanced admin dashboard route"""
    try:
        # Fetch all ITS IDs from database
        its_ids_list = ItsID.query.all()
        its_ids = {its_id.id for its_id in its_ids_list}
        
        # Get active sessions from database
        active_sessions = ActiveSession.query.all()
        
        # Get webinar settings
        webinar_settings = load_webinar_settings()
        
        # Get active sessions by ITS ID
        sessions_status = set()
        sessions_data = []
        for session in active_sessions:
            sessions_status.add(session.its_id)
            # Format session data for display
            sessions_data.append({
                'its_id': session.its_id,
                'login_time_formatted': session.login_time.strftime('%Y-%m-%d %H:%M:%S'),
                'session_token': session.token
            })
        
        # Prepare stats
        stats = {
            'total_its': len(its_ids),
            'active_sessions': len(active_sessions),
            'total_sessions': len(active_sessions)
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
                                  settings=webinar_settings)
    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        return f"Error loading admin dashboard: {str(e)}"

@app.route('/admin/add_bulk_its', methods=['POST'])
def admin_add_bulk_its():
    """Add multiple ITS IDs from a textarea"""
    bulk_its = request.form.get('bulk_its', '').strip()
    
    if not bulk_its:
        return redirect(url_for('admin_dashboard') + '?message=No ITS IDs provided&type=error')
    
    try:
        # Get existing IDS IDs
        existing_ids = {its_id.id for its_id in ItsID.query.all()}
        new_ids = set()
        
        # Split by lines or commas and validate each ID
        for line in bulk_its.splitlines():
            for its_id in line.split(','):
                its_id = its_id.strip()
                if len(its_id) == 8 and its_id.isdigit() and its_id not in existing_ids:
                    new_ids.add(its_id)
        
        if not new_ids:
            return redirect(url_for('admin_dashboard') + '?message=No valid ITS IDs to add&type=error')
        
        # Add new ITS IDs to database
        for its_id in new_ids:
            new_id = ItsID(id=its_id)
            db.session.add(new_id)
        
        db.session.commit()
        
        return redirect(url_for('admin_dashboard') + f'?message=Added {len(new_ids)} ITS IDs successfully&type=success')
    
    except Exception as e:
        db.session.rollback()
        print(f"Error adding bulk ITS IDs: {e}")
        return redirect(url_for('admin_dashboard') + f'?message=Error adding ITS IDs: {str(e)}&type=error')

@app.route('/admin/delete_its', methods=['POST'])
def admin_delete_its():
    """Delete a specific ITS ID"""
    its_id = request.form.get('its_id', '').strip()
    
    if not its_id or len(its_id) != 8 or not its_id.isdigit():
        return redirect(url_for('admin_dashboard') + '?message=Invalid ITS ID format&type=error')
    
    try:
        # Find ITS ID in database
        id_to_delete = ItsID.query.get(its_id)
        
        if not id_to_delete:
            return redirect(url_for('admin_dashboard') + '?message=ITS ID not found&type=error')
        
        # Delete any associated sessions first
        ActiveSession.query.filter_by(its_id=its_id).delete()
        
        # Delete the ITS ID
        db.session.delete(id_to_delete)
        db.session.commit()
        
        return redirect(url_for('admin_dashboard') + '?message=ITS ID deleted successfully&type=success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting ITS ID: {e}")
        return redirect(url_for('admin_dashboard') + f'?message=Error deleting ITS ID: {str(e)}&type=error')

@app.route('/admin/delete_all_its', methods=['POST'])
def admin_delete_all_its():
    """Delete all ITS IDs"""
    try:
        # Count ITS IDs for message
        count = ItsID.query.count()
        
        if count == 0:
            return redirect(url_for('admin_dashboard') + '?message=No ITS IDs to delete&type=error')
            
        # Delete all active sessions first
        ActiveSession.query.delete()
        
        # Delete all ITS IDs
        ItsID.query.delete()
        
        db.session.commit()
        
        return redirect(url_for('admin_dashboard') + f'?message=Deleted {count} ITS IDs successfully&type=success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting all ITS IDs: {e}")
        return redirect(url_for('admin_dashboard') + f'?message=Error deleting ITS IDs: {str(e)}&type=error')

@app.route('/admin/clear_sessions', methods=['POST'])
def admin_clear_sessions():
    """Clear all active sessions"""
    try:
        # Count sessions for message
        count = ActiveSession.query.count()
        
        if count == 0:
            return redirect(url_for('admin_dashboard') + '?message=No active sessions to clear&type=error')
        
        # Delete all sessions
        ActiveSession.query.delete()
        db.session.commit()
        
        return redirect(url_for('admin_dashboard') + f'?message=Cleared {count} active sessions successfully&type=success')
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing sessions: {e}")
        return redirect(url_for('admin_dashboard') + f'?message=Error clearing sessions: {str(e)}&type=error')

@app.route('/admin/kick_session', methods=['POST'])
def admin_kick_session():
    """Kick a specific user session"""
    session_token = request.form.get('session_token', '').strip()
    
    if not session_token:
        return redirect(url_for('admin_dashboard') + '?message=Invalid session token&type=error')
    
    try:
        # Find session by token
        session = ActiveSession.query.get(session_token)
        
        if not session:
            return redirect(url_for('admin_dashboard') + '?message=Session not found&type=error')
        
        its_id = session.its_id
        
        # Delete the session
        db.session.delete(session)
        db.session.commit()
        
        return redirect(url_for('admin_dashboard') + f'?message=Kicked user {its_id} successfully&type=success')
    except Exception as e:
        db.session.rollback()
        print(f"Error kicking session: {e}")
        return redirect(url_for('admin_dashboard') + f'?message=Error kicking session: {str(e)}&type=error')


if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
        init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)