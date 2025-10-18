# Crew Information Display in Crew Certificates View

## Overview
Added crew member information display in the Crew Certificates View, replacing the hidden Ship Information section. Shows key crew details for the selected crew member whose certificates are being viewed.

## User Request
"Trong Crew Certificates View, phía dưới Title CREW RECORD (khu vực hiển thị Ship info trước đây) hãy hiển thị Crew Info của Select Crew gồm các field sau Full Name / Rank / Date of Birth / Place of Birth / Passport / Status / Ship Sign On"

Translation: "In Crew Certificates View, below the CREW RECORD title (area that previously showed ship info), display Crew Info of selected crew with fields: Full Name / Rank / Date of Birth / Place of Birth / Passport / Status / Ship Sign On"

## Implementation

### Location
**File:** `/app/frontend/src/App.js` (lines ~9518-9583)

**Position:** Immediately after Ship Information section (which is now hidden in Certificates View)

### Code Structure

```jsx
{/* Crew Information - Shown in Crew Certificates View */}
{showCertificatesView && selectedCrewForCertificates && (
  <div className="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 p-5 rounded-lg border border-blue-200">
    <h4 className="font-bold text-lg mb-4 text-blue-800 flex items-center">
      <span className="mr-2">👤</span>
      {language === 'vi' ? 'Thông tin Thuyền viên' : 'Crew Member Information'}
    </h4>
    
    {/* 3-column grid layout */}
    <div className="grid grid-cols-3 gap-4 text-sm">
      {/* Row 1: Full Name, Rank, Date of Birth */}
      {/* Row 2: Place of Birth, Passport, Status */}
      {/* Row 3: Ship Sign On */}
    </div>
  </div>
)}
```

### Conditional Display

**Shown when:**
- `showCertificatesView = true` (in Crew Certificates View)
- `selectedCrewForCertificates` exists (crew member selected)

**Hidden when:**
- `showCertificatesView = false` (in Crew List View)
- No crew selected

## Fields Displayed

### Row 1

**1. Full Name (Họ và tên / Full Name)**
- **Source:** `selectedCrewForCertificates.full_name` or `full_name_en`
- **Display:** Uppercase, medium font weight
- **Logic:** Shows English name if language is English and available, otherwise Vietnamese name

**2. Rank (Chức danh / Rank)**
- **Source:** `selectedCrewForCertificates.rank`
- **Display:** Normal text
- **Fallback:** "-" if not available

**3. Date of Birth (Ngày sinh / Date of Birth)**
- **Source:** `selectedCrewForCertificates.date_of_birth`
- **Display:** Localized date format
  - Vietnamese: DD/MM/YYYY (vi-VN)
  - English: MM/DD/YYYY (en-US)
- **Fallback:** "-" if not available

### Row 2

**4. Place of Birth (Nơi sinh / Place of Birth)**
- **Source:** `selectedCrewForCertificates.place_of_birth`
- **Display:** Normal text
- **Fallback:** "-" if not available

**5. Passport (Hộ chiếu / Passport)**
- **Source:** `selectedCrewForCertificates.passport`
- **Display:** Monospace font (font-mono)
- **Fallback:** "-" if not available

**6. Status (Trạng thái / Status)**
- **Source:** `selectedCrewForCertificates.status`
- **Display:** Color-coded based on status:
  - "Sign on" → Green (text-green-600)
  - "Sign off" → Orange (text-orange-600)
  - "Standby" → Blue (text-blue-600)
  - Other → Gray (text-gray-600)
- **Fallback:** "-" if not available

### Row 3

**7. Ship Sign On (Tàu đăng ký / Ship Sign On)**
- **Source:** `selectedCrewForCertificates.ship_sign_on`
- **Display:** Color-coded:
  - "-" (Standby) → Orange (text-orange-600)
  - Ship name → Blue (text-blue-600)
- **Fallback:** "-" if not available

