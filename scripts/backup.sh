#!/bin/sh

# Database backup script
# Runs daily at 2 AM via cron

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/wnba_backup_$TIMESTAMP.sql"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Perform backup
echo "Starting backup at $(date)"
PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h postgres -U $POSTGRES_USER -d $POSTGRES_DB > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

echo "Backup completed: ${BACKUP_FILE}.gz"

# Clean up old backups (keep last 7 days)
find $BACKUP_DIR -name "wnba_backup_*.sql.gz" -mtime +7 -delete

echo "Old backups cleaned up"

# Add cron job for daily backups at 2 AM
echo "0 2 * * * /backup.sh" > /etc/crontabs/root