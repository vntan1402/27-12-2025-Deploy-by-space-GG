// Google Apps Script for Document AI Integration
// Standalone Script - Version 1.0
// Purpose: Handle Document AI API calls for Ship Management System
// Separate from Google Drive Management Script

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
      return createJsonResponse(true, "Document AI Service v1.0 is WORKING!", {
        version: "1.0-document-ai-standalone",
        timestamp: new Date().toISOString(),
        service: "Google Document AI Integration",
        supported_actions: [
          "test_connection",
          "test_document_ai",
          "analyze_passport",
          "analyze_document",
          "get_processor_info"
        ]
      });
    }
    
    var action = requestData.action || "default";
    
    switch (action) {
      case 'test_connection':
        return handleTestConnection(requestData);
        
      case 'test_document_ai':
      case 'test_document_ai_connection':
        return handleTestDocumentAI(requestData);
        
      case 'analyze_passport':
      case 'analyze_passport_document_ai':
        return handleAnalyzePassport(requestData);
        
      case 'analyze_document':
        return handleAnalyzeDocument(requestData);
        
      case 'get_processor_info':
        return handleGetProcessorInfo(requestData);
        
      default:
        return createJsonResponse(false, "Unknown action: " + action + ". Supported actions: test_connection, test_document_ai, analyze_passport, analyze_document, get_processor_info");
    }
    
  } catch (error) {
    console.error("Request handling error: " + error.toString());
    return createJsonResponse(false, "Error processing request: " + error.toString());
  }
}

// ===========================================
// DOCUMENT AI CORE FUNCTIONS
// ===========================================

/**
 * Test basic connectivity
 */
function handleTestConnection(data) {
  try {
    return createJsonResponse(true, "Document AI Service is running successfully", {
      timestamp: new Date().toISOString(),
      version: "1.0-standalone",
      uptime_check: "OK"
    });
  } catch (error) {
    return createJsonResponse(false, "Connection test failed: " + error.toString());
  }
}

/**
 * Test Document AI API connectivity and processor access
 */
function handleTestDocumentAI(data) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;
    
    if (!projectId) {
      return createJsonResponse(false, "Missing required parameter: project_id");
    }
    
    if (!processorId) {
      return createJsonResponse(false, "Missing required parameter: processor_id");
    }
    
    console.log("Testing Document AI connection for project: " + projectId + ", processor: " + processorId);
    
    // Get OAuth access token
    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token. Please check OAuth scopes and permissions.");
    }
    
    // Test processor access
    var processorName = "projects/" + projectId + "/locations/" + location + "/processors/" + processorId;
    var url = "https://documentai.googleapis.com/v1/" + processorName;
    
    var options = {
      'method': 'GET',
      'headers': {
        'Authorization': 'Bearer ' + accessToken,
        'Content-Type': 'application/json'
      }
    };
    
    console.log("Making request to Document AI API: " + url);
    
    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();
    
    console.log("Document AI API Response Code: " + responseCode);
    
    if (responseCode === 200) {
      var processorInfo = JSON.parse(responseText);
      return createJsonResponse(true, "Document AI connection successful", {
        processor_name: processorInfo.displayName || processorInfo.name || "Unknown",
        processor_type: processorInfo.type || "Unknown", 
        processor_state: processorInfo.state || "Unknown",
        processor_id: processorId,
        project_id: projectId,
        location: location
      });
    } else {
      console.error("Document AI API Error: " + responseText);
      return createJsonResponse(false, "Document AI API returned error code " + responseCode + ": " + responseText);
    }
    
  } catch (error) {
    console.error("Document AI test error: " + error.toString());
    return createJsonResponse(false, "Document AI test failed: " + error.toString());
  }
}

/**
 * Analyze passport document
 */