## Visual Design

### Container Styling
```css
bg-gradient-to-r from-blue-50 to-indigo-50  /* Gradient background */
p-5                                         /* Padding */
rounded-lg                                  /* Rounded corners */
border border-blue-200                      /* Blue border */
mb-6                                        /* Margin bottom */
```

### Header
```jsx
<h4 className="font-bold text-lg mb-4 text-blue-800 flex items-center">
  <span className="mr-2">👤</span>
  Thông tin Thuyền viên / Crew Member Information
</h4>
```

### Grid Layout
- **Structure:** 3 columns
- **Gap:** 4 spacing units
- **Text Size:** Small (text-sm)
- **Responsive:** May stack on smaller screens (inherent grid behavior)

## Data Source

### State Variable
```javascript
const [selectedCrewForCertificates, setSelectedCrewForCertificates] = useState(null);
```

### Set When
1. **Double-click crew name** in Crew List:
```javascript
const handleCrewNameDoubleClick = (crew) => {
  setSelectedCrewForCertificates(crew);
  setShowCertificatesView(true);
  // ...
};
```

2. **Open Add Certificate modal** and select crew

### Available Fields
All fields from crew_members table:
- `full_name` / `full_name_en`
- `rank`
- `date_of_birth`
- `place_of_birth`
- `passport`
- `status`
- `ship_sign_on`
- Plus others not displayed here

## Color Coding

### Status Colors
| Status | Color | Class | Visual |
|--------|-------|-------|--------|
| Sign on | Green | text-green-600 | 🟢 Sign on |
| Sign off | Orange | text-orange-600 | 🟠 Sign off |
| Standby | Blue | text-blue-600 | 🔵 Standby |
| Other | Gray | text-gray-600 | ⚫ Other |

### Ship Sign On Colors
| Value | Color | Class | Visual |
|-------|-------|-------|--------|
| "-" (Standby) | Orange | text-orange-600 | 🟠 - |
| Ship name | Blue | text-blue-600 | 🔵 BROTHER 36 |

## Example Display

### English View
```
┌────────────────────────────────────────────────────────────┐
│ 👤 Crew Member Information                                 │
├────────────────────────────────────────────────────────────┤
│ Full Name: NGUYEN VAN A    Rank: Captain                  │
│ Date of Birth: 01/15/1985                                  │
│                                                            │
│ Place of Birth: Ha Noi, Vietnam                           │
│ Passport: A123456789      Status: Sign on                 │
│                                                            │
│ Ship Sign On: BROTHER 36                                  │
└────────────────────────────────────────────────────────────┘
```

### Vietnamese View
```
┌────────────────────────────────────────────────────────────┐
│ 👤 Thông tin Thuyền viên                                   │
├────────────────────────────────────────────────────────────┤
│ Họ và tên: NGUYỄN VĂN A    Chức danh: Thuyền trưởng      │
│ Ngày sinh: 15/01/1985                                      │
│                                                            │
│ Nơi sinh: Hà Nội, Việt Nam                                │
│ Hộ chiếu: A123456789      Trạng thái: Sign on             │
│                                                            │
│ Tàu đăng ký: BROTHER 36                                   │
└────────────────────────────────────────────────────────────┘
```

### Standby Crew Example
```
┌────────────────────────────────────────────────────────────┐
│ 👤 Crew Member Information                                 │
├────────────────────────────────────────────────────────────┤
│ Full Name: JOHN DOE        Rank: Engineer                 │
│ Date of Birth: 03/20/1990                                  │
│                                                            │
│ Place of Birth: Manila, Philippines                        │
│ Passport: P987654321      Status: Standby                 │
│                                                            │
│ Ship Sign On: -                                           │
└────────────────────────────────────────────────────────────┘
```
(Note: "-" and "Standby" would be in orange color)

## Toggle Behavior

### In Crew List View
- Ship Information: ✅ Visible
- Crew Information: ❌ Hidden

