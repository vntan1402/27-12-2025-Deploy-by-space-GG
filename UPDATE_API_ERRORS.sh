#!/bin/bash
# Script to update hardcoded error messages in API files

echo "🔄 Updating API error messages to use centralized messages.py..."

# List of files to update
FILES=(
  "/app/backend/app/api/v1/crew_certificates.py"
  "/app/backend/app/api/v1/audit_certificates.py"
  "/app/backend/app/api/v1/survey_reports.py"
  "/app/backend/app/api/v1/test_reports.py"
  "/app/backend/app/api/v1/other_documents.py"
  "/app/backend/app/api/v1/supply_documents.py"
  "/app/backend/app/api/v1/other_audit_documents.py"
  "/app/backend/app/api/v1/drawings_manuals.py"
  "/app/backend/app/api/v1/system_settings.py"
  "/app/backend/app/api/v1/gdrive.py"
)

for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "  Updating $file..."
    
    # Replace "Insufficient permissions" with PERMISSION_DENIED
    sed -i 's/detail="Insufficient permissions"/detail=PERMISSION_DENIED/g' "$file"
    
    # Replace "Access denied" with ACCESS_DENIED
    sed -i 's/detail="Access denied"/detail=ACCESS_DENIED/g' "$file"
    
    # Add import if not exists
    if ! grep -q "from app.core.messages import" "$file"; then
      # Find the line with "from app.core.security import" and add after it
      sed -i '/from app.core.security import/a from app.core import messages' "$file"
    fi
  fi
done

echo "✅ Done! Remember to manually review changes."
