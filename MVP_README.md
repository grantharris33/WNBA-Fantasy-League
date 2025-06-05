# WNBA Fantasy League - MVP Guide

Welcome to the WNBA Fantasy League MVP! This guide will help you get started quickly.

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
./start-mvp.sh
```

### Option 2: Manual Setup
```bash
# Backend
poetry install
poetry run alembic upgrade head
poetry run python scripts/seed_mvp.py --force
poetry run uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## 🔗 Access Points

- **Application**: http://localhost:3000 (via Docker) or http://localhost:5173 (manual)
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 👤 Demo Accounts

### Admin Account
- Email: `me@grantharris.tech`
- Password: `Thisisapassword1`

### Demo Users
- `demo@example.com` / `demo123`
- `alice@example.com` / `alice123`
- `bob@example.com` / `bob123`
- `charlie@example.com` / `charlie123`

## 🎯 MVP Features

### User Management
- ✅ User registration and login
- ✅ JWT-based authentication
- ✅ Admin and regular user roles

### League Management
- ✅ Create and join leagues
- ✅ Invite codes for private leagues
- ✅ Commissioner controls
- ✅ League settings configuration

### Team Management
- ✅ Create teams within leagues
- ✅ Roster management (add/drop players)
- ✅ Set starting lineups
- ✅ View team statistics

### Draft System
- ✅ Snake draft support
- ✅ Real-time draft updates via WebSocket
- ✅ Draft timer with configurable time per pick
- ✅ Commissioner controls (pause/resume/revert)
- ✅ Auto-pick when timer expires

### Players & Stats
- ✅ WNBA player database
- ✅ Player search and filtering
- ✅ Detailed player pages
- ✅ Free agent listings

### Scoring
- ✅ Configurable scoring systems
- ✅ Head-to-head and rotisserie formats
- ✅ Weekly scoring calculations
- ✅ Bonus points system

### Admin Dashboard
- ✅ System monitoring
- ✅ Data quality checks
- ✅ User management
- ✅ Manual data ingestion
- ✅ Audit logging

## 🏀 Getting Started

### 1. Create an Account
- Click "Create one" on the login page
- Enter your email and password
- You'll be automatically logged in

### 2. Join or Create a League
- **Join existing league**: Use invite code `MVP-DEMO` or `TEST-123`
- **Create new league**: Click "Create League" on dashboard

### 3. Build Your Team
- Once in a league, you'll have a team
- Browse available players
- Add players to your roster
- Set your starting lineup

### 4. Participate in Draft (if available)
- Join the draft room when it starts
- Make your picks when it's your turn
- Use the player filters to find the best available
- Queue players for auto-pick

## 📊 Scoring System

Default scoring values:
- Points: 1.0
- Rebounds: 1.2
- Assists: 1.5
- Steals: 3.0
- Blocks: 3.0
- Turnovers: -1.0
- Double-Double Bonus: 5.0
- Triple-Double Bonus: 10.0

## 🛠️ Development

### Database
- SQLite for simplicity
- Located at `data/mvp.db` (Docker) or `prod.db` (local)

### API Endpoints
Key endpoints available at http://localhost:8000/docs:
- `/api/v1/auth/token` - Login
- `/api/v1/users/` - User registration
- `/api/v1/leagues/` - League operations
- `/api/v1/teams/` - Team management
- `/api/v1/players/` - Player data
- `/api/v1/draft/` - Draft operations

### WebSocket
Draft updates via WebSocket at `ws://localhost:8000/ws/draft/{league_id}`

## 🐛 Troubleshooting

### Can't login?
- Ensure backend is running (`docker-compose -f docker-compose.mvp.yml ps`)
- Check credentials are correct
- Try creating a new account

### Draft not working?
- WebSocket connection required
- Check browser console for errors
- Ensure you're in a league with active draft

### Missing data?
- Run seed script: `poetry run python scripts/seed_mvp.py --force`
- Check logs: `docker-compose -f docker-compose.mvp.yml logs backend`

## 🌟 Enhanced MVP Features

### Real WNBA Data Integration
- Add your RapidAPI key to `.env.mvp` to enable real WNBA data
- Run `poetry run python scripts/seed_mvp_real_data.py --force` to import:
  - Real WNBA teams and rosters
  - Recent game data and player statistics
  - Live player performance tracking

### Automated Scoring
- Scores update automatically every hour
- Manual update button on the scoreboard page
- Idempotent scoring prevents duplicate counts
- Historical lineup tracking for past weeks

## 📝 MVP Limitations

This MVP version has some limitations:
- Limited to SQLite database
- No email notifications
- Single-server deployment only
- Basic UI without advanced visualizations

## 🚦 Next Steps

Ready to move beyond MVP?
1. Configure RapidAPI key for real WNBA data
2. Set up PostgreSQL for production
3. Enable scheduled jobs for automated updates
4. Deploy to cloud infrastructure
5. Add email notifications

## 📧 Support

For issues or questions:
- Check the logs
- Review API documentation
- Create a GitHub issue

Enjoy your WNBA Fantasy League! 🏀