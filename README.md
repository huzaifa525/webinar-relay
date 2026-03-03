# Webinar Relay Centre - Next.js

Modern, high-performance Next.js implementation of the Ratlam Relay Centre Webinar Access Portal.

## ✨ Features

### Real-Time Updates (Server-Sent Events)
- ✅ **Live Session Monitoring** - See users connect/disconnect instantly
- ✅ **Instant Kick/Force Logout** - Users are immediately logged out when admin kicks them
- ✅ **Auto-Updating Dashboard** - No manual refresh needed
- ✅ **Live ID Count Updates** - See totals update as you add/delete IDs
- ✅ **Live Status Indicator** - Green pulsing dot shows connection status

### User Features
- 8-digit ID authentication (ITS/Majlis)
- Dual-access role selection (if registered in both)
- YouTube player with auto-hide controls (3s timeout)
- Custom volume + fullscreen controls
- YouTube brand masking overlays
- Keyboard shortcuts (Space/K/M/F)
- Screen wake lock
- 30min client-side inactivity timeout
- Real-time force logout detection
- Session dropdown (logout this device / logout all devices)
- Developer tools protection

### Admin Panel Features
- **Modern Dashboard UI** with 4 tabs:
  - Overview (stats + recent activity)
  - ITS Management
  - Majlis Management
  - Active Sessions
- Real-time session monitoring
- Live search/filter for IDs
- Bulk ID import (comma/newline separated)
- Webinar settings with auto-activation times
- Kick specific session or force logout all user sessions
- No manual cache refresh needed (automatic)

### Technical Features
- Next.js 15 App Router
- TypeScript for type safety
- Prisma ORM (PostgreSQL)
- Redis for sessions + caching
- Server-Sent Events for real-time updates
- Tailwind CSS + Custom design system
- Edge-ready architecture

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env
# Edit .env with your DATABASE_URL and REDIS_URL

# Generate Prisma client (connects to existing DB)
npx prisma generate

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
src/
├── app/                      # Next.js App Router
│   ├── page.tsx              # Login page
│   ├── select-role/          # Dual-access role selection
│   ├── webinar/              # ITS portal
│   ├── majlis/               # Majlis portal
│   ├── admin/
│   │   ├── login/            # Admin login
│   │   └── dashboard/        # Admin panel
│   └── api/
│       ├── auth/             # User auth endpoints
│       │   ├── login/
│       │   ├── logout/
│       │   ├── force-logout/
│       │   ├── status/
│       │   └── events/       # SSE for users (force logout)
│       ├── admin/            # Admin endpoints
│       │   ├── login/
│       │   ├── logout/
│       │   ├── its/          # ITS ID CRUD
│       │   ├── majlis/       # Majlis ID CRUD
│       │   ├── webinar-settings/
│       │   ├── majlis-settings/
│       │   ├── sessions/     # Session management
│       │   ├── cache/        # (deprecated - auto now)
│       │   └── events/       # SSE for admin (real-time updates)
│       └── health/           # Health check
├── components/
│   ├── AdminDashboard.tsx    # Full admin UI
│   ├── LoginForm.tsx
│   ├── RoleSelection.tsx
│   ├── YouTubePlayer.tsx     # Player with masking
│   ├── NoWebinar.tsx
│   ├── SessionDropdown.tsx
│   └── NotificationToast.tsx
├── lib/
│   ├── db.ts                 # Prisma client
│   ├── redis.ts              # Redis client
│   ├── auth.ts               # Session verification
│   ├── session.ts            # Session CRUD + events
│   ├── cache.ts              # ID validation + settings + events
│   ├── websocket.ts          # Event emitter (SSE backend)
│   └── utils.ts              # Helpers
└── types/
    └── index.ts              # TypeScript types
```

## 🔄 Real-Time Architecture

### How It Works

1. **User connects** → `createSession()` → Emits `user_connected` event
2. **Admin panel** listening via `/api/admin/events` (SSE) → Receives event → Refreshes data
3. **Admin kicks user** → `logoutSession()` → Emits `user_disconnected` event
4. **User's browser** listening via `/api/auth/events` → Receives `force_logout` → Logs out immediately
5. **Admin panel** also receives `user_disconnected` → Updates session list in real-time

### Event Flow

```
User Action              Backend Event           Admin Panel        User Browser
─────────────────────────────────────────────────────────────────────────────────
Login                 → user_connected        → +1 session       → (none)
Logout                → user_disconnected     → -1 session       → (none)
Admin Kick            → user_disconnected     → -1 session       → Force logout
Admin Add ID          → ids_updated           → Update count     → (none)
Admin Update Settings → settings_updated      → Refresh          → (none)
```

### Why SSE Instead of WebSocket?

- ✅ Simpler (HTTP-based, no separate server)
- ✅ Auto-reconnects on disconnect
- ✅ Works through most firewalls/proxies
- ✅ Lower overhead for one-way communication (server → client)
- ✅ Built into browsers (no libraries needed)

## 🗄️ Database

Uses **existing PostgreSQL tables** from Flask app:
- `its_ids`
- `majlis_ids`
- `admin_credentials`
- `webinar_settings`
- `majlis_webinar_settings`

No migration needed - Prisma connects to existing schema.

## 🔐 Environment Variables

```env
DATABASE_URL="postgresql://user:pass@host:port/db?sslmode=require"
REDIS_URL="redis://default:pass@host:port"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="Huzaifa5253@"
NEXTAUTH_SECRET="your-secret-key"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

## 🚢 Deployment

### Vercel (Recommended)
```bash
vercel deploy
```

### Railway
```bash
railway up
```

### Docker
```bash
docker build -t webinar-relay-nextjs .
docker run -p 3000:3000 --env-file .env webinar-relay-nextjs
```

## 📊 Performance

- **Redis-first architecture** (90% fewer DB queries)
- **Server Components** for fast initial load
- **Client Components** only for interactive parts
- **Automatic code splitting**
- **Edge-ready** (can deploy to Vercel Edge)

## 🎨 Design System

- **Colors:** Brand blue + accent gold
- **Theme:** Dark mode with glassmorphic cards
- **Typography:** Inter (body) + Montserrat (display)
- **Animations:** Smooth transitions, auto-hide, pulse effects

## 🔧 Scripts

```bash
npm run dev          # Development server
npm run build        # Production build
npm run start        # Production server
npm run lint         # ESLint
npx prisma generate  # Generate Prisma client
npx prisma db pull   # Pull schema from DB
```

## 🐛 Troubleshooting

### "Can't connect to database"
- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running
- Verify connection string format

### "Can't connect to Redis"
- Check `REDIS_URL` in `.env`
- Ensure Redis is running
- Verify connection string format

### "Real-time updates not working"
- Check browser console for SSE errors
- Verify `/api/admin/events` endpoint is accessible
- Check admin session cookie is valid

## 📝 License

MIT

---

**Built with ❤️ by Huzefa Nalkheda wala**
