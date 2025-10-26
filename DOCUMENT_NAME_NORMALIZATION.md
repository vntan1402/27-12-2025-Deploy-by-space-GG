# Document Name Normalization System

## 📋 Overview
Hệ thống tự động chuẩn hóa tên tài liệu (Document Name) trong Drawings & Manuals List để đảm bảo consistency và professional display.

---

## 🎯 Vấn Đề Cần Giải Quyết

### **Before (Không đồng nhất):**
```
Document 1: "G.A. Plan"
Document 2: "General Arrangement"
Document 3: "general arrangement drawing"
Document 4: "GA Drawing"

→ Cùng loại bản vẽ nhưng 4 cách viết khác nhau!
```

### **After (Đồng nhất):**
```
Document 1: "General Arrangement (GA)"
Document 2: "General Arrangement (GA)"
Document 3: "General Arrangement (GA)"
Document 4: "General Arrangement (GA)"

→ Tất cả hiển thị chuẩn "General Arrangement (GA)"!
```

---

## 📊 Danh Sách Document Mappings

### **🎨 Ship Drawings (Bản Vẽ Tàu)**

| Original Variations | Normalized Format |
|---------------------|-------------------|
| "General Arrangement", "G.A.", "GA Plan", "GA Drawing" | **General Arrangement (GA)** |
| "Capacity Plan", "Tank Capacity Plan" | **Capacity Plan** |
| "Safety Plan", "Fire Safety Plan" | **Safety Plan** |
| "Fire Control Plan", "Fire Fighting Plan", "Fire Plan" | **Fire Control Plan** |
| "Damage Control Plan", "Damage Control Drawing" | **Damage Control Plan** |
| "Shell Expansion", "Shell Expansion Drawing" | **Shell Expansion** |
| "Midship Section", "Mid-ship Section" | **Midship Section** |
| "Lines Plan", "Lines Drawing", "Body Plan" | **Lines Plan** |
| "Loading Manual", "Cargo Loading Manual" | **Loading Manual** |
| "Stability Booklet", "Stability Manual" | **Stability Booklet** |

---

### **📖 Manuals (Sổ Tay Hướng Dẫn)**

| Original Variations | Normalized Format |
|---------------------|-------------------|
| "Operation Manual", "Operating Manual", "O.M.", "OM" | **Operation Manual (OM)** |
| "Instruction Manual", "Instructions Manual", "I.M.", "IM" | **Instruction Manual (IM)** |
| "Maintenance Manual", "Maintenance Instruction", "M.M.", "MM" | **Maintenance Manual (MM)** |
| "Service Manual", "Servicing Manual", "S.M.", "SM" | **Service Manual (SM)** |
| "Technical Manual", "Technical Documentation", "T.M.", "TM" | **Technical Manual (TM)** |
| "Installation Manual", "Installation Guide" | **Installation Manual** |
| "User Manual", "Users Manual", "User Guide" | **User Manual** |
| "Spare Parts Catalog", "Parts List", "Parts Catalog" | **Spare Parts Catalog** |

---

### **🔐 Safety Documents**

| Original Variations | Normalized Format |
|---------------------|-------------------|
| "Safety Data Sheet", "Material Safety Data Sheet", "MSDS", "SDS" | **Safety Data Sheet (SDS)** |
| "Safety Manual", "Safety Instruction" | **Safety Manual** |
| "Emergency Procedure", "Emergency Procedures", "Emergency Response" | **Emergency Procedure** |

---

### **📜 Certificates & Approvals**

| Original Variations | Normalized Format |
|---------------------|-------------------|
| "Type Approval", "Type Approval Certificate" | **Type Approval Certificate** |
| "Certificate of Approval", "Approval Certificate" | **Certificate of Approval** |

---

### **⚙️ Engine & Machinery Manuals**

| Original Variations | Normalized Format |
|---------------------|-------------------|
| "Engine Manual", "Main Engine Manual" | **Engine Manual** |
| "Pump Manual", "Pump Operation Manual" | **Pump Manual** |
| "Compressor Manual", "Air Compressor Manual" | **Compressor Manual** |
| "Generator Manual", "Diesel Generator Manual" | **Generator Manual** |
| "Boiler Manual", "Boiler Operation Manual" | **Boiler Manual** |

