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
- `/webinar` - Protected webinar viewing page for ITS users
- `/majlis` - Protected webinar viewing page for Majlis users  
- `/admin/*` - Admin panel routes with separate tabs for ITS/Majlis management
- `/api/status` - JSON API endpoint for session status checks
- `/health` - Health check endpoint

### Authentication Flow
1. User enters 8-digit ID on home page
2. System checks ITS ID cache first (Redis lookup)
3. If not found, checks Majlis ID cache (Redis lookup)
4. If ITS ID found: redirect to `/webinar`
5. If Majlis ID found: redirect to `/majlis`
6. If neither found: access denied
7. Creates Redis session with TTL (no database session storage)

### Resource Optimization Strategy
- **Redis-First Architecture**: All session operations use Redis with TTL
- **Minimal Database Hits**: PostgreSQL only for admin operations and initial cache loading
- **Connection Pooling**: Max 3 PostgreSQL connections configured
- **Cache Invalidation**: Manual refresh only when admin makes changes
- **No Session Cleanup**: Redis TTL handles automatic expiration

## Development Commands

### Running the Application
```bash
# Install dependencies
pip install redis flask-sqlalchemy psycopg2-binary

# Set Redis connection (Railway)
export REDIS_URL="redis://default:disvEqUIUIJGKERTqkWhdgWOxncsbaJR@switchback.proxy.rlwy.net:43339"

# Run development server (optimized for minimal resource usage)
python app.py

# Alternative using Flask CLI
export FLASK_APP=app.py
flask run
```

### Windows Quick Start
```bash
# Use the provided batch file
start.bat
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

### Redis Connection
```python
# Railway Redis URL
REDIS_URL = "redis://default:disvEqUIUIJGKERTqkWhdgWOxncsbaJR@switchback.proxy.rlwy.net:43339"
```

### Database Connection (PostgreSQL)
Railway-hosted PostgreSQL with connection pooling:
- Max connections: 3
- Pool size: 3
- Pool timeout: 30s
- Pool recycle: 3600s

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

### Credentials in Code
- Database connection string with credentials is hardcoded in app.py:26
- Redis URL with credentials is hardcoded 
- Admin password is hardcoded in app.py:32
- Flask secret key is hardcoded in app.py:23

**Production Requirements**: Move all credentials to environment variables.

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