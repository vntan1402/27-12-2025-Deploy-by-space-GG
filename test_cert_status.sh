#!/bin/bash

API_URL="https://fleet-cert-dash.preview.emergentagent.com/api"

# Login
TOKEN=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"123456"}' | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

echo "🔑 Token: ${TOKEN:0:20}..."

# Get ship ID
SHIP_ID=$(curl -s -X GET "${API_URL}/ships" \
  -H "Authorization: Bearer $TOKEN" | grep -o '"id":"[^"]*' | head -1 | sed 's/"id":"//')

echo "🚢 Ship ID: $SHIP_ID"

# Get crew
CREW_DATA=$(curl -s -X GET "${API_URL}/crew" -H "Authorization: Bearer $TOKEN")
CREW_ID=$(echo $CREW_DATA | grep -o '"id":"[^"]*' | head -1 | sed 's/"id":"//')
CREW_NAME=$(echo $CREW_DATA | grep -o '"full_name":"[^"]*' | head -1 | sed 's/"full_name":"//')
PASSPORT=$(echo $CREW_DATA | grep -o '"passport":"[^"]*' | head -1 | sed 's/"passport":"//')

echo "👤 Crew: $CREW_NAME (ID: $CREW_ID)"
echo ""

# Create 3 test certificates with different statuses

echo "📋 Test 1: Creating Valid certificate (expires in 2025)..."
curl -s -X POST "${API_URL}/crew-certificates/manual?ship_id=$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"crew_id\": \"$CREW_ID\",
    \"crew_name\": \"$CREW_NAME\",
    \"passport\": \"$PASSPORT\",
    \"cert_name\": \"Certificate of Competency (COC)\",
    \"cert_no\": \"COC-VALID-001\",
    \"issued_by\": \"Maritime Authority\",
    \"issued_date\": \"2024-01-15\",
    \"cert_expiry\": \"2025-12-31\",
    \"note\": \"Valid certificate\"
  }" | python3 -m json.tool | grep -E "cert_name|status"

echo ""
echo "📋 Test 2: Creating Expiring Soon certificate (expires in 60 days)..."
EXPIRING_DATE=$(date -u -d "+60 days" +%Y-%m-%d)
curl -s -X POST "${API_URL}/crew-certificates/manual?ship_id=$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"crew_id\": \"$CREW_ID\",
    \"crew_name\": \"$CREW_NAME\",
    \"passport\": \"$PASSPORT\",
    \"cert_name\": \"STCW Basic Safety Training\",
    \"cert_no\": \"STCW-EXPIRING-001\",
    \"issued_by\": \"Training Center\",
    \"issued_date\": \"2023-01-15\",
    \"cert_expiry\": \"$EXPIRING_DATE\",
    \"note\": \"Expiring soon\"
  }" | python3 -m json.tool | grep -E "cert_name|status"

echo ""
echo "📋 Test 3: Creating Expired certificate (expired in 2023)..."
curl -s -X POST "${API_URL}/crew-certificates/manual?ship_id=$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"crew_id\": \"$CREW_ID\",
    \"crew_name\": \"$CREW_NAME\",
    \"passport\": \"$PASSPORT\",
    \"cert_name\": \"Medical Certificate\",
    \"cert_no\": \"MED-EXPIRED-001\",
    \"issued_by\": \"Medical Center\",
    \"issued_date\": \"2022-01-15\",
    \"cert_expiry\": \"2023-01-15\",
    \"note\": \"Expired certificate\"
  }" | python3 -m json.tool | grep -E "cert_name|status"

echo ""
echo "📋 Getting all certificates to verify status calculation..."
curl -s -X GET "${API_URL}/crew-certificates/$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | grep -E "cert_name|cert_no|status" | head -20

