# GOOGLE SERVICE ACCOUNT SOLUTION FOR CROSS-ACCOUNT ACCESS

## Problem
- Apps Script runs under System Google Account
- Need to upload files to Company Google Drive (different account)
- Direct access blocked due to account separation

## Solution: Google Service Account

### Step 1: Create Service Account
1. Go to Google Cloud Console (under System Account)
2. Navigate to IAM & Admin > Service Accounts
3. Create New Service Account:
   - Name: "Maritime Apps Script Service"
   - Description: "Service account for Maritime Document AI file uploads"
4. Generate JSON Key file
5. Download and securely store the JSON key

### Step 2: Share Company Drive with Service Account
1. In Company Google Drive
2. Share target folder (Company Drive root) with service account email
3. Grant "Editor" permission to service account
4. Service account email format: maritime-service@project-id.iam.gserviceaccount.com

### Step 3: Update Apps Script to use Service Account
```javascript
// Add service account credentials to Apps Script
const SERVICE_ACCOUNT_EMAIL = 'maritime-service@project-id.iam.gserviceaccount.com';
const PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n';

function getServiceAccountToken() {
  const jwt = createJWT(SERVICE_ACCOUNT_EMAIL, PRIVATE_KEY);
  const response = UrlFetchApp.fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    payload: 'grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=' + jwt
  });
  return JSON.parse(response.getContentText()).access_token;
}

function uploadToCompanyDrive(fileBlob, folderId) {
  const token = getServiceAccountToken();
  const response = DriveApp.createFile(fileBlob); // Use service account token
  return response;
}
```

### Step 4: Security Considerations
- Store service account key securely in Apps Script properties
- Use PropertiesService.getScriptProperties() for sensitive data
- Rotate keys periodically
- Monitor access logs

## Pros:
✅ Secure cross-account access
✅ No manual sharing required
✅ Programmatic control
✅ Audit trail

## Cons: 
❌ Complex setup
❌ Key management required
❌ Additional security considerations