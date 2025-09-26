# Last Docking 1 & 2 Determination Workflow

## Tổng Quan
Hệ thống sử dụng AI-enhanced analysis để xác định Last Docking 1 (gần nhất) và Last Docking 2 (gần nhất thứ 2) từ CSSC certificates với fallback mechanisms.

---

## 🔄 COMPLETE WORKFLOW

### **STEP 1: User Interaction**
```
User clicks "Recalculate Docking Dates" button
├── Frontend: handleRecalculateDockingDates(shipId)
├── API Call: POST /api/ships/{ship_id}/calculate-docking-dates
└── Headers: Authorization Bearer token
```

### **STEP 2: Backend Authentication & Validation**
```
API Endpoint: calculate_ship_docking_dates()
├── ✅ Check user permissions (EDITOR/MANAGER/ADMIN/SUPER_ADMIN)
├── ✅ Validate ship exists in database
└── ✅ Call extract_docking_dates_with_ai_analysis(ship_id)
```

### **STEP 3: AI Configuration Check**
```
extract_docking_dates_with_ai_analysis()
├── 🔍 Get AI config from mongo_db.find_one("ai_config", {"id": "system_ai"})
├── ✅ If found: Use AI analysis (Google Gemini 2.0-flash + Emergent LLM key)
├── ❌ If not found: Fallback to extract_last_docking_dates_from_certificates()
└── 📝 Log: "Using AI analysis for docking dates extraction: {provider} {model}"
```

### **STEP 4: Certificate Discovery & Filtering**
```
Certificate Collection Process:
├── 🔍 Get all certificates for ship: mongo_db.find_all("certificates", {"ship_id": ship_id})
├── 🎯 Filter CSSC certificates by keywords:
│   ├── 'safety construction'
│   ├── 'cssc'  
│   ├── 'cargo ship safety construction'
│   ├── 'construction certificate'
│   └── 'safety certificate'
├── ✅ Require certificates to have text_content OR google_drive_file_id
└── 📝 Log: "Found {count} CSSC certificates for AI analysis"
```

### **STEP 5: AI Analysis Process**
```
For Each CSSC Certificate:
├── 📄 Check text_content availability
│   ├── ✅ If available: Proceed with AI analysis
│   └── ❌ If missing: Skip with warning log
├── 🤖 AI Analysis with specialized prompt:
│   ├── Focus: "Inspections of the outside of the ship's bottom" 
│   ├── Target: Bottom inspection dates, dry dock dates, hull surveys
│   ├── Priority: DD/MM/YYYY patterns with docking context
│   └── Output: JSON with dates, context, confidence scores
├── 📊 Parse AI Response:
│   ├── Extract docking_dates array
│   ├── Validate date formats with parse_date_string()
│   ├── Filter dates (1980 ≤ year ≤ current_year + 1)
│   └── Store with metadata: {date, source, confidence, context, method: 'AI_analysis'}
└── 🔄 Fallback: If AI fails, use traditional regex extraction
```

### **STEP 6: Traditional & Survey Status Extraction**
```
Additional Data Sources:
├── 🔄 Traditional Extraction: extract_docking_dates_from_text()
│   ├── CSSC bottom patterns (highest priority)
│   ├── Survey status patterns (medium priority)  
│   └── General docking patterns (lowest priority)
├── 📋 Survey Status: extract_docking_dates_from_survey_status()
│   ├── Check certificate text_content for survey sections
│   ├── Check ship.survey_status field
│   └── Method: 'traditional_extraction'
└── 📝 Log extraction results for each method
```

### **STEP 7: Data Consolidation & Deduplication**
```
All Docking Dates Processing:
├── 📊 Combine all sources: AI + Traditional + Survey Status
├── 🔄 Sort by: (date DESC, confidence == 'high')
├── 🚫 Remove duplicates within 7 days:
│   ├── Compare each date with existing dates
│   ├── If date_diff ≤ 7 days: Consider duplicate
│   ├── Keep higher confidence: 'high' > 'medium' > 'low'
│   └── Replace lower confidence entries
└── 📋 Result: unique_dates sorted by recency + confidence
```

