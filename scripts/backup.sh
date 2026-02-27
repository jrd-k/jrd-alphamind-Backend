#!/bin/bash
# simple backup script for database and redis
# usage: ./scripts/backup.sh /path/to/backup/dir
# requires pg_dump and redis-cli installed

set -e
BACKUP_DIR=${1:-/tmp/alphamind-backup}
DATE=$(date +"%Y%m%d_%H%M")

mkdir -p "$BACKUP_DIR"

echo "Backing up Postgres..."
pg_dump "$DATABASE_URL" -Fc -f "$BACKUP_DIR/postgres_$DATE.dump"

echo "Backing up Redis..."
redis-cli -u "$REDIS_URL" SAVE
# copy dump from redis server if persistent store
# assuming redis is using appendonly, just tar the file
if [[ -f "/var/lib/redis/appendonly.aof" ]]; then
  cp /var/lib/redis/appendonly.aof "$BACKUP_DIR/redis_$DATE.aof"
fi

echo "Backup completed: $BACKUP_DIR"