#!/bin/bash

# WNBA Fantasy League VPS Setup Script
# Run this on a fresh Ubuntu/Debian VPS

set -e

echo "🏀 WNBA Fantasy League VPS Setup"
echo "================================"
echo ""

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
apt-get install -y \
    curl \
    git \
    htop \
    vim \
    ufw \
    fail2ban \
    ca-certificates \
    gnupg \
    lsb-release

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "🎼 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

# Configure firewall
echo "🔥 Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban
echo "🛡️  Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Create app directory
echo "📁 Creating application directory..."
mkdir -p /opt/wnba-fantasy
cd /opt/wnba-fantasy

# Clone repository
echo "📥 Cloning repository..."
if [ ! -d ".git" ]; then
    git clone https://github.com/grantharris33/WNBA-Fantasy-League-2.git .
else
    echo "Repository already cloned, pulling latest..."
    git pull
fi

# Create required directories
mkdir -p logs backups letsencrypt

# Set up swap (recommended for smaller VPS)
echo "💾 Setting up swap file..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
else
    echo "Swap already configured"
fi

# Set up automatic updates
echo "🔄 Configuring automatic security updates..."
apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Create systemd service for auto-start
echo "⚙️  Creating systemd service..."
cat > /etc/systemd/system/wnba-fantasy.service << EOF
[Unit]
Description=WNBA Fantasy League
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/wnba-fantasy
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable wnba-fantasy

# Set up cron for backups
echo "⏰ Setting up backup cron..."
(crontab -l 2>/dev/null; echo "0 3 * * * cd /opt/wnba-fantasy && docker-compose exec -T backup /backup.sh") | crontab -

echo ""
echo "✅ VPS setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Copy your .env.production file to /opt/wnba-fantasy/"
echo "2. Update the environment variables with your values"
echo "3. Run: cd /opt/wnba-fantasy && ./scripts/deploy.sh"
echo ""
echo "🔒 Security recommendations:"
echo "- Change SSH port in /etc/ssh/sshd_config"
echo "- Disable root login"
echo "- Use SSH keys instead of passwords"
echo "- Set up regular backups to external storage"