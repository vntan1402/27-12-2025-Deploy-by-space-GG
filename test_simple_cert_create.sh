#!/bin/bash

API_URL="https://maritime-docs-1.preview.emergentagent.com/api"

# Login
TOKEN=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"123456"}' | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

echo "Token: ${TOKEN:0:20}..."

# Get ship ID
SHIP_ID=$(curl -s -X GET "${API_URL}/ships" \
  -H "Authorization: Bearer $TOKEN" | grep -o '"id":"[^"]*' | head -1 | sed 's/"id":"//')

echo "Ship ID: $SHIP_ID"

# Get crew
CREW_ID=$(curl -s -X GET "${API_URL}/crew" \
  -H "Authorization: Bearer $TOKEN" | grep -o '"id":"[^"]*' | head -1 | sed 's/"id":"//')

CREW_NAME=$(curl -s -X GET "${API_URL}/crew" \
  -H "Authorization: Bearer $TOKEN" | grep -o '"full_name":"[^"]*' | head -1 | sed 's/"full_name":"//')

PASSPORT=$(curl -s -X GET "${API_URL}/crew" \
  -H "Authorization: Bearer $TOKEN" | grep -o '"passport":"[^"]*' | head -1 | sed 's/"passport":"//')

echo "Crew: $CREW_NAME (ID: $CREW_ID)"

# Create certificate
echo "Creating certificate..."
curl -X POST "${API_URL}/crew-certificates/manual?ship_id=$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"crew_id\": \"$CREW_ID\",
    \"crew_name\": \"$CREW_NAME\",
    \"passport\": \"$PASSPORT\",
    \"cert_name\": \"COC Test\",
    \"cert_no\": \"COC-001\",
    \"issued_by\": \"Maritime Authority\",
    \"issued_date\": \"2024-01-15\",
    \"cert_expiry\": \"2029-01-15\",
    \"note\": \"Test\"
  }" | python3 -m json.tool

echo ""
echo "Getting certificates..."
curl -s -X GET "${API_URL}/crew-certificates/$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

