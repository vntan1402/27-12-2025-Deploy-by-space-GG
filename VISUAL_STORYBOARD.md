# 🎨 VISUAL STORYBOARD - VIDEO GUIDE

## 📐 Layout Guide

```
┌───────────────────────────────────────────────┐
│  Standard Screen Layout: 1920x1080           │
├───────────────────────────────────────────────┤
│                                               │
│  [========= TITLE / HEADER AREA =========]   │  ← Top 15%
│                                               │
│                                               │
│  [=========== MAIN CONTENT ==============]   │  ← Middle 70%
│  [                                       ]   │
│  [         Terminal / Browser           ]   │
│  [                                       ]   │
│  [                                       ]   │
│                                               │
│  [========= ANNOTATIONS / TEXT ==========]   │  ← Bottom 15%
│                                               │
└───────────────────────────────────────────────┘
```

---

## 🎬 FRAME-BY-FRAME STORYBOARD

---

### FRAME 1: Title Card (0:00)
```
┌─────────────────────────────────────────────────┐
│                                                 │
│                                                 │
│              🔐 TẠO SYSTEM ADMIN                │
│            TRONG PRODUCTION                     │
│                                                 │
│                                                 │
│          ┌─────────────────────┐               │
│          │  ✅ Tested 100%     │               │
│          │  ⚡ 2 phút           │               │
│          │  🎯 Dễ dàng         │               │
│          └─────────────────────┘               │
│                                                 │
│                                                 │
│         [ Nhấn SPACE để bắt đầu ]              │
│                                                 │
└─────────────────────────────────────────────────┘

Animation: Fade in from black (1 second)
Background: Gradient blue to purple
Text: White, bold, centered
```

---

### FRAME 2: Prerequisites Checklist (0:30)
```
┌─────────────────────────────────────────────────┐
│  CHECKLIST TRƯỚC KHI BẮT ĐẦU                    │
├─────────────────────────────────────────────────┤
│                                                 │
│    ☐ App đã deploy thành công                  │ ← Animate check
│                                                 │
│    ☐ Có production URL                         │ ← Animate check
│                                                 │
│    ☐ Truy cập được backend terminal            │ ← Animate check
│                                                 │
│    ☐ MongoDB đang chạy                         │ ← Animate check
│                                                 │
│                                                 │
│  ┌────────────────────────────────────────┐    │
│  │ $ pwd                                  │    │
│  │ /app/backend  ✅                       │    │
│  └────────────────────────────────────────┘    │
│                                                 │
└─────────────────────────────────────────────────┘

Animation: Checkboxes tick one by one (0.5s each)
Sound: Soft click for each check
Terminal: Fade in after last checkbox
```

---

### FRAME 3: Method Selection (0:50)
```
┌─────────────────────────────────────────────────┐
│  CHỌN PHƯƠNG PHÁP TẠO ADMIN                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌────────────────┐      ┌────────────────┐    │
│  │  METHOD 1      │      │  METHOD 2      │    │
│  │  ⚡ Quick       │      │  📝 Script     │    │
│  │                │      │                │    │
│  │ Copy-Paste     │      │ Edit File      │    │
│  │ 1 Command      │      │ Then Run       │    │
│  │                │      │                │    │
│  │ ⏱️ 30 giây     │      │ ⏱️ 1 phút      │    │
│  │                │      │                │    │
│  │ [Chọn] ←───────┼──────┤ [Chọn]         │    │
│  └────────────────┘      └────────────────┘    │
│                                                 │
│  Cả 2 cách đều đơn giản. Tôi sẽ demo cả 2!    │
│                                                 │
└─────────────────────────────────────────────────┘

Animation: Cards slide in from left & right
Hover effect: Cards glow on hover
Transition: Split screen when both selected
```

---

