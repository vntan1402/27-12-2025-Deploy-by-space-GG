#!/usr/bin/env python3
"""
Batch update API files to replace hardcoded error messages with centralized messages
"""
import re
from pathlib import Path

# Files to update
API_FILES = [
    "/app/backend/app/api/v1/crew_certificates.py",
    "/app/backend/app/api/v1/survey_reports.py",
    "/app/backend/app/api/v1/test_reports.py",
    "/app/backend/app/api/v1/other_documents.py",
    "/app/backend/app/api/v1/supply_documents.py",
    "/app/backend/app/api/v1/other_audit_documents.py",
    "/app/backend/app/api/v1/drawings_manuals.py",
    "/app/backend/app/api/v1/system_settings.py",
    "/app/backend/app/api/v1/gdrive.py",
]

def update_file(filepath):
    """Update a single file"""
    path = Path(filepath)
    if not path.exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    content = path.read_text()
    original_content = content
    changes_made = []
    
    # Replace hardcoded error messages
    replacements = {
        'detail="Insufficient permissions"': 'detail=PERMISSION_DENIED',
        'detail="Access denied"': 'detail=ACCESS_DENIED',
        'detail="Admin permission required"': 'detail=ADMIN_ONLY',
    }
    
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            changes_made.append(f"{old} → {new}")
    
    # Add import if needed and changes were made
    if changes_made:
        # Check if messages import exists
        if 'from app.core.messages import' not in content and 'from app.core import messages' not in content:
            # Find the security import line
            if 'from app.core.security import' in content:
                content = content.replace(
                    'from app.core.security import',
                    'from app.core.security import get_current_user\nfrom app.core import messages\n# Original import: from app.core.security import'
                )
                # Clean up
                content = content.replace('# Original import: from app.core.security import get_current_user', '')
            else:
                # Add at top after other imports
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('from app.') or line.startswith('import'):
                        continue
                    else:
                        lines.insert(i, 'from app.core import messages')
                        break
                content = '\n'.join(lines)
    
    if content != original_content:
        path.write_text(content)
        print(f"✅ Updated {filepath}")
        for change in changes_made:
            print(f"   - {change}")
        return True
    else:
        print(f"⏭️  No changes needed: {filepath}")
        return False

def main():
    print("🔄 Batch updating API error messages...\n")
    
    updated = 0
    skipped = 0
    
    for filepath in API_FILES:
        if update_file(filepath):
            updated += 1
        else:
            skipped += 1
        print()
    
    print(f"\n✅ Summary: {updated} files updated, {skipped} files skipped")

if __name__ == "__main__":
    main()
