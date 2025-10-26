# Test Report Valid Date Calculation Logic

## 📋 Overview
This document describes the **automated Valid Date calculation logic** for Test Reports in the Ship Management System. The system **ALWAYS calculates Valid Date** based on equipment intervals and ship data, **WITHOUT relying on AI extraction**.

---

## 🎯 Core Principle
**Valid Date = Issued Date + Equipment-Specific Interval**

The calculation is based on:
1. **IMO MSC.1/Circ.1432** - Fire protection systems maintenance
2. **SOLAS regulations** - Lifesaving appliances requirements
3. **Ship-specific data** - Anniversary Date and Special Survey Cycle

---

## 🔧 Equipment Intervals

### **Type 1: Fixed Monthly Intervals (12 months)**
These equipment types have a fixed 12-month maintenance cycle:

| Equipment Category | Equipment Types | Interval | Description |
|-------------------|-----------------|----------|-------------|
| **Lifesaving Appliances** | Life Raft, Life Jacket, Life Vest | 12 months | Annual service/inspection |
| **Protective Equipment** | EEBD, SCBA, Chemical Suit, Immersion Suit, Fireman Outfit | 12 months | Annual maintenance |
| **Fire Extinguishers** | Portable Fire Extinguisher, Wheeled Fire Extinguisher | 12 months | Annual inspection |
| **Fixed Fire Systems** | CO2 System, Fire Detection, Fire Alarm | 12 months | Annual inspection |
| **Gas Detection** | Gas Detector, Gas Detection System | 12 months | Annual calibration |

**Calculation Formula:**
```
Valid Date = Issued Date + 12 months
```

**Example:**
```
Equipment: EEBD
Issued Date: 2025-01-15
Valid Date = 2025-01-15 + 12 months = 2026-01-15
```

---

### **Type 2: Next Annual Survey**
These equipment types are tied to the ship's Annual Survey cycle:

| Equipment Types |
|-----------------|
| EPIRB |
| SART |
| AIS |
| SSAS |
| Lifeboat |
| Rescue Boat |
| Davit |
| Launching Appliance |

**Calculation Logic:**

#### Step 1: Get Ship Data
- **Anniversary Date** (day/month) from Ship Information
- **Special Survey Cycle To** (full date) from Ship Information

#### Step 2: Calculate Anniversary Date for Next Year
```
Anniversary Next Year = Anniversary Date in (Year of Issued Date + 1)

Example:
  Issued Date: 2025-03-10 → Year = 2025
  Anniversary: 15/May (day: 15, month: 5)
  Anniversary Next Year = 2026-05-15 (2025 + 1 = 2026)
```

#### Step 3: Determine Adjustment (+3M or -3M)

**Rule A: If Anniversary Date (next year) == Special Survey Cycle To**
```
Valid Date = Anniversary Next Year - 3 months (keep same day)

Example:
  Anniversary Next Year: 2026-05-15
  Valid Date = 2026-05-15 - 3 months = 2026-02-15
  (Month: 5 - 3 = 2, Day: 15 remains unchanged)
```
*Reason: To ensure equipment is tested BEFORE the special survey*

**Rule B: If Anniversary Date (next year) ≠ Special Survey Cycle To**
```
Valid Date = Anniversary Next Year + 3 months (keep same day)

Example:
  Anniversary Next Year: 2026-08-20
  Valid Date = 2026-08-20 + 3 months = 2026-11-20
  (Month: 8 + 3 = 11, Day: 20 remains unchanged)
```
*Reason: Standard 3-month window after anniversary*

#### Step 4: Handle Missing Data
If Special Survey Cycle To is not available:
```
Valid Date = Anniversary Next Year + 3 months (default)
```

---

## 📊 Calculation Examples

### **Example 1: EEBD (12-month interval)**
```yaml
Input:
  Equipment: EEBD
  Issued Date: 2025-02-15
  Ship ID: SHIP-001

Calculation:
  1. Match "EEBD" → Type: months, Value: 12
  2. Valid Date = 2025-02-15 + 12 months
  
Output:
  Valid Date: 2026-02-15
```

---

### **Example 2: EPIRB (Next Annual Survey - Case A)**
```yaml
Input:
  Equipment: EPIRB
  Issued Date: 2025-03-10
  Ship ID: SHIP-001
  Anniversary Date: 15/May (day: 15, month: 5)
  Special Survey Cycle To: 2026-05-15

Calculation:
  1. Match "EPIRB" → Type: next_annual_survey
  2. Anniversary Next Year = 2026-05-15 (15/May in 2026)
  3. Compare: 2026-05-15 == 2026-05-15 ✅
  4. Apply Rule A: Valid Date = 2026-05-15 - 3 months = 2026-02-15
  
Output:
  Valid Date: 2026-02-15
```

