#!/usr/bin/env bash
# cron/setup-cron.sh — installs daily cron at 15:00

set -e

LOG_FILE="/home/vfalbor/hnreviewer/data/cron.log"
CRON_LINE="0 15 * * * docker exec hnreviewer node /app/src/orchestrator/run.js >> $LOG_FILE 2>&1"

if crontab -l 2>/dev/null | grep -qF 'hnreviewer'; then
  echo "Removing old cron entry..."
  crontab -l 2>/dev/null | grep -vF 'hnreviewer' | crontab -
fi

(crontab -l 2>/dev/null; echo "# hnreviewer"; echo "$CRON_LINE") | crontab -

echo "Cron installed: $CRON_LINE"
echo "Logs: $LOG_FILE"
echo ""
echo "Manual test: docker exec hnreviewer node /app/src/orchestrator/run.js"
