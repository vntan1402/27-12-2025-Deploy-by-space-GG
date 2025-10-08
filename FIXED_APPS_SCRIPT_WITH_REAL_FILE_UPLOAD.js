function doPost(e) {
  return handleRequest(e);
}

function doGet(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  try {
    console.log("🔄 REQUEST RECEIVED");
    
    var requestData = {};

    if (e && e.postData && e.postData.contents) {
      console.log("📥 POST DATA DETECTED");
      console.log("Content length:", e.postData.contents.length);
      
      try {
        requestData = JSON.parse(e.postData.contents);
        console.log("✅ JSON PARSED SUCCESS");
        console.log("Action:", requestData.action);
        console.log("Filename:", requestData.filename);
      } catch (parseError) {
        console.log("❌ JSON PARSE ERROR:", parseError.toString());
        return createJsonResponse(false, "Invalid JSON: " + parseError.toString());
      }
    } else {
      console.log("📥 NO DATA - Returning test response");
      return createJsonResponse(true, "Fixed Apps Script with Real File Upload is WORKING!", {
        version: "fixed-real-upload-v1.0",
        timestamp: new Date().toISOString(),
        supported_actions: [
          "analyze_passport_document_ai",
          "upload_file"
        ]
      });
    }

    var action = requestData.action || "default";
    console.log("🎯 ACTION TO EXECUTE:", action);

    // Handle all maritime document actions
    switch (action) {
      case "analyze_passport_document_ai":
        return handleDocumentAnalysis(requestData, "passport");
      case "upload_file":
        return handleRealFileUpload(requestData);
      default:
        console.log("❌ UNKNOWN ACTION:", action);
        return createJsonResponse(false, "Unknown action: " + action);
    }

  } catch (error) {
    console.error("❌ REQUEST ERROR:", error.toString());
    return createJsonResponse(false, "Request handling error: " + error.toString());
  }
}

function handleDocumentAnalysis(data, documentType) {
  try {
    console.log("🔄 DOCUMENT ANALYSIS STARTED");
    console.log("Document Type:", documentType);
    
    // Validate required parameters
    var projectId = data.project_id;
    var processorId = data.processor_id;
    var location = data.location || "us";
    var fileContent = data.file_content;
    var filename = data.filename || "document";
    
    console.log("📄 File:", filename);
    console.log("🏗️ Project:", projectId);
    console.log("📍 Location:", location);
    console.log("⚙️ Processor:", processorId);
    console.log("📊 Content size:", fileContent ? fileContent.length : 0);
    
    if (!projectId || !processorId || !fileContent) {
      console.log("❌ Missing required parameters");
      return createJsonResponse(false, "Missing required parameters for Document AI");
    }

    try {
      // Call Document AI API
      var apiUrl = `https://${location}-documentai.googleapis.com/v1/projects/${projectId}/locations/${location}/processors/${processorId}:process`;
      
      var payload = {
        rawDocument: {
          content: fileContent,
          mimeType: data.content_type || "application/pdf"
        }
      };

      var options = {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + ScriptApp.getOAuthToken(),
          "Content-Type": "application/json"
        },
        payload: JSON.stringify(payload)
      };

      console.log("🤖 Calling Document AI...");
      var response = UrlFetchApp.fetch(apiUrl, options);
      var responseData = JSON.parse(response.getContentText());
      
      console.log("✅ Document AI analysis completed");
      
      // Extract text from Document AI response
      var extractedText = "";
      if (responseData.document && responseData.document.text) {
        extractedText = responseData.document.text;
      }
      
      console.log("📝 Extracted text length:", extractedText.length);
      
      // Create summary based on extracted text
      var summary = createDocumentSummary(extractedText, filename, documentType);
      
      return createJsonResponse(true, "Document AI analysis completed successfully", {
        summary: summary,
        extracted_text_length: extractedText.length,
        document_type: documentType,
        filename: filename,
        processor_id: processorId
      });
      
    } catch (apiError) {
      console.error("❌ Document AI API Error:", apiError.toString());
      return createJsonResponse(false, "Document AI processing failed: " + apiError.toString());
    }
    
  } catch (error) {
    console.error("❌ DOCUMENT ANALYSIS ERROR:", error.toString());
    return createJsonResponse(false, "Document analysis failed: " + error.toString());
  }
}