### **STEP 8: Assignment & Database Update**
```
Final Assignment:
├── 🥇 Last Docking 1 = unique_dates[0] (most recent)
├── 🥈 Last Docking 2 = unique_dates[1] (second most recent)  
├── 💾 Update ship record: mongo_db.update("ships", {"id": ship_id}, update_data)
│   ├── update_data["last_docking"] = last_docking
│   └── update_data["last_docking_2"] = last_docking_2
└── 📝 Log: "AI-enhanced docking dates for ship {ship_id}"
```

### **STEP 9: Response Formatting & Frontend Display**
```
API Response:
├── ✅ Success Response:
│   ├── success: true
│   ├── message: "Docking dates extracted from CSSC/DD certificates"
│   ├── docking_dates: {
│   │   ├── last_docking: "DD/MM/YYYY"
│   │   └── last_docking_2: "DD/MM/YYYY"
│   │   }
├── ❌ No Results Response:
│   ├── success: false
│   ├── message: "No docking dates found in CSSC or Dry Docking certificates"
│   └── docking_dates: null
└── Frontend Alert: Display extracted dates to user + refresh ship data
```

---

## 🔧 FALLBACK MECHANISMS

### **AI Failure Fallbacks:**
```
1. No AI Config → Traditional extraction
2. No CSSC certs → Traditional extraction  
3. No text_content → Skip certificate (warning log)
4. AI API error → Traditional extraction for that certificate
5. No dates found → Return null results with appropriate message
```

### **Traditional Extraction Priority:**
```
1. 🏆 CSSC Bottom Patterns (Highest Priority):
   - "inspections of the outside of the ship's bottom"
   - "bottom inspection", "hull bottom inspection"
   
2. 🥈 Survey Status Patterns (Medium Priority):
   - "survey status.*docking", "docking inspection status"
   - "last docking inspection", "docking survey completed"
   
3. 🥉 General Docking Patterns (Lowest Priority):  
   - "dry dock date", "docking survey date"
   - "last dry dock", "construction survey"
```

---

## 📊 DATA FLOW SUMMARY

```
User Click → API Auth → AI Config → Certificate Filter → AI Analysis 
    ↓
Traditional Extraction ← Survey Status ← Consolidation ← Deduplication
    ↓
Assignment ← Database Update ← Response Format ← Frontend Display
```

---

## 🎯 CURRENT LIMITATIONS

### **Primary Limitation:**
- **Missing text_content**: Certificates lack OCR-extracted text content
- **Impact**: Both AI and traditional extraction cannot function without text data
- **Status**: Infrastructure ready, needs OCR implementation

### **Success Conditions:**
- ✅ AI Configuration: Available (Google Gemini 2.0-flash)
- ✅ CSSC Detection: Working correctly  
- ✅ API Endpoint: Functional with proper error handling
- ✅ Logic Flow: Complete with fallbacks
- ❌ Text Content: Missing for pattern analysis

---

## 🔄 AUTO-CALCULATION TRIGGERS

### **Current Triggers:**
1. **Manual Only**: User clicks "Recalculate Docking Dates" button
2. **Ship Update**: DISABLED - No longer auto-calculates during ship updates

### **Previous Behavior (Disabled):**
- ❌ Auto-calculate when ship update has no docking values
- ❌ Background calculation during ship save/update operations

### **Design Decision:**
- Users must explicitly request AI analysis via dedicated button
- Provides control over when expensive AI analysis occurs
- Allows users to see results before accepting them

---

## 🚀 PERFORMANCE CHARACTERISTICS

### **Execution Time:**
- AI Analysis: ~2-5 seconds per CSSC certificate
- Traditional Extraction: ~100-200ms per certificate  
- Database Operations: ~50-100ms per query
- Total: Varies by certificate count and text content length

### **Resource Usage:**
- AI API calls consume Emergent LLM key credits
- MongoDB queries for certificates and ship records
- Memory usage for certificate text processing
- Network calls to AI providers (Google Gemini)

---

**Last Updated:** Current implementation as of latest codebase
**Version:** AI-Enhanced with System Settings Integration
**Status:** ✅ Implemented, ⚠️ Limited by missing text_content