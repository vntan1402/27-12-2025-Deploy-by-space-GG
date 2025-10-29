#!/bin/bash

echo "=========================================="
echo "Testing Google Apps Script with API Key"
echo "=========================================="

# Apps Script Web App URL (replace with actual URL)
WEB_APP_URL="https://script.google.com/macros/s/YOUR_WEB_APP_URL/exec"

API_KEY="Vntan1402sms"
FOLDER_ID="1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"

echo ""
echo "Test 1: Without API Key (Should fail)"
echo "--------------------------------------"
curl -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test_connection"
  }' \
  2>&1 | jq '.' || echo "Response: $?"

echo ""
echo ""
echo "Test 2: With WRONG API Key (Should fail)"
echo "--------------------------------------"
curl -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test_connection",
    "api_key": "wrong_key_123"
  }' \
  2>&1 | jq '.' || echo "Response: $?"

echo ""
echo ""
echo "Test 3: With CORRECT API Key (Should succeed)"
echo "--------------------------------------"
curl -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"action\": \"test_connection\",
    \"api_key\": \"$API_KEY\"
  }" \
  2>&1 | jq '.' || echo "Response: $?"

echo ""
echo ""
echo "Test 4: Create folder with API Key"
echo "--------------------------------------"
curl -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"action\": \"create_folder\",
    \"api_key\": \"$API_KEY\",
    \"parent_id\": \"$FOLDER_ID\",
    \"folder_name\": \"test-$(date +%Y-%m-%d)\"
  }" \
  2>&1 | jq '.' || echo "Response: $?"

echo ""
echo "=========================================="
echo "Testing complete!"
echo "=========================================="