### FRAME 4: Method 1 - Show Command (1:00)
```
┌─────────────────────────────────────────────────┐
│  METHOD 1: QUICK ONE-COMMAND                    │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │ export $(cat .env | xargs) && \         │   │
│  │ python3 << 'EOF'                        │   │
│  │ import asyncio                          │   │
│  │ from mongodb_database import mongo_db   │   │
│  │ ...                                     │   │
│  │                                         │   │
│  │ # ================================      │   │
│  │ # 🔧 EDIT THESE 5 VALUES: ←──────┐     │   │
│  │ # ================================│     │   │
│  │ username = "your_admin"      ←────┼──┐  │   │
│  │ email = "admin@company.com"  ←────┼──┤  │   │
│  │ full_name = "Your Name"      ←────┼──┤  │   │
│  │ password = "Secure@2024"     ←────┼──┤  │   │
│  │ company = "Company Ltd"      ←────┼──┘  │   │
│  │ # ================================      │   │
│  │ ...                                     │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  Chỉ cần edit 5 giá trị này! ────────────────► │
│                                                 │
└─────────────────────────────────────────────────┘

Animation: 
- Code scrolls slowly from top
- Highlight box appears around edit section
- Arrows point to each value sequentially
- Numbers (1-5) appear next to each value
```

---

### FRAME 5: Method 1 - Editing Values (1:15)
```
┌─────────────────────────────────────────────────┐
│  EDITING VALUES - EXAMPLE                       │
├─────────────────────────────────────────────────┤
│                                                 │
│  BEFORE (❌):           →    AFTER (✅):        │
│  ─────────────────────────────────────────────  │
│                                                 │
│  username = "your_admin"  →  "production_admin" │
│                              ^^^^^^^^^^^^^^^^   │
│                                                 │
│  email = "admin@..."      →  "admin@abc.com"    │
│                              ^^^^^^^^^^^^^^^    │
│                                                 │
│  full_name = "Your..."    →  "Nguyễn Văn A"     │
│                              ^^^^^^^^^^^^^      │
│                                                 │
│  password = "Secure..."   →  "MyPass@2024"      │
│                              ^^^^^^^^^^^^       │
│  ⚠️ Use strong password!                        │
│                                                 │
│  company = "Company..."   →  "ABC Maritime"     │
│                              ^^^^^^^^^^^^^      │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │ 💡 TIP: Password phải có:               │   │
│  │    - 8+ ký tự                           │   │
│  │    - Chữ hoa & thường                   │   │
│  │    - Số & ký tự đặc biệt                │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘

Animation:
- Split screen appears
- Values type out character by character
- Green checkmarks appear after each value
- Tip box slides up from bottom
```

---

### FRAME 6: Method 1 - Running (1:45)
```
┌─────────────────────────────────────────────────┐
│  TERMINAL - EXECUTING COMMAND                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  $ cd /app/backend                              │
│  $ export $(cat .env | xargs) && python3 << ... │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │                                         │   │
│  │         ⏳ ĐANG XỬ LÝ...                │   │
│  │                                         │   │
│  │    [████████████░░░░░░░░] 60%          │   │
│  │                                         │   │
│  │    ✓ Loading environment variables     │   │
│  │    ✓ Connecting to MongoDB             │   │
│  │    ⏳ Creating company...               │   │
│  │      Hashing password...                │   │
│  │      Creating admin user...             │   │
│  │                                         │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  Estimated time: 5 seconds ────────────────────►│
│                                                 │
└─────────────────────────────────────────────────┘

Animation:
- Progress bar fills gradually
- Checkmarks appear for completed steps
- Loading spinner next to current step
- Terminal cursor blinks
```

---

