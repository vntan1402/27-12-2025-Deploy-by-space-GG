/**
 * Company Google Apps Script - File Upload Only
 * Version: Company File Upload v1.0
 * Purpose: Handle file uploads to Company Google Drive
 * This script runs under Company Google Account with full Drive access
 */

function doPost(e) {
  return handleFileUpload(e);
}

function doGet(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  if (e && e.parameter) {
    return handleFileUpload(e);
  } else {
    return createJsonResponse(true, "Company File Upload Service is WORKING!", {
      version: "company-file-upload-v1.0",
      timestamp: new Date().toISOString(),
      service: "File Upload to Company Google Drive",
      account: "Company Google Account",
      permissions: "Full Google Drive Access",
      supported_actions: [
        "upload_file",
        "create_folder",
        "test_connection"
      ],
      note: "This Apps Script handles file uploads only - Document AI processed separately"
    });
  }
}

function handleFileUpload(e) {
  try {
    console.log("📁 COMPANY FILE UPLOAD STARTED");
    
    var requestData = {};
    
    // Parse request data
    if (e && e.postData && e.postData.contents) {
      try {
        requestData = JSON.parse(e.postData.contents);
      } catch (parseError) {
        return createJsonResponse(false, "Invalid JSON: " + parseError.toString());
      }
    } else if (e && e.parameter) {
      requestData = e.parameter;
    } else {
      return createJsonResponse(false, "No request data provided");
    }
    
    console.log("📊 Request data keys:", Object.keys(requestData));
    
    // Extract required parameters
    var fileContent = requestData.file_content;
    var filename = requestData.filename || "unknown_file";
    var folderPath = requestData.folder_path || "";
    var contentType = requestData.content_type || "application/octet-stream";
    
    console.log("📄 File:", filename);
    console.log("📁 Folder Path:", folderPath);
    console.log("📋 Content Type:", contentType);
    console.log("📊 Content Length:", fileContent ? fileContent.length : 0);
    
    if (!fileContent) {
      console.log("❌ No file content provided");
      return createJsonResponse(false, "No file content provided");
    }
    
    // Decode base64 file content
    var fileBlob;
    try {
      console.log("🔄 Decoding base64 file content...");
      var binaryContent = Utilities.base64Decode(fileContent);
      fileBlob = Utilities.newBlob(binaryContent, contentType, filename);
      console.log("✅ File content decoded successfully");
    } catch (decodeError) {
      console.log("❌ File decode error:", decodeError.toString());
      return createJsonResponse(false, "Failed to decode file content: " + decodeError.toString());
    }
    
    // Create folder structure if needed
    var targetFolder;
    try {
      if (folderPath && folderPath.trim() !== "") {
        console.log("📁 Creating folder structure:", folderPath);
        targetFolder = createFolderStructure(folderPath);
        console.log("✅ Folder structure ready");
      } else {
        console.log("📁 Using root folder");
        targetFolder = DriveApp.getRootFolder();
      }
    } catch (folderError) {
      console.log("❌ Folder creation error:", folderError.toString());
      return createJsonResponse(false, "Failed to create folder structure: " + folderError.toString());
    }
    
    // Upload file to Google Drive
    try {
      console.log("📤 Uploading file to Company Google Drive...");
      var uploadedFile = targetFolder.createFile(fileBlob);
      
      var fileId = uploadedFile.getId();
      var fileSize = uploadedFile.getSize();
      var webViewLink = uploadedFile.getUrl();
      
      console.log("✅ File uploaded successfully!");
      console.log("📄 File ID:", fileId);
      console.log("📊 File Size:", fileSize, "bytes");
      console.log("📁 Folder:", targetFolder.getName());
      console.log("🔗 Web Link:", webViewLink);
      
      return createJsonResponse(true, "File uploaded successfully to Company Google Drive", {
        file_id: fileId,
        filename: filename,
        folder_path: folderPath,
        folder_id: targetFolder.getId(),
        folder_name: targetFolder.getName(),
        file_size: fileSize,
        web_view_link: webViewLink,
        upload_method: "company_apps_script",
        upload_timestamp: new Date().toISOString(),
        company_account: true
      });
      
    } catch (uploadError) {
      console.log("❌ File upload error:", uploadError.toString());
      return createJsonResponse(false, "Failed to upload file to Google Drive: " + uploadError.toString());
    }
    
  } catch (error) {
    console.error("❌ COMPANY FILE UPLOAD ERROR:", error.toString());
    return createJsonResponse(false, "File upload failed: " + error.toString());
  }
}

function createFolderStructure(folderPath) {
  try {
    console.log("🔍 Creating folder structure for path:", folderPath);
    
    // Start from Company's root folder (this script runs under company account)
    var currentFolder = DriveApp.getRootFolder();
    console.log("📁 Starting from company root folder");
    
    // Split path and create nested folders
    var pathParts = folderPath.split('/');
    
    for (var i = 0; i < pathParts.length; i++) {
      var folderName = pathParts[i].trim();
      if (folderName && folderName !== "") {
        console.log("🔍 Processing folder:", folderName);
        
        // Look for existing folder
        var existingFolders = currentFolder.getFoldersByName(folderName);
        
        if (existingFolders.hasNext()) {
          // Use existing folder
          currentFolder = existingFolders.next();
          console.log("📁 Found existing folder:", folderName, "(ID:", currentFolder.getId() + ")");
        } else {
          // Create new folder
          console.log("📁 Creating new folder:", folderName);
          currentFolder = currentFolder.createFolder(folderName);
          console.log("✅ Folder created:", folderName, "(ID:", currentFolder.getId() + ")");
        }
      }
    }
    
    console.log("✅ Final folder structure ready:", folderPath);
    console.log("📁 Target folder ID:", currentFolder.getId());
    console.log("📁 Target folder name:", currentFolder.getName());
    
    return currentFolder;
    
  } catch (error) {
    console.log("❌ Error creating folder structure:", error.toString());
    throw error;
  }
}

function testConnection() {
  try {
    console.log("🔍 Testing Company Google Drive connection...");
    
    // Test basic Drive access
    var rootFolder = DriveApp.getRootFolder();
    var folderName = rootFolder.getName();
    var folderId = rootFolder.getId();
    
    console.log("✅ Company Google Drive connection successful");
    console.log("📁 Root folder name:", folderName);
    console.log("📁 Root folder ID:", folderId);
    
    return createJsonResponse(true, "Company Google Drive connection successful", {
      root_folder_id: folderId,
      root_folder_name: folderName,
      connection_test: "passed",
      account_type: "company_google_account",
      permissions: "full_drive_access",
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.log("❌ Company Google Drive connection failed:", error.toString());
    return createJsonResponse(false, "Connection test failed: " + error.toString());
  }
}

function createJsonResponse(success, message, data) {
  var result = {
    success: success,
    message: message,
    timestamp: new Date().toISOString(),
    service: "Company File Upload Service v1.0",
    account: "Company Google Account"
  };

  if (data) {
    if (success) {
      result.data = data;
    } else {
      result.error_details = data;
    }
  }

  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}