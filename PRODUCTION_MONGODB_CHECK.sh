#!/bin/bash

# Script để kiểm tra MongoDB production setup
# Chạy script này để verify production MongoDB connection

echo "======================================================================="
echo "  KIỂM TRA MONGODB PRODUCTION SETUP"
echo "======================================================================="
echo ""

# 1. Check environment variables
echo "1️⃣  ENVIRONMENT VARIABLES"
echo "-----------------------------------------------------------------------"
if grep -q "MONGO_URL" /app/backend/.env 2>/dev/null; then
    echo "✅ MONGO_URL found in .env"
    MONGO_URL=$(grep MONGO_URL /app/backend/.env | cut -d'=' -f2-)
    
    # Parse connection string (hide password)
    if [[ $MONGO_URL == *"@"* ]]; then
        echo "   Authentication: Yes"
        HOST=$(echo $MONGO_URL | sed 's/.*@\(.*\)\/.*/.../\1\/.../')
        echo "   Connection: mongodb://***:***@$HOST"
    else
        echo "   Authentication: No"
        echo "   Connection: $MONGO_URL"
    fi
else
    echo "❌ MONGO_URL not found in .env"
fi
echo ""

# 2. Check MongoDB version expectation
echo "2️⃣  EXPECTED MONGODB VERSION"
echo "-----------------------------------------------------------------------"
echo "   Development: MongoDB 7.0.25"
echo "   Production:  MongoDB 5.x - 7.x (Emergent managed)"
echo ""

# 3. Database structure
echo "3️⃣  DATABASE STRUCTURE"
echo "-----------------------------------------------------------------------"
echo "   Database Name:     ship_management"
echo "   Collections:       21"
echo "   Critical Collections:"
echo "     - users"
echo "     - companies"
echo "     - ships"
echo "     - certificates"
echo "     - crew_members"
echo ""

# 4. Required indexes
echo "4️⃣  REQUIRED INDEXES"
echo "-----------------------------------------------------------------------"
echo "   users.username (unique)"
echo "   users.email (unique, sparse)"
echo "   companies.tax_id (unique)"
echo "   ships.imo + company (unique compound)"
echo ""

# 5. Connection test (if in production environment)
echo "5️⃣  CONNECTION TEST"
echo "-----------------------------------------------------------------------"
if command -v curl &> /dev/null; then
    echo "   Testing API endpoint..."
    RESPONSE=$(curl -s https://nautical-records.emergent.cloud/api/admin/status 2>&1)
    
    if [[ $RESPONSE == *"admin_exists"* ]]; then
        echo "   ✅ API responding"
        if [[ $RESPONSE == *"true"* ]]; then
            echo "   ✅ Admin exists in database"
        else
            echo "   ⚠️  Admin does not exist"
        fi
    else
        echo "   ❌ API not responding or error"
    fi
else
    echo "   ⚠️  curl not available - skipping API test"
fi
echo ""

# 6. Permissions check
echo "6️⃣  REQUIRED PERMISSIONS"
echo "-----------------------------------------------------------------------"
echo "   MongoDB user must have:"
echo "     - readWrite on ship_management database"
echo "     - createIndex permission"
echo "     - createCollection permission"
echo ""

# 7. Wrapper class check
echo "7️⃣  MONGODB WRAPPER"
echo "-----------------------------------------------------------------------"
if [ -f "/app/backend/mongodb_database.py" ]; then
    echo "   ✅ MongoDatabase wrapper found"
    
    # Check if create method exists
    if grep -q "async def create" /app/backend/mongodb_database.py; then
        echo "   ✅ create() method available"
    fi
    
    if grep -q "async def find_one" /app/backend/mongodb_database.py; then
        echo "   ✅ find_one() method available"
    fi
    
    if grep -q "async def update" /app/backend/mongodb_database.py; then
        echo "   ✅ update() method available"
    fi
else
    echo "   ❌ MongoDatabase wrapper not found"
fi
echo ""

# 8. Startup script check
echo "8️⃣  ADMIN INITIALIZATION"
echo "-----------------------------------------------------------------------"
if [ -f "/app/backend/init_admin_startup.py" ]; then
    echo "   ✅ init_admin_startup.py found"
    
    # Check if using wrapper methods
    if grep -q "mongo_db.create" /app/backend/init_admin_startup.py; then
        echo "   ✅ Using mongo_db.create() (CORRECT)"
    elif grep -q "insert_one" /app/backend/init_admin_startup.py; then
        echo "   ⚠️  Using insert_one() - may have permission issues"
    fi
else
    echo "   ❌ init_admin_startup.py not found"
fi
echo ""

echo "======================================================================="
echo "  KIỂM TRA HOÀN TẤT"
echo "======================================================================="
echo ""
echo "Để kiểm tra chi tiết hơn, xem:"
echo "  - /app/MONGODB_DETAILED_INFO.md"
echo "  - /app/MONGODB_SUMMARY.md"
echo ""
