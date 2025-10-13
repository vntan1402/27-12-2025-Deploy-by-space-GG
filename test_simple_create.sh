#!/bin/bash

API_URL="https://crew-cert-tracker.preview.emergentagent.com/api"

TOKEN=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"123456"}' | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

SHIP_ID="7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7"
CREW_ID="d4e75288-986b-43ea-8be5-2a9b987c3515"

echo "Creating certificate..."
curl -X POST "${API_URL}/crew-certificates/manual?ship_id=$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "crew_id": "d4e75288-986b-43ea-8be5-2a9b987c3515",
    "crew_name": "HO SY CHUONG",
    "passport": "C13996116",
    "cert_name": "COC Test",
    "cert_no": "COC-999",
    "issued_by": "Authority",
    "issued_date": "2024-01-15",
    "cert_expiry": "2025-12-31",
    "note": "Test"
  }' 

echo ""
echo ""
echo "Getting certificates..."
curl -s -X GET "${API_URL}/crew-certificates/$SHIP_ID" \
  -H "Authorization: Bearer $TOKEN"

