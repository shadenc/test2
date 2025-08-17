# Evidence Mapping Solution: Quarter References vs Screenshot Naming

## Problem Description

There was a mismatch between the data structure and screenshot naming conventions:

- **Data shows**: الأرباح المبقاة للربع السابق (2024Q4) - Previous quarter value
- **Screenshot exists**: `annual_2024_evidence.png` - Annual statement screenshot
- **Issue**: The system couldn't properly link "previous quarter (2024Q4)" to the "annual_2024_evidence.png" screenshot

## Root Cause

The problem occurred because:

1. **Q1 2025 calculation logic**: 
   - Current quarter = Q1 2025
   - Previous quarter = Annual 2024 (not Q4 2024)
   - But screenshots were named by statement type, not by quarter reference

2. **Screenshot naming convention**:
   - `{company}_q1_2025_evidence.png` for Q1 2025
   - `{company}_annual_2024_evidence.png` for Annual 2024
   - No direct mapping for "2024Q4" reference

## Solution Implemented

### 1. Updated Screenshot Serving Logic

Modified `/api/evidence/<company_symbol>.png` endpoint to handle special cases:

```python
if quarter == "Q1_2025":
    # Q1 2025 previous quarter is Annual 2024, so look for both
    quarter_pattern = f"{company_symbol}_*_q1_2025_evidence.png"
    # Also look for annual 2024 as fallback since it's the "previous quarter" reference
    fallback_pattern = f"{company_symbol}_*_annual_2024_evidence.png"
```

### 2. Added New Endpoints

#### `/api/evidence/<company_symbol>/quarter_mapping`
Shows the complete mapping between quarter references and evidence screenshots:

```json
{
  "requested_quarter": "Q1_2025",
  "company_symbol": "2030",
  "evidence_mapping": {
    "current_quarter": {
      "reference": "Q1 2025",
      "screenshot_pattern": "2030_*_q1_2025_evidence.png",
      "description": "الأرباح المبقاة للربع الحالي (2025Q1)"
    },
    "previous_quarter": {
      "reference": "Annual 2024",
      "screenshot_pattern": "2030_*_annual_2024_evidence.png",
      "description": "الأرباح المبقاة للربع السابق (2024Q4) - Annual Statement"
    }
  }
}
```

#### `/api/evidence/<company_symbol>/previous_quarter`
Specifically handles the "previous quarter" reference mapping:

```json
{
  "company_symbol": "2030",
  "requested_quarter": "Q1_2025",
  "previous_quarter_description": "Annual 2024 (الأرباح المبقاة للربع السابق)",
  "previous_quarter_pattern": "2030_*_annual_2024_evidence.png",
  "note": "This endpoint specifically handles the case where 'previous quarter' for Q1 refers to Annual statement"
}
```

### 3. Enhanced Excel Export

Added evidence mapping notes to the Excel export:

- **Q1**: "Note: Previous quarter (2024Q4) refers to Annual 2024 statement screenshot"
- **Q2**: "Note: Previous quarter (2025Q1) refers to Q1 2025 statement screenshot"
- **Q3**: "Note: Previous quarter (2025Q2) refers to Q2 2025 statement screenshot"
- **Q4**: "Note: Previous quarter (2025Q3) refers to Q3 2025 statement screenshot"

## How It Works Now

### For Q1 2025:
1. **Current quarter**: Looks for `{company}_q1_2025_evidence.png`
2. **Previous quarter**: Automatically falls back to `{company}_annual_2024_evidence.png`
3. **Data mapping**: الأرباح المبقاة للربع السابق (2024Q4) → Annual 2024 screenshot

### For Other Quarters:
1. **Q2 2025**: Previous = Q1 2025 screenshot
2. **Q3 2025**: Previous = Q2 2025 screenshot  
3. **Q4 2025**: Previous = Q3 2025 screenshot

## API Usage Examples

### Get Evidence for Q1 2025 (with fallback to Annual 2024):
```
GET /api/evidence/2030.png?quarter=Q1_2025
```

### Get Quarter Mapping Information:
```
GET /api/evidence/2030/quarter_mapping?quarter=Q1_2025
```

### Get Previous Quarter Evidence:
```
GET /api/evidence/2030/previous_quarter?quarter=Q1_2025
```

## Benefits

1. **Automatic Fallback**: System automatically finds the right evidence even when naming conventions don't match
2. **Clear Documentation**: Users can see exactly which screenshots correspond to which quarter references
3. **Flexible Search**: Multiple screenshot patterns are tried to ensure evidence is found
4. **Audit Trail**: Excel exports include notes explaining the evidence mapping
5. **API Consistency**: All endpoints now handle the quarter reference mapping correctly

## Future Improvements

1. **Standardize Screenshot Naming**: Consider renaming screenshots to include quarter references
2. **Database Mapping**: Store explicit mappings between quarter references and screenshot files
3. **Validation**: Add checks to ensure evidence exists for all quarter references
4. **User Interface**: Show evidence mapping visually in the frontend
