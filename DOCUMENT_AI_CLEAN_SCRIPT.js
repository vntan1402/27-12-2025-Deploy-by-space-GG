// Google Apps Script for Document AI Integration
// Standalone Script - Version 1.0 Clean
// Purpose: Handle Document AI API calls for Ship Management System

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
          "analyze_document"
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
      default:
        return createJsonResponse(false, "Unknown action: " + action);
    }
    
  } catch (error) {
    console.error("Request handling error: " + error.toString());
    return createJsonResponse(false, "Error processing request: " + error.toString());
  }
}

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
    
    console.log("Testing Document AI connection for project: " + projectId);
    
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
    
    console.log("Making request to Document AI API");
    
    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();
    
    if (responseCode === 200) {
      var processorInfo = JSON.parse(responseText);
      return createJsonResponse(true, "Document AI connection successful", {
        processor_name: processorInfo.displayName || "Unknown",
        processor_type: processorInfo.type || "Unknown",
        processor_state: processorInfo.state || "Unknown",
        processor_id: processorId,
        project_id: projectId,
        location: location
      });
    } else {
      return createJsonResponse(false, "Document AI API error: " + responseText);
    }
    
  } catch (error) {
    console.error("Document AI test error: " + error.toString());
    return createJsonResponse(false, "Document AI test failed: " + error.toString());
  }
}

function handleAnalyzePassport(data) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;
    var fileContent = data.file_content;
    var filename = data.filename || "passport_document";
    var contentType = data.content_type || "application/pdf";
    
    if (!projectId || !processorId || !fileContent) {
      return createJsonResponse(false, "Missing required parameters");
    }
    
    console.log("Starting passport analysis for file: " + filename);
    
    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token");
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
    
    console.log("Sending document to Document AI for processing");
    
    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();
    
    if (responseCode === 200) {
      var result = JSON.parse(responseText);
      var extractedInfo = extractPassportInformation(result);
      
      console.log("Passport analysis completed successfully");
      
      return createJsonResponse(true, "Passport analysis completed successfully", {
        analysis: extractedInfo,
        processing_details: {
          filename: filename,
          content_type: contentType,
          processor_id: processorId
        }
      });
      
    } else {
      console.error("Document AI processing error: " + responseText);
      return createJsonResponse(false, "Document AI processing failed: " + responseText);
    }
    
  } catch (error) {
    console.error("Passport analysis error: " + error.toString());
    return createJsonResponse(false, "Passport analysis failed: " + error.toString());
  }
}

function handleAnalyzeDocument(data) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;
    var fileContent = data.file_content;
    var filename = data.filename || "document";
    var contentType = data.content_type || "application/pdf";
    
    if (!projectId || !processorId || !fileContent) {
      return createJsonResponse(false, "Missing required parameters");
    }
    
    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token");
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
        filename: filename,
        text_length: result.document && result.document.text ? result.document.text.length : 0
      });
    } else {
      return createJsonResponse(false, "Document analysis failed: " + response.getContentText());
    }
    
  } catch (error) {
    return createJsonResponse(false, "Document analysis failed: " + error.toString());
  }
}

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
    
    if (document.entities && document.entities.length > 0) {
      var confidenceScores = [];
      
      for (var i = 0; i < document.entities.length; i++) {
        var entity = document.entities[i];
        var entityType = (entity.type || "").toLowerCase();
        var entityText = entity.mentionText || "";
        if (entity.textAnchor && entity.textAnchor.content) {
          entityText = entityText || entity.textAnchor.content;
        }
        var confidence = entity.confidence || 0;
        
        if (confidence > 0) {
          confidenceScores.push(confidence);
        }
        
        switch (entityType) {
          case 'person_name':
          case 'name':
          case 'full_name':
            if (!extractedInfo.full_name) {
              extractedInfo.full_name = entityText.trim();
            }
            break;
          case 'sex':
          case 'gender':
            extractedInfo.sex = entityText.toUpperCase().charAt(0);
            break;
          case 'date_of_birth':
          case 'birth_date':
            extractedInfo.date_of_birth = formatDate(entityText);
            break;
          case 'place_of_birth':
            extractedInfo.place_of_birth = entityText.trim();
            break;
          case 'passport_number':
          case 'document_number':
            extractedInfo.passport_number = entityText.trim().replace(/\s+/g, '');
            break;
          case 'nationality':
            extractedInfo.nationality = entityText.trim();
            break;
          case 'issue_date':
            extractedInfo.issue_date = formatDate(entityText);
            break;
          case 'expiry_date':
            extractedInfo.expiry_date = formatDate(entityText);
            break;
        }
      }
      
      if (confidenceScores.length > 0) {
        var sum = 0;
        for (var j = 0; j < confidenceScores.length; j++) {
          sum += confidenceScores[j];
        }
        extractedInfo.confidence_score = sum / confidenceScores.length;
      }
    }
    
    if (document.text && (!extractedInfo.passport_number || !extractedInfo.full_name)) {
      var textInfo = extractFromTextPatterns(document.text);
      
      if (!extractedInfo.full_name && textInfo.full_name) {
        extractedInfo.full_name = textInfo.full_name;
      }
      if (!extractedInfo.passport_number && textInfo.passport_number) {
        extractedInfo.passport_number = textInfo.passport_number;
      }
    }
    
    if (extractedInfo.confidence_score === 0.0 && 
        (extractedInfo.full_name || extractedInfo.passport_number)) {
      extractedInfo.confidence_score = 0.7;
    }
    
    return extractedInfo;
    
  } catch (error) {
    console.error("Information extraction error: " + error.toString());
    return {
      error: "Information extraction failed: " + error.toString(),
      confidence_score: 0.0
    };
  }
}

function extractFromTextPatterns(text) {
  var info = {
    full_name: "",
    passport_number: ""
  };
  
  try {
    var passportPattern = /(?:Passport\s*(?:No|Number)[:.\s]*([A-Z0-9]{6,12}))/gi;
    var match = passportPattern.exec(text);
    if (match && match[1]) {
      info.passport_number = match[1].replace(/\s+/g, '');
    }
    
    var namePattern = /(?:Name[:.\s]*([A-Z][a-z]+(?: [A-Z][a-z]+)+))/gi;
    match = namePattern.exec(text);
    if (match && match[1]) {
      info.full_name = match[1].trim();
    }
    
    return info;
    
  } catch (error) {
    return info;
  }
}

function formatDate(dateString) {
  if (!dateString) return "";
  
  try {
    var cleanDate = dateString.replace(/[^\d\/\-\.]/g, "");
    var parts = cleanDate.split(/[\/\-\.]/);
    
    if (parts.length === 3) {
      var day = parts[0];
      var month = parts[1];
      var year = parts[2];
      
      if (day.length === 1) day = "0" + day;
      if (month.length === 1) month = "0" + month;
      
      if (year.length === 2) {
        var currentYear = new Date().getFullYear();
        var century = Math.floor(currentYear / 100) * 100;
        year = century + parseInt(year);
        
        if (year > currentYear + 10) {
          year -= 100;
        }
      }
      
      return year + "-" + month + "-" + day;
    }
    
    return dateString;
  } catch (error) {
    return dateString;
  }
}

function getDocumentAIAccessToken() {
  try {
    var token = ScriptApp.getOAuthToken();
    
    if (!token) {
      console.error("Failed to obtain OAuth token");
      return null;
    }
    
    return token;
    
  } catch (error) {
    console.error("Failed to get access token: " + error.toString());
    return null;
  }
}

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