---

### **📡 Navigation & Communication**

| Original Variations | Normalized Format |
|---------------------|-------------------|
| "Radar Manual" | **Radar Manual** |
| "Navigation Manual" | **Navigation Manual** |
| "GPS Manual" | **GPS Manual** |
| "AIS Manual" | **AIS Manual** |
| "VHF Manual", "Radio Manual" | **VHF Manual** / **Radio Manual** |

---

### **🌬️ HVAC**

| Original Variations | Normalized Format |
|---------------------|-------------------|
| "HVAC Manual", "Air Conditioning Manual", "Ventilation Manual" | **HVAC Manual** |

---

### **⚡ Electrical**

| Original Variations | Normalized Format |
|---------------------|-------------------|
| "Electrical Drawing", "Electrical Diagram", "Wiring Diagram", "Circuit Diagram" | **Electrical Drawing** |
| "Electrical Manual", "Electrical System Manual" | **Electrical Manual** |

---

### **🔧 Piping**

| Original Variations | Normalized Format |
|---------------------|-------------------|
| "Piping Diagram", "Piping Drawing", "Piping Plan", "P&ID", "P and ID" | **Piping Diagram** |

---

## 🔍 Logic Matching

### **1. Direct Match (Khớp trực tiếp)**
```python
Input: "ga"
Mapping: "ga" → "General Arrangement (GA)"
Output: "General Arrangement (GA)" ✅
```

### **2. Case-Insensitive Match**
```python
Input: "Operation Manual"
Lowercase: "operation manual"
Mapping: "operation manual" → "Operation Manual (OM)"
Output: "Operation Manual (OM)" ✅
```

### **3. Cleaned Match (Bỏ ký tự đặc biệt)**
```python
Input: "G.A. Plan"
Cleaned: "g a plan" → "ga plan"
Mapping: "ga plan" → "General Arrangement (GA)"
Output: "General Arrangement (GA)" ✅
```

### **4. Partial Match**
```python
Input: "Main Engine Operation Manual"
Contains: "operation manual"
Mapping: "operation manual" → "Operation Manual (OM)"
Output: "Operation Manual (OM)" ✅
```

### **5. No Match**
```python
Input: "Custom Vessel Documentation"
No mapping found
Output: "Custom Vessel Documentation" (capitalized)
```

---

## 🔄 Workflow

```
1. User uploads PDF
   ↓
2. AI extracts document_name: "G.A. Drawing"
   ↓
3. Normalization runs: "G.A. Drawing" → "General Arrangement (GA)"
   ↓
4. Save to DB: document_name = "General Arrangement (GA)"
   ↓
5. Display in UI: "General Arrangement (GA)" (đồng nhất)
```

---

## 📝 Implementation Details

### **File Structure:**
```
/app/backend/
├── document_name_normalization.py  (NEW - Logic module)
└── server.py                       (Updated - Integration)
```

### **Integration Point (server.py):**
```python
# After AI extraction completes
if analysis_result.get('document_name'):
    from document_name_normalization import normalize_document_name
    
    original_doc_name = analysis_result['document_name']
    normalized_doc_name = normalize_document_name(original_doc_name)
    analysis_result['document_name'] = normalized_doc_name
    
    logger.info(f"✅ Normalized: '{original_doc_name}' → '{normalized_doc_name}'")
```

---

## 🎓 Usage Examples

### **Example 1: General Arrangement Variations**
```yaml
Test 1:
  AI Extracted: "G.A. Plan"
  Normalized: "General Arrangement (GA)"
  Saved: "General Arrangement (GA)" ✅

Test 2:
  AI Extracted: "general arrangement drawing"
  Normalized: "General Arrangement (GA)"
  Saved: "General Arrangement (GA)" ✅

Test 3:
  AI Extracted: "GA"
  Normalized: "General Arrangement (GA)"
  Saved: "General Arrangement (GA)" ✅
```

### **Example 2: Manual Variations**
```yaml
Operation Manual:
  AI Extracted: "Operating Manual"
  Normalized: "Operation Manual (OM)"
  Saved: "Operation Manual (OM)" ✅

Maintenance:
  AI Extracted: "Maintenance Instruction"
  Normalized: "Maintenance Manual (MM)"
  Saved: "Maintenance Manual (MM)" ✅
```

