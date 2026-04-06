#!/usr/bin/env bash
# cron/setup-cron.sh — installs daily cron at 15:00 UTC

set -e

LOG_FILE="/home/vfalbor/hnreviewer/data/cron.log"
CRON_LINE="0 15 * * * cd /home/vfalbor/hnreviewer && npm run review >> $LOG_FILE 2>&1"

if crontab -l 2>/dev/null | grep -qF "hnreviewer"; then
  echo "Removing old cron entry..."
  crontab -l 2>/dev/null | grep -vF "hnreviewer" | crontab -
fi

(crontab -l 2>/dev/null; echo "# hnreviewer"; echo "$CRON_LINE") | crontab -

echo "Cron installed: $CRON_LINE"
echo "Logs: $LOG_FILE"
echo ""
echo "Manual test: cd /home/vfalbor/hnreviewer && npm run review"