### FRAME 7: Method 1 - Success (2:10)
```
┌─────────────────────────────────────────────────┐
│                                                 │
│                                                 │
│    ============================================  │
│    ✅ SYSTEM_ADMIN CREATED SUCCESSFULLY!        │
│    ============================================  │
│                                                 │
│    ┌────────────────────────────────────────┐  │
│    │  Username:     production_admin        │  │
│    │  Email:        admin@abc.com           │  │
│    │  Password:     MyPass@2024             │  │
│    │  Role:         SYSTEM_ADMIN (Lv 6)     │  │
│    │  Company:      ABC Maritime            │  │
│    └────────────────────────────────────────┘  │
│                                                 │
│    ============================================  │
│    🚀 Ready to login!                           │
│    ============================================  │
│                                                 │
│    ⚠️  LƯU THÔNG TIN NÀY AN TOÀN!              │
│                                                 │
│                                                 │
└─────────────────────────────────────────────────┘

Animation:
- Green background fills screen
- Success message bounces in
- Credentials box fades in
- Yellow warning pulses
Sound Effect: Success chime
Duration: Hold for 3 seconds
```

---

### FRAME 8: Method 2 - File Editor (2:45)
```
┌─────────────────────────────────────────────────┐
│  nano quick_create_admin.py                     │
├─────────────────────────────────────────────────┤
│                                                 │
│ 78│ if __name__ == "__main__":                  │
│ 79│     print()                                 │
│ 80│     print("🎯 Creating admin...")           │
│ 81│                                             │
│ 82│     # ================================       │
│ 83│     # 🔧 CUSTOMIZE THESE VALUES:            │
│ 84│     # ================================       │
│ 85│     ADMIN_USERNAME = "production_admin" ←──┐│
│ 86│     ADMIN_EMAIL = "admin@company.com"   ←─┤││
│ 87│     ADMIN_FULL_NAME = "Admin Name"      ←─┤││
│ 88│     ADMIN_PASSWORD = "Admin@2024"       ←─┤││
│ 89│     COMPANY_NAME = "Company Ltd"        ←─┘││
│ 90│     # ================================       │
│ 91│                                             │
│                                                 │
│ ^X Exit  ^O WriteOut  ^R Read File             │
└─────────────────────────────────────────────────┘
      ▲                                    ▲
      │                                    │
  Nhấn Ctrl+X                          Scroll đến đây
     để save                            để edit

Animation:
- Nano interface appears
- Scroll to line 85
- Highlight editing area
- Show keyboard shortcuts at bottom
- Cursor blinks at first value
```

---

### FRAME 9: Login Test (4:15)
```
┌─────────────────────────────────────────────────┐
│  🌐 https://your-app.emergentagent.com          │
├─────────────────────────────────────────────────┤
│                                                 │
│         ┌──────────────────────────┐            │
│         │  🔐 LOGIN                │            │
│         ├──────────────────────────┤            │
│         │                          │            │
│         │  Username:               │            │
│         │  [production_admin]  ◄───┼─ Type...   │
│         │                          │            │
│         │  Password:               │            │
│         │  [••••••••••••••]    ◄───┼─ Type...   │
│         │                          │            │
│         │  [ Login ]  ◄────────────┼─ Click!    │
│         │                          │            │
│         └──────────────────────────┘            │
│                                                 │
│         ┌──────────────────────────┐            │
│         │ ⏳ Đang đăng nhập...     │            │
│         └──────────────────────────┘            │
│                                                 │
└─────────────────────────────────────────────────┘

Animation:
- Browser window fades in
- Typing animation for username
- Password shows dots as typed
- Loading spinner after click
- Transition to homepage with page turn effect
```

---

### FRAME 10: Verify Permissions (4:25)
```
┌─────────────────────────────────────────────────┐
│  User Management                                │
├─────────────────────────────────────────────────┤
│                                                 │
│  [+ Add User] ◄────── Click here                │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  Add New User                           │   │
│  ├─────────────────────────────────────────┤   │
│  │                                         │   │
│  │  Role: [Select Role ▼] ◄─── Click      │   │
│  │        ┌───────────────────────┐        │   │
│  │        │ ✅ system_admin       │◄──┐    │   │
│  │        │ ✅ super_admin        │   │    │   │
│  │        │ ✅ admin              │   ├─ All│   │
│  │        │ ✅ manager            │   │ roles│
│  │        │ ✅ editor             │   │    │   │
│  │        │ ✅ viewer             │   │    │   │
│  │        └───────────────────────┘◄──┘    │   │
│  │                                         │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  ✅ Confirmed: You are SYSTEM_ADMIN!            │
│     (Can create all roles)                      │
│                                                 │
└─────────────────────────────────────────────────┘

Animation:
- Page loads with smooth transition
- "+ Add User" button pulses
- Modal opens with slide down
- Dropdown expands
- Green checkmarks appear next to each role
- Confirmation box slides up from bottom
Sound: Success notification
```

---

### FRAME 11: Common Issues (4:30)
```
┌─────────────────────────────────────────────────┐
│  ⚠️  COMMON ISSUES & SOLUTIONS                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ ❌ Error: MONGO_URL not set              │  │
│  │ ├─ Solution:                             │  │
│  │ └─ Check .env file exists                │  │
│  │    $ cat .env | grep MONGO_URL           │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ ❌ Error: bcrypt module not found        │  │
│  │ ├─ Solution:                             │  │
│  │ └─ Install bcrypt                        │  │
│  │    $ pip install bcrypt                  │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ ❌ Error: Username already exists        │  │
│  │ ├─ Solution:                             │  │
│  │ └─ Use different username                │  │
│  │    OR delete old user first              │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘

Animation:
- Issues appear one by one
- Error icon pulses
- Solution expands when clicked
- Code boxes have copy button
```

---

### FRAME 12: Final Summary (4:45)
```
┌─────────────────────────────────────────────────┐
│                                                 │
│             ✅ WHAT WE ACCOMPLISHED             │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ 1. ✓ Prepared environment                │ │
│  │ 2. ✓ Edited 5 credential values          │ │
│  │ 3. ✓ Created SYSTEM_ADMIN user           │ │
│  │ 4. ✓ Auto-created company                │ │
│  │ 5. ✓ Verified in database                │ │
│  │ 6. ✓ Tested login successfully           │ │
│  │ 7. ✓ Confirmed highest permissions       │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │  ⏱️  Total Time: < 3 minutes              │ │
│  │  🎯 Difficulty: Easy                      │ │
│  │  ✅ Status: Production Ready              │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│           🎉 CONGRATULATIONS! 🎉                │
│                                                 │
└─────────────────────────────────────────────────┘

Animation:
- Checklist items appear with checkmark sound
- Stats boxes slide in from sides
- Confetti animation
- Congratulations text bounces
```

---

### FRAME 13: End Card (4:55)
```
┌─────────────────────────────────────────────────┐
│                                                 │
│              🎉 THANK YOU! 🎉                   │
│                                                 │
│         Bạn đã học được cách tạo                │
│            SYSTEM_ADMIN cho                     │
│          production environment!                │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  📖 TÀI LIỆU THAM KHẢO:                  │  │
│  │                                          │  │
│  │  • TESTED_PRODUCTION_SCRIPT.md           │  │
│  │  • QUICK_START_GUIDE.md                  │  │
│  │  • ROLE_PERMISSIONS_TABLE.md             │  │
│  │  • DEPLOYMENT_SUMMARY.md                 │  │
│  │                                          │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  🚀 NEXT STEPS:                          │  │
│  │                                          │  │
│  │  → Tạo users khác qua UI                 │  │
│  │  → Upload company logo                   │  │
│  │  → Setup ships & certificates            │  │
│  │                                          │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│           Questions? Check docs! 📖             │
│                                                 │
└─────────────────────────────────────────────────┘

Animation:
- Fade in from previous scene
- Text appears line by line
- Document links highlight on hover
- Next steps checkboxes appear
- Final fade to black (2 seconds)
```

---

## 🎨 COLOR PALETTE

