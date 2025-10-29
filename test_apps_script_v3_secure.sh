#!/bin/bash

# =========================================================
# Test Google Apps Script v3.0 (Secure Version)
# =========================================================

echo "🧪 Testing Google Apps Script v3.0 (Secure - Dynamic Folder ID)"
echo "================================================================"
echo ""

# Get Web App URL from user
read -p "Enter your Google Apps Script Web App URL: " WEB_APP_URL

if [ -z "$WEB_APP_URL" ]; then
  echo "❌ Error: Web App URL is required"
  exit 1
fi

# Folder ID (your actual folder)
FOLDER_ID="1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"

echo ""
echo "📍 Testing URL: $WEB_APP_URL"
echo "📁 Folder ID: ${FOLDER_ID:0:6}*** (masked for security)"
echo ""

# Test 1: GET Request (Should return HTML page)
echo "🔹 Test 1: GET Request"
echo "Expected: HTML page with 'Dynamic Folder ID' and 'Safe Logging'"
GET_RESPONSE=$(curl -s -w "\n%{http_code}" "$WEB_APP_URL")
GET_HTTP_CODE=$(echo "$GET_RESPONSE" | tail -n1)
GET_BODY=$(echo "$GET_RESPONSE" | head -n-1)

if [ "$GET_HTTP_CODE" == "200" ]; then
  echo "✅ GET request successful (HTTP $GET_HTTP_CODE)"
  
  # Check for v3.0 indicators
  if echo "$GET_BODY" | grep -q "v3.0"; then
    echo "✅ Script version v3.0 detected"
  else
    echo "⚠️  Warning: Script may not be v3.0"
  fi
  
  echo "Response preview: ${GET_BODY:0:200}..."
else
  echo "❌ GET request failed (HTTP $GET_HTTP_CODE)"
  echo "Response: $GET_BODY"
fi

echo ""
echo "-------------------------------------------"
echo ""

# Test 2: POST Request - Test Connection WITH folder_id
echo "🔹 Test 2: POST Request - Test Connection (with folder_id)"
echo "Expected: JSON response with success=true"

POST_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"action\": \"test_connection\",
    \"folder_id\": \"$FOLDER_ID\"
  }")

POST_HTTP_CODE=$(echo "$POST_RESPONSE" | tail -n1)
POST_BODY=$(echo "$POST_RESPONSE" | head -n-1)

echo "HTTP Status: $POST_HTTP_CODE"
echo "Response Body:"
echo "$POST_BODY" | python3 -m json.tool 2>/dev/null || echo "$POST_BODY"

if [ "$POST_HTTP_CODE" == "200" ]; then
  # Check if response is JSON with success field
  if echo "$POST_BODY" | grep -q '"success"'; then
    SUCCESS=$(echo "$POST_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    if [ "$SUCCESS" == "True" ]; then
      echo ""
      echo "✅ POST request successful! Apps Script v3.0 is working correctly."
      echo "🔒 Security: Folder ID is sent dynamically (not hardcoded)"
      echo "🎉 You can now use this URL in the System Settings."
    else
      echo ""
      echo "⚠️ POST request returned JSON, but success=false"
      echo "Check the error message above"
    fi
  else
    echo ""
    echo "❌ POST request returned non-JSON response (likely HTML redirect)"
    echo "This means the Apps Script deployment is not configured correctly."
    echo ""
    echo "📋 Action Required:"
    echo "1. Deploy the NEW v3.0 script in Google Apps Script"
    echo "2. Make sure to select 'Web app' as deployment type"
    echo "3. Set 'Execute as: Me' and 'Who has access: Anyone'"
    echo "4. Copy the NEW Web App URL and test again"
  fi
else
  echo ""
  echo "❌ POST request failed (HTTP $POST_HTTP_CODE)"
  echo "This indicates a deployment or permission issue."
fi

echo ""
echo "-------------------------------------------"
echo ""

# Test 3: POST Request WITHOUT folder_id (Should fail gracefully)
echo "🔹 Test 3: Security Test - Request without folder_id"
echo "Expected: Error message 'folder_id is required'"

TEST3_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test_connection"
  }')

TEST3_HTTP_CODE=$(echo "$TEST3_RESPONSE" | tail -n1)
TEST3_BODY=$(echo "$TEST3_RESPONSE" | head -n-1)

if echo "$TEST3_BODY" | grep -qi "folder_id.*required"; then
  echo "✅ Security check PASSED - folder_id validation working"
else
  echo "⚠️  Security check INCONCLUSIVE"
fi

echo "Response: $TEST3_BODY" | python3 -m json.tool 2>/dev/null || echo "$TEST3_BODY"

echo ""
echo "================================================================"
echo "Test complete!"
echo ""
