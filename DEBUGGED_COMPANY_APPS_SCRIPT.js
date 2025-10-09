function doPost(e) {
  return handleRequest(e);
}

function doGet(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  try {
    var requestData = {};
    
    if (e && e.postData && e.postData.contents) {
      requestData = JSON.parse(e.postData.contents);
    } else if (e && e.parameter) {
      requestData = e.parameter;
    }
    
    var action = requestData.action || "passport_upload";
    
    Logger.log("🔄 Request action: " + action);
    Logger.log("📋 Request data: " + JSON.stringify(requestData, null, 2));
    
    switch (action) {
      case "passport_upload":
        return handlePassportUpload(requestData);
      case "test_drive_permission":
        return testDrivePermission(requestData);
      case "upload_file_with_folder_creation":
        return handleUpload(requestData);
      case "test_connection":
        return handleTestConnection(requestData);
      case "create_complete_ship_structure":
        return handleCreateShipStructure(requestData);
      default:
        return handlePassportUpload(requestData);
    }
    
  } catch (error) {
    Logger.log("❌ Request handling error: " + error.toString());
    Logger.log("❌ Stack trace: " + error.stack);
    return createResponse(false, "Error: " + error.toString(), {
      error_type: "request_handling_error",
      stack_trace: error.stack
    });
  }
}

/**
 * Test Google Drive permissions and access
 */
function testDrivePermission(requestData) {
  try {
    Logger.log("🧪 Testing Google Drive permissions...");
    
    var parentFolderId = requestData.parent_folder_id;
    var results = {
      tests: {},
      permissions: {},
      environment: {}
    };
    
    // Test 1: Basic DriveApp access
    try {
      var rootFolder = DriveApp.getRootFolder();
      results.tests.driveapp_access = {
        success: true,
        message: "DriveApp access successful"
      };
      Logger.log("✅ DriveApp access test passed");
    } catch (e) {
      results.tests.driveapp_access = {
        success: false,
        error: e.toString()
      };
      Logger.log("❌ DriveApp access test failed: " + e.toString());
    }
    
    // Test 2: Folder access (if parent_folder_id provided)
    if (parentFolderId) {
      try {
        var testFolder = DriveApp.getFolderById(parentFolderId);
        var folderName = testFolder.getName();
        results.tests.folder_access = {
          success: true,
          folder_name: folderName,
          folder_id: parentFolderId
        };
        Logger.log("✅ Folder access test passed: " + folderName);
        
        // Test 3: Create test file
        try {
          var testFileName = "TEST_DRIVE_ACCESS_" + new Date().getTime() + ".txt";
          var testFileContent = "This is a test file created at " + new Date().toISOString();
          var testFile = testFolder.createFile(testFileName, testFileContent, "text/plain");
          
          results.tests.file_creation = {
            success: true,
            file_id: testFile.getId(),
            file_name: testFile.getName(),
            file_url: testFile.getUrl()
          };
          Logger.log("✅ File creation test passed: " + testFile.getId());
          
          // Clean up: delete test file
          try {
            testFile.setTrashed(true);
            Logger.log("🗑️ Test file cleaned up");
          } catch (cleanupError) {
            Logger.log("⚠️ Cleanup warning: " + cleanupError.toString());
          }
          
        } catch (fileError) {
          results.tests.file_creation = {
            success: false,
            error: fileError.toString(),
            error_type: "file_creation_error"
          };
          Logger.log("❌ File creation test failed: " + fileError.toString());
        }
        
      } catch (folderError) {
        results.tests.folder_access = {
          success: false,
          error: folderError.toString(),
          error_type: "folder_access_error"
        };
        Logger.log("❌ Folder access test failed: " + folderError.toString());
      }
    } else {
      results.tests.folder_access = {
        success: false,
        message: "No parent_folder_id provided for testing"
      };
    }
    
    // Check authorization info
    try {
      results.permissions.user_email = Session.getActiveUser().getEmail();
      results.environment.timezone = Session.getScriptTimeZone();
      Logger.log("📧 User email: " + results.permissions.user_email);
    } catch (e) {
      results.permissions.error = e.toString();
    }
    
    return createResponse(true, "Drive permission test completed", results);
    
  } catch (error) {
    Logger.log("❌ Drive permission test error: " + error.toString());
    return createResponse(false, "Drive permission test failed: " + error.toString(), {
      error_type: "permission_test_error",
      stack_trace: error.stack
    });
  }
}

/**
 * Enhanced passport upload with detailed debugging
 */
