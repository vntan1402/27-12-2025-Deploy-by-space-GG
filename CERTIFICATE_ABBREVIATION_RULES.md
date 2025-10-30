# QUY TẮC XÁC ĐỊNH ABBREVIATION CỦA CERTIFICATE NAME

## 📋 Tổng Quan

Hệ thống có 2 cách xác định Certificate Abbreviation (Tên viết tắt):

1. **User-Defined Mapping** (Ưu tiên cao nhất)
2. **Auto-Generation Algorithm** (Fallback)

---

## 🎯 CÁCH 1: USER-DEFINED MAPPING (Priority)

### Database Collection: `certificate_abbreviation_mappings`

**Cấu trúc:**
```json
{
  "id": "uuid",
  "cert_name": "Safety Management Certificate",
  "cert_abbreviation": "SMC",
  "created_by": "user_id",
  "usage_count": 15,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### API Endpoints:

**1. Get All Mappings:**
```
GET /api/certificate-abbreviation-mappings
```

**2. Create New Mapping:**
```
POST /api/certificate-abbreviation-mappings
Body: {
  "cert_name": "Safety Management Certificate",
  "cert_abbreviation": "SMC"
}
```

**3. Auto-lookup khi nhập cert_name:**
- Frontend gọi backend với cert_name
- Backend check mapping table trước
- Nếu có → trả về abbreviation từ mapping
- Nếu không → chạy auto-generation algorithm

---

## 🤖 CÁCH 2: AUTO-GENERATION ALGORITHM (Fallback)

### Thuật Toán (Backend: `generate_certificate_abbreviation()`)

**Bước 1: Remove Common Phrases**
```
Input: "Statement of Compliance with ISM Code"
→ Remove "Statement of Compliance"
→ Result: "ISM Code"
```

**Bước 2: Remove Common Words**
```
Common words: the, of, and, a, an, for, in, on, at, to, is, are, was, were

Input: "Certificate of Registry"
→ Remove "of"
→ Result: "Certificate Registry"
```

**Bước 3: Extract Significant Words**
```
Input: "Certificate Registry"
→ Significant words: ["Certificate", "Registry"]
```

**Bước 4: Take First Letter of Each Word (Max 6)**
```
["Certificate", "Registry"]
→ C + R = "CR"
```

**Bước 5: Remove Trailing 'C' from "Certificate"**
```
If last word is "Certificate" and abbreviation ends with 'C':
→ Remove trailing 'C'

Example: "Safety Management Certificate"
→ S + M + C = "SMC"
→ Remove trailing C → "SM" ❌

BUT if not last word:
"Certificate of Registry"
→ C + R = "CR" (keep as is) ✅
```

---

## 📝 VÍ DỤ CỤ THỂ

### Example 1: "Safety Management Certificate"
```
1. No mapping found
2. Remove common words: ["Safety", "Management", "Certificate"]
3. Take first letters: S + M + C = "SMC"
4. Last word is "Certificate" → Remove 'C' → "SM"
Result: "SM"
```

### Example 2: "International Load Line Certificate"
```
1. No mapping found
2. Remove common words: ["International", "Load", "Line", "Certificate"]
3. Take first letters: I + L + L + C = "ILLC"
4. Last word is "Certificate" → Remove 'C' → "ILL"
Result: "ILL"
```

### Example 3: "ISM Code Document of Compliance"
```
1. No mapping found
2. Remove "of": ["ISM", "Code", "Document", "Compliance"]
3. Take first letters: I + C + D + C = "ICDC"
4. Last word is NOT "Certificate" → Keep as is
Result: "ICDC"
```

### Example 4: With User Mapping
```
1. Check mapping: "Safety Management Certificate" → "SMC" (found!)
2. Return "SMC" immediately
3. Skip auto-generation
Result: "SMC" ✅
```

---

## 🔧 IMPLEMENTATION IN V2

### Frontend: AddShipCertificateModal.jsx

**Option 1: Auto-lookup on cert_name change**
```javascript
const handleCertNameChange = async (value) => {
  setCertificateData(prev => ({ ...prev, cert_name: value }));
  
  // Auto-lookup abbreviation
  if (value.length > 3) {
    try {
      const response = await api.get(`/api/certificate-abbreviation/lookup?cert_name=${value}`);
      if (response.data.abbreviation) {
        setCertificateData(prev => ({ 
          ...prev, 
          cert_abbreviation: response.data.abbreviation 
        }));
      }
    } catch (error) {
      console.error('Abbreviation lookup error:', error);
    }
  }
};
```

**Option 2: Button to auto-generate**
```javascript
const handleGenerateAbbreviation = async () => {
  if (!certificateData.cert_name) return;
  
  try {
    const response = await api.post('/api/certificate-abbreviation/generate', {
      cert_name: certificateData.cert_name
    });
    
    setCertificateData(prev => ({ 
      ...prev, 
      cert_abbreviation: response.data.abbreviation 
    }));
    
    toast.success('Abbreviation generated!');
  } catch (error) {
    toast.error('Failed to generate abbreviation');
  }
};
```

**Option 3: Auto-fill from AI analysis**
```javascript
// Already implemented in handleMultiCertUpload
if (firstSuccess.extracted_info) {
  const autoFillData = {
    cert_name: firstSuccess.extracted_info.cert_name,
    cert_abbreviation: firstSuccess.extracted_info.cert_abbreviation, // If AI extracted
    // ... other fields
  };
}
```

---

## 📊 PRIORITY ORDER

1. **User Manual Input** (Highest priority)
   - User types abbreviation directly
   - Always respected, never overwritten

2. **User-Defined Mapping** (High priority)
   - From `certificate_abbreviation_mappings` collection
   - Created by users for consistency

3. **AI Extraction** (Medium priority)
   - From document analysis
   - May not always be accurate

4. **Auto-Generation** (Lowest priority)
   - Algorithm-based fallback
   - Consistent but may not match industry standards

---

## 🎯 BEST PRACTICES

### For Users:
1. Create mappings for frequently used certificates
2. Use standard industry abbreviations (SMC, IOPP, etc.)
3. Keep abbreviations short (2-5 characters)
4. Review auto-generated abbreviations for accuracy

### For Developers:
1. Check mapping table first (performance)
2. Cache common mappings
3. Allow manual override
4. Validate abbreviation length (max 10 chars)
5. Log usage_count for popular mappings

---

## 🔍 DEBUGGING

**Check if mapping exists:**
```bash
# In MongoDB
db.certificate_abbreviation_mappings.findOne({ cert_name: "Safety Management Certificate" })
```

**Test auto-generation:**
```javascript
console.log(await generateCertificateAbbreviation("Safety Management Certificate"));
// Expected: "SM" or "SMC" (depending on algorithm)
```

**Check API endpoint:**
```bash
curl -X GET "http://localhost:8001/api/certificate-abbreviation/lookup?cert_name=Safety%20Management%20Certificate"
```

---

## ✅ SUMMARY

- **User Mappings = Best** (consistent, accurate)
- **Auto-Generation = OK** (fallback, may need refinement)
- **Manual Input = Always Allowed** (user has final say)
- **AI Extraction = Helpful** (but validate results)

**Recommendation:** Build a comprehensive mapping table over time based on actual usage!
