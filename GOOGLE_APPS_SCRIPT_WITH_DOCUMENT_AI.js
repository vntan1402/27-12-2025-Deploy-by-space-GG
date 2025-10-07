// Google Apps Script with Document AI Integration
// Version: 3.8-with-document-ai

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
      try {
        requestData = JSON.parse(e.postData.contents);
      } catch (parseError) {
        return createJsonResponse(false, "Invalid JSON: " + parseError.toString());
      }
    } else if (e && e.parameter) {
      requestData = e.parameter;
    } else {
      return createJsonResponse(true, "Ship Management Apps Script v3.8-with-document-ai is WORKING!", {
        version: "3.8-document-ai-integration",
        timestamp: new Date().toISOString(),
        supported_actions: [
          "test_connection",
          "test_document_ai_connection",
          "analyze_passport_document_ai", 
          "create_complete_ship_structure", 
          "upload_file_with_folder_creation",
          "check_ship_folder_exists",
          "get_folder_structure",
          "move_file",
          "delete_file",
          "rename_file",
          "delete_complete_ship_structure"
        ]
      });
    }
    
    var action = requestData.action || "default";
    
    switch (action) {
      case 'test_connection':
        return handleTestConnection(requestData);
        
      case 'test_document_ai_connection':
        return handleTestDocumentAIConnection(requestData);
        
      case 'analyze_passport_document_ai':
        return handleAnalyzePassportDocumentAI(requestData);
        
      case 'create_complete_ship_structure':
        return handleCreateCompleteShipStructure(requestData);
        
      case 'upload_file_with_folder_creation':
        return handleUploadFileWithFolderCreation(requestData);
        
      case 'check_ship_folder_exists':
        return handleCheckShipFolderExists(requestData);
        
      case 'get_folder_structure':
        return handleGetFolderStructure(requestData);
        
      case 'move_file':
        return handleMoveFile(requestData);
        
      case 'delete_file':
        return handleDeleteFile(requestData);
        
      case 'rename_file':
        return handleRenameFile(requestData);
        
      case 'delete_complete_ship_structure':
        return handleDeleteCompleteShipStructure(requestData);
        
      default:
        return createJsonResponse(false, "Unknown action: " + action);
    }
    
  } catch (error) {
    return createJsonResponse(false, "Error: " + error.toString());
  }
}

// ===========================================
// DOCUMENT AI FUNCTIONS
// ===========================================

/**
 * Test connection to Google Document AI
 */
function handleTestDocumentAIConnection(data) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;
    
    if (!projectId || !processorId) {
      return createJsonResponse(false, "Missing required parameters: project_id, processor_id");
    }
    
    // Get access token
    var token = getDocumentAIAccessToken();
    if (!token) {
      return createJsonResponse(false, "Failed to obtain access token for Document AI");
    }
    
    // Test connection by getting processor info
    var processorName = "projects/" + projectId + "/locations/" + location + "/processors/" + processorId;
    var url = "https://documentai.googleapis.com/v1/" + processorName;
    
    var options = {
      'method': 'GET',
      'headers': {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
      }
    };
    
    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    
    if (responseCode === 200) {
      var processorInfo = JSON.parse(response.getContentText());
      return createJsonResponse(true, "Document AI connection successful", {
        processor_name: processorInfo.displayName || processorInfo.name,
        processor_type: processorInfo.type || 'Unknown',
        processor_state: processorInfo.state || 'Unknown'
      });
    } else {
      var errorText = response.getContentText();
      return createJsonResponse(false, "Document AI connection failed: " + errorText);
    }
    
  } catch (error) {
    return createJsonResponse(false, "Document AI connection test error: " + error.toString());
  }
}

/**
 * Analyze passport document using Google Document AI
 */
function handleAnalyzePassportDocumentAI(data) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;
    var fileContent = data.file_content; // Base64 encoded
    var filename = data.filename;
    var contentType = data.content_type;
    
    if (!projectId || !processorId || !fileContent) {
      return createJsonResponse(false, "Missing required parameters: project_id, processor_id, file_content");
    }
    
    // Get access token
    var token = getDocumentAIAccessToken();
    if (!token) {
      return createJsonResponse(false, "Failed to obtain access token for Document AI");
    }
    
    // Prepare Document AI request
    var processorName = "projects/" + projectId + "/locations/" + location + "/processors/" + processorId;
    var url = "https://documentai.googleapis.com/v1/" + processorName + ":process";
    
    var requestBody = {
      "rawDocument": {
        "content": fileContent,
        "mimeType": contentType || "application/pdf"
      }
    };
    
    var options = {
      'method': 'POST',
      'headers': {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
      },
      'payload': JSON.stringify(requestBody)
    };
    
    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    
    if (responseCode === 200) {
      var result = JSON.parse(response.getContentText());
      
      // Extract information from Document AI result
      var extractedInfo = extractPassportInformation(result);
      
      return createJsonResponse(true, "Passport analysis completed", {
        analysis: extractedInfo,
        document_ai_response: result.document ? {
          text: result.document.text ? result.document.text.substring(0, 500) + "..." : "",
          entities_count: result.document.entities ? result.document.entities.length : 0
        } : null
      });
      
    } else {
      var errorText = response.getContentText();
      return createJsonResponse(false, "Document AI processing failed: " + errorText);
    }
    
  } catch (error) {
    return createJsonResponse(false, "Document AI analysis error: " + error.toString());
  }
}