function handlePassportUpload(requestData) {
  try {
    Logger.log("🔄 Starting ENHANCED passport upload with debugging...");
    Logger.log("📋 Request keys: " + Object.keys(requestData).join(", "));
    
    var filename = requestData.filename;
    var fileContent = requestData.file_content;
    var folderPath = requestData.folder_path;
    var contentType = requestData.content_type || "application/pdf";
    var parentFolderId = requestData.parent_folder_id;
    
    // Validate parameters
    var validation = validateUploadParameters(filename, fileContent, folderPath, parentFolderId);
    if (!validation.valid) {
      return createResponse(false, validation.error);
    }
    
    Logger.log("✅ Parameter validation passed");
    Logger.log("📁 Parent folder ID: " + parentFolderId);
    Logger.log("📂 Target folder path: " + folderPath);
    Logger.log("📄 Filename: " + filename);
    Logger.log("📊 Content type: " + contentType);
    Logger.log("📏 Content length: " + (fileContent ? fileContent.length : 0) + " characters");
    
    // Step 1: Get parent folder
    var parentFolder;
    try {
      parentFolder = DriveApp.getFolderById(parentFolderId);
      Logger.log("✅ Parent folder accessed: " + parentFolder.getName());
    } catch (folderError) {
      Logger.log("❌ Parent folder access error: " + folderError.toString());
      return createResponse(false, "Parent folder not accessible: " + folderError.toString(), {
        error_type: "folder_access_error",
        parent_folder_id: parentFolderId
      });
    }
    
    // Step 2: Create folder path
    var targetFolder;
    try {
      targetFolder = createFolderPath(parentFolder, folderPath);
      if (!targetFolder) {
        Logger.log("❌ Failed to create folder path: " + folderPath);
        return createResponse(false, "Failed to create folder path: " + folderPath);
      }
      Logger.log("✅ Target folder ready: " + targetFolder.getName() + " (ID: " + targetFolder.getId() + ")");
    } catch (pathError) {
      Logger.log("❌ Folder path creation error: " + pathError.toString());
      return createResponse(false, "Folder path creation failed: " + pathError.toString(), {
        error_type: "folder_creation_error"
      });
    }
    
    // Step 3: Decode file content
    var binaryData;
    try {
      binaryData = Utilities.base64Decode(fileContent);
      Logger.log("✅ File content decoded successfully");
      Logger.log("📏 Binary data length: " + binaryData.length + " bytes");
    } catch (decodeError) {
      Logger.log("❌ Base64 decode error: " + decodeError.toString());
      return createResponse(false, "File content decode failed: " + decodeError.toString(), {
        error_type: "base64_decode_error"
      });
    }
    
    // Step 4: Create blob
    var blob;
    try {
      blob = Utilities.newBlob(binaryData, contentType, filename);
      Logger.log("✅ Blob created successfully");
      Logger.log("📊 Blob size: " + blob.getBytes().length + " bytes");
      Logger.log("📊 Blob type: " + blob.getContentType());
    } catch (blobError) {
      Logger.log("❌ Blob creation error: " + blobError.toString());
      return createResponse(false, "Blob creation failed: " + blobError.toString(), {
        error_type: "blob_creation_error"
      });
    }
    
    // Step 5: Create file in Google Drive
    var uploadedFile;
    try {
      Logger.log("📤 Creating file in Google Drive...");
      uploadedFile = targetFolder.createFile(blob);
      
      // Verify file was actually created
      var fileId = uploadedFile.getId();
      var fileName = uploadedFile.getName();
      var fileUrl = uploadedFile.getUrl();
      var fileSize = uploadedFile.getSize();
      
      Logger.log("🎉 FILE CREATED SUCCESSFULLY!");
      Logger.log("🆔 File ID: " + fileId);
      Logger.log("📝 File name: " + fileName);
      Logger.log("🔗 File URL: " + fileUrl);
      Logger.log("📏 File size: " + fileSize + " bytes");
      
      // Double-check file exists by trying to access it
      try {
        var verifyFile = DriveApp.getFileById(fileId);
        Logger.log("✅ File verification passed: " + verifyFile.getName());
      } catch (verifyError) {
        Logger.log("❌ File verification failed: " + verifyError.toString());
        return createResponse(false, "File created but verification failed: " + verifyError.toString(), {
          error_type: "file_verification_error",
          file_id: fileId
        });
      }
      
      return createResponse(true, "File uploaded successfully to " + folderPath, {
        file_id: fileId,
        file_name: fileName,
        file_url: fileUrl,
        folder_path: folderPath,
        folder_id: targetFolder.getId(),
        folder_name: targetFolder.getName(),
        upload_timestamp: new Date().toISOString(),
        file_size: fileSize,
        content_type: contentType,
        verification_status: "passed",
        debug_info: {
          parent_folder_accessible: true,
          target_folder_created: true,
          file_content_decoded: true,
          blob_created: true,
          drive_file_created: true,
          file_verified: true
        }
      });
      
    } catch (createError) {
      Logger.log("❌ CRITICAL: File creation failed: " + createError.toString());
      Logger.log("❌ Error stack: " + createError.stack);
      
      return createResponse(false, "Google Drive file creation failed: " + createError.toString(), {
        error_type: "drive_file_creation_error",
        stack_trace: createError.stack,
        debug_info: {
          parent_folder_accessible: !!parentFolder,
          target_folder_created: !!targetFolder,
          file_content_decoded: !!binaryData,
          blob_created: !!blob,
          drive_file_created: false
        }
      });
    }
    
  } catch (error) {
    Logger.log("❌ CRITICAL: Passport upload handler error: " + error.toString());
    Logger.log("❌ Stack trace: " + error.stack);
    return createResponse(false, "Upload failed: " + error.toString(), {
      folder_path: requestData.folder_path || "unknown",
      filename: requestData.filename || "unknown",
      error_type: "general_upload_error",
      stack_trace: error.stack
    });
  }
}

