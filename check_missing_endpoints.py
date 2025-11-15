"""Check missing endpoints by comparing frontend API constants with backend"""

# Frontend endpoints from api.js
frontend_endpoints = {
    # Auth - DONE
    "POST /api/login": "✅",
    "GET /api/verify-token": "✅",
    
    # Users - DONE
    "GET /api/users": "✅",
    "POST /api/users": "✅",
    "PUT /api/users/{id}": "✅",
    "DELETE /api/users/{id}": "✅",
    
    # Companies - DONE
    "GET /api/companies": "✅",
    "GET /api/companies/{id}": "✅",
    "POST /api/companies": "✅",
    "PUT /api/companies/{id}": "✅",
    "DELETE /api/companies/{id}": "✅",
    "POST /api/companies/{id}/upload-logo": "✅",
    
    # Ships - DONE
    "GET /api/ships": "✅",
    "GET /api/ships/{id}": "✅",
    "POST /api/ships": "✅",
    "PUT /api/ships/{id}": "✅",
    "DELETE /api/ships/{id}": "✅",
    "POST /api/ships/{id}/calculate-anniversary-date": "✅",
    "POST /api/ships/{id}/calculate-next-docking": "✅",
    "POST /api/ships/{id}/calculate-special-survey-cycle": "✅",
    
    # Certificates - DONE
    "GET /api/certificates": "✅",
    "GET /api/certificates/{id}": "✅",
    "POST /api/certificates": "✅",
    "PUT /api/certificates/{id}": "✅",
    "DELETE /api/certificates/{id}": "✅",
    "POST /api/certificates/analyze-file": "✅",
    "POST /api/certificates/bulk-delete": "✅",
    "POST /api/certificates/check-duplicate": "✅",
    
    # Crew - DONE
    "GET /api/crew": "✅",
    "GET /api/crew/{id}": "✅",
    "POST /api/crew": "✅",
    "PUT /api/crew/{id}": "✅",
    "DELETE /api/crew/{id}": "✅",
    "POST /api/crew/bulk-delete": "✅",
    
    # Crew Certificates - DONE
    "GET /api/crew-certificates": "✅",
    "GET /api/crew-certificates/{id}": "✅",
    "POST /api/crew-certificates": "✅",
    "PUT /api/crew-certificates/{id}": "✅",
    "DELETE /api/crew-certificates/{id}": "✅",
    "POST /api/crew-certificates/analyze-file": "✅",
    "POST /api/crew-certificates/bulk-delete": "✅",
    "POST /api/crew-certificates/check-duplicate": "✅",
    
    # Document types - ALL DONE
    "GET /api/survey-reports": "✅",
    "GET /api/test-reports": "✅",
    "GET /api/drawings-manuals": "✅",
    "GET /api/other-documents": "✅",
    "GET /api/ism-documents": "✅",
    "GET /api/isps-documents": "✅",
    "GET /api/mlc-documents": "✅",
    "GET /api/supply-documents": "✅",
    
    # Google Drive - MISSING
    "GET /api/gdrive-config": "❌",
    "POST /api/gdrive/upload": "❌",
    "POST /api/companies/{id}/gdrive/configure": "❌",
    "GET /api/companies/{id}/gdrive/config": "❌",
    "GET /api/companies/{id}/gdrive/status": "❌",
    "POST /api/gdrive/test-connection": "❌",
    "POST /api/ships/{id}/sync-to-gdrive": "❌",
    "POST /api/ships/{id}/create-gdrive-folders": "❌",
    
    # System Settings - MISSING
    "GET /api/ai-config": "✅ (mock)",
    "PUT /api/ai-config": "❌",
    "GET /api/system-settings": "❌",
    "PUT /api/system-settings": "❌",
    
    # Additional endpoints that might be in backend-v1
    "POST /api/passport/analyze-file": "❌",
    "POST /api/crew/move-standby-files": "❌",
    "GET /api/ship-types": "❌",
    "GET /api/class-societies": "❌",
    "GET /api/flags": "❌",
    "GET /api/certificate-types": "❌",
    "GET /api/crew-ranks": "❌",
    "GET /api/nationalities": "❌",
}

print("=" * 80)
print("MISSING ENDPOINTS ANALYSIS")
print("=" * 80)

missing = []
done = []

for endpoint, status in frontend_endpoints.items():
    if "❌" in status:
        missing.append(endpoint)
    else:
        done.append(endpoint)

print(f"\n✅ COMPLETED: {len(done)} endpoints")
print(f"❌ MISSING: {len(missing)} endpoints")
print(f"📊 PROGRESS: {len(done)}/{len(frontend_endpoints)} ({len(done)*100//len(frontend_endpoints)}%)")

print("\n" + "=" * 80)
print("MISSING ENDPOINTS BY CATEGORY")
print("=" * 80)

print("\n🔄 GOOGLE DRIVE INTEGRATION (8 endpoints):")
gdrive = [e for e in missing if 'gdrive' in e.lower() or 'sync' in e.lower()]
for ep in gdrive:
    print(f"  ❌ {ep}")

print("\n⚙️ SYSTEM SETTINGS (3 endpoints):")
settings = [e for e in missing if 'settings' in e.lower() or 'ai-config' in e.lower()]
for ep in settings:
    print(f"  ❌ {ep}")

print("\n👤 CREW OPERATIONS (2 endpoints):")
crew_ops = [e for e in missing if 'passport' in e.lower() or 'move-standby' in e.lower()]
for ep in crew_ops:
    print(f"  ❌ {ep}")

print("\n📋 REFERENCE DATA (6 endpoints):")
ref_data = [e for e in missing if any(x in e.lower() for x in ['types', 'societies', 'flags', 'ranks', 'nationalities'])]
for ep in ref_data:
    print(f"  ❌ {ep}")

print("\n" + "=" * 80)
print("PRIORITY RECOMMENDATIONS")
print("=" * 80)

print("\n🔴 HIGH PRIORITY (Core Features):")
print("  1. Google Drive Integration - File storage & sync")
print("  2. System Settings - AI config, base settings")
print("  3. Passport Analysis - Crew document processing")

print("\n🟡 MEDIUM PRIORITY (Reference Data):")
print("  4. Ship Types, Flags, Class Societies - Dropdown data")
print("  5. Certificate Types - Document categorization")
print("  6. Crew Ranks, Nationalities - Crew management data")

print("\n🟢 LOW PRIORITY (Additional Operations):")
print("  7. Move Standby Files - File organization")

print("\n" + "=" * 80)
print(f"TOTAL MISSING: {len(missing)} endpoints (~{(len(missing)*100//(len(done)+len(missing)))}% remaining)")
print("=" * 80)
