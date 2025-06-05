# WNBA Fantasy League Deployment Guide

This guide covers deploying the WNBA Fantasy League application to a Hetzner VPS using Docker, Traefik, and Cloudflare.

## Prerequisites

- A Hetzner VPS (or any Ubuntu/Debian server) with at least 2GB RAM
- A domain name pointed to your VPS IP
- Cloudflare account with your domain configured
- RapidAPI key for WNBA data

## Architecture Overview

The deployment uses Docker Compose to orchestrate the following services:

- **PostgreSQL**: Primary database
- **Backend**: FastAPI application
- **Frontend**: React application served by Nginx
- **Traefik**: Reverse proxy with automatic SSL via Cloudflare
- **Portainer**: Docker management UI
- **Backup**: Automated PostgreSQL backups

## Quick Start

### 1. Initial VPS Setup

SSH into your VPS and run the setup script:

```bash
wget https://raw.githubusercontent.com/grantharris33/WNBA-Fantasy-League-2/main/scripts/setup-vps.sh
chmod +x setup-vps.sh
sudo ./setup-vps.sh
```

This script will:
- Install Docker and Docker Compose
- Configure firewall (UFW)
- Set up fail2ban for security
- Create necessary directories
- Clone the repository
- Configure automatic system updates

### 2. Configure Environment

```bash
cd /opt/wnba-fantasy
cp .env.production .env.production
```

Edit `.env.production` with your values:

```bash
# Required configurations
DOMAIN=your-domain.com
POSTGRES_PASSWORD=generate-secure-password
SECRET_KEY=generate-long-random-string
RAPIDAPI_KEY=your-rapidapi-key
CF_API_EMAIL=your-cloudflare-email
CF_API_KEY=your-cloudflare-global-api-key
ADMIN_EMAIL=your-admin-email
ADMIN_PASSWORD=your-admin-password

# Generate Traefik dashboard password
# htpasswd -nb admin your-password
TRAEFIK_DASHBOARD_AUTH=admin:$2y$10$...
```

### 3. Deploy

```bash
./scripts/deploy.sh production
```

The application will be available at:
- Main app: `https://your-domain.com`
- Traefik dashboard: `https://traefik.your-domain.com`
- Portainer: `https://portainer.your-domain.com`

## Manual Deployment Steps

If you prefer manual deployment:

### 1. Create Docker Network

```bash
docker network create web
```

### 2. Build and Start Services

```bash
docker-compose build
docker-compose up -d
```

### 3. Check Service Status

```bash
docker-compose ps
docker-compose logs -f
```

## SSL Configuration

SSL certificates are automatically managed by Traefik using Cloudflare DNS challenge:

1. Ensure your domain is using Cloudflare nameservers
2. Generate a Global API Key in Cloudflare dashboard
3. Add the key to `.env.production`

Traefik will automatically:
- Request certificates from Let's Encrypt
- Validate via Cloudflare DNS
- Auto-renew certificates

## Database Management

### Backups

Automatic daily backups at 2 AM:
```bash
# Manual backup
docker-compose exec backup /backup.sh

# View backups
ls -la backups/

# Restore from backup
docker-compose exec -T postgres psql -U wnba wnba_fantasy < backups/wnba_backup_20240105_020000.sql
```

### Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision -m "description"
```

## Monitoring

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Application logs
tail -f logs/app.log
```

### Health Checks

```bash
# Check all services
curl https://your-domain.com/health
curl https://your-domain.com/api/v1/health

# Database connection
docker-compose exec postgres pg_isready
```

### Portainer

Access Portainer at `https://portainer.your-domain.com` for:
- Container management
- Resource monitoring
- Log viewing
- Shell access

## Admin Dashboard

The admin dashboard provides comprehensive system management:

1. Access at `https://your-domain.com` and login with admin credentials
2. Navigate to Admin section
3. Available features:
   - Data quality monitoring
   - System logs and audit trails
   - Team management
   - Manual data ingestion
   - Score recalculation

## Scheduled Jobs

The following jobs run automatically:

- **Data Ingestion**: Daily at 3:00 AM UTC
- **Score Calculation**: Daily at 3:30 AM UTC
- **Weekly Move Reset**: Mondays at 5:00 AM UTC
- **Bonus Calculation**: Mondays at 5:59 AM UTC
- **Player Updates**: Tuesdays at 2:00 AM UTC
- **Analytics**: Daily at 4:00 AM UTC
- **Draft Timers**: Every second
- **Database Backups**: Daily at 2:00 AM

View scheduled jobs:
```bash
curl https://your-domain.com/jobs
```

## Updating

To update the application:

```bash
cd /opt/wnba-fantasy
git pull
./scripts/deploy.sh production
```

## Troubleshooting

### Container Issues

```bash
# Restart a service
docker-compose restart backend

# Rebuild a service
docker-compose build --no-cache backend
docker-compose up -d backend

# View container details
docker inspect wnba-backend
```

### Database Issues

```bash
# Connect to database
docker-compose exec postgres psql -U wnba wnba_fantasy

# Check connections
SELECT pid, usename, application_name, state 
FROM pg_stat_activity;
```

### Traefik Issues

```bash
# Check Traefik logs
docker-compose logs -f traefik

# Verify certificates
docker-compose exec traefik cat /letsencrypt/acme.json
```

### Performance

```bash
# Check resource usage
docker stats

# System resources
htop

# Disk usage
df -h
```

## Security Checklist

- [ ] Change default SSH port
- [ ] Disable root SSH login
- [ ] Use SSH keys only
- [ ] Configure fail2ban
- [ ] Enable UFW firewall
- [ ] Use strong passwords
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Backup to external storage
- [ ] Use secure environment variables

## Maintenance

### Regular Tasks

Weekly:
- Check disk usage
- Review error logs
- Verify backups

Monthly:
- Update Docker images
- Review security logs
- Test backup restoration
- Update dependencies

### Commands Reference

```bash
# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Restart specific service
docker-compose restart backend

# View real-time logs
docker-compose logs -f

# Execute command in container
docker-compose exec backend python -m app.cli.main

# Database backup
docker-compose exec backup /backup.sh

# Clean up Docker
docker system prune -a
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs [service]`
2. Review this documentation
3. Check GitHub issues
4. Contact support

Remember to keep your environment variables secure and never commit them to version control!