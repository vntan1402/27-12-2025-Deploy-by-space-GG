#!/bin/bash

echo "🔍 Checking Crew Certificates Field Names"
echo "=========================================="

# Get backend URL
BACKEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
API="${BACKEND_URL}/api"

# Login
LOGIN_RESPONSE=$(curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"123456"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

# Get ship
SHIPS_RESPONSE=$(curl -s -X GET "$API/ships" \
  -H "Authorization: Bearer $TOKEN")

SHIP_ID=$(echo $SHIPS_RESPONSE | jq -r '.[0].id')
echo "📍 Ship ID: $SHIP_ID"
echo ""

# Get certificates
echo "📜 Getting crew certificates..."
CERTS=$(curl -s -X GET "$API/crew-certificates/$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Total certificates: $(echo $CERTS | jq 'length')"
echo ""

# Check first 3 certificates for field names
echo "🔍 Checking field names in certificates:"
echo "=========================================="
for i in 0 1 2; do
  CERT=$(echo $CERTS | jq ".[$i]")
  
  if [ "$CERT" != "null" ]; then
    CERT_NAME=$(echo $CERT | jq -r '.cert_name')
    CREW_NAME=$(echo $CERT | jq -r '.crew_name')
    
    # Check old field names
    OLD_FILE_ID=$(echo $CERT | jq -r '.cert_file_id // "null"')
    OLD_SUMMARY_ID=$(echo $CERT | jq -r '.cert_summary_file_id // "null"')
    
    # Check new field names
    NEW_FILE_ID=$(echo $CERT | jq -r '.crew_cert_file_id // "null"')
    NEW_SUMMARY_ID=$(echo $CERT | jq -r '.crew_cert_summary_file_id // "null"')
    
    echo ""
    echo "Certificate $((i+1)): $CREW_NAME - $CERT_NAME"
    echo "  Old fields:"
    echo "    cert_file_id: $OLD_FILE_ID"
    echo "    cert_summary_file_id: $OLD_SUMMARY_ID"
    echo "  New fields:"
    echo "    crew_cert_file_id: $NEW_FILE_ID"
    echo "    crew_cert_summary_file_id: $NEW_SUMMARY_ID"
  fi
done

echo ""
echo "=========================================="
