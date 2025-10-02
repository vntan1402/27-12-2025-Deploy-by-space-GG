# TIMEZONE HANDLING GUIDE - Ship Management System

## 🚨 CRITICAL: Date/Timezone Handling Principles

This document outlines the **MANDATORY** principles for handling dates and timezones in the Ship Management System. These principles were established after fixing multiple timezone-related bugs that caused **1-day date shifts** across the application.

---

## ⚠️ The Problem: Naive DateTime Objects

**MongoDB stores datetime objects WITHOUT timezone information (naive datetime).**

When naive datetime objects are serialized to JSON/ISO strings, they can be **incorrectly interpreted** based on local timezone, causing dates to shift by 1 day.

**Example Bug:**
```
Database: 2022-05-05 00:00:00 (naive, no timezone)
JavaScript: new Date("2022-05-05").toISOString() 
  → Parsed as LOCAL midnight
  → With UTC+7: "2022-05-04T17:00:00.000Z" ❌ (1 day shift!)
```

---

## ✅ SOLUTION: Universal Timezone Principles

### Principle 1: ALL Dates MUST Be Treated as UTC

**Rule:** Every date in the system represents a date at **UTC midnight (00:00:00 UTC)**.

**Why:** Maritime operations span multiple timezones. Using UTC as universal reference prevents confusion.

---

## 📋 Implementation Guidelines

### BACKEND (Python/FastAPI)

#### 1. When READING from MongoDB

**❌ WRONG:**
```python
@api_router.get("/ships/{ship_id}")
async def get_ship(ship_id: str):
    ship = await mongo_db.find_one("ships", {"id": ship_id})
    return ShipResponse(**ship)  # ❌ Naive datetime will be serialized incorrectly!
```

**✅ CORRECT:**
```python
@api_router.get("/ships/{ship_id}")
async def get_ship(ship_id: str):
    ship = await mongo_db.find_one("ships", {"id": ship_id})
    
    # FIX: Add UTC timezone to ALL naive datetime objects
    date_fields = ['last_docking', 'last_docking_2', 'next_docking', 
                  'delivery_date', 'keel_laid', 'issue_date', 'valid_date']
    
    for field in date_fields:
        if field in ship and isinstance(ship[field], datetime):
            if ship[field].tzinfo is None:
                # Treat naive datetime as UTC
                ship[field] = ship[field].replace(tzinfo=timezone.utc)
    
    return ShipResponse(**ship)
```

#### 2. When WRITING to MongoDB

**✅ ALWAYS use timezone-aware datetime:**
```python
from datetime import datetime, timezone

# Creating new dates
issue_date = datetime.now(timezone.utc)  # ✅ CORRECT

# Parsing date strings
from dateutil.parser import parse
date = parse(date_string).replace(tzinfo=timezone.utc)  # ✅ CORRECT

# Never use
datetime.now()  # ❌ WRONG - naive datetime
datetime.utcnow()  # ❌ DEPRECATED - naive datetime
```

#### 3. Date Parsing Helper Function

**Use this function for parsing date strings from AI/forms:**
```python
def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string and return timezone-aware datetime (UTC)"""
    if not date_str:
        return None
    
    try:
        # Parse the date
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
        # Add UTC timezone
        return parsed_date.replace(tzinfo=timezone.utc)
    except:
        return None
```

---

### FRONTEND (React/JavaScript)

#### 1. When DISPLAYING Dates from Backend

**✅ ALWAYS use UTC methods:**
```javascript
const formatDate = (isoDateString) => {
  const date = new Date(isoDateString);  // Parse ISO string
  
  // ✅ CORRECT - Use UTC methods
  const day = String(date.getUTCDate()).padStart(2, '0');
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const year = date.getUTCFullYear();
  
  return `${day}/${month}/${year}`;
};
```

**❌ WRONG - Will cause timezone shift:**
```javascript
const formatDate = (isoDateString) => {
  const date = new Date(isoDateString);
  
  // ❌ WRONG - Uses LOCAL timezone
  return date.toLocaleDateString();
  
  // ❌ WRONG - Uses LOCAL timezone
  const day = date.getDate();
};
```

#### 2. When LOADING Dates into HTML Date Inputs

**✅ CORRECT - Format for HTML input (YYYY-MM-DD):**
```javascript
const formatDateForInput = (isoDateString) => {
  if (!isoDateString) return '';
  
  const date = new Date(isoDateString);
  
  // ✅ Use UTC methods to prevent timezone shifts
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  
  return `${year}-${month}-${day}`;
};
```

**❌ WRONG:**
```javascript
const formatDateForInput = (isoDateString) => {
  // ❌ WRONG - Will shift date by 1 day!
  return new Date(isoDateString).toISOString().split('T')[0];
};
```

#### 3. When SUBMITTING Dates to Backend

**✅ CORRECT - Convert to UTC ISO datetime:**
```javascript
const convertDateInputToUTC = (dateString) => {
  if (!dateString) return null;
  
  // HTML date input format: YYYY-MM-DD
  // Append T00:00:00Z to explicitly specify UTC midnight
  return `${dateString.trim()}T00:00:00Z`;
};

// Usage
const shipData = {
  last_docking: convertDateInputToUTC('2022-05-05'),  // → "2022-05-05T00:00:00Z" ✅
  delivery_date: convertDateInputToUTC('2019-01-04')   // → "2019-01-04T00:00:00Z" ✅
};
```

**❌ WRONG:**
```javascript
// ❌ WRONG - Will cause timezone shift!
const shipData = {
  last_docking: new Date('2022-05-05').toISOString()  // → "2022-05-04T17:00:00.000Z" ❌
};
```

---

## 🎯 Checklist for Date Fields

Whenever you add a NEW date field to the system, follow this checklist:

### Backend Checklist
- [ ] Field type is `Optional[datetime]` in Pydantic model
- [ ] When reading from MongoDB, add UTC timezone if naive
- [ ] When writing to MongoDB, ensure datetime has UTC timezone
- [ ] AI extraction uses `parse_date_string()` helper
- [ ] API response includes timezone marker (Z or +00:00)

### Frontend Checklist
- [ ] Display uses `formatDate()` with UTC methods
- [ ] Form input uses `formatDateForInput()` with UTC methods
- [ ] Submit uses `convertDateInputToUTC()` helper
- [ ] No use of `toISOString().split('T')[0]` ❌
- [ ] No use of `toLocaleDateString()` ❌
- [ ] No use of `getDate()`, `getMonth()`, `getFullYear()` without UTC ❌

---

## 📝 Common Patterns

### Pattern 1: GET Endpoint with Dates
```python
@api_router.get("/items/{item_id}")
async def get_item(item_id: str):
    item = await db.find_one("items", {"id": item_id})
    
    # Add UTC timezone to date fields
    for field in ['date1', 'date2', 'date3']:
        if field in item and isinstance(item[field], datetime):
            if item[field].tzinfo is None:
                item[field] = item[field].replace(tzinfo=timezone.utc)
    
    return ItemResponse(**item)
```

### Pattern 2: POST Endpoint with Dates
```python
@api_router.post("/items")
async def create_item(data: ItemCreate):
    item_dict = data.dict()
    
    # Ensure dates have timezone
    for field in ['date1', 'date2']:
        if field in item_dict and item_dict[field]:
            if item_dict[field].tzinfo is None:
                item_dict[field] = item_dict[field].replace(tzinfo=timezone.utc)
    
    await db.insert_one("items", item_dict)
```

### Pattern 3: Frontend Form Submit
```javascript
const handleSubmit = async () => {
  const payload = {
    ...formData,
    date1: convertDateInputToUTC(formData.date1),
    date2: convertDateInputToUTC(formData.date2)
  };
  
  await axios.post(`${API}/items`, payload);
};
```