function handleAnalyzePassport(data) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;
    var fileContent = data.file_content; // Base64 encoded
    var filename = data.filename || "passport_document";
    var contentType = data.content_type || "application/pdf";
    
    // Validate required parameters
    if (!projectId || !processorId || !fileContent) {
      return createJsonResponse(false, "Missing required parameters. Need: project_id, processor_id, file_content");
    }
    
    console.log("Starting passport analysis for file: " + filename);
    
    // Get OAuth access token
    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token for Document AI");
    }
    
    // Prepare Document AI process request
    var processorName = "projects/" + projectId + "/locations/" + location + "/processors/" + processorId;
    var url = "https://documentai.googleapis.com/v1/" + processorName + ":process";
    
    var requestBody = {
      "rawDocument": {
        "content": fileContent,
        "mimeType": contentType
      }
    };
    
    var options = {
      'method': 'POST',
      'headers': {
        'Authorization': 'Bearer ' + accessToken,
        'Content-Type': 'application/json'
      },
      'payload': JSON.stringify(requestBody)
    };
    
    console.log("Sending document to Document AI for processing...");
    
    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();
    
    console.log("Document AI Processing Response Code: " + responseCode);
    
    if (responseCode === 200) {
      var result = JSON.parse(responseText);
      
      // Extract passport information from Document AI result
      var extractedInfo = extractPassportInformation(result);
      
      console.log("Passport analysis completed successfully");
      
      return createJsonResponse(true, "Passport analysis completed successfully", {
        analysis: extractedInfo,
        processing_details: {
          filename: filename,
          content_type: contentType,
          processor_id: processorId,
          text_length: result.document && result.document.text ? result.document.text.length : 0,
          entities_found: result.document && result.document.entities ? result.document.entities.length : 0
        }
      });
      
    } else {
      console.error("Document AI processing error: " + responseText);
      return createJsonResponse(false, "Document AI processing failed with code " + responseCode + ": " + responseText);
    }
    
  } catch (error) {
    console.error("Passport analysis error: " + error.toString());
    return createJsonResponse(false, "Passport analysis failed: " + error.toString());
  }
}

/**
 * General document analysis (can be used for other document types)
 */
function handleAnalyzeDocument(data) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;
    var fileContent = data.file_content;
    var filename = data.filename || "document";
    var contentType = data.content_type || "application/pdf";
    var documentType = data.document_type || "general";
    
    if (!projectId || !processorId || !fileContent) {
      return createJsonResponse(false, "Missing required parameters. Need: project_id, processor_id, file_content");
    }
    
    console.log("Starting document analysis for: " + filename + " (type: " + documentType + ")");
    
    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token for Document AI");
    }
    
    var processorName = "projects/" + projectId + "/locations/" + location + "/processors/" + processorId;
    var url = "https://documentai.googleapis.com/v1/" + processorName + ":process";
    
    var requestBody = {
      "rawDocument": {
        "content": fileContent,
        "mimeType": contentType
      }
    };
    
    var options = {
      'method': 'POST',
      'headers': {
        'Authorization': 'Bearer ' + accessToken,
        'Content-Type': 'application/json'
      },
      'payload': JSON.stringify(requestBody)
    };
    
    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    
    if (responseCode === 200) {
      var result = JSON.parse(response.getContentText());
      
      return createJsonResponse(true, "Document analysis completed", {
        document_type: documentType,
        filename: filename,
        text_content: result.document && result.document.text ? result.document.text.substring(0, 1000) + "..." : "",
        entities_count: result.document && result.document.entities ? result.document.entities.length : 0,
        pages_count: result.document && result.document.pages ? result.document.pages.length : 0
      });
    } else {
      return createJsonResponse(false, "Document analysis failed: " + response.getContentText());
    }
    
  } catch (error) {
    console.error("Document analysis error: " + error.toString());
    return createJsonResponse(false, "Document analysis failed: " + error.toString());
  }
}

/**
 * Get processor information
 */
function handleGetProcessorInfo(data) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;
    
    if (!projectId || !processorId) {
      return createJsonResponse(false, "Missing required parameters: project_id, processor_id");
    }
    
    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token");
    }
    
    var processorName = "projects/" + projectId + "/locations/" + location + "/processors/" + processorId;
    var url = "https://documentai.googleapis.com/v1/" + processorName;
    
    var options = {
      'method': 'GET',
      'headers': {
        'Authorization': 'Bearer ' + accessToken,
        'Content-Type': 'application/json'
      }
    };
    
    var response = UrlFetchApp.fetch(url, options);
    
    if (response.getResponseCode() === 200) {
      var processorInfo = JSON.parse(response.getContentText());
      return createJsonResponse(true, "Processor information retrieved", processorInfo);
    } else {
      return createJsonResponse(false, "Failed to get processor info: " + response.getContentText());
    }
    
  } catch (error) {
    return createJsonResponse(false, "Get processor info failed: " + error.toString());
  }
}

