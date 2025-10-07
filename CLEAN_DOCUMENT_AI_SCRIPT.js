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
        return createJsonResponse(false, "Unknown action: " + action);
    }
    
  } catch (error) {
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
    
    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token. Please check OAuth scopes and permissions.");
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
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();
    
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
      return createJsonResponse(false, "Document AI API returned error code " + responseCode + ": " + responseText);
    }
    
  } catch (error) {
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
      return createJsonResponse(false, "Missing required parameters. Need: project_id, processor_id, file_content");
    }
    
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
    var responseText = response.getContentText();
    
    if (responseCode === 200) {
      var result = JSON.parse(responseText);
      var extractedInfo = extractPassportInformation(result);
      
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
      return createJsonResponse(false, "Document AI processing failed with code " + responseCode + ": " + responseText);
    }
    
  } catch (error) {
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
    var documentType = data.document_type || "general";
    
    if (!projectId || !processorId || !fileContent) {
      return createJsonResponse(false, "Missing required parameters. Need: project_id, processor_id, file_content");
    }
    
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
    return createJsonResponse(false, "Document analysis failed: " + error.toString());
  }
}

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
        var confidence = entity.confidence || 0;
        
        if (confidence > 0) {
          confidenceScores.push(confidence);
        }
        
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
            extractedInfo.sex = entityText.toUpperCase().charAt(0);
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
    
    if (extractedInfo.confidence_score === 0.0 && 
        (extractedInfo.full_name || extractedInfo.passport_number)) {
      extractedInfo.confidence_score = 0.7;
    }
    
    return extractedInfo;
    
  } catch (error) {
    return {
      error: "Information extraction failed: " + error.toString(),
      confidence_score: 0.0,
      processing_method: "error"
    };
  }
}

function extractFromTextPatterns(text) {
  var info = {
    full_name: "",
    passport_number: "",
    date_of_birth: ""
  };
  
  try {
    var passportPatterns = [
      /Passport\s*(?:No|Number|#)\s*:?\s*([A-Z0-9]{6,12})/gi,
      /Document\s*(?:No|Number|#)\s*:?\s*([A-Z0-9]{6,12})/gi,
      /\b([A-Z]{1,2}[0-9]{6,10})\b/g
    ];
    
    for (var i = 0; i < passportPatterns.length; i++) {
      var match = passportPatterns[i].exec(text);
      if (match && match[1]) {
        info.passport_number = match[1].replace(/\s+/g, '');
        break;
      }
    }
    
    var datePatterns = [
      /Date\s*of\s*birth\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})/gi,
      /DOB\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})/gi,
      /\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})\b/g
    ];
    
    for (var j = 0; j < datePatterns.length; j++) {
      var dateMatch = datePatterns[j].exec(text);
      if (dateMatch && dateMatch[1]) {
        info.date_of_birth = formatDate(dateMatch[1]);
        break;
      }
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
        var currentCentury = Math.floor(currentYear / 100) * 100;
        year = currentCentury + parseInt(year);
        
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
      return null;
    }
    
    return token;
    
  } catch (error) {
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