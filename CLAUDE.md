# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask web application called "Ratlam Relay Centre - Webinar Access Portal" that provides authorized access to webinar streams for registered ITS (Islamic Text Society) members and Majlis members. The application features user authentication via 8-digit ITS/Majlis ID, session management with Redis, and an admin panel for managing users and webinar settings.

## Architecture

### Database Models (PostgreSQL with SQLAlchemy)
- **ItsID**: Stores authorized 8-digit ITS member IDs
- **MajlisID**: Stores authorized 8-digit Majlis member IDs
- **AdminCredential**: Stores admin login credentials (hashed)
- **WebinarSetting**: Stores webinar configuration for ITS users (YouTube video ID, title, description, date, time, speaker)
- **MajlisWebinarSetting**: Stores webinar configuration for Majlis users (separate content management)

### Session Management (Redis)
- **Primary Storage**: Redis for all session data with TTL
- **Cache Strategy**: ITS/Majlis IDs cached in Redis, refreshed only on admin changes
- **Session Format**: `sessions:{token}` → `{user_type: 'its'/'majlis', user_id: '12345678', login_time: ...}`
- **Cache Keys**:
  - `cached:its_ids` → Set of all ITS IDs
  - `cached:majlis_ids` → Set of all Majlis IDs  
  - `cached:webinar_settings` → JSON for ITS webinar settings
  - `cached:majlis_settings` → JSON for Majlis webinar settings

### Key Routes Structure
- `/` - Home page with ITS/Majlis ID login form (checks both ID types)
- `/select_role` - Role selection page for dual-registered users (POST only)
- `/webinar` - Protected webinar viewing page for ITS users
- `/majlis` - Protected webinar viewing page for Majlis users
- `/admin/*` - Admin panel routes with separate tabs for ITS/Majlis management
- `/api/status` - JSON API endpoint for session status checks
- `/health` - Health check endpoint

### Authentication Flow
1. User enters 8-digit ID on home page
2. System checks both ITS ID cache and Majlis ID cache (Redis lookups)
3. **Dual-Access Scenario**: If ID exists in BOTH tables:
   - Show role selection UI with two buttons (ITS Portal / Majlis Portal)
   - User chooses which portal to access
   - System creates session with selected user_type
   - Redirect to appropriate portal
4. **Single-Access Scenario**: If ID exists in only one table:
   - If ITS ID found: redirect to `/webinar`
   - If Majlis ID found: redirect to `/majlis`
5. If neither found: access denied
6. Creates Redis session with TTL (no database session storage)

### Dual-Access User Support
The application supports users registered in **both** ITS and Majlis tables:
- **Detection**: Login checks both ID caches simultaneously
- **User Choice**: Role selection UI allows user to choose portal access
- **Session Isolation**: Each login creates a single-portal session (ITS or Majlis)
- **Device Restrictions**: "One device per ID" rule applies separately to each portal access
- **Admin Flexibility**: Admins can intentionally register the same ID in both tables for privileged users

### Video Player Features
The webinar player includes professional auto-hiding controls:
- **Auto-Hide Controls**: Player controls (volume, fullscreen) automatically fade out after 3 seconds of inactivity
- **Smart Visibility**: Controls reappear on:
  - Mouse movement over video
  - Mouse hover on video container
  - Click/tap on video
  - Touch events (mobile support)
- **Persistent on Hover**: Controls stay visible when hovering directly over them
- **Fullscreen Exception**: Controls remain visible in fullscreen mode
- **Smooth Transitions**: CSS animations for fade in/out (0.3s ease)
- **Mobile Optimized**: Touch-friendly with responsive button sizing

### RTMP Live Streaming Integration (Majlis Only)
The application supports self-hosted RTMP live streaming for Majlis users with secure token-based authentication.

#### Architecture
- **Environment Variable**: `MAJLIS_RTMP_URL` - URL of external RTMP streaming server (optional)
- **Conditional Rendering**: If `MAJLIS_RTMP_URL` is set, Majlis page uses RTMP stream; otherwise falls back to YouTube embed
- **Token Generation**: Secure tokens generated per-user for stream access
- **Video Player**: Video.js with HLS.js for professional live streaming playback

#### Token Security
- **Format**: `majlis_{user_id}_{sha256_hash}` (e.g., `majlis_12345678_a1b2c3d4e5f6g7h8`)
- **Generation**: Based on user_id + timestamp for uniqueness
- **Storage**: Redis with 24-hour expiry (`stream_token:{token}` → `user_id`)
- **Refresh**: Automatic token refresh every 20 hours (before 24hr expiry)
- **Validation**: Every HLS request (.m3u8 playlist and .ts segments) requires valid token