### **Example 3: Safety Documents**
```yaml
SDS:
  AI Extracted: "MSDS"
  Normalized: "Safety Data Sheet (SDS)"
  Saved: "Safety Data Sheet (SDS)" ✅

Fire Plan:
  AI Extracted: "Fire Fighting Plan"
  Normalized: "Fire Control Plan"
  Saved: "Fire Control Plan" ✅
```

---

## ➕ Thêm Document Mapping Mới

### **Option 1: Thêm vào Code (Permanent)**
Chỉnh sửa file `/app/backend/document_name_normalization.py`:

```python
DOCUMENT_NAME_MAPPINGS = {
    # ... existing entries ...
    
    # Add new document type
    "new document type": "New Document Type (Abbreviation)",
    "ndt": "New Document Type (Abbreviation)",
}
```

### **Option 2: Thêm Runtime (Dynamic)**
```python
from document_name_normalization import add_custom_document_mapping

add_custom_document_mapping("Custom Plan", "Custom Plan (CP)")
# Now "Custom Plan" → "Custom Plan (CP)"
```

---

## 📊 Before & After Comparison

### **Database Records:**

#### **Before Normalization:**
```json
[
  { "id": "1", "document_name": "G.A. Plan", "document_type": "Drawing" },
  { "id": "2", "document_name": "General Arrangement", "document_type": "Drawing" },
  { "id": "3", "document_name": "ga drawing", "document_type": "Drawing" },
  { "id": "4", "document_name": "General Arrangement (GA)", "document_type": "Drawing" }
]
```

#### **After Normalization:**
```json
[
  { "id": "1", "document_name": "General Arrangement (GA)", "document_type": "Drawing" },
  { "id": "2", "document_name": "General Arrangement (GA)", "document_type": "Drawing" },
  { "id": "3", "document_name": "General Arrangement (GA)", "document_type": "Drawing" },
  { "id": "4", "document_name": "General Arrangement (GA)", "document_type": "Drawing" }
]
```

### **UI Display:**

#### **Before:**
```
Row 1: G.A. Plan                  ❌
Row 2: General Arrangement        ❌
Row 3: ga drawing                 ❌
Row 4: General Arrangement (GA)   ❌
```

#### **After:**
```
Row 1: General Arrangement (GA)   ✅
Row 2: General Arrangement (GA)   ✅
Row 3: General Arrangement (GA)   ✅
Row 4: General Arrangement (GA)   ✅
```

---

## 🏷️ Category Classification

Hệ thống cũng có thể tự động phân loại document:

```python
from document_name_normalization import get_document_category

get_document_category("General Arrangement (GA)")  # → "Drawing"
get_document_category("Operation Manual (OM)")      # → "Manual"
get_document_category("Type Approval Certificate") # → "Certificate"
get_document_category("Custom Document")           # → "Other"
```

---

## ⚠️ Important Notes

### **1. Existing Records:**
Logic này chỉ áp dụng cho **Drawings & Manuals mới** được upload sau khi cập nhật.

### **2. Manual Entries:**
Nếu người dùng nhập manual qua "Add Drawing/Manual Modal", document_name sẽ KHÔNG được normalize tự động.

### **3. Case Sensitivity:**
Matching không phân biệt chữ hoa/thường.

---

## 🚀 Benefits

1. **Consistency**: Cùng loại document luôn hiển thị cùng format
2. **Professional**: Hiển thị chuẩn với abbreviations rõ ràng
3. **Easy Filtering**: Dễ filter/group by document type
4. **Search Optimization**: Tìm kiếm dễ dàng hơn
5. **Data Quality**: Cải thiện chất lượng dữ liệu tổng thể

---

## 📈 Coverage

Hệ thống hỗ trợ hơn **100+ document name variations** bao gồm:
- ✅ Ship Drawings (GA, Capacity, Fire Control, etc.)
- ✅ Operation & Maintenance Manuals
- ✅ Safety Documents (SDS, Emergency Procedures)
- ✅ Equipment Manuals (Engine, Pump, Generator, etc.)
- ✅ Navigation & Communication Manuals
- ✅ Electrical & Piping Diagrams
- ✅ Certificates & Approvals

---

*Last Updated: 2025-01-26*
