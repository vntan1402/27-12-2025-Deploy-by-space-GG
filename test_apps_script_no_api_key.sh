#!/bin/bash

# =========================================================
# Test Google Apps Script (No API Key Version)
# =========================================================

echo "🧪 Testing Google Apps Script (No API Key)"
echo "==========================================="
echo ""

# Get Web App URL from user
read -p "Enter your Google Apps Script Web App URL: " WEB_APP_URL

if [ -z "$WEB_APP_URL" ]; then
  echo "❌ Error: Web App URL is required"
  exit 1
fi

echo ""
echo "📍 Testing URL: $WEB_APP_URL"
echo ""

# Test 1: GET Request (Should return HTML page)
echo "🔹 Test 1: GET Request"
echo "Expected: HTML page with status 'Active'"
GET_RESPONSE=$(curl -s -w "\n%{http_code}" "$WEB_APP_URL")
GET_HTTP_CODE=$(echo "$GET_RESPONSE" | tail -n1)
GET_BODY=$(echo "$GET_RESPONSE" | head -n-1)

if [ "$GET_HTTP_CODE" == "200" ]; then
  echo "✅ GET request successful (HTTP $GET_HTTP_CODE)"
  echo "Response preview: ${GET_BODY:0:200}..."
else
  echo "❌ GET request failed (HTTP $GET_HTTP_CODE)"
  echo "Response: $GET_BODY"
fi

echo ""
echo "-------------------------------------------"
echo ""

# Test 2: POST Request - Test Connection (WITHOUT API Key)
echo "🔹 Test 2: POST Request - Test Connection"
echo "Expected: JSON response with success=true"

POST_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test_connection"
  }')

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
      echo "✅ POST request successful! Apps Script is working correctly."
      echo "🎉 You can now configure this URL in the System Settings."
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
    echo "1. Create a NEW deployment in Google Apps Script"
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
echo "==========================================="
echo "Test complete!"
echo ""
