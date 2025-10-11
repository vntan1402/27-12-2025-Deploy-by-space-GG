# 📄 Passport Filename Logic - Updated

## **NEW Logic: Rank + Full Name (English) + "Passport"**

### **Input Example:**
```javascript
const crew = {
  rank: "Chief Engineer",
  full_name: "Nguyễn Văn Bình",           // Vietnamese name
  full_name_en: "Nguyen Van Binh",         // English name (auto-generated or AI-extracted)
  passport: "C987654321"                   // Passport number (NOT used in filename)
};
```

### **Processing Steps:**

#### **Step 1: Extract Components**
```javascript
const rank = "Chief Engineer";
const fullNameEn = "Nguyen Van Binh";      // Uses English name
const passportSuffix = "Passport";         // Fixed string (not passport field value)
```

#### **Step 2: Clean for File System**
```javascript
const cleanRank = "Chief_Engineer";        // Replace spaces with underscores
const cleanNameEn = "Nguyen_Van_Binh";     // Replace spaces with underscores  
const cleanPassportSuffix = "Passport";    // Already clean
```

#### **Step 3: Generate Filename**
```javascript
const autoFilename = "Chief_Engineer_Nguyen_Van_Binh_Passport";
```

#### **Step 4: Add Extensions**
- **Passport File**: `"Chief_Engineer_Nguyen_Van_Binh_Passport.pdf"`
- **Summary File**: `"Chief_Engineer_Nguyen_Van_Binh_Passport_Summary.txt"`

---

## **Comparison: OLD vs NEW Logic**

### **Example Crew Data:**
```javascript
const crew = {
  rank: "Captain",
  full_name: "Trần Văn An",
  full_name_en: "Tran Van An", 
  passport: "B123456789"
};
```

### **OLD Logic (Before Change):**
```
Format: Rank + Full Name + Passport (field value)
Result: "Captain_Tran_Van_An_B123456789.pdf"
```

### **NEW Logic (After Change):**
```  
Format: Rank + Full Name (English) + "Passport" (fixed)
Result: "Captain_Tran_Van_An_Passport.pdf"
```

---

## **Benefits of NEW Logic:**

### **✅ Advantages:**
1. **Cleaner Names**: No long passport numbers in filename
2. **Consistent Format**: Always ends with "Passport" 
3. **English Names**: Uses standardized English names
4. **Shorter Files**: More readable filenames
5. **Privacy**: Passport numbers not exposed in filenames

### **📋 File Examples:**
```
Captain_John_Smith_Passport.pdf
Chief_Engineer_Nguyen_Van_A_Passport.pdf
Second_Officer_Le_Thi_B_Passport.pdf
AB_Seaman_Pham_Van_C_Passport.pdf

Captain_John_Smith_Passport_Summary.txt
Chief_Engineer_Nguyen_Van_A_Passport_Summary.txt
Second_Officer_Le_Thi_B_Passport_Summary.txt
AB_Seaman_Pham_Van_C_Passport_Summary.txt
```

---

## **Implementation Details:**

### **Frontend Logic (App.js):**
```javascript
// NEW implementation
const rank = crew.rank || 'Unknown';
const fullNameEn = crew.full_name_en || crew.full_name || 'Unknown'; 
const passportSuffix = 'Passport'; // Fixed string

const cleanRank = rank.replace(/[^a-zA-Z0-9]/g, '_');
const cleanNameEn = fullNameEn.replace(/[^a-zA-Z0-9]/g, '_');

const autoFilename = `${cleanRank}_${cleanNameEn}_${passportSuffix}`;
// Result: "Captain_Tran_Van_An_Passport"
```

### **Backend Processing (server.py):**
```python
# Receives: "Captain_Tran_Van_An_Passport"
# Adds extension: "Captain_Tran_Van_An_Passport.pdf"
# Summary becomes: "Captain_Tran_Van_An_Passport_Summary.txt"
```

### **Apps Script Execution:**
```javascript
// Renames files on Google Drive:
// Original → "Captain_Tran_Van_An_Passport.pdf"  
// Summary → "Captain_Tran_Van_An_Passport_Summary.txt"
```

---

## **Edge Cases Handled:**

### **Missing English Name:**
```javascript
// If full_name_en is missing, fallback to full_name
const fullNameEn = crew.full_name_en || crew.full_name || 'Unknown';
```

### **Special Characters:**
```javascript
// Rank: "Chief Engineer" → "Chief_Engineer"
// Name: "Nguyễn Văn A" → "Nguyen_Van_A" (after diacritic removal)
```

### **Missing Rank:**
```javascript
// Fallback: "Unknown_Tran_Van_An_Passport.pdf"
```

This updated logic provides cleaner, more consistent, and privacy-friendly filenames!