#!/bin/bash

# WNBA Fantasy League MVP Startup Script
# Quick start for local development/testing

set -e

echo "🏀 WNBA Fantasy League MVP"
echo "=========================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "🔨 Building containers..."
docker-compose -f docker-compose.mvp.yml build

echo ""
echo "🚀 Starting services..."
docker-compose -f docker-compose.mvp.yml up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo "🏥 Checking service health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend health check failed"
fi

echo ""
echo "🎉 MVP is ready!"
echo ""
echo "🔗 Access points:"
echo "   - Application: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "👤 Demo Accounts:"
echo "   - Admin: me@grantharris.tech / Thisisapassword1"
echo "   - User: demo@example.com / demo123"
echo ""
echo "📊 View logs: docker-compose -f docker-compose.mvp.yml logs -f"
echo "🛑 Stop: docker-compose -f docker-compose.mvp.yml down"
echo ""