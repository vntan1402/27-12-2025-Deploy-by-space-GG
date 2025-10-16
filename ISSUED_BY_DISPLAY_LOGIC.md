# Logic Hiển Thị Cột "Issued By" trong Crew Certificates

## 📋 OVERVIEW
Cột "Issued By" hiển thị cơ quan/tổ chức cấp chứng chỉ với 2 chức năng chính:
1. **Normalization**: Chuẩn hóa tên cơ quan về format chuẩn
2. **Abbreviation**: Tạo viết tắt cho hiển thị gọn

---

## 🔄 WORKFLOW HOÀN CHỈNH

### Step 1: AI Extraction
**Khi upload certificate file, Document AI extract raw text:**
```
Example raw text:
"the RERL Maritime Authority of the Republic of Panama"
"Socialist Republic of Vietnam Maritime Administration"
"Det Norske Veritas"
```

### Step 2: Backend Normalization
**Function: `normalize_issued_by()` (server.py line 14366-14539)**

#### A. Dictionary Matching
```python
MARITIME_AUTHORITIES = {
    'Panama Maritime Authority': [
        'PANAMA MARITIME AUTHORITY',
        'MARITIME AUTHORITY OF PANAMA',
        'REPUBLIC OF PANAMA MARITIME',
        'RERL MARITIME AUTHORITY OF THE REPUBLIC OF PANAMA'
    ],
    'Vietnam Maritime Administration': [
        'VIETNAM MARITIME ADMINISTRATION',
        'SOCIALIST REPUBLIC OF VIETNAM MARITIME',
        'CỤC HÀNG HẢI VIỆT NAM'
    ],
    'Det Norske Veritas': [
        'DET NORSKE VERITAS',
        'DNV GL',
        'DNV'
    ],
    # ... 20+ other maritime authorities
}
```

**Process:**
1. Convert input to UPPERCASE
2. Check for matches in dictionary
3. If found → replace với standard name
4. If not found → proceed to cleaning

**Examples:**
```
Input: "the RERL Maritime Authority of the Republic of Panama"
Output: "Panama Maritime Authority"

Input: "Socialist Republic of Vietnam Maritime Administration"  
Output: "Vietnam Maritime Administration"

Input: "Det Norske Veritas"
Output: "Det Norske Veritas"
```

#### B. Prefix/Suffix Cleaning
**If no dictionary match, remove common unnecessary prefixes:**
```python
prefixes_to_remove = [
    'the ', 'The ', 'THE ',
    'of the ', 'Of the ', 'OF THE ',
    'Republic of ', 'REPUBLIC OF ',
    'Socialist Republic of ',
    'Government of '
]
```

**Example:**
```
Input: "the Government of Marshall Islands"
No dictionary match → Remove "the Government of "
Output: "Marshall Islands"
```

### Step 3: Generate Abbreviation
**Function: `generate_organization_abbreviation()` (server.py line 1072-1181)**

#### A. Exact Mappings (Hardcoded)
```python
exact_mappings = {
    # Panama
    'PANAMA MARITIME DOCUMENTATION SERVICES': 'PMDS',
    'PANAMA MARITIME AUTHORITY': 'PMA',
    
    # Classification Societies (IACS Members)
    'DET NORSKE VERITAS': 'DNV',
    'AMERICAN BUREAU OF SHIPPING': 'ABS',
    'LLOYD\'S REGISTER': 'LR',
    'BUREAU VERITAS': 'BV',
    'CHINA CLASSIFICATION SOCIETY': 'CCS',
    'NIPPON KAIJI KYOKAI': 'ClassNK',
    'KOREAN REGISTER OF SHIPPING': 'KR',
    'REGISTRO ITALIANO NAVALE': 'RINA',
    
    # Flag State Authorities  
    'LIBERIA MARITIME AUTHORITY': 'LISCR',
    'MARSHALL ISLANDS MARITIME AUTHORITY': 'MIMA',
    'SINGAPORE MARITIME AND PORT AUTHORITY': 'MPA',
    'MALAYSIA MARINE DEPARTMENT': 'MMD',
    'HONG KONG MARINE DEPARTMENT': 'MARDEP',
    
    # Others
    'MARITIME SAFETY ADMINISTRATION': 'MSA',
    'COAST GUARD': 'CG',
}
```