function validateUploadParameters(filename, fileContent, folderPath, parentFolderId) {
  if (!filename) {
    return { valid: false, error: "Missing required parameter: filename" };
  }
  if (!fileContent) {
    return { valid: false, error: "Missing required parameter: file_content" };
  }
  if (!folderPath) {
    return { valid: false, error: "Missing required parameter: folder_path" };
  }
  if (!parentFolderId) {
    return { valid: false, error: "Missing required parameter: parent_folder_id" };
  }
  return { valid: true };
}

/**
 * Enhanced folder path creation with debugging
 */
function createFolderPath(rootFolder, folderPath) {
  try {
    Logger.log("🏗️ Creating folder path: " + folderPath);
    
    if (!folderPath || folderPath === "/" || folderPath === "") {
      Logger.log("✅ Using root folder as target");
      return rootFolder;
    }
    
    var pathParts = folderPath.split('/').filter(function(part) {
      return part.length > 0;
    });
    
    Logger.log("📁 Path parts: " + JSON.stringify(pathParts));
    
    var currentFolder = rootFolder;
    
    for (var i = 0; i < pathParts.length; i++) {
      var folderName = pathParts[i].trim();
      Logger.log("📂 Processing folder: " + folderName + " (" + (i + 1) + "/" + pathParts.length + ")");
      
      try {
        var existingFolder = findFolderByName(currentFolder, folderName);
        if (existingFolder) {
          Logger.log("   ✅ Found existing folder: " + folderName + " (ID: " + existingFolder.getId() + ")");
          currentFolder = existingFolder;
        } else {
          Logger.log("   🆕 Creating new folder: " + folderName);
          currentFolder = currentFolder.createFolder(folderName);
          Logger.log("   ✅ Created folder: " + folderName + " (ID: " + currentFolder.getId() + ")");
        }
      } catch (folderError) {
        Logger.log("   ❌ Failed to process folder: " + folderName + " - " + folderError.toString());
        return null;
      }
    }
    
    Logger.log("✅ Final target folder: " + currentFolder.getName() + " (ID: " + currentFolder.getId() + ")");
    return currentFolder;
    
  } catch (error) {
    Logger.log("❌ Error creating folder path: " + error.toString());
    return null;
  }
}

function createResponse(success, message, data) {
  var response = {
    success: success,
    message: message,
    timestamp: new Date().toISOString(),
    service: "Company Apps Script - Enhanced Debug",
    version: "v5.0-debug-enhanced"
  };
  
  if (data) {
    for (var key in data) {
      response[key] = data[key];
    }
  }
  
  Logger.log("📤 Response: " + JSON.stringify(response, null, 2));
  
  return ContentService
    .createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}

// Utility functions
function findFolderByName(parentFolder, folderName) {
  try {
    var folders = parentFolder.getFoldersByName(folderName);
    return folders.hasNext() ? folders.next() : null;
  } catch (error) {
    Logger.log("❌ Error finding folder: " + folderName + " - " + error.toString());
    return null;
  }
}

function handleTestConnection(requestData) {
  try {
    var folderId = requestData.folder_id || requestData.parent_folder_id;
    if (!folderId) {
      return createResponse(false, "Missing folder_id or parent_folder_id");
    }
    
    var folder = DriveApp.getFolderById(folderId);
    return createResponse(true, "Connection successful", {
      folder_name: folder.getName(),
      folder_id: folderId,
      test_result: "PASSED"
    });
    
  } catch (error) {
    return createResponse(false, "Connection failed: " + error.toString());
  }
}