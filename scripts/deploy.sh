#!/bin/bash

# WNBA Fantasy League Deployment Script
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.yml"

echo "🏀 WNBA Fantasy League Deployment Script"
echo "========================================"
echo "Environment: $ENVIRONMENT"
echo ""

# Check if .env file exists
if [ ! -f ".env.$ENVIRONMENT" ]; then
    echo "❌ Error: .env.$ENVIRONMENT file not found!"
    echo "Please create it from .env.production template"
    exit 1
fi

# Load environment variables
export $(cat .env.$ENVIRONMENT | grep -v '^#' | xargs)

# Check required variables
required_vars=(
    "DOMAIN"
    "POSTGRES_PASSWORD"
    "SECRET_KEY"
    "RAPIDAPI_KEY"
    "CF_API_EMAIL"
    "CF_API_KEY"
    "TRAEFIK_DASHBOARD_AUTH"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set in .env.$ENVIRONMENT"
        exit 1
    fi
done

echo "✅ Environment variables loaded"

# Create required directories
echo "📁 Creating required directories..."
mkdir -p logs backups letsencrypt

# Create docker network if not exists
echo "🌐 Setting up Docker network..."
docker network create web 2>/dev/null || echo "Network 'web' already exists"

# Build images
echo "🔨 Building Docker images..."
docker-compose build --no-cache

# Pull latest images
echo "📥 Pulling latest base images..."
docker-compose pull

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
services=("postgres" "backend" "frontend" "traefik" "portainer")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose ps | grep -q "${service}.*Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running properly"
        all_healthy=false
    fi
done

if [ "$all_healthy" = true ]; then
    echo ""
    echo "🎉 Deployment successful!"
    echo ""
    echo "🔗 Access points:"
    echo "   - Application: https://$DOMAIN"
    echo "   - Traefik Dashboard: https://traefik.$DOMAIN"
    echo "   - Portainer: https://portainer.$DOMAIN"
    echo ""
    echo "📊 View logs with: docker-compose logs -f [service]"
    echo "🔄 Update with: git pull && ./deploy.sh"
else
    echo ""
    echo "⚠️  Some services failed to start properly"
    echo "Check logs with: docker-compose logs [service]"
    exit 1
fi