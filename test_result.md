# Test Result Documentation

## Testing Protocol
- Always run tests through this document
- Document all test results

## Current Test Focus
Testing Certificate Status calculation logic after update

## Test Requirements

### 1. Backend Test - Certificate Status Logic
Test the getCertificateStatus function in frontend files:
- `/app/frontend/src/components/CertificateList/CertificateTable.jsx`
- `/app/frontend/src/components/AuditCertificate/AuditCertificateTable.jsx`
- `/app/frontend/src/pages/ClassAndFlagCert.jsx`
- `/app/frontend/src/pages/IsmIspsMLc.jsx`

### 2. Frontend Visual Test
Login with credentials:
- Username: admin
- Password: Admin@123456

Verify:
1. Navigate to Class & Flag Cert page
2. Select a ship (if available)
3. Check that Status column shows:
   - "Còn hiệu lực" (Valid) - Green badge
   - "Quá hạn" (Over Due) - Orange badge (for Class & Flag)
   - "Hết hiệu lực" (Expired) - Red badge

4. Navigate to ISM-ISPS-MLC page
5. Check that Status column shows:
   - "Còn hiệu lực" (Valid) - Green badge
   - "Sắp hết hạn" (Due Soon) - Orange badge (for Audit certificates)
   - "Hết hiệu lực" (Expired) - Red badge

### 3. Test Cases for Status Calculation
According to `/app/CERTIFICATE_STATUS_LOGIC.md`:

**Class & Flag Certificates (30 days threshold, "Over Due" label):**
- next_survey_display = "28/06/2026 (±3M)" → windowClose = 28/09/2026
- If today > windowClose → "Expired"
- If (windowClose - today) <= 30 days → "Over Due"
- Otherwise → "Valid"

**Audit Certificates (90 days threshold, "Due Soon" label):**
- next_survey_display = "28/06/2026 (±3M)" → windowClose = 28/09/2026
- If today > windowClose → "Expired"
- If (windowClose - today) <= 90 days → "Due Soon"
- Otherwise → "Valid"

## Incorporate User Feedback
- User wants Status logic to match documentation in /app/CERTIFICATE_STATUS_LOGIC.md
- Class & Flag should show "Over Due" instead of "Due Soon"
- Audit certificates should show "Due Soon"
- Both should use next_survey_display as priority, fallback to valid_date

## Test Status
- [ ] Backend tests pending
- [ ] Frontend visual tests pending