---

### **Example 3: Lifeboat (Next Annual Survey - Case B)**
```yaml
Input:
  Equipment: Lifeboat
  Issued Date: 2025-04-01
  Ship ID: SHIP-002
  Anniversary Date: 20/August (day: 20, month: 8)
  Special Survey Cycle To: 2028-08-20

Calculation:
  1. Match "Lifeboat" → Type: next_annual_survey
  2. Anniversary Next Year = 2026-08-20 (20/Aug in 2026)
  3. Compare: 2026-08-20 ≠ 2028-08-20 ❌
  4. Apply Rule B: Valid Date = 2026-08-20 + 3 months = 2026-11-20
  
Output:
  Valid Date: 2026-11-20
```

---

### **Example 4: Fire Extinguisher (12-month interval)**
```yaml
Input:
  Equipment: Portable Fire Extinguisher
  Issued Date: 2025-06-10
  Ship ID: SHIP-003

Calculation:
  1. Match "Fire Extinguisher" → Type: months, Value: 12
  2. Valid Date = 2025-06-10 + 12 months
  
Output:
  Valid Date: 2026-06-10
```

---

## 🔄 Workflow Integration

### **When Valid Date is Calculated:**
✅ **Every time** a Test Report is analyzed from a PDF file  
✅ **Both** single file upload and batch processing  
✅ **Regardless** of whether AI extracts a valid_date or not

### **Data Flow:**
```
1. User uploads Test Report PDF
   ↓
2. AI analyzes file → Extracts: test_report_name, issued_date, note, issued_by, etc.
   ↓
3. Backend IGNORES any AI-extracted valid_date
   ↓
4. Backend calls calculate_valid_date():
   - Input: test_report_name, issued_date, ship_id
   - Logic: Match equipment → Apply interval
   - Output: calculated valid_date
   ↓
5. Backend saves Test Report with calculated valid_date
   ↓
6. System auto-calculates status (Valid/Expired/Expiring Soon)
```

---

## 🚨 Fallback Logic

### **Unknown Equipment:**
If equipment name doesn't match any predefined intervals:
```
Default: 12 months interval
Valid Date = Issued Date + 12 months
```

### **Missing Anniversary Date (for Next Annual Survey):**
If Anniversary Date is not available in Ship Information:
```
Fallback: 12 months from Issued Date
Valid Date = Issued Date + 12 months
```

### **Missing Issued Date:**
```
Cannot calculate → Valid Date = NULL
Warning logged in system
```

---

## 📝 Equipment Matching Rules

### **Case-Insensitive Partial Matching:**
```python
Input: "EEBD Service Report"
Match: "eebd" ✅
Result: 12-month interval

Input: "Life Raft Annual Inspection"
Match: "life raft" ✅
Result: 12-month interval

Input: "EPIRB Battery Replacement"
Match: "epirb" ✅
Result: Next Annual Survey
```

### **Priority:**
1. Exact match (e.g., "EEBD" matches "eebd")
2. Partial match (e.g., "EEBD Service" contains "eebd")
3. Default to 12 months if no match

---

## 🎓 References

- **IMO MSC.1/Circ.1432**: Revised Guidelines for Maintenance and Inspections of Fire Protection Systems and Appliances
- **SOLAS Chapter III**: Lifesaving Appliances and Arrangements
- **IMO Resolution MSC.402(96)**: Revised Recommendation on Testing of Life-Saving Appliances

---

## 🛠 Implementation Files

- **Logic Module**: `/app/backend/test_report_valid_date_calculator.py`
- **API Integration**: `/app/backend/server.py` (analyze_test_report_file endpoint)
- **Equipment Intervals**: `EQUIPMENT_INTERVALS` dictionary in calculator module

---

## ✅ Key Changes from Previous Version

| Aspect | Old Logic | New Logic |
|--------|-----------|-----------|
| **AI Extraction** | Used AI-extracted valid_date if available | ❌ IGNORES AI extraction |
| **Certificate Reference** | Parsed Note for certificate references | ❌ REMOVED |
| **Calculation Trigger** | Only if AI failed | ✅ ALWAYS calculates |
| **Next Annual Survey** | Used Anniversary Date only | ✅ Uses Anniversary + Special Survey Cycle |
| **3-Month Window** | Not implemented | ✅ ±3 months based on Special Survey |

---

*Last Updated: 2025-01-26*
