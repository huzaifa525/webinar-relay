import os
from flask import Flask, render_template_string, request, redirect, session, url_for, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import secrets
import urllib.parse
import logging

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'YOUR_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5001/auth/callback')
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'openid',
    'email',
    'profile'
]

# YouTube API Service
def get_youtube_service():
    if 'credentials' not in session:
        return None
    
    credentials = Credentials(
        token=session['credentials']['token'],
        refresh_token=session['credentials']['refresh_token'],
        token_uri=session['credentials']['token_uri'],
        client_id=session['credentials']['client_id'],
        client_secret=session['credentials']['client_secret'],
        scopes=session['credentials']['scopes']
    )
    
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            session['credentials'] = credentials_to_dict(credentials)
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return None
    
    return build('youtube', 'v3', credentials=credentials)

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

# Auth Routes
@app.route('/auth/google')
def auth_google():
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/auth/callback')
def auth_callback():
    if 'error' in request.args:
        return render_template_string("<h1>Auth Error</h1><p>{{error}}</p><a href='/'>← Back</a>", error=request.args.get('error'))
    
    if 'code' not in request.args:
        return render_template_string("<h1>Missing authorization code</h1><a href='/'>← Back</a>")
    
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        return render_template_string("<h1>Invalid state parameter</h1><a href='/'>← Back</a>")
    
    try:
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI]
                }
            },
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
            state=state
        )
        
        flow.fetch_token(code=request.args.get('code'))
        credentials = flow.credentials
        
        session['credentials'] = credentials_to_dict(credentials)
        
        # Get user info
        youtube = get_youtube_service()
        if youtube:
            channels_response = youtube.channels().list(
                part='snippet',
                mine=True
            ).execute()
            
            if channels_response.get('items'):
                channel = channels_response['items'][0]
                session['user_info'] = {
                    'name': channel['snippet']['title'],
                    'email': credentials.id_token.get('email'),
                    'channel_id': channel['id'],
                    'picture': channel['snippet']['thumbnails']['default']['url']
                }
        
        session['authenticated'] = True
        return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Auth callback error: {str(e)}")
        return render_template_string("<h1>Authentication failed</h1><p>{{error}}</p><a href='/'>← Back</a>", error=str(e))

@app.route('/auth/logout')
def auth_logout():
    session.clear()
    return redirect(url_for('index'))

# API Endpoints
@app.route('/api/test-public-video')
def api_test_public_video():
    youtube = get_youtube_service()
    if not youtube:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        response = youtube.videos().list(
            part='snippet,statistics,status',
            chart='mostPopular',
            maxResults=1,
            regionCode='US'
        ).execute()
        
        if not response.get('items'):
            return jsonify({'error': 'No public videos found'}), 404
            
        video = response['items'][0]
        return jsonify({
            'title': video['snippet']['title'],
            'privacy': video['status']['privacyStatus'],
            'viewCount': video['statistics'].get('viewCount', 'N/A')
        })
    except Exception as e:
        logger.error(f"Public video error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-my-channel')
def api_test_my_channel():
    youtube = get_youtube_service()
    if not youtube:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        response = youtube.channels().list(
            part='snippet,statistics',
            mine=True
        ).execute()
        
        if not response.get('items'):
            return jsonify({'error': 'Channel not found'}), 404
            
        channel = response['items'][0]
        return jsonify({
            'title': channel['snippet']['title'],
            'subscriberCount': channel['statistics'].get('subscriberCount', '0'),
            'videoCount': channel['statistics'].get('videoCount', '0'),
            'channelId': channel['id']
        })
    except Exception as e:
        logger.error(f"Channel error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-my-videos')
def api_test_my_videos():
    youtube = get_youtube_service()
    if not youtube:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get all videos
        search_response = youtube.search().list(
            part='snippet',
            forMine=True,
            type='video',
            maxResults=50
        ).execute()
        
        if not search_response.get('items'):
            return jsonify({'error': 'No videos found'}), 404
        
        # Count by privacy status
        privacy_counts = {'private': 0, 'public': 0, 'unlisted': 0}
        videos = []
        
        for item in search_response['items']:
            video_id = item['id']['videoId']
            video_response = youtube.videos().list(
                part='status',
                id=video_id
            ).execute()
            
            if video_response.get('items'):
                status = video_response['items'][0]['status']['privacyStatus']
                privacy_counts[status] += 1
                
                videos.append({
                    'title': item['snippet']['title'],
                    'privacy': status,
                    'id': video_id
                })
        
        return jsonify({
            'totalCount': len(search_response['items']),
            'privateCount': privacy_counts['private'],
            'unlistedCount': privacy_counts['unlisted'],
            'publicCount': privacy_counts['public'],
            'recentVideos': videos[:5]  # Return first 5 videos
        })
    except Exception as e:
        logger.error(f"My videos error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-private-access')
def api_test_private_access():
    youtube = get_youtube_service()
    if not youtube:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get private/unlisted videos
        search_response = youtube.search().list(
            part='snippet',
            forMine=True,
            type='video',
            maxResults=50
        ).execute()
        
        private_videos = []
        unlisted_videos = []
        
        for item in search_response['items']:
            video_id = item['id']['videoId']
            video_response = youtube.videos().list(
                part='status',
                id=video_id
            ).execute()
            
            if video_response.get('items'):
                status = video_response['items'][0]['status']['privacyStatus']
                
                if status == 'private':
                    private_videos.append({
                        'title': item['snippet']['title'],
                        'id': video_id
                    })
                elif status == 'unlisted':
                    unlisted_videos.append({
                        'title': item['snippet']['title'],
                        'id': video_id
                    })
        
        return jsonify({
            'privateCount': len(private_videos),
            'unlistedCount': len(unlisted_videos),
            'examples': private_videos[:3] + unlisted_videos[:3]  # Return 3 examples each
        })
    except Exception as e:
        logger.error(f"Private access error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-live-streams')
def api_test_live_streams():
    youtube = get_youtube_service()
    if not youtube:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get live broadcasts
        live_response = youtube.liveBroadcasts().list(
            part='snippet,status',
            broadcastStatus='active',
            maxResults=50
        ).execute()
        
        # Get upcoming broadcasts
        upcoming_response = youtube.liveBroadcasts().list(
            part='snippet,status',
            broadcastStatus='upcoming',
            maxResults=50
        ).execute()
        
        # Get completed broadcasts
        completed_response = youtube.liveBroadcasts().list(
            part='snippet,status',
            broadcastStatus='completed',
            maxResults=50
        ).execute()
        
        return jsonify({
            'liveCount': len(live_response.get('items', [])),
            'currentlyLive': len(live_response.get('items', [])),
            'upcoming': len(upcoming_response.get('items', [])),
            'completed': len(completed_response.get('items', []))
        })
    except Exception as e:
        logger.error(f"Live streams error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Main Route
@app.route('/')
def index():
    authenticated = session.get('authenticated', False)
    user_info = session.get('user_info', {})
    
    # Use the same HTML template from your original code
    return render_template_string(REDIRECT_AUTH_TEMPLATE, 
                               authenticated=authenticated,
                               user_info=user_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)