#### API Endpoints
- **`GET /api/majlis/stream-token`**: Generate secure token for authenticated Majlis users
  - **Authentication**: Requires valid Majlis session cookie
  - **Response**: JSON with `token`, `stream_url`, `expires_in` (86400 seconds)
  - **Usage**: Called by MAJLIS_RTMP_TEMPLATE on page load and every 20 hours

#### Security Features
- **URL Obfuscation**: Console methods overridden to prevent URL logging/extraction
- **Right-Click Disabled**: Context menu and developer tools blocked
- **Token in URL**: Stream URL includes token parameter, validated on every request
- **No Direct Access**: RTMP server's Nginx config blocks direct HLS access (internal directive)
- **Session Bound**: Tokens tied to active Majlis sessions, invalidated on logout

#### Templates
- **MAJLIS_RTMP_TEMPLATE**: Full-featured live streaming template with:
  - Video.js 8.10.0 player with HLS support
  - Custom gold-themed player controls matching app design
  - Loading, error, and success states
  - WebSocket integration for real-time notifications
  - Automatic token fetching and refresh
  - LIVE indicator with pulsing animation
  - Responsive design for mobile devices

#### RTMP Server Integration
The separate `live-stream/` folder contains a complete self-hosted RTMP → HLS server:
- **Dockerfile**: Ubuntu + Nginx-RTMP + Flask
- **nginx.conf**: RTMP ingest on port 1935, HLS output with token validation
- **app.py**: Flask token validation proxy (validates tokens from main app's Redis)
- **Deployment**: Designed for Railway/Docker with OBS Studio streaming

#### Configuration
Set the environment variable in production:
```bash
export MAJLIS_RTMP_URL="https://your-rtmp-server.railway.app"
# or in Railway dashboard: MAJLIS_RTMP_URL = https://your-rtmp-server.railway.app
```

If not set, Majlis users see YouTube embed (fallback behavior).

#### Redis Keys Used
- `stream_token:{token}` → `user_id`, TTL 86400 seconds (24 hours)
- Main session keys: `sessions:{session_token}` (validates user before token generation)

#### Workflow
1. Majlis user logs in with valid ID
2. System checks `MAJLIS_RTMP_URL` environment variable
3. If set: Render MAJLIS_RTMP_TEMPLATE
4. Template JavaScript calls `/api/majlis/stream-token`
5. Backend validates session, generates secure token, stores in Redis
6. Frontend receives token + stream URL
7. Video.js initializes with HLS stream URL (includes token parameter)
8. Every HLS request validated by RTMP server's Flask app
9. Token auto-refreshes every 20 hours to prevent expiration
10. On logout, session deleted (tokens remain valid until Redis TTL expires)

### WebSocket Real-Time Features
The application uses **Flask-SocketIO** with **eventlet** for real-time bidirectional communication:

#### Connection Management
- **Automatic Connection**: All users (ITS/Majlis/Admin) automatically connect via WebSocket on page load
- **Room-Based Broadcasting**: Users join specific rooms based on their type and ID
  - `user_{user_id}_{user_type}` - Individual user room for targeted notifications
  - `type_{user_type}` - Type-specific room (all ITS or all Majlis users)
  - `all_users` - Global room for broadcasting to everyone
  - `admin_room` - Admin-only room for control panel updates

#### Real-Time Features
- **Session Monitoring**: Server detects expired sessions and notifies clients to logout
- **Heartbeat System**: 30-second intervals verify connection and session validity
- **Automatic Inactivity Logout**: Users inactive for 1+ hour are automatically force-logged out
- **Activity Tracking**: Redis tracks last WebSocket activity (connect, disconnect, heartbeat)
- **Background Monitoring**: Checks every 5 minutes for inactive users
- **Admin Broadcasts**: Admins can send messages to all users or specific groups
- **Webinar Updates**: Automatic page refresh when webinar settings change
- **Force Logout**: Admins can remotely logout specific users
- **Connection Status**: Visual notifications for connect/disconnect events
- **Live Statistics**: Real-time user count updates in admin panel

#### WebSocket Events (Server → Client)
- `connection_established` - Confirms WebSocket connection with user details
- `session_expired` - Forces logout when session expires
- `admin_message` - Admin broadcast messages to users
- `notification` - Generic notifications
- `webinar_updated` - Webinar settings changed, triggers reload
- `force_logout` - Admin-initiated logout
- `heartbeat_ack` - Confirms heartbeat received
- `user_connected` / `user_disconnected` - Admin notifications of user activity
- `stats_update` - Real-time session statistics

#### WebSocket Events (Client → Server)
- `heartbeat` - Client keepalive with session verification
- `admin_broadcast` - Admin sends message to users
- `request_stats` - Request current active session counts

#### Technology Stack
- **Flask-SocketIO 5.x**: WebSocket server implementation
- **Socket.IO Client 4.5.4**: JavaScript client (loaded via CDN)
- **Eventlet**: Async worker for production deployment
- **Gunicorn with eventlet worker**: Production WSGI server

#### Deployment Configuration
- **Procfile**: Uses `gunicorn --worker-class eventlet -w 1` for WebSocket support
- **Single Worker**: Required for Socket.IO session affinity
- **Graceful Degradation**: Falls back to long-polling if WebSocket unavailable

#### Automatic Inactivity Logout System
**Problem**: Users who close their browser or lose connection remain logged in, blocking other devices.

**Solution**: Background monitoring with automatic force logout after 1 hour of inactivity.

**How It Works**:
1. **Activity Tracking**: Every WebSocket event (connect, disconnect, heartbeat) updates `activity:{user_id}:{user_type}` in Redis
2. **Background Task**: Runs every 5 minutes checking all active sessions
3. **Inactivity Check**: Compares current time vs. last activity timestamp
4. **Auto-Logout**: If inactive > 1 hour:
   - Delete session from Redis (`sessions:{token}`)
   - Send WebSocket `force_logout` event to user (if still connected)
   - Delete activity tracker (`activity:{user_id}:{user_type}`)
   - Log the action with inactive duration

**Redis Keys Used**:
- `activity:{user_id}:{user_type}` → ISO timestamp, TTL 2 hours
- Updates on: WebSocket connect, disconnect, heartbeat (every 30s)

**Example Timeline**:
```
10:00 AM - User connects → activity:12345678:its = "2025-01-05T10:00:00"
10:30 AM - Heartbeat received → activity updated to "2025-01-05T10:30:00"
10:35 AM - User closes browser (no explicit logout)
11:05 AM - Background check runs: Last activity = 10:30 AM (35 min ago) → Keep session
11:35 AM - Background check runs: Last activity = 10:30 AM (1 hr 5 min ago) → FORCE LOGOUT
```

**Benefits**:
- Prevents "stuck" sessions from blocking device access
- Automatic cleanup without manual admin intervention
- Works even if user loses connection without logout
- Configurable threshold (currently 1 hour)

### Resource Optimization Strategy
- **Redis-First Architecture**: All session operations use Redis with TTL
- **Minimal Database Hits**: PostgreSQL only for admin operations and initial cache loading
- **Connection Pooling**: Max 3 PostgreSQL connections configured
- **Cache Invalidation**: Manual refresh only when admin makes changes
- **No Session Cleanup**: Redis TTL handles automatic expiration
- **WebSocket Efficiency**: Single persistent connection per user instead of HTTP polling

## Development Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt
# Or manually:
pip install redis flask-sqlalchemy psycopg2-binary flask-socketio eventlet

# Set environment variables (required for database and Redis connections)
export DATABASE_URL="postgresql://user:password@host:port/database"
export REDIS_URL="redis://default:password@host:port"

# Or copy .env.example to .env and update values
cp .env.example .env
# Edit .env with your actual credentials

# Run development server (optimized for minimal resource usage)
python app.py

# Alternative using Flask CLI
export FLASK_APP=app.py
flask run
```

### Windows Quick Start
```bash
# Set environment variables (Windows CMD)
set DATABASE_URL=postgresql://user:password@host:port/database
set REDIS_URL=redis://default:password@host:port

# Or use PowerShell
$env:DATABASE_URL="postgresql://user:password@host:port/database"
$env:REDIS_URL="redis://default:password@host:port"

# Then run
python app.py
```

### Database Management
The application uses PostgreSQL with automatic table creation on first run. The `init_database()` function handles:
- Creating all database tables (ItsID, MajlisID, AdminCredential, WebinarSetting, MajlisWebinarSetting)
- Setting up default admin credentials
- Creating default webinar settings for both ITS and Majlis
- Initial Redis cache population

### Redis Cache Management
```bash
# Manual cache refresh (admin operation)
# ITS IDs: Load from PostgreSQL → Store in Redis set
# Majlis IDs: Load from PostgreSQL → Store in Redis set
# Settings: Load from PostgreSQL → Store as JSON
```

### Docker Deployment
```bash
# Build container
docker build -t webinar-relay .

# Run container with Redis
docker run -e REDIS_URL="redis://..." -p 5000:5000 webinar-relay
```

## Configuration

### Environment Variables
The application **requires** environment variables for database and Redis connections. See `.env.example` for template.

**Required Environment Variables:**
- `DATABASE_URL`: PostgreSQL connection string (REQUIRED)
  - Format: `postgresql://user:password@host:port/database`
  - Example (Neon): `postgresql://user:password@ep-xxxxx-sg.neon.tech/neondb?sslmode=require`
  - Example (Railway): `postgresql://postgres:password@host:port/railway`

- `REDIS_URL`: Redis connection string (REQUIRED)
  - Format: `redis://username:password@host:port` or `rediss://` for SSL
  - Example (Upstash): `rediss://default:password@host.upstash.io:6379`
  - Example (Railway): `redis://default:password@host:port`

**Optional Environment Variables:**
- `MAJLIS_RTMP_URL`: External RTMP streaming server URL (OPTIONAL)
  - Format: `https://your-rtmp-server.railway.app` (no trailing slash)
  - If set: Majlis users see RTMP live stream with Video.js player
  - If not set: Majlis users see YouTube embed (fallback)
  - Used by: `/majlis` route and `/api/majlis/stream-token` endpoint
  - Example: `https://majlis-stream.railway.app`

**Important:**
The application will fail to start if required environment variables (DATABASE_URL, REDIS_URL) are not set. There are no hardcoded fallback credentials.

### Database Connection (PostgreSQL)
Connection pooling configuration:
- Max connections: 3
- Pool size: 3
- Pool timeout: 30s
- Pool recycle: 3600s

### Redis Connection
Redis client configuration:
- Decode responses: True (automatic string decoding)
- Connection URL: From environment variable or fallback

### Admin Credentials
Default admin credentials:
- Username: `admin` 
- Password: `Huzaifa5253@` (should be changed in production)

### YouTube Integration
Separate video embedding for ITS and Majlis users:
- ITS users: Configured via WebinarSetting table
- Majlis users: Configured via MajlisWebinarSetting table
- Both use YouTube video IDs with optimized parameters

## Performance Optimization

### Session Management
- **No Database Sessions**: All session data in Redis with 24hr TTL
- **No Cleanup Jobs**: Redis handles automatic expiration
- **Minimal Lookups**: Cache hit for 99% of session verifications

### Database Optimization
- **Connection Pooling**: Reuse connections across requests
- **Batch Operations**: Group related database operations
- **Indexes**: Optimized for ID lookups and admin queries
- **Minimal Queries**: Redis cache reduces database load by 90%+

### Cost Targets
- **Resource Usage**: Optimized for Railway $5/month tier
- **Concurrent Users**: 50+ users on minimal resource usage
- **Database Load**: <10 queries per minute under normal operation
- **Memory Usage**: Redis cache + minimal Flask overhead

## Security Notes

### Credentials Management
**✅ DATABASE_URL and REDIS_URL are now required environment variables**
- No hardcoded database or Redis credentials in code
- Application will fail to start if environment variables are missing
- See `.env.example` for configuration template
- Credentials are completely removed from version control

**⚠️ Still hardcoded in app.py:**
- Admin password (app.py:52-53)
- Flask secret key (app.py:26)

**Production Requirements**:
- ✅ Set `DATABASE_URL` environment variable (REQUIRED)
- ✅ Set `REDIS_URL` environment variable (REQUIRED)
- ⚠️ Move admin credentials to environment variables (recommended)
- ⚠️ Use strong, random Flask secret key (recommended)

### Session Security
- Redis sessions with SHA-256 tokens
- 24-hour TTL for automatic expiration
- User type validation for route access
- No fallback to database if Redis is unavailable

## File Structure

### Core Application
- `app.py` - Main Flask application with Redis integration
- `requirements.txt` - Dependencies including redis and optimized packages

### Database Models
- **ItsID** - Regular user IDs
- **MajlisID** - Majlis user IDs  
- **WebinarSetting** - ITS webinar configuration
- **MajlisWebinarSetting** - Majlis webinar configuration
- **AdminCredential** - Admin authentication

### Static Assets
- `background.svg` - Background image for web interface
- Optimized for minimal bandwidth usage

## Testing Strategy

### Performance Testing
- Load test with 50+ concurrent users
- Database connection pool stress testing  
- Redis failover scenarios
- Cache invalidation testing

### Functional Testing
- ITS/Majlis authentication flow
- Admin panel dual management
- Session management across user types
- Video content delivery optimization

### Resource Monitoring
- Database connection usage
- Redis memory consumption
- Response time optimization
- Cost per user tracking

## Admin Panel Features

### Dual User Management
- **Separate Tabs**: ITS management and Majlis management
- **Unified Dashboard**: Combined statistics and session monitoring
- **Bulk Operations**: Import/export for both user types
- **Content Management**: Separate video settings for each type

### Cache Management
- Manual cache refresh triggers
- Cache invalidation on data changes
- Performance monitoring dashboard
- Resource usage tracking