function handleRealFileUpload(data) {
  try {
    console.log("📁 REAL FILE UPLOAD STARTED");
    console.log("Data keys:", Object.keys(data || {}));
    
    var filename = data.filename || "unknown_file";
    var fileContent = data.file_content;
    var contentType = data.content_type || "text/plain";
    var shipName = data.ship_name;
    var category = data.category;
    var parentCategory = data.parent_category;
    
    console.log("📄 File:", filename);
    console.log("🚢 Ship:", shipName);
    console.log("📂 Category:", category);
    console.log("📂 Parent Category:", parentCategory);
    console.log("📊 Content size:", fileContent ? fileContent.length : 0);
    
    if (!fileContent) {
      console.log("❌ No file content provided");
      return createJsonResponse(false, "No file content provided");
    }
    
    // Get the company folder from parent_folder_id
    var parentFolderId = data.parent_folder_id;
    var rootFolder;
    
    if (parentFolderId) {
      try {
        rootFolder = DriveApp.getFolderById(parentFolderId);
        console.log("✅ Using company folder ID: " + parentFolderId);
      } catch (folderError) {
        console.log("❌ Cannot access folder ID: " + parentFolderId + ", using root folder");
        rootFolder = DriveApp.getRootFolder();
      }
    } else {
      console.log("⚠️ No parent_folder_id provided, using root folder");
      rootFolder = DriveApp.getRootFolder();
    }
    
    // Create folder structure
    var targetFolder;
    
    if (shipName) {
      // Ship-specific file: Ship > Category
      console.log("📁 Creating ship-specific folder structure...");
      var shipFolder = findOrCreateFolder(rootFolder, shipName);
      targetFolder = findOrCreateFolder(shipFolder, category);
      console.log("✅ Ship folder structure created: " + shipName + "/" + category);
    } else {
      // Root-level folder like SUMMARY
      console.log("📁 Creating root-level folder: " + category);
      targetFolder = findOrCreateFolder(rootFolder, category);
      console.log("✅ Root folder created: " + category);
    }
    
    // Decode base64 file content
    var fileBlob;
    try {
      var binaryContent = Utilities.base64Decode(fileContent);
      fileBlob = Utilities.newBlob(binaryContent, contentType, filename);
      console.log("✅ File content decoded successfully");
    } catch (decodeError) {
      console.log("❌ File decode error:", decodeError.toString());
      return createJsonResponse(false, "Failed to decode file content: " + decodeError.toString());
    }
    
    // Upload file to Google Drive
    try {
      var uploadedFile = targetFolder.createFile(fileBlob);
      console.log("✅ File uploaded successfully");
      console.log("📁 File ID:", uploadedFile.getId());
      console.log("📍 Folder ID:", targetFolder.getId());
      
      return createJsonResponse(true, "File uploaded successfully to Google Drive", {
        file_id: uploadedFile.getId(),
        filename: filename,
        folder_id: targetFolder.getId(),
        folder_name: targetFolder.getName(),
        ship_name: shipName,
        category: category,
        file_url: uploadedFile.getUrl(),
        upload_method: "google_drive_real_upload"
      });
      
    } catch (uploadError) {
      console.log("❌ File upload error:", uploadError.toString());
      return createJsonResponse(false, "Failed to upload file: " + uploadError.toString());
    }
    
  } catch (error) {
    console.error("❌ FILE UPLOAD ERROR:", error.toString());
    return createJsonResponse(false, "File upload failed: " + error.toString());
  }
}

function findOrCreateFolder(parentFolder, folderName) {
  try {
    // Look for existing folder
    var folders = parentFolder.getFoldersByName(folderName);
    if (folders.hasNext()) {
      console.log("📁 Found existing folder: " + folderName);
      return folders.next();
    }
    
    // Create new folder
    console.log("📁 Creating new folder: " + folderName);
    var newFolder = parentFolder.createFolder(folderName);
    console.log("✅ Folder created successfully: " + folderName);
    return newFolder;
    
  } catch (error) {
    console.log("❌ Error creating folder '" + folderName + "':", error.toString());
    throw error;
  }
}

function createDocumentSummary(extractedText, filename, documentType) {
  try {
    console.log("📋 Creating document summary...");
    
    var summary = `DOCUMENT AI SUMMARY
Generated on: ${new Date().toISOString()}
File: ${filename}
Document Type: ${documentType}

EXTRACTED CONTENT:
${extractedText}

This summary was generated using Google Document AI for maritime document processing.`;
    
    console.log("✅ Summary created, length:", summary.length);
    return summary;
    
  } catch (error) {
    console.error("❌ Summary creation error:", error.toString());
    return "Summary creation failed: " + error.toString();
  }
}

function createJsonResponse(success, message, data) {
  var result = {
    success: success,
    message: message,
    timestamp: new Date().toISOString(),
    service: "Maritime Document AI with Real Upload v1.0"
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