// ===========================================
// INFORMATION EXTRACTION FUNCTIONS
// ===========================================

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
      confidence_score: 0.0,
      processing_method: "document_ai_entities"
    };
    
    if (!document) {
      return extractedInfo;
    }
    
    // Extract from entities if available
    if (document.entities && document.entities.length > 0) {
      var confidenceScores = [];
      
      document.entities.forEach(function(entity) {
        var entityType = (entity.type || "").toLowerCase();
        var entityText = entity.mentionText || entity.textAnchor && entity.textAnchor.content || "";
        var confidence = entity.confidence || 0;
        
        if (confidence > 0) {
          confidenceScores.push(confidence);
        }
        
        // Map entity types to passport fields
        switch (entityType) {
          case 'person_name':
          case 'name':
          case 'full_name':
          case 'given_names':
          case 'surname':
            if (!extractedInfo.full_name) {
              extractedInfo.full_name = entityText.trim();
            }
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
          case 'place_birth':
            extractedInfo.place_of_birth = entityText.trim();
            break;
          case 'passport_number':
          case 'document_number':
          case 'passport_id':
          case 'document_id':
            extractedInfo.passport_number = entityText.trim().replace(/\s+/g, '');
            break;
          case 'nationality':
          case 'country':
          case 'issuing_country':
            extractedInfo.nationality = entityText.trim();
            break;
          case 'issue_date':
          case 'date_of_issue':
          case 'issued_date':
            extractedInfo.issue_date = formatDate(entityText);
            break;
          case 'expiry_date':
          case 'expiration_date':
          case 'date_of_expiry':
          case 'expires':
            extractedInfo.expiry_date = formatDate(entityText);
            break;
        }
      });
      
      // Calculate average confidence
      if (confidenceScores.length > 0) {
        extractedInfo.confidence_score = confidenceScores.reduce(function(a, b) { return a + b; }) / confidenceScores.length;
      }
    }
    
    // Fallback: extract from text using patterns if entities didn't provide enough info
    if (document.text && (!extractedInfo.passport_number || !extractedInfo.full_name)) {
      console.log("Using text pattern extraction as fallback");
      var textInfo = extractFromTextPatterns(document.text);
      
      if (!extractedInfo.full_name && textInfo.full_name) {
        extractedInfo.full_name = textInfo.full_name;
        extractedInfo.processing_method = "text_patterns";
      }
      if (!extractedInfo.passport_number && textInfo.passport_number) {
        extractedInfo.passport_number = textInfo.passport_number;
        extractedInfo.processing_method = "text_patterns";
      }
      if (!extractedInfo.date_of_birth && textInfo.date_of_birth) {
        extractedInfo.date_of_birth = textInfo.date_of_birth;
      }
    }
    
    // Set minimum confidence if we extracted some information
    if (extractedInfo.confidence_score === 0.0 && 
        (extractedInfo.full_name || extractedInfo.passport_number)) {
      extractedInfo.confidence_score = 0.7; // Reasonable confidence for pattern matching
    }
    
    console.log("Extraction completed - Full Name: " + extractedInfo.full_name + 
                ", Passport: " + extractedInfo.passport_number + 
                ", Confidence: " + extractedInfo.confidence_score);
    
    return extractedInfo;
    
  } catch (error) {
    console.error("Information extraction error: " + error.toString());
    return {
      error: "Information extraction failed: " + error.toString(),
      confidence_score: 0.0,
      processing_method: "error"
    };
  }
}

/**
 * Extract passport information from text using patterns (fallback method)
 */
