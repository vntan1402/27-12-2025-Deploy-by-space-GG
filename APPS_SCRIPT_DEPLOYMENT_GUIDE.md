# 🚀 Google Apps Script Deployment Guide v3.0

## 📋 Overview
This guide will help you deploy the updated Google Apps Script for Ship Management System Multi Cert Upload functionality.

## ⚠️ Current Issue
Your existing Apps Script URL is returning HTML redirects instead of JSON responses:
```
Current URL: https://script.google.com/macros/s/AKfycby_mu-LZ2GGCndrwgTaxaM3VGjQW9wGfVbfQfF8ZGpGZ7PBsASd-UHkr6esmMKYlpU/exec
Status: ❌ Not Working (HTML redirects)
```

## 🔧 Step-by-Step Deployment

### Step 1: Access Google Apps Script
1. Go to https://script.google.com/
2. Sign in with your Google account (same account used for Google Drive)

### Step 2: Create New Project or Update Existing
**Option A: Update Existing Project (Recommended)**
1. Find your existing "Ship Management" project
2. Open the project
3. Replace all content in `Code.gs` with the new code (see below)

**Option B: Create New Project**
1. Click **"New Project"**
2. Name it "Ship Management v3.0"
3. Replace default code with new code (see below)

### Step 3: Copy the Updated Apps Script Code
Copy the COMPLETE code from `/app/UPDATED_APPS_SCRIPT.js`:

```javascript
/**
 * Ship Management System - Updated Google Apps Script
 * Version: 3.0 - Multi Cert Upload Compatible
 */

function doPost(e) {
  return handleRequest(e);
}

function doGet(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  try {
    // Parse request data
    let requestData = {};
    
    if (e && e.postData && e.postData.contents) {
      try {
        requestData = JSON.parse(e.postData.contents);
      } catch (parseError) {
        return createJsonResponse(false, `Invalid JSON: ${parseError.toString()}`);
      }
    } else if (e && e.parameter) {
      requestData = e.parameter;
    } else {
      // Default response - this proves the script is working
      return createJsonResponse(true, "Ship Management Apps Script v3.0 is WORKING!", {
        version: "3.0-multi-cert-compatible",
        timestamp: new Date().toISOString(),
        supported_actions: [
          "test_connection", 
          "create_complete_ship_structure", 
          "upload_file_with_folder_creation",
          "check_ship_folder_exists"
        ]
      });
    }
    
    const action = requestData.action || "default";
    
    // Handle different actions
    switch (action) {
      case 'test_connection':
        return handleTestConnection(requestData);
        
      case 'create_complete_ship_structure':
        return handleCreateCompleteShipStructure(requestData);
        
      case 'upload_file_with_folder_creation':
        return handleUploadFileWithFolderCreation(requestData);
        
      case 'check_ship_folder_exists':
        return handleCheckShipFolderExists(requestData);
        
      default:
        return createJsonResponse(true, "Apps Script working - no action specified", {
          received_action: action,
          available_actions: [
            "test_connection", 
            "create_complete_ship_structure", 
            "upload_file_with_folder_creation",
            "check_ship_folder_exists"
          ]
        });
    }
    
  } catch (error) {
    return createJsonResponse(false, `Error: ${error.toString()}`);
  }
}

// ... [REST OF THE CODE - Copy everything from UPDATED_APPS_SCRIPT.js]
```

### Step 4: Deploy as Web App
1. **Save the project**: Press `Ctrl+S` or click **Save**
2. **Click Deploy**: In the top-right, click **Deploy** → **New deployment**
3. **Set deployment settings**:
   - **Type**: Web app ⚙️
   - **Execute as**: Me (your-email@gmail.com)
   - **Who has access**: Anyone ⚠️ (Required for external API access)
4. **Click Deploy**
5. **Authorize permissions**:
   - You'll see "Authorization required"
   - Click **Review permissions**
   - Choose your Google account
   - Click **Advanced** → **Go to [Project Name] (unsafe)**
   - Click **Allow**

### Step 5: Copy New Web App URL
After successful deployment, you'll see:
```
✅ Deployment successful!
Web app URL: https://script.google.com/macros/s/[NEW-DEPLOYMENT-ID]/exec
```

**⚠️ IMPORTANT**: Copy this COMPLETE URL (including `/exec`)

### Step 6: Update Ship Management System
1. **Login to your Ship Management System** with admin credentials
2. **Go to System Settings** → **Company Google Drive Configuration**
3. **Update Web App URL** with your new URL
4. **Test Connection** - should show "PASSED"

## 🧪 Testing the Deployment

### Test 1: Direct URL Test
Open your new Web App URL in browser. You should see:
```json
{
  "success": true,
  "message": "Ship Management Apps Script v3.0 is WORKING!",
  "version": "3.0-multi-cert-compatible",
  "supported_actions": ["test_connection", "create_complete_ship_structure", "upload_file_with_folder_creation"]
}
```

### Test 2: Ship Management System Test
1. Login as admin1
2. Go to Company Google Drive settings
3. Click "Test Connection" - should show ✅ PASSED

### Test 3: Multi Cert Upload Test
1. Select a ship (e.g., SUNSHINE 01)
2. Use "Add New Record" → "Certificate" 
3. Upload a PDF certificate
4. Should work without "Upload failed: None" error

## 🔍 Troubleshooting

### Issue: "Authorization required"
**Solution**: Make sure you clicked "Allow" for all permissions during deployment

### Issue: "Script not found" 
**Solution**: Ensure you copied the complete URL including `/exec`

### Issue: Still getting HTML responses
**Solution**: 
1. Check that deployment type is "Web app" not "Add-on"
2. Ensure "Who has access" is set to "Anyone"
3. Try creating a completely new deployment (not updating existing)

### Issue: "Folder not found" errors
**Solution**: Make sure your Google Drive folder ID is correct in Company settings

## 📝 New Features in v3.0

### ✅ Enhanced Multi Cert Upload Support
- **Parameter compatibility**: Matches backend API calls exactly
- **Better error handling**: Clear error messages for debugging
- **Folder structure validation**: Checks if ship folders exist

### ✅ New Actions Supported
- `test_connection`: Test Google Drive access
- `create_complete_ship_structure`: Create ship folders with full hierarchy  
- `upload_file_with_folder_creation`: Upload files to existing ship folders
- `check_ship_folder_exists`: Validate folder structure exists

### ✅ Improved Debugging
- **Detailed response logs**: Better error tracking
- **Version information**: Easy to identify script version
- **Action validation**: Clear supported actions list

## 🎯 Expected Results After Deployment

1. **✅ Google Drive Connection**: Test connection shows "PASSED"
2. **✅ Ship Folder Creation**: New ships create proper folder structure
3. **✅ Certificate Upload**: Multi Cert Upload works without errors
4. **✅ File Organization**: Files upload to correct ship/category folders

## 📞 Support

If you encounter issues:
1. **Check the browser console** for JavaScript errors
2. **Verify permissions** in Google Apps Script project
3. **Test URL directly** in browser first
4. **Ensure Google Drive folder permissions** are correct

---

**🚢 Ready to deploy? Follow the steps above and your Multi Cert Upload will be fully operational!**