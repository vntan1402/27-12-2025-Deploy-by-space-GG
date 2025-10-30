# UPCOMING SURVEY LOGIC - WINDOW-BASED SYSTEM

## ⚠️ QUAN TRỌNG: Survey Window Concept

Backend **KHÔNG** hiển thị tất cả surveys trong tương lai. Thay vào đó, chỉ hiển thị certificates **trong survey window hiện tại** (±3 tháng từ ngày hôm nay).

---

## 📅 VÍ DỤ THỰC TẾ

**Ngày hiện tại:** 15/12/2024

**Certificate CRMDML:**
- Next Survey: **28/11/2025**
- Next Survey Type: **Annual**
- Survey Window: 28/08/2025 - 28/02/2026 (±3 tháng)

**Kết quả:** ❌ KHÔNG hiển thị vì:
- Window chưa mở (window open = 28/08/2025)
- Hiện tại (15/12/2024) < Window open (28/08/2025)
- Survey này sẽ hiển thị khi đến 28/08/2025

---

## 🎯 SURVEY WINDOW RULES

### **1. Annual/Intermediate/Renewal Survey**
**Window:** ±3 months (Before & After)
```
Next Survey: 28/11/2025
Window Open: 28/08/2025 (-3M)
Window Close: 28/02/2026 (+3M)
```

**Example Timeline:**
```
|---[Before Window]---|--[In Window]--|---[After Window]---|
        <28/08         28/08-28/02          >28/02
```

**Status:**
- Before Window Open: Not shown (too far future)
- In Window: ✅ SHOWN
- After Window Close: Overdue

---

### **2. Special Survey**
**Window:** -3 months ONLY (Before deadline)
```
Next Survey: 15/05/2025
Window Open: 15/02/2025 (-3M)
Window Close: 15/05/2025 (deadline)
```

**Status:**
- Before Window: Not shown
- In Window (02-05): ✅ SHOWN
- After Deadline: Overdue (no grace period)

---

### **3. Condition Certificate Expiry**
**Window:** Issue Date → Valid Date
```
Issue Date: 01/01/2025
Valid Date: 31/12/2025
Window: Entire validity period
```

**Status:**
- Before Issue: Not shown
- During Validity: ✅ SHOWN (if within ±3M of valid date)
- After Valid Date: Expired

---

### **4. Initial SMC/ISSC/MLC**
**Window:** Valid Date - 3M → Valid Date
```
Valid Date: 01/06/2025
Window Open: 01/03/2025
Window Close: 01/06/2025
```

---

## 🔍 WHY THIS DESIGN?

### **Benefits:**
1. **Actionable Items Only** - Shows only surveys you can/should act on now
2. **Reduce Noise** - Doesn't overwhelm with far-future surveys
3. **Focus on Urgent** - Highlights what needs attention
4. **Industry Standard** - Follows IMO window requirements

### **Trade-offs:**
- ❌ Cannot see ALL future surveys at once
- ❌ Surveys 6-12 months away won't appear
- ✅ Clear focus on current priorities
- ✅ Matches survey company scheduling practices

---

## 💡 HOW TO SEE FUTURE SURVEYS?

### **Option 1: Filter Next Survey Column**
- In Certificate List table
- Sort by "Next Survey" column
- See all surveys sorted by date

### **Option 2: Check Periodically**
- Run "Upcoming Survey" check monthly
- New surveys enter window as time progresses

### **Option 3: Custom Report (Future Feature)**
- Generate "All Future Surveys" report
- Export to Excel/PDF
- Filter by date range

---

## 🐛 DEBUGGING

**If a survey doesn't show up:**

1. **Check Current Date:**
   ```javascript
   console.log('Today:', new Date().toISOString().split('T')[0]);
   ```

2. **Check Survey Date:**
   ```
   Next Survey: 28/11/2025
   ```

3. **Calculate Window:**
   ```
   Window Open: 28/08/2025 (survey date - 3 months)
   Window Close: 28/02/2026 (survey date + 3 months)
   ```

4. **Compare:**
   ```
   Is Today >= Window Open? 
   15/12/2024 >= 28/08/2025? NO → Won't show
   ```

5. **Wait or Change Date:**
   - Certificate will appear when date reaches 28/08/2025
   - Or check Certificate List table directly

---

## 📊 BACKEND LOGIC (Simplified)

```python
def is_in_upcoming_window(next_survey_date, survey_type):
    today = datetime.now().date()
    
    if survey_type in ['Annual', 'Intermediate', 'Renewal']:
        window_open = next_survey_date - timedelta(days=90)  # -3M
        window_close = next_survey_date + timedelta(days=90)  # +3M
    elif survey_type == 'Special Survey':
        window_open = next_survey_date - timedelta(days=90)  # -3M
        window_close = next_survey_date  # No grace period
    # ... other types
    
    return window_open <= today <= window_close
```

---

## ✅ EXPECTED BEHAVIOR

**Scenario 1: Survey Too Far (Your Case)**
```
Today: 15/12/2024
Next Survey: 28/11/2025 (11 months away)
Window Opens: 28/08/2025
Result: ❌ "Không có survey trong window hiện tại"
Reason: Still 8 months until window opens
```

**Scenario 2: Survey In Window**
```
Today: 15/12/2024
Next Survey: 15/01/2025 (1 month away)
Window: 15/10/2024 - 15/04/2025
Result: ✅ Shows in "Upcoming Survey" modal
```

**Scenario 3: Survey Overdue**
```
Today: 15/12/2024
Next Survey: 15/08/2024 (4 months ago, beyond window)
Window: 15/05/2024 - 15/11/2024
Result: ✅ Shows as "Overdue" status
```

---

## 🎯 SUMMARY

- **Upcoming Survey button** = "Show surveys in current window"
- **NOT** = "Show all future surveys"
- This is **by design** to match industry practice
- Certificate 28/11/2025 **IS CORRECT** - just not in window yet
- Check Certificate List table to see ALL surveys including future ones

**Your system is working correctly!** ✅
