# Smooth Progress Bar Implementation Plan

## Overview
Implement smooth, time-based progress bars for all batch processing modals (Test Reports, Survey Reports, Drawings & Manuals).

## Changes Required:

### 1. Add New State for Smooth Progress
```javascript
// For each type, add smooth progress state
const [testReportSmoothProgress, setTestReportSmoothProgress] = useState(0); // 0-100
const [surveyReportSmoothProgress, setSurveyReportSmoothProgress] = useState(0);
const [drawingsManualSmoothProgress, setDrawingsManualSmoothProgress] = useState(0);
```

### 2. Progress Calculation Logic
- **Base Time Estimate**: 30 seconds per file (default)
- **File Size Factor**: +5 seconds per MB
- **Page Count Factor**: +2 seconds per page (if available)
- **Total Time**: baseTime + (fileSize * 5) + (pageCount * 2)

### 3. Progress Phases
- **Phase 1 (0-30%)**: Analyzing file with Document AI
- **Phase 2 (30-60%)**: Creating database record
- **Phase 3 (60-90%)**: Uploading to Google Drive
- **Phase 4 (90-100%)**: Waiting for API confirmation

### 4. Implementation Strategy
1. Start smooth progress animation when file processing begins
2. Progress increases incrementally (every 100ms)
3. Progress slows down as it approaches 90%
4. Jump to 100% when API confirms completion
5. Reset for next file

### 5. UI Updates
- Replace simple progress bar with smooth animated one
- Show estimated time remaining
- Display current phase (optional)

## Files to Modify:
- `/app/frontend/src/App.js` (main implementation)