function extractFromTextPatterns(text) {
  var info = {
    full_name: "",
    passport_number: "",
    date_of_birth: ""
  };
  
  try {
    // Passport number patterns
    var passportPatterns = [
      /(?:Passport\s*(?:No|Number|#)[:.\s]*([A-Z0-9]{6,12}))/gi,
      /(?:Document\s*(?:No|Number|#)[:.\s]*([A-Z0-9]{6,12}))/gi,
      /\b([A-Z]{1,2}[0-9]{6,10})\b/g,
      /(?:No\.?\s*([A-Z0-9]{8,12}))/gi
    ];
    
    for (var i = 0; i < passportPatterns.length; i++) {
      var matches = text.match(passportPatterns[i]);
      if (matches && matches.length > 0) {
        // Extract the captured group
        var match = passportPatterns[i].exec(text);
        if (match && match[1]) {
          info.passport_number = match[1].replace(/\s+/g, '');
          break;
        }
      }
    }
    
    // Name extraction (look for patterns like "Given names:", "Surname:", etc.)
    var namePatterns = [
      /(?:Given\s*names?[:.\s]*([A-Z][a-z]+(?: [A-Z][a-z]+)*))/gi,
      /(?:Surname[:.\s]*([A-Z][a-z]+))/gi,
      /(?:Name[:.\s]*([A-Z][a-z]+(?: [A-Z][a-z]+)+))/gi
    ];
    
    var nameParts = [];
    namePatterns.forEach(function(pattern) {
      var match = pattern.exec(text);
      if (match && match[1]) {
        nameParts.push(match[1].trim());
      }
    });
    
    if (nameParts.length > 0) {
      info.full_name = nameParts.join(' ');
    }
    
    // Date patterns
    var datePatterns = [
      /(?:Date\s*of\s*birth[:.\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4}))/gi,
      /(?:DOB[:.\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4}))/gi,
      /\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})\b/g
    ];
    
    for (var j = 0; j < datePatterns.length; j++) {
      var match = datePatterns[j].exec(text);
      if (match && match[1]) {
        info.date_of_birth = formatDate(match[1]);
        break;
      }
    }
    
    return info;
    
  } catch (error) {
    console.error("Text pattern extraction error: " + error.toString());
    return info;
  }
}

/**
 * Format date to YYYY-MM-DD format
 */
function formatDate(dateString) {
  if (!dateString) return "";
  
  try {
    // Clean the date string
    var cleanDate = dateString.replace(/[^\d\/\-\.]/g, "");
    var parts = cleanDate.split(/[\/\-\.]/);
    
    if (parts.length === 3) {
      var day = parts[0].padStart(2, '0');
      var month = parts[1].padStart(2, '0');
      var year = parts[2];
      
      // Handle 2-digit years
      if (year.length === 2) {
        var currentYear = new Date().getFullYear();
        var currentCentury = Math.floor(currentYear / 100) * 100;
        year = currentCentury + parseInt(year);
        
        // If the year is more than 10 years in the future, assume previous century
        if (year > currentYear + 10) {
          year -= 100;
        }
      }
      
      // Return in YYYY-MM-DD format
      return year + "-" + month + "-" + day;
    }
    
    return dateString;
  } catch (error) {
    console.error("Date formatting error: " + error.toString());
    return dateString;
  }
}

// ===========================================
// UTILITY FUNCTIONS
// ===========================================

/**
 * Get OAuth access token for Document AI API
 */
function getDocumentAIAccessToken() {
  try {
    // Get OAuth token with Document AI scope
    var token = ScriptApp.getOAuthToken();
    
    if (!token) {
      console.error("Failed to obtain OAuth token - check scopes configuration");
      return null;
    }
    
    console.log("OAuth token obtained successfully");
    return token;
    
  } catch (error) {
    console.error("Failed to get access token: " + error.toString());
    return null;
  }
}

/**
 * Create standardized JSON response
 */
function createJsonResponse(success, message, data) {
  var response = {
    success: success,
    message: message,
    timestamp: new Date().toISOString(),
    service: "Document AI Standalone v1.0"
  };
  
  if (data) {
    if (success) {
      response.data = data;
    } else {
      response.error_details = data;
    }
  }
  
  return ContentService
    .createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}