# 🤖 AI ANALYSIS - TODO FOR FUTURE IMPLEMENTATION

**Status:** Currently using MOCK DATA  
**Priority:** HIGH - Critical feature for maritime document management  
**Estimated Time:** 30-45 minutes  
**Dependencies:** AI config migration from backend-v1

---

## 📋 CURRENT STATUS

### What's Working (Mock Data)
✅ Endpoint exists: `POST /api/certificates/analyze-file`  
✅ Returns mock certificate data structure  
✅ Frontend can call the endpoint  
⚠️ Data is hardcoded, not extracted from actual PDF

### Mock Data Response
```json
{
  "success": true,
  "message": "Certificate analyzed successfully (mock data)",
  "analysis": {
    "cert_name": "SAFETY MANAGEMENT CERTIFICATE",
    "cert_type": "Full Term",
    "cert_no": "SMC-2024-001",
    "issue_date": "15/01/2024",
    "valid_date": "15/01/2029",
    "issued_by": "DNV GL",
    "ship_name": "MV Test Ship"
  }
}
```

---

## 🎯 WHAT NEEDS TO BE IMPLEMENTED

### 1. AI Config Migration (FIRST STEP)
**Location in backend-v1:** 
- AI configuration stored in database or environment
- LLM provider settings (OpenAI, Claude, etc.)
- Model selection (GPT-4, GPT-3.5, etc.)
- API keys management

**Files to check:**
- `/app/backend-v1/server.py` - AI config endpoints
- Database collection: `ai_config` or `system_settings`
- Environment variables for AI keys

**Migration tasks:**
- [ ] Create AI config model (`app/models/ai_config.py`)
- [ ] Create AI config repository
- [ ] Create AI config service
- [ ] Create API endpoints: GET/PUT `/api/ai-config`
- [ ] Migrate existing AI config from database

---

### 2. Certificate Analysis Implementation

**Required capabilities:**
1. **PDF Text Extraction**
   - Use PyPDF2 or pdfplumber for text extraction
   - Handle scanned PDFs with OCR (pytesseract already installed)

2. **AI-Powered Information Extraction**
   - Use EMERGENT_LLM_KEY (already available)
   - Install emergentintegrations: `pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/`
   - Extract structured data from unstructured text

3. **Data Fields to Extract**
   ```python
   {
     "cert_name": str,           # Certificate name/title
     "cert_type": str,           # Full Term, Interim, etc.
     "cert_no": str,             # Certificate number
     "issue_date": str,          # Date format: DD/MM/YYYY
     "valid_date": str,          # Expiry date
     "issued_by": str,           # Issuing authority
     "ship_name": str,           # Ship name from certificate
     "imo_number": Optional[str], # IMO number if present
     "flag": Optional[str],       # Flag state
     "confidence": float         # AI confidence score
   }
   ```

4. **Date Parsing Intelligence**
   - Handle multiple date formats: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD
   - Extract dates from natural language: "18 March 2024", "March 18, 2024"
   - Validate date ranges (issue < valid date)

---

## 🔧 IMPLEMENTATION APPROACH

### Step 1: Get EMERGENT_LLM_KEY
```python
# In certificate_service.py
from emergentintegrations import get_emergent_key

key = get_emergent_key()
```

### Step 2: Install emergentintegrations
```bash
cd /app/backend
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
echo "emergentintegrations" >> requirements.txt
```

### Step 3: Extract Text from PDF
```python
import PyPDF2
from io import BytesIO

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    pdf_file = BytesIO(file_content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    
    return text
```

### Step 4: Call LLM for Analysis
```python
from emergentintegrations import call_llm

async def analyze_certificate_with_ai(text: str) -> dict:
    """Use LLM to extract certificate information"""
    
    prompt = f"""
    You are a maritime document expert. Extract the following information from this ship certificate:
    
    Certificate Text:
    {text}
    
    Please extract and return in JSON format:
    {{
      "cert_name": "Full certificate name",
      "cert_type": "Full Term/Interim/Provisional/etc",
      "cert_no": "Certificate number",
      "issue_date": "DD/MM/YYYY",
      "valid_date": "DD/MM/YYYY",
      "issued_by": "Issuing authority",
      "ship_name": "Ship name"
    }}
    
    If a field is not found, use null.
    """
    
    response = await call_llm(prompt, model="gpt-4")
    return parse_llm_response(response)
```

