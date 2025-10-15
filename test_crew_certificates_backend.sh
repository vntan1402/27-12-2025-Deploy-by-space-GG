#!/bin/bash

# Test script for Crew Certificates Backend APIs (Steps 1-5)

API_URL="https://crew-cert-manager.preview.emergentagent.com/api"

echo "=========================================="
echo "CREW CERTIFICATES BACKEND API TESTING"
echo "=========================================="
echo ""

# Step 1: Login to get auth token
echo "Step 1: Authenticating..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"123456"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed!"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Login successful!"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Step 2: Get ships list to get ship_id
echo "Step 2: Getting ships list..."
SHIPS_RESPONSE=$(curl -s -X GET "${API_URL}/ships" \
  -H "Authorization: Bearer $TOKEN")

echo "Ships Response: $SHIPS_RESPONSE" | head -c 200
echo ""

# Extract first ship_id (you may need to adjust this based on actual response)
SHIP_ID=$(echo $SHIPS_RESPONSE | grep -o '"id":"[^"]*' | head -1 | sed 's/"id":"//')

if [ -z "$SHIP_ID" ]; then
  echo "❌ No ships found!"
  exit 1
fi

echo "✅ Found ship ID: $SHIP_ID"
echo ""

# Step 3: Get crew members to get crew_id
echo "Step 3: Getting crew members..."
CREW_RESPONSE=$(curl -s -X GET "${API_URL}/crew" \
  -H "Authorization: Bearer $TOKEN")

echo "Crew Response: $CREW_RESPONSE" | head -c 200
echo ""

# Extract first crew_id
CREW_ID=$(echo $CREW_RESPONSE | grep -o '"id":"[^"]*' | head -1 | sed 's/"id":"//')
CREW_NAME=$(echo $CREW_RESPONSE | grep -o '"full_name":"[^"]*' | head -1 | sed 's/"full_name":"//')
PASSPORT=$(echo $CREW_RESPONSE | grep -o '"passport":"[^"]*' | head -1 | sed 's/"passport":"//')

if [ -z "$CREW_ID" ]; then
  echo "❌ No crew members found!"
  exit 1
fi

echo "✅ Found crew: $CREW_NAME (ID: $CREW_ID, Passport: $PASSPORT)"
echo ""

# Step 4: Test Manual Certificate Creation (POST /crew-certificates/manual)
echo "Step 4: Testing Manual Certificate Creation..."
CREATE_CERT_RESPONSE=$(curl -s -X POST "${API_URL}/crew-certificates/manual?ship_id=$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"crew_id\": \"$CREW_ID\",
    \"crew_name\": \"$CREW_NAME\",
    \"passport\": \"$PASSPORT\",
    \"cert_name\": \"Certificate of Competency (COC)\",
    \"cert_no\": \"COC-2024-001\",
    \"issued_by\": \"Maritime Authority\",
    \"issued_date\": \"2024-01-15\",
    \"cert_expiry\": \"2029-01-15\",
    \"note\": \"Test certificate created via API\"
  }")

echo "Create Certificate Response:"
echo "$CREATE_CERT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CREATE_CERT_RESPONSE"
echo ""

# Extract certificate ID
CERT_ID=$(echo $CREATE_CERT_RESPONSE | grep -o '"id":"[^"]*' | head -1 | sed 's/"id":"//')

if [ -z "$CERT_ID" ]; then
  echo "⚠️ Certificate creation might have failed"
else
  echo "✅ Certificate created with ID: $CERT_ID"
fi
echo ""

# Step 5: Test Get Certificates (GET /crew-certificates/{ship_id})
echo "Step 5: Testing Get Certificates..."
GET_CERTS_RESPONSE=$(curl -s -X GET "${API_URL}/crew-certificates/$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Get Certificates Response:"
echo "$GET_CERTS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$GET_CERTS_RESPONSE"
echo ""

# Count certificates
CERT_COUNT=$(echo $GET_CERTS_RESPONSE | grep -o '"id":"[^"]*' | wc -l)
echo "✅ Found $CERT_COUNT certificate(s)"
echo ""

# Step 6: Test Get Certificates with Crew Filter
if [ ! -z "$CREW_ID" ]; then
  echo "Step 6: Testing Get Certificates with Crew Filter..."
  GET_CREW_CERTS_RESPONSE=$(curl -s -X GET "${API_URL}/crew-certificates/$SHIP_ID?crew_id=$CREW_ID" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "Get Crew Certificates Response:"
  echo "$GET_CREW_CERTS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$GET_CREW_CERTS_RESPONSE"
  echo ""
  
  CREW_CERT_COUNT=$(echo $GET_CREW_CERTS_RESPONSE | grep -o '"id":"[^"]*' | wc -l)
  echo "✅ Found $CREW_CERT_COUNT certificate(s) for crew member"
  echo ""
fi

# Step 7: Test Update Certificate (if we have a cert_id)
if [ ! -z "$CERT_ID" ]; then
  echo "Step 7: Testing Update Certificate..."
  UPDATE_CERT_RESPONSE=$(curl -s -X PUT "${API_URL}/crew-certificates/$CERT_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "note": "Updated certificate note via API test"
    }')
  
  echo "Update Certificate Response:"
  echo "$UPDATE_CERT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPDATE_CERT_RESPONSE"
  echo ""
  
  if echo "$UPDATE_CERT_RESPONSE" | grep -q '"id"'; then
    echo "✅ Certificate updated successfully"
  else
    echo "⚠️ Certificate update might have failed"
  fi
  echo ""
fi

# Step 8: Test Delete Certificate (if we have a cert_id)
if [ ! -z "$CERT_ID" ]; then
  echo "Step 8: Testing Delete Certificate..."
  DELETE_CERT_RESPONSE=$(curl -s -X DELETE "${API_URL}/crew-certificates/$CERT_ID" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "Delete Certificate Response:"
  echo "$DELETE_CERT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$DELETE_CERT_RESPONSE"
  echo ""
  
  if echo "$DELETE_CERT_RESPONSE" | grep -q '"success".*true'; then
    echo "✅ Certificate deleted successfully"
  else
    echo "⚠️ Certificate deletion might have failed"
  fi
  echo ""
fi

echo "=========================================="
echo "BACKEND API TESTING COMPLETED"
echo "=========================================="
echo ""
echo "Summary:"
echo "- Manual Certificate Creation: Tested"
echo "- Get All Certificates: Tested"
echo "- Get Crew Certificates (filtered): Tested"
echo "- Update Certificate: Tested"
echo "- Delete Certificate: Tested"
echo ""
echo "Note: File upload (analyze-file endpoint) requires actual file content"
echo "      and will be tested separately during frontend integration."
