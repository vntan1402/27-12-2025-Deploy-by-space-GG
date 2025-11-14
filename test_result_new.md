#===================================================
# TESTING PROTOCOL & RESULTS
# Ship Management System
#===================================================

## 📋 Testing Protocol

### Communication Protocol with Testing Sub-Agent

**CRITICAL INSTRUCTIONS:**
1. **ALWAYS READ THIS FILE BEFORE invoking testing agent**
2. **ALWAYS UPDATE backend or frontend sections after testing**
3. **MINIMUM STEPS when editing - be precise and targeted**

### Testing Workflow

1. **Before Testing:**
   - Read this file completely
   - Understand current test status
   - Plan what needs testing

2. **During Testing:**
   - Testing agent will update results
   - Monitor progress
   - Review findings

3. **After Testing:**
   - Verify results in this file
   - Act on feedback if needed
   - Mark as tested

---

## 🗂️ TESTING RESULTS

### Standby Crew Certificate Upload Feature

**Status:** ✅ TESTED & WORKING
**Date:** 2025-01-16
**Testing Agent:** deep_testing_backend_v2

**Test Coverage:**
- Analyze endpoint with no ship_id (standby crew) ✅
- Analyze endpoint with valid ship_id (ship-assigned crew) ✅
- Certificate creation with ship_id=None ✅
- Certificate creation with valid ship_id ✅
- File upload to correct folders ✅
- Error handling ✅

**Success Rate:** 100% (9/9 tests passed)

---

## 📝 TRIMMED NOTICE

**Date Trimmed:** $(date +%Y-%m-%d)
**Reason:** File size optimization (reduced from 1.9MB)
**Full History:** Archived to /app/docs/archive/test_results/

**Retention Policy:**
- Keep last ~100-150 test entries
- Archive older entries monthly
- Full history available in archive

---

## 🧪 Recent Testing History

