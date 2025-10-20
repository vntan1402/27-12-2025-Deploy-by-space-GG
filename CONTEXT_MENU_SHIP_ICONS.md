# Context Menu Icons Update - Ship Icons

## Summary
Updated icons in Company Crew List context menu to use ship-themed SVG icons with integrated arrows for better visual representation.

## Changes Made

### New Icons Design

#### 1. Edit Ship Sign On (🚢)
- **Icon**: Ship icon (simple)
- **Color**: Purple (`text-purple-700`)
- **SVG**: Material Design ship icon
- **Purpose**: Change which ship a crew member is assigned to

```svg
<svg className="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 24 24">
  <path d="M20 21c-1.39 0-2.78-.47-4-1.32-2.44 1.71-5.56 1.71-8 0C6.78 20.53 5.39 21 4 21H2v2h2c1.38 0 2.74-.35 4-.99 2.52 1.29 5.48 1.29 8 0 1.26.65 2.62.99 4 .99h2v-2h-2zM3.95 19H4c1.6 0 3.02-.88 4-2 .98 1.12 2.4 2 4 2s3.02-.88 4-2c.98 1.12 2.4 2 4 2h.05l1.89-6.68c.08-.26.06-.54-.06-.78s-.32-.42-.6-.5L20 10.62V6c0-1.1-.9-2-2-2h-3V1H9v3H6c-1.1 0-2 .9-2 2v4.62l-1.29.42c-.26.08-.48.26-.6.5s-.15.52-.06.78L3.95 19zM6 6h12v3.97L12 8 6 9.97V6z"/>
</svg>
```

#### 2. Edit Date Sign On (🚢➡️)
- **Icon**: Ship with arrow pointing RIGHT/IN
- **Color**: Green (`text-green-700`)
- **SVG**: Ship + overlaid arrow pointing right
- **Purpose**: Edit the date when crew member signed on (boarded) the ship
- **Visual**: Arrow integrated into the ship design, pointing inward

```svg
<svg className="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 24 24">
  <g>
    {/* Ship body */}
    <path d="M20 21c-1.39 0-2.78-.47-4-1.32-2.44 1.71-5.56 1.71-8 0C6.78 20.53 5.39 21 4 21H2v2h2c1.38 0 2.74-.35 4-.99 2.52 1.29 5.48 1.29 8 0 1.26.65 2.62.99 4 .99h2v-2h-2zM3.95 19H4c1.6 0 3.02-.88 4-2 .98 1.12 2.4 2 4 2s3.02-.88 4-2c.98 1.12 2.4 2 4 2h.05l1.89-6.68c.08-.26.06-.54-.06-.78s-.32-.42-.6-.5L20 10.62V6c0-1.1-.9-2-2-2h-3V1H9v3H6c-1.1 0-2 .9-2 2v4.62l-1.29.42c-.26.08-.48.26-.6.5s-.15.52-.06.78L3.95 19zM6 6h12v3.97L12 8 6 9.97V6z"/>
    {/* Arrow pointing IN/RIGHT */}
    <path d="M19 8l-4 4h3c0 2.2-1.8 4-4 4v2c3.3 0 6-2.7 6-6h3l-4-4z" opacity="0.9"/>
  </g>
</svg>
```

#### 3. Edit Date Sign Off (⬅️🚢)
- **Icon**: Ship with arrow pointing LEFT/OUT
- **Color**: Orange (`text-orange-700`)
- **SVG**: Ship + overlaid arrow pointing left
- **Purpose**: Edit the date when crew member signed off (left) the ship
- **Visual**: Arrow integrated into the ship design, pointing outward

```svg
<svg className="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 24 24">
  <g>
    {/* Ship body */}
    <path d="M20 21c-1.39 0-2.78-.47-4-1.32-2.44 1.71-5.56 1.71-8 0C6.78 20.53 5.39 21 4 21H2v2h2c1.38 0 2.74-.35 4-.99 2.52 1.29 5.48 1.29 8 0 1.26.65 2.62.99 4 .99h2v-2h-2zM3.95 19H4c1.6 0 3.02-.88 4-2 .98 1.12 2.4 2 4 2s3.02-.88 4-2c.98 1.12 2.4 2 4 2h.05l1.89-6.68c.08-.26.06-.54-.06-.78s-.32-.42-.6-.5L20 10.62V6c0-1.1-.9-2-2-2h-3V1H9v3H6c-1.1 0-2 .9-2 2v4.62l-1.29.42c-.26.08-.48.26-.6.5s-.15.52-.06.78L3.95 19zM6 6h12v3.97L12 8 6 9.97V6z"/>
    {/* Arrow pointing OUT/LEFT */}
    <path d="M5 8l4 4H6c0 2.2 1.8 4 4 4v2c-3.3 0-6-2.7-6-6H1l4-4z" opacity="0.9"/>
  </g>
</svg>
```

## Icon Design Rationale

### Before
- **Edit Ship Sign On**: Building/office icon (didn't represent ship concept)
- **Edit Date Sign On**: Calendar icon (generic, didn't show direction)
- **Edit Date Sign Off**: Exit/logout icon (not maritime-themed)

### After
- **Edit Ship Sign On**: Clear ship icon representing vessel selection
- **Edit Date Sign On**: Ship with arrow pointing IN → represents boarding/joining
- **Edit Date Sign Off**: Ship with arrow pointing OUT → represents departing/leaving

## Visual Design Features

1. **Consistent Theme**: All icons use ship imagery
2. **Directional Clarity**: Arrows show direction of movement (in/out)
3. **Integrated Design**: Arrows are overlaid on ship, not separate
4. **Color Coding**: Each action has distinct color for easy recognition
5. **Size Optimized**: 20x20px (w-5 h-5) for clear visibility

## Technical Implementation

### File Modified
- `frontend/src/App.js` (lines ~11253-11290)

### Changes
- Replaced 3 SVG icon definitions in context menu
- Increased icon size from `w-4 h-4` to `w-5 h-5` for better visibility
- Used Material Design ship icon as base
- Added custom arrow paths overlaid on ship body
- Set arrow opacity to 0.9 for subtle integration

## User Experience

### Context Menu Location
Right-click on crew member row → Opens context menu with options

### Visual Hierarchy
```
Context Menu
├── 🚢 Edit Ship Sign On (Purple)
├── 🚢➡️ Edit Date Sign On (Green) 
├── ⬅️🚢 Edit Date Sign Off (Orange)
└── 🗑️ Delete Crew Member (Red)
```

## Benefits

1. **Better Semantics**: Icons directly represent maritime operations
2. **Improved Recognition**: Users instantly understand ship-related actions
3. **Direction Clarity**: Arrows show boarding (→) vs departing (←)
4. **Professional Look**: Cohesive ship theme throughout crew management
5. **Visual Consistency**: Matches the maritime/shipping domain

## Date
January 20, 2025
