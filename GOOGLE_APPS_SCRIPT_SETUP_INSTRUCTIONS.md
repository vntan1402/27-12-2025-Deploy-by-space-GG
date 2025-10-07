# Google Apps Script Setup Instructions for Document AI Integration

## Overview
This document provides step-by-step instructions to set up Google Apps Script with Document AI integration for the Ship Management System.

## Prerequisites
1. Google Cloud Project with Document AI API enabled
2. Google Apps Script project
3. Admin access to Google Drive

## Setup Steps

### 1. Create/Update Google Apps Script
1. Go to [Google Apps Script](https://script.google.com)
2. Create a new project or open existing project
3. Replace the code with the content from `GOOGLE_APPS_SCRIPT_WITH_DOCUMENT_AI.js`
4. Save the project

### 2. Configure OAuth Scopes
Add the following scopes to your Apps Script manifest (`appsscript.json`):

```json
{
  "timeZone": "Asia/Ho_Chi_Minh",
  "dependencies": {
    "enabledAdvancedServices": []
  },
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "oauthScopes": [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/documentai"
  ]
}
```

### 3. Deploy as Web App
1. In Apps Script editor, click "Deploy" → "New deployment"
2. Choose type: "Web app"
3. Description: "Ship Management with Document AI v3.8"
4. Execute as: "Me"
5. Who has access: "Anyone" (or "Anyone with Google account" for security)
6. Click "Deploy"
7. Copy the Web App URL

### 4. Configure Document AI Permissions
Ensure your Google account (the one running the Apps Script) has the following IAM roles in your Google Cloud Project:
- Document AI API User
- Service Usage Consumer

### 5. Test the Setup
1. Open the Web App URL in browser
2. You should see: "Ship Management Apps Script v3.8-with-document-ai is WORKING!"
3. The supported_actions should include:
   - `test_document_ai_connection`
   - `analyze_passport_document_ai`

### 6. Update Ship Management System Configuration
1. Login to Ship Management System as Admin
2. Go to System Settings → System Google Drive Configuration
3. Update the Google Apps Script URL with your new deployment URL
4. Save configuration

### 7. Configure Document AI Settings
1. Go to System Settings → AI Configuration
2. Enable Google Document AI
3. Enter your Project ID, Location, and Processor ID
4. Click "Test Connection" to verify setup
5. Save configuration

## Troubleshooting

### Common Issues:

1. **"Authorization required" error**
   - Run any function in Apps Script editor manually first
   - This will trigger OAuth authorization flow

2. **"Document AI API not enabled"**
   - Enable Document AI API in Google Cloud Console
   - Ensure billing is enabled for the project

3. **"Insufficient permissions"**
   - Check IAM roles in Google Cloud Console
   - Ensure the Google account has Document AI API User role

4. **"Invalid processor ID"**
   - Verify processor ID in Google Cloud Console → Document AI
   - Ensure processor is in the correct location (us, eu, etc.)

### Testing Individual Components:

1. **Test Apps Script directly:**
   ```
   Open Web App URL → Should show success message
   ```

2. **Test Document AI connection:**
   ```
   POST to Apps Script URL with:
   {
     "action": "test_document_ai_connection",
     "project_id": "your-project-id",
     "location": "us",
     "processor_id": "your-processor-id"
   }
   ```

3. **Test passport analysis:**
   ```
   POST to Apps Script URL with:
   {
     "action": "analyze_passport_document_ai",
     "project_id": "your-project-id",
     "processor_id": "your-processor-id",
     "file_content": "base64-encoded-file-content",
     "filename": "passport.pdf",
     "content_type": "application/pdf"
   }
   ```

## Security Considerations

1. **OAuth Scopes**: Only include necessary scopes
2. **Access Control**: Consider restricting Web App access to specific users/domain
3. **API Keys**: Never store API keys in Apps Script code - use OAuth instead
4. **Logging**: Monitor Apps Script execution logs for security events

## Support

If you encounter issues:
1. Check Apps Script execution logs
2. Verify Google Cloud Console settings
3. Test individual components as described above
4. Contact system administrator with specific error messages