**Process:**
1. Convert to UPPERCASE
2. Check for exact match
3. If found → return abbreviation
4. If not → proceed to pattern matching

#### B. Pattern-Based Matching
```python
if 'PANAMA MARITIME' in org_name and 'DOCUMENTATION' in org_name:
    return 'PMDS'
elif 'AMERICAN BUREAU' in org_name and 'SHIPPING' in org_name:
    return 'ABS'
elif 'LLOYD' in org_name and 'REGISTER' in org_name:
    return 'LR'
# ... more patterns
```

#### C. Fallback: Auto-Generate
**If no match found, auto-generate from significant words:**

```python
# 1. Extract words
words = ['Vietnam', 'Maritime', 'Administration']

# 2. Filter out common words (but keep maritime terms)
common_words = ['the', 'of', 'and', 'inc', 'ltd', ...]
keep_words = ['authority', 'maritime', 'classification', ...]

significant_words = ['Vietnam', 'Maritime', 'Administration']

# 3. Take first letter of each word (max 4)
abbreviation = 'VMA'
```

**Examples:**
```
"Vietnam Maritime Administration" → VMA
"Thailand Marine Department" → TMD
"Greece Ministry of Maritime Affairs" → GMMA
```

### Step 4: Store in Database
**When creating/updating crew certificate:**
```python
# Backend (server.py line ~1591)
if issued_by:
    cert_dict['issued_by_abbreviation'] = generate_organization_abbreviation(issued_by)
else:
    cert_dict['issued_by_abbreviation'] = ""
```

**Certificate object stored:**
```json
{
  "cert_name": "COC",
  "issued_by": "Panama Maritime Authority",
  "issued_by_abbreviation": "PMA",
  "cert_expiry": "2025-12-31"
}
```

### Step 5: Frontend Display
**Display logic (App.js line 8913-8918):**
```javascript
<td className="border border-gray-300 px-4 py-2 text-sm font-semibold text-blue-700" 
    title={cert.issued_by}>
  {cert.issued_by_abbreviation || (cert.issued_by ? 
    (cert.issued_by.length > 8 ? `${cert.issued_by.substring(0, 8)}...` : cert.issued_by)
    : '-'
  )}
</td>
```

**Display Priority:**
1. **If `issued_by_abbreviation` exists** → Show abbreviation (e.g., "PMA", "DNV", "ABS")
2. **Else if `issued_by` exists:**
   - If length > 8 → Truncate and add "..." (e.g., "Panama M...")
   - If length ≤ 8 → Show full (e.g., "DNV", "BV")
3. **Else** → Show "-"

**Tooltip:** Always shows full `issued_by` on hover

---

## 📊 EXAMPLES

### Example 1: Panama Maritime Authority
```
Step 1: AI Extract
  Raw: "the RERL Maritime Authority of the Republic of Panama"

Step 2: Normalize
  Match found in dictionary
  Result: "Panama Maritime Authority"

Step 3: Generate Abbreviation
  Exact match found in mappings
  Result: "PMA"

Step 4: Store
  issued_by: "Panama Maritime Authority"
  issued_by_abbreviation: "PMA"

Step 5: Display
  Shows: "PMA" (with tooltip "Panama Maritime Authority")
```

### Example 2: Det Norske Veritas
```
Step 1: AI Extract
  Raw: "Det Norske Veritas"

Step 2: Normalize
  Match found in dictionary
  Result: "Det Norske Veritas"

Step 3: Generate Abbreviation
  Exact match found
  Result: "DNV"

Step 4: Store
  issued_by: "Det Norske Veritas"
  issued_by_abbreviation: "DNV"

Step 5: Display
  Shows: "DNV" (with tooltip "Det Norske Veritas")
```

### Example 3: Unknown Organization
```
Step 1: AI Extract
  Raw: "ABC Maritime Services Limited"

Step 2: Normalize
  No match in dictionary
  Clean prefixes: (none to remove)
  Result: "ABC Maritime Services Limited"

Step 3: Generate Abbreviation
  No exact match
  No pattern match
  Fallback: Extract significant words
    Words: ['ABC', 'Maritime', 'Services', 'Limited']
    Filter common: ['ABC', 'Maritime'] (remove 'Services', 'Limited')
    Generate: 'AM'
  Result: "AM"

Step 4: Store
  issued_by: "ABC Maritime Services Limited"
  issued_by_abbreviation: "AM"

Step 5: Display
  Shows: "AM" (with tooltip "ABC Maritime Services Limited")
```