### In Crew Certificates View
- Ship Information: ❌ Hidden
- Crew Information: ✅ Visible

### Transition
```javascript
// From Crew List → Certificates View
handleCrewNameDoubleClick(crew) {
  setShowCertificatesView(true);          // Hide ship, show crew
  setSelectedCrewForCertificates(crew);    // Set crew data
}

// From Certificates View → Crew List
handleBackToCrewList() {
  setShowCertificatesView(false);          // Show ship, hide crew
  setSelectedCrewForCertificates(null);    // Clear crew data
}
```

## Comparison with Ship Information

### Ship Info (Hidden in Certificates View)
- Shows: Ship name, IMO, Gross tonnage, Flag, etc.
- Context: Relevant for crew list (filtering by ship)
- Location: Same area

### Crew Info (Shown in Certificates View)
- Shows: Full name, Rank, DOB, Passport, Status, etc.
- Context: Relevant for certificates (whose certs are these?)
- Location: Same area

**Result:** User always sees relevant information for current context.

## Edge Cases

### Case 1: No Crew Selected
- Component doesn't render (conditional check)
- No empty/error state shown

### Case 2: Missing Fields
- Each field has fallback: "-"
- No errors or blank spaces

### Case 3: Long Names
- Text wraps naturally (no explicit truncation)
- 3-column grid accommodates most names

### Case 4: Special Characters
- Passport: Monospace font handles well
- Names: Uppercase maintains consistency

### Case 5: Date Formatting Error
- Try-catch in date conversion
- Fallback: "-"

## Benefits

### 1. Context Awareness
- Shows relevant info for current view
- Crew details when viewing crew's certificates
- Ship details when viewing crew list

### 2. Information Accessibility
- Key crew info always visible
- No need to go back to crew list to check details
- Quick reference while viewing certificates

### 3. Visual Hierarchy
- Prominent header with icon
- Color-coded status indicators
- Clear field labels

### 4. Consistency
- Same grid layout as ship info (3 columns)
- Same area of screen
- Familiar UX pattern

### 5. Bilingual Support
- All labels translated
- Appropriate date formats per language
- Maintains professional appearance

## Files Modified

**Frontend:**
- `/app/frontend/src/App.js`
  - Added Crew Information section (lines ~9518-9583)
  - Conditional display based on `showCertificatesView`
  - 3-column grid layout with 7 crew fields

**Documentation:**
- This file: `/app/CREW_INFO_DISPLAY_IN_CERTIFICATES_VIEW.md`

## Testing Checklist

### Basic Display
- [ ] Open Crew List → Crew info hidden
- [ ] Double-click crew name → Switches to Certificates View
- [ ] Crew info section visible below title
- [ ] All 7 fields displayed correctly

### Data Accuracy
- [ ] Full name matches crew record
- [ ] Rank matches crew record
- [ ] Date of birth formatted correctly
- [ ] Place of birth displayed
- [ ] Passport number displayed
- [ ] Status color-coded correctly
- [ ] Ship sign on matches and color-coded

### Language Toggle
- [ ] Vietnamese: All labels in Vietnamese
- [ ] English: All labels in English
- [ ] Date format changes with language
- [ ] English name shown if available and language = English

### Status Colors
- [ ] "Sign on" → Green
- [ ] "Sign off" → Orange
- [ ] "Standby" → Blue
- [ ] Ship Sign On "-" → Orange
- [ ] Ship Sign On (ship name) → Blue

### Navigation
- [ ] Back to Crew List → Crew info hidden
- [ ] Re-open Certificates → Crew info shown again
- [ ] Different crew → Info updates correctly

## Status
✅ Crew Information section added
✅ 7 fields displayed (Full Name, Rank, DOB, Place of Birth, Passport, Status, Ship Sign On)
✅ Color coding implemented
✅ Bilingual support
✅ Conditional display working
✅ Ready for testing