/**
 * Extract passport information from Document AI response
 */
function extractPassportInformation(documentAIResult) {
  try {
    var document = documentAIResult.document;
    var extractedInfo = {
      full_name: "",
      sex: "",
      date_of_birth: "",
      place_of_birth: "",
      passport_number: "",
      nationality: "",
      issue_date: "",
      expiry_date: "",
      confidence_score: 0.0
    };
    
    if (!document || !document.entities) {
      return extractedInfo;
    }
    
    var entities = document.entities;
    var confidenceScores = [];
    
    // Map Document AI entities to passport fields
    entities.forEach(function(entity) {
      var entityType = entity.type || "";
      var entityText = entity.mentionText || "";
      var confidence = entity.confidence || 0;
      
      confidenceScores.push(confidence);
      
      switch (entityType.toLowerCase()) {
        case 'person_name':
        case 'name':
        case 'full_name':
          extractedInfo.full_name = entityText;
          break;
        case 'sex':
        case 'gender':
          extractedInfo.sex = entityText.toUpperCase().charAt(0); // M or F
          break;
        case 'date_of_birth':
        case 'birth_date':
        case 'dob':
          extractedInfo.date_of_birth = formatDate(entityText);
          break;
        case 'place_of_birth':
        case 'birth_place':
          extractedInfo.place_of_birth = entityText;
          break;
        case 'passport_number':
        case 'document_number':
        case 'passport_id':
          extractedInfo.passport_number = entityText;
          break;
        case 'nationality':
        case 'country':
          extractedInfo.nationality = entityText;
          break;
        case 'issue_date':
        case 'date_of_issue':
          extractedInfo.issue_date = formatDate(entityText);
          break;
        case 'expiry_date':
        case 'expiration_date':
        case 'date_of_expiry':
          extractedInfo.expiry_date = formatDate(entityText);
          break;
      }
    });
    
    // Calculate average confidence
    if (confidenceScores.length > 0) {
      extractedInfo.confidence_score = confidenceScores.reduce(function(a, b) { return a + b; }) / confidenceScores.length;
    }
    
    // Fallback: try to extract from document text using patterns
    if (document.text && (!extractedInfo.full_name || !extractedInfo.passport_number)) {
      var textInfo = extractFromText(document.text);
      if (!extractedInfo.full_name) extractedInfo.full_name = textInfo.full_name;
      if (!extractedInfo.passport_number) extractedInfo.passport_number = textInfo.passport_number;
      if (!extractedInfo.date_of_birth) extractedInfo.date_of_birth = textInfo.date_of_birth;
    }
    
    return extractedInfo;
    
  } catch (error) {
    return {
      error: "Information extraction failed: " + error.toString(),
      confidence_score: 0.0
    };
  }
}

/**
 * Extract passport info from text using patterns (fallback method)
 */
function extractFromText(text) {
  var info = {
    full_name: "",
    passport_number: "",
    date_of_birth: ""
  };
  
  try {
    // Common passport number patterns
    var passportPatterns = [
      /(?:Passport\s*(?:No|Number)[:.]?\s*)([A-Z0-9]{6,12})/i,
      /(?:Document\s*(?:No|Number)[:.]?\s*)([A-Z0-9]{6,12})/i,
      /\b([A-Z]{1,2}[0-9]{6,10})\b/
    ];
    
    for (var i = 0; i < passportPatterns.length; i++) {
      var match = text.match(passportPatterns[i]);
      if (match && match[1]) {
        info.passport_number = match[1];
        break;
      }
    }
    
    // Date patterns (DD/MM/YYYY, DD-MM-YYYY, etc.)
    var datePatterns = [
      /\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})\b/g
    ];
    
    datePatterns.forEach(function(pattern) {
      var matches = text.match(pattern);
      if (matches && matches.length > 0) {
        info.date_of_birth = formatDate(matches[0]);
      }
    });
    
    return info;
    
  } catch (error) {
    return info;
  }
}

