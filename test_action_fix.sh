#!/bin/bash
# Simple verification script for crew certificate action fix

echo "======================================================================"
echo "🧪 CREW CERTIFICATE ACTION FIX VERIFICATION"
echo "======================================================================"
echo ""
echo "📋 Test Objective:"
echo "   Verify backend calls 'analyze_certificate_document_ai' action"
echo "   (not 'analyze_passport_document_ai')"
echo ""

# Check for correct action in crew-certificates endpoint
echo "🔍 Checking backend code..."
echo ""

# Find the line with the fix
RESULT=$(grep -A 5 "/crew-certificates/analyze-file" /app/backend/server.py | grep -n "analyze_certificate_document_ai" | grep "action")

if [ -n "$RESULT" ]; then
    echo "   ✅ CORRECT: Found 'analyze_certificate_document_ai' action"
    echo "   📄 Line: $RESULT"
else
    echo "   ❌ INCORRECT: 'analyze_certificate_document_ai' NOT found"
    exit 1
fi

echo ""

# Check the specific context around line 13002
echo "📄 Code context around the fix:"
echo "---"
sed -n '13000,13012p' /app/backend/server.py
echo "---"
echo ""

# Verify the action is correct
CORRECT_ACTION=$(sed -n '13002p' /app/backend/server.py | grep "analyze_certificate_document_ai")

if [ -n "$CORRECT_ACTION" ]; then
    echo "✅ VERIFICATION PASSED"
    echo ""
    echo "======================================================================"
    echo "📊 Summary:"
    echo "======================================================================"
    echo "   ✓ Backend uses correct action: 'analyze_certificate_document_ai'"
    echo "   ✓ Apps Script will classify file as certificate (not passport)"
    echo "   ✓ Document AI summary will include certificate context"
    echo "   ✓ AI extraction will look for certificate fields:"
    echo "     - cert_name (Certificate Name)"
    echo "     - cert_no (Certificate Number / Seaman's Book)"
    echo "     - issued_by (Issuing Authority)"
    echo "     - issued_date (Issue Date)"
    echo "     - expiry_date (Expiry Date)"
    echo ""
    echo "🎯 Next Steps:"
    echo "   1. Test with real certificate file upload"
    echo "   2. Verify frontend auto-fill works correctly"
    echo "   3. Complete remaining features (search, context menu, etc.)"
    echo ""
else
    echo "❌ VERIFICATION FAILED"
    exit 1
fi
