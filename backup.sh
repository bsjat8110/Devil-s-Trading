#!/bin/bash

BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "📦 Creating backup..."

mkdir -p $BACKUP_DIR

# Backup database
cp data/trades.db "$BACKUP_DIR/trades_$DATE.db"

# Backup logs
if [ -f "data/trading.log" ]; then
    cp data/trading.log "$BACKUP_DIR/trading_$DATE.log"
fi

# Backup .env (encrypted)
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/env_$DATE.backup"
fi

echo "✅ Backup created: $BACKUP_DIR"
ls -lh $BACKUP_DIR/*$DATE*