### Pattern 4: Frontend Display
```javascript
<div>
  Date: {formatDate(item.date1)}  {/* Uses UTC methods */}
</div>

<input 
  type="date" 
  value={formatDateForInput(item.date1)}  {/* Uses UTC methods */}
/>
```

---

## 🐛 Common Mistakes to AVOID

### ❌ Mistake 1: Using toISOString().split('T')[0]
```javascript
// ❌ WRONG - Causes 1-day shift
const dateStr = new Date(isoDate).toISOString().split('T')[0];
```

### ❌ Mistake 2: Creating Date Without Timezone
```python
# ❌ WRONG - Naive datetime
date = datetime(2022, 5, 5)

# ✅ CORRECT - Timezone-aware
date = datetime(2022, 5, 5, tzinfo=timezone.utc)
```

### ❌ Mistake 3: Using Local Timezone Methods
```javascript
// ❌ WRONG - Uses local timezone
const day = date.getDate();
const month = date.getMonth();

// ✅ CORRECT - Uses UTC
const day = date.getUTCDate();
const month = date.getUTCMonth();
```

### ❌ Mistake 4: Not Adding Timezone When Reading from MongoDB
```python
# ❌ WRONG - Naive datetime will be serialized incorrectly
ship = await db.find_one("ships", {"id": ship_id})
return ShipResponse(**ship)

# ✅ CORRECT - Add UTC timezone first
ship = await db.find_one("ships", {"id": ship_id})
if ship['date'].tzinfo is None:
    ship['date'] = ship['date'].replace(tzinfo=timezone.utc)
return ShipResponse(**ship)
```

---

## 🧪 Testing Date Handling

### Test 1: Backend Returns Correct Timezone
```bash
curl http://localhost:8001/api/ships/{id}

# Expected response:
{
  "last_docking": "2022-05-05T00:00:00Z",  # ✅ Has Z or +00:00
  "delivery_date": "2019-01-04T00:00:00+00:00"  # ✅ Has timezone
}

# NOT:
{
  "last_docking": "2022-05-05T00:00:00",  # ❌ Missing timezone marker
}
```

### Test 2: Frontend Displays Correct Date
```javascript
// Given backend returns: "2022-05-05T00:00:00Z"
// formatDate should return: "05/05/2022" ✅
// NOT: "04/05/2022" ❌
```

### Test 3: Round-trip Consistency
```
1. User enters in form: 05/05/2022
2. Frontend converts: "2022-05-05T00:00:00Z"
3. Backend stores: 2022-05-05 00:00:00+00:00
4. Backend returns: "2022-05-05T00:00:00Z"
5. Frontend displays: 05/05/2022 ✅
```

---

## 📚 Reference Functions

### Global Helper Functions Location

**Backend (server.py):**
- `parse_date_string()` - Parse date strings with timezone
- Located near top of file with other helpers

**Frontend (App.js):**
- `formatDate()` - Display dates (DD/MM/YYYY)
- `formatDateForInput()` - Format for HTML date input (YYYY-MM-DD)
- `convertDateInputToUTC()` - Convert form input to UTC ISO string
- Located at component level (lines ~2823, ~2857, ~2838)

---

## 🔧 Migration Note

**Existing Data in Database:**
- All existing dates in MongoDB are naive datetime objects
- Backend adds UTC timezone when reading (no database migration needed)
- This approach is backward-compatible

---

## ✅ Summary

**Golden Rule:** 
> **ALL dates represent UTC midnight. Use UTC methods everywhere. Never assume local timezone.**

**Quick Reference:**
- Backend READ: Add `.replace(tzinfo=timezone.utc)` ✅
- Backend WRITE: Use `datetime.now(timezone.utc)` ✅
- Frontend DISPLAY: Use `.getUTCDate()`, `.getUTCMonth()`, `.getUTCFullYear()` ✅
- Frontend SUBMIT: Use `convertDateInputToUTC()` helper ✅

**When in doubt, ask:** "Does this use UTC methods?" If no → fix it!

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Author:** Ship Management System Team  
**Status:** MANDATORY - Must follow for all date fields