```css
/* Main Colors */
--success-green:   #10B981
--warning-orange:  #F59E0B
--error-red:       #EF4444
--info-blue:       #3B82F6
--background-dark: #1F2937
--text-light:      #F9FAFB
--highlight:       #FBBF24

/* Gradients */
--gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
--gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)
--gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)

/* Terminal Theme */
--terminal-bg:     #1E1E1E
--terminal-text:   #D4D4D4
--terminal-prompt: #4EC9B0
--terminal-output: #CE9178
```

---

## 🎭 ANIMATION LIBRARY

### Entrance Animations:
```
fadeIn:        opacity 0→1 (0.5s)
slideUp:       translateY(100%)→0 (0.6s)
slideDown:     translateY(-100%)→0 (0.6s)
slideLeft:     translateX(100%)→0 (0.6s)
slideRight:    translateX(-100%)→0 (0.6s)
zoomIn:        scale(0)→1 (0.5s)
bounceIn:      scale with bounce (0.8s)
```

### Emphasis Animations:
```
pulse:         scale 1→1.1→1 (loop)
shake:         translateX -5→5→-5→0
glow:          box-shadow intensity
highlight:     background color flash
underline:     border-bottom animate
```

### Transitions:
```
pageTurn:      3D rotate effect
wipe:          mask transition
fade:          cross-fade
slide:         push transition
zoom:          scale transition
```

---

## 📐 RESPONSIVE LAYOUT

### For Different Screen Sizes:

```
Desktop (1920x1080):   Main layout
Laptop (1366x768):     Scaled 80%
Tablet (1024x768):     Scaled 70%, larger fonts
Mobile (Portrait):     Not recommended for this tutorial
```

---

## 🎤 AUDIO SPECS

### Narration:
```
Microphone: Condenser or dynamic
Sample Rate: 48kHz
Bit Depth: 24-bit
Format: WAV (lossless)
Normalize: -3dB peak
Noise reduction: Applied
De-esser: Applied
EQ: Slight high-pass filter
```

### Background Music:
```
Genre: Soft electronic/ambient
Volume: -25dB to -30dB (under narration)
Fade in: 2 seconds
Fade out: 3 seconds
No vocals
Tempo: 80-100 BPM
```

### Sound Effects:
```
Success chime: Short, pleasant
Error beep: Subtle, not alarming
Click: Soft, UI click
Typing: Keyboard sounds (optional)
Notification: Gentle alert
```

---

## ✅ PRE-PRODUCTION CHECKLIST

```
□ Script finalized and approved
□ Storyboard reviewed
□ Screen recording software tested
□ Microphone tested and positioned
□ Production environment prepared
□ Example data ready
□ Browser cleared and ready
□ Terminal theme set up
□ Code editor configured
□ Backup recordings planned
□ Lighting checked
□ Background noise minimized
```

---

## 🎬 SHOOT CHECKLIST

```
□ Record in one take per section
□ Leave 2-second buffer before/after
□ Speak clearly and slowly
□ Pause between major steps
□ Multiple takes for important parts
□ Record screen at 1080p 30fps
□ Record audio separately (if needed)
□ Monitor levels during recording
□ Save files with descriptive names
□ Backup immediately after recording
```

---

## ✂️ POST-PRODUCTION CHECKLIST

```
□ Import all footage
□ Sync audio (if separate)
□ Cut out mistakes and pauses
□ Add transitions between scenes
□ Add text overlays
□ Add highlights and arrows
□ Add background music
□ Add sound effects
□ Color grade for consistency
□ Export test version
□ Review and make adjustments
□ Final export at 1080p
□ Create thumbnail
□ Write YouTube description
□ Add chapters/timestamps
```

---

**Visual storyboard hoàn chỉnh!** 🎨

Bây giờ bạn có thể dùng để:
- Quay video hướng dẫn
- Tạo slide presentation
- Training materials
- Documentation visuals
