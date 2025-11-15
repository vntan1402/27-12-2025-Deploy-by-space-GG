#!/bin/bash
# Update supervisor config to use new backend structure

CONFIG_FILE="/etc/supervisor/conf.d/supervisord.conf"

# Backup original
sudo cp $CONFIG_FILE ${CONFIG_FILE}.backup

# Update backend command
sudo sed -i 's|command=/root/.venv/bin/uvicorn server:app|command=/root/.venv/bin/uvicorn app.main:app|' $CONFIG_FILE

echo "✅ Supervisor config updated"
echo "Old: uvicorn server:app"
echo "New: uvicorn app.main:app"
echo ""
echo "Now run: sudo supervisorctl reread && sudo supervisorctl update && sudo supervisorctl restart backend"
