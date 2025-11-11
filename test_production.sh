#!/bin/bash

# Script kiểm tra Production endpoints
DOMAIN="https://nautical-records.emergent.cloud"

echo "======================================================================="
echo "  KIỂM TRA PRODUCTION - NAUTICAL RECORDS"
echo "======================================================================="
echo ""
echo "Domain: $DOMAIN"
echo ""

# Test 1: Admin Status
echo "1️⃣  Testing Admin Status"
echo "-----------------------------------------------------------------------"
echo "GET $DOMAIN/api/admin/status"
echo ""
ADMIN_STATUS=$(curl -s "$DOMAIN/api/admin/status" 2>&1)
echo "$ADMIN_STATUS" | python3 -m json.tool 2>/dev/null || echo "$ADMIN_STATUS"
echo ""

if echo "$ADMIN_STATUS" | grep -q "admin_exists.*true"; then
    echo "✅ Admin exists"
elif echo "$ADMIN_STATUS" | grep -q "admin_exists.*false"; then
    echo "❌ Admin does NOT exist - Database is empty!"
else
    echo "⚠️  Cannot determine admin status"
fi
echo ""

# Test 2: Companies Endpoint
echo "2️⃣  Testing Companies Endpoint"
echo "-----------------------------------------------------------------------"
echo "GET $DOMAIN/api/companies"
echo ""
COMPANIES=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$DOMAIN/api/companies" 2>&1)
HTTP_CODE=$(echo "$COMPANIES" | grep HTTP_CODE | cut -d: -f2)
BODY=$(echo "$COMPANIES" | grep -v HTTP_CODE)

echo "HTTP Status: $HTTP_CODE"
echo "Response:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" = "500" ]; then
    echo "❌ 500 ERROR - This is the problem!"
elif [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Endpoint working"
else
    echo "⚠️  Unexpected status: $HTTP_CODE"
fi
echo ""

# Test 3: Health Check
echo "3️⃣  Testing Health Endpoint"
echo "-----------------------------------------------------------------------"
echo "GET $DOMAIN/api/health"
echo ""
HEALTH=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$DOMAIN/api/health" 2>&1)
HTTP_CODE=$(echo "$HEALTH" | grep HTTP_CODE | cut -d: -f2)
BODY=$(echo "$HEALTH" | grep -v HTTP_CODE)

echo "HTTP Status: $HTTP_CODE"
echo "Response: $BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Backend is running"
else
    echo "❌ Backend health check failed"
fi
echo ""

# Test 4: Login Attempt (will fail if no admin)
echo "4️⃣  Testing Login (with test credentials)"
echo "-----------------------------------------------------------------------"
echo "POST $DOMAIN/api/auth/login"
echo ""

LOGIN_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$DOMAIN/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"system_admin","password":"test"}' 2>&1)
  
HTTP_CODE=$(echo "$LOGIN_RESPONSE" | grep HTTP_CODE | cut -d: -f2)
BODY=$(echo "$LOGIN_RESPONSE" | grep -v HTTP_CODE)

echo "HTTP Status: $HTTP_CODE"
echo "Response:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Login working (but password might be wrong)"
elif echo "$BODY" | grep -q "Invalid credentials"; then
    echo "⚠️  Admin exists but wrong password"
elif echo "$BODY" | grep -q "User not found"; then
    echo "❌ Admin does not exist"
else
    echo "❌ Login endpoint error"
fi
echo ""

# Summary
echo "======================================================================="
echo "  SUMMARY"
echo "======================================================================="
echo ""

ISSUES=0

if echo "$ADMIN_STATUS" | grep -q "admin_exists.*false"; then
    echo "❌ Issue 1: Admin does not exist in database"
    ISSUES=$((ISSUES + 1))
fi

if echo "$COMPANIES" | grep -q "HTTP_CODE:500"; then
    echo "❌ Issue 2: /api/companies returns 500 error"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo "✅ No critical issues detected"
else
    echo ""
    echo "🔥 Found $ISSUES critical issue(s)"
    echo ""
    echo "📋 RECOMMENDED ACTIONS:"
    echo ""
    echo "1. Contact Emergent Support:"
    echo "   Discord: https://discord.gg/VzKfwCXC4A"
    echo "   Email: support@emergent.sh"
    echo ""
    echo "2. Share these files with support:"
    echo "   - /app/production_users_export.json"
    echo "   - /app/production_companies_export.json"
    echo "   - /app/IMPORT_INSTRUCTIONS_FOR_SUPPORT.md"
    echo ""
    echo "3. Request database import"
    echo ""
    echo "4. OR re-deploy with environment variables:"
    echo "   - INIT_ADMIN_USERNAME=system_admin"
    echo "   - INIT_ADMIN_PASSWORD=YourSecure@Pass2024"
    echo "   - INIT_ADMIN_EMAIL=admin@nautical-records.com"
    echo "   - INIT_ADMIN_FULL_NAME=System Administrator"
    echo "   - INIT_COMPANY_NAME=Nautical Records Company"
fi

echo ""
echo "======================================================================="
