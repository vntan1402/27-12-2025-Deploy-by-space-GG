#!/bin/bash

echo "=========================================="
echo "Certificate Update Logs Checker"
echo "=========================================="
echo ""
echo "Instructions:"
echo "1. Open the app in browser"
echo "2. Edit a Ship Certificate"
echo "3. Update the Next Survey field to: 13/12/2025"
echo "4. Click 'Update Certificate'"
echo "5. Come back here and press Enter"
echo ""
read -p "Press Enter after you've updated the certificate..."

echo ""
echo "Checking backend logs for DEBUG messages..."
echo "=========================================="

# Get the last 200 lines and filter for certificate update logs
tail -n 200 /var/log/supervisor/backend.err.log | grep -A 5 -B 2 "DEBUG"

echo ""
echo "=========================================="
echo "Log check complete!"