### Step 5: Update CertificateService
```python
@staticmethod
async def analyze_certificate_file(file: UploadFile, ship_id: Optional[str], current_user: UserResponse) -> dict:
    """Analyze certificate file using AI"""
    
    # Validate file
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Read file
    file_content = await file.read()
    
    # Extract text
    text = extract_text_from_pdf(file_content)
    
    # If text is empty, try OCR
    if not text or len(text) < 100:
        text = await extract_text_with_ocr(file_content)
    
    # Analyze with AI
    analysis = await analyze_certificate_with_ai(text)
    
    return {
        "success": True,
        "message": "Certificate analyzed successfully",
        "analysis": analysis
    }
```

---

## 📦 DEPENDENCIES NEEDED

```txt
# Already installed:
- pytesseract (for OCR)
- PyPDF2 (for PDF text extraction)

# To install:
- emergentintegrations (for LLM calls)
- pdfplumber (alternative PDF library, optional)
```

---

## 🧪 TESTING STRATEGY

### Test Cases:
1. **Full Term Certificate** - Extract all fields correctly
2. **Scanned PDF** - Use OCR + AI analysis
3. **Multiple Date Formats** - Parse correctly
4. **Missing Fields** - Handle gracefully with null values
5. **Invalid File** - Reject non-PDF files
6. **Large File** - Handle files up to 10MB

### Test Data Locations:
- Real certificates in: `/app/backend-v1/uploads/`
- Test with various certificate types:
  - Class certificates
  - Statutory certificates (SOLAS)
  - Flag state certificates
  - Insurance certificates

---

## 📝 FILES TO MODIFY

### Primary Implementation:
1. **`app/services/certificate_service.py`**
   - Replace mock data with real AI analysis
   - Add text extraction functions
   - Add LLM integration

2. **`app/utils/pdf_processor.py`** (NEW)
   - PDF text extraction
   - OCR processing
   - Image preprocessing

3. **`app/utils/ai_helper.py`** (NEW)
   - LLM prompt templates
   - Response parsing
   - Error handling

### Configuration:
4. **`app/models/ai_config.py`** (NEW)
   - AI configuration model
   - Provider settings
   - Model selection

5. **`requirements.txt`**
   - Add emergentintegrations
   - Add any additional PDF libraries

---

## ⚠️ IMPORTANT NOTES

### Security Considerations:
- ✅ EMERGENT_LLM_KEY already in environment (secure)
- ✅ File size validation (10MB limit)
- ✅ File type validation (PDF only)
- ⚠️ Consider rate limiting for LLM calls
- ⚠️ Add timeout for long-running analysis

### Performance:
- PDF extraction: ~1-2 seconds
- OCR (if needed): ~3-5 seconds per page
- LLM analysis: ~2-3 seconds
- **Total:** ~5-10 seconds per certificate

### Error Handling:
- Handle PDF parsing failures gracefully
- Fallback to OCR if text extraction fails
- Return partial data if some fields missing
- Log all errors for debugging

---

## 🔗 RELATED ENDPOINTS

### Also Need AI Analysis:
1. **Crew Certificates:** `POST /api/crew-certificates/analyze-file`
   - Similar to ship certificates
   - Different fields (passport data, crew info)

2. **Passport Analysis:** `POST /api/passport/analyze-file`
   - Extract passport data
   - Photo detection
   - Personal information extraction

3. **Other Documents:** Survey reports, test reports, etc.
   - Custom analysis per document type
   - Different field structures

---

## ✅ COMPLETION CHECKLIST

**When implementing, check off:**

### Phase 1: Setup (5 min)
- [ ] Get EMERGENT_LLM_KEY from environment
- [ ] Install emergentintegrations
- [ ] Test LLM connection

### Phase 2: Text Extraction (10 min)
- [ ] Implement PDF text extraction
- [ ] Implement OCR fallback
- [ ] Test with sample PDFs

### Phase 3: AI Analysis (10 min)
- [ ] Create LLM prompt template
- [ ] Implement LLM call
- [ ] Parse LLM response to JSON

### Phase 4: Integration (5 min)
- [ ] Update certificate_service.py
- [ ] Remove mock data
- [ ] Add error handling

### Phase 5: Testing (10 min)
- [ ] Test with real certificates
- [ ] Test with scanned PDFs
- [ ] Test error cases
- [ ] Verify all fields extracted correctly

---

## 🎯 SUCCESS CRITERIA

Implementation is complete when:
- ✅ Real PDFs analyzed successfully
- ✅ All required fields extracted with >80% accuracy
- ✅ OCR fallback works for scanned documents
- ✅ Response time < 10 seconds
- ✅ Error handling robust
- ✅ Frontend receives correct data structure

---

**Last Updated:** November 15, 2025  
**Assigned To:** Future implementation after AI config migration  
**Priority:** HIGH  
**Blocked By:** AI config migration from backend-v1