### Example 4: Short Name
```
Step 1: AI Extract
  Raw: "BV"

Step 2: Normalize
  Match found: "Bureau Veritas"
  Result: "Bureau Veritas"

Step 3: Generate Abbreviation
  Exact match
  Result: "BV"

Step 4: Store
  issued_by: "Bureau Veritas"
  issued_by_abbreviation: "BV"

Step 5: Display
  Shows: "BV" (with tooltip "Bureau Veritas")
```

---

## 🎯 SUPPORTED ORGANIZATIONS

### Classification Societies (IACS Members):
- **DNV** - Det Norske Veritas
- **ABS** - American Bureau of Shipping
- **LR** - Lloyd's Register
- **BV** - Bureau Veritas
- **CCS** - China Classification Society
- **ClassNK** - Nippon Kaiji Kyokai
- **KR** - Korean Register of Shipping
- **RINA** - Registro Italiano Navale
- **RS** - Russian Maritime Register
- **CRS** - Croatian Register of Shipping
- **PRS** - Polish Register of Shipping
- **IRClass** - Indian Register of Shipping

### Flag State Authorities:
- **PMA** - Panama Maritime Authority
- **PMDS** - Panama Maritime Documentation Services
- **LISCR** - Liberia Maritime Authority
- **MIMA** - Marshall Islands Maritime Authority
- **MPA** - Singapore Maritime and Port Authority
- **MMD** - Malaysia Marine Department
- **MARDEP** - Hong Kong Marine Department

### Coast Guards:
- **USCG** - United States Coast Guard
- **JCG** - Japan Coast Guard
- **PCG** - Philippines Coast Guard

### Others:
- **VMA** - Vietnam Maritime Administration
- **MSA** - Maritime Safety Administration
- **IMO** - International Maritime Organization

---

## 🔧 HOW TO ADD NEW ORGANIZATION

### Method 1: Add to Dictionary (Backend)
**Edit `server.py` line 14384-14503:**
```python
MARITIME_AUTHORITIES = {
    # ... existing entries
    'New Organization Name': [
        'NEW ORGANIZATION NAME',
        'VARIATION 1',
        'VARIATION 2'
    ]
}
```

### Method 2: Add to Abbreviation Mapping
**Edit `server.py` line 1081-1118:**
```python
exact_mappings = {
    # ... existing entries
    'NEW ORGANIZATION NAME': 'NON',  # Your abbreviation
}
```

### Method 3: Auto-Generation (No Code Change)
System will automatically generate abbreviation from significant words.

---

## 💡 DESIGN DECISIONS

### Why Abbreviations?
1. **Space Saving**: Table columns are limited in width
2. **Readability**: Shorter text easier to scan
3. **Consistency**: Standard abbreviations across industry
4. **UX**: Full name available on hover (tooltip)

### Why Normalization?
1. **Data Quality**: AI extracts inconsistent formats
2. **Deduplication**: Same org might have many variations
3. **Reporting**: Easier to group/filter by organization
4. **Standards**: Follow maritime industry conventions

### Display Logic Priority:
```
1. Abbreviation (if exists) → "PMA", "DNV"
2. Full name (if ≤8 chars) → "BV", "CCS"
3. Truncated name (if >8) → "Panama M..."
4. Dash (if empty) → "-"
```

---

## 🐛 EDGE CASES HANDLED

1. **Empty issued_by**: Shows "-"
2. **Very long names**: Truncated with "..." (tooltip shows full)
3. **Unknown organizations**: Auto-generate abbreviation
4. **Multiple variations**: Normalized to single standard name
5. **Case sensitivity**: All comparisons use UPPERCASE
6. **Special characters**: Handled in regex extraction

---

## 📝 MAINTENANCE NOTES

- Dictionary has **20+ major maritime authorities**
- Abbreviation mappings have **30+ organizations**
- Auto-generation fallback ensures no blank abbreviations
- All normalization logged for debugging
- Tooltip always shows full name for verification