/**
 * Format date to YYYY-MM-DD format
 */
function formatDate(dateString) {
  if (!dateString) return "";
  
  try {
    // Handle various date formats
    var cleanDate = dateString.replace(/[^\d\/\-\.]/g, "");
    var parts = cleanDate.split(/[\/\-\.]/);
    
    if (parts.length === 3) {
      var day = parts[0];
      var month = parts[1];
      var year = parts[2];
      
      // Ensure 4-digit year
      if (year.length === 2) {
        year = "19" + year; // Assume 19xx for 2-digit years
      }
      
      // Return in YYYY-MM-DD format
      return year + "-" + month.padStart(2, '0') + "-" + day.padStart(2, '0');
    }
    
    return dateString;
  } catch (error) {
    return dateString;
  }
}

/**
 * Get access token for Document AI API
 */
function getDocumentAIAccessToken() {
  try {
    // Use Google Apps Script's built-in OAuth token with Document AI scope
    var token = ScriptApp.getOAuthToken();
    
    // Alternatively, you can use Service Account credentials stored in PropertiesService
    // var serviceAccountKey = PropertiesService.getScriptProperties().getProperty('DOCUMENT_AI_SERVICE_ACCOUNT');
    // if (serviceAccountKey) {
    //   return getServiceAccountToken(serviceAccountKey);
    // }
    
    return token;
  } catch (error) {
    console.error("Failed to get access token: " + error.toString());
    return null;
  }
}

// ===========================================
// EXISTING SHIP MANAGEMENT FUNCTIONS
// ===========================================

function handleTestConnection(data) {
  try {
    return createJsonResponse(true, "Connection successful", {
      timestamp: new Date().toISOString(),
      version: "3.8-document-ai"
    });
  } catch (error) {
    return createJsonResponse(false, "Connection failed: " + error.toString());
  }
}

function handleCreateCompleteShipStructure(data) {
  try {
    var shipName = data.ship_name;
    var categories = data.categories || [
      "Class & Flag Cert",
      "Crew Records", 
      "ISM Records",
      "ISPS Records",
      "MLC Records",
      "Supplies"
    ];
    
    if (!shipName) {
      return createJsonResponse(false, "Ship name is required");
    }
    
    var rootFolder = DriveApp.getFoldersByName(shipName);
    var shipFolder;
    
    if (rootFolder.hasNext()) {
      shipFolder = rootFolder.next();
    } else {
      shipFolder = DriveApp.createFolder(shipName);
    }
    
    var createdFolders = [];
    
    categories.forEach(function(category) {
      var categoryFolders = shipFolder.getFoldersByName(category);
      if (!categoryFolders.hasNext()) {
        var newFolder = shipFolder.createFolder(category);
        createdFolders.push(category);
      }
    });
    
    return createJsonResponse(true, "Ship structure created successfully", {
      ship_folder_id: shipFolder.getId(),
      created_folders: createdFolders
    });
    
  } catch (error) {
    return createJsonResponse(false, "Failed to create ship structure: " + error.toString());
  }
}

function handleUploadFileWithFolderCreation(data) {
  try {
    var fileName = data.file_name;
    var fileContent = data.file_content;
    var folderPath = data.folder_path;
    var contentType = data.content_type || 'application/octet-stream';
    
    if (!fileName || !fileContent || !folderPath) {
      return createJsonResponse(false, "Missing required parameters: file_name, file_content, folder_path");
    }
    
    var folder = createNestedFolders(folderPath);
    var blob = Utilities.newBlob(Utilities.base64Decode(fileContent), contentType, fileName);
    var file = folder.createFile(blob);
    
    return createJsonResponse(true, "File uploaded successfully", {
      file_id: file.getId(),
      file_url: file.getUrl(),
      folder_path: folderPath
    });
    
  } catch (error) {
    return createJsonResponse(false, "File upload failed: " + error.toString());
  }
}

// Helper function to create nested folders
function createNestedFolders(folderPath) {
  var pathParts = folderPath.split('/');
  var currentFolder = DriveApp.getRootFolder();
  
  pathParts.forEach(function(folderName) {
    if (folderName.trim() === '') return;
    
    var existingFolders = currentFolder.getFoldersByName(folderName);
    if (existingFolders.hasNext()) {
      currentFolder = existingFolders.next();
    } else {
      currentFolder = currentFolder.createFolder(folderName);
    }
  });
  
  return currentFolder;
}

function createJsonResponse(success, message, data) {
  var response = {
    success: success,
    message: message,
    timestamp: new Date().toISOString()
  };
  
  if (data) {
    response.data = data;
  }
  
  return ContentService
    .createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}