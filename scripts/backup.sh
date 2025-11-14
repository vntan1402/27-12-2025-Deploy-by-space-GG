#!/bin/bash

# ============================================
# Automatic Backup Script
# Backs up MongoDB database daily
# ============================================

set -e

# Configuration
MONGO_HOST="${MONGO_HOST:-mongodb}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_USER="${MONGO_USER:-admin}"
MONGO_PASS="${MONGO_PASS:-SecurePass123}"
MONGO_DB="${MONGO_DB:-company_offline}"

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${MONGO_DB}_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}.archive"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "Ship Management - Automatic Backup"
echo "============================================"
echo "Database: ${MONGO_DB}"
echo "Timestamp: ${TIMESTAMP}"
echo "============================================"

# Create backup directory if not exists
mkdir -p "${BACKUP_DIR}"

# Perform backup
echo -e "${YELLOW}Starting backup...${NC}"
mongodump \
  --uri="mongodb://${MONGO_USER}:${MONGO_PASS}@${MONGO_HOST}:${MONGO_PORT}" \
  --db="${MONGO_DB}" \
  --archive="${BACKUP_PATH}" \
  --gzip \
  2>&1 | grep -v "warning"

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    echo -e "${GREEN}✅ Backup completed successfully${NC}"
    echo "   File: ${BACKUP_NAME}.archive"
    echo "   Size: ${BACKUP_SIZE}"
else
    echo -e "${RED}❌ Backup failed${NC}"
    exit 1
fi

# Create metadata file
cat > "${BACKUP_DIR}/${BACKUP_NAME}.json" <<EOF
{
  "database": "${MONGO_DB}",
  "timestamp": "${TIMESTAMP}",
  "host": "${MONGO_HOST}",
  "backup_file": "${BACKUP_NAME}.archive",
  "backup_size": "$(stat -f%z "${BACKUP_PATH}" 2>/dev/null || stat -c%s "${BACKUP_PATH}")",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo -e "${GREEN}✅ Metadata created${NC}"

# Cleanup old backups (keep last 7 days)
echo -e "${YELLOW}Cleaning up old backups...${NC}"
RETENTION_DAYS=7
find "${BACKUP_DIR}" -name "backup_*.archive" -type f -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "backup_*.json" -type f -mtime +${RETENTION_DAYS} -delete

REMAINING_BACKUPS=$(ls -1 "${BACKUP_DIR}"/backup_*.archive 2>/dev/null | wc -l)
echo -e "${GREEN}✅ Cleanup completed${NC}"
echo "   Remaining backups: ${REMAINING_BACKUPS}"

# Calculate total backup size
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
echo "   Total backup size: ${TOTAL_SIZE}"

echo "============================================"
echo -e "${GREEN}Backup process completed${NC}"
echo "============================================"

exit 0
