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
        return createResponse(false, "Invalid JSON");
      }
    } else if (e && e.parameter) {
      requestData = e.parameter;
    } else {
      return createResponse(true, "Document AI Service is working", {
        version: "1.0",
        service: "Document AI Integration"
      });
    }
    
    var action = requestData.action;
    if (!action) {
      action = "default";
    }
    
    if (action === "test_connection") {
      return handleTestConnection();
    } else if (action === "test_document_ai" || action === "test_document_ai_connection") {
      return handleTestDocumentAI(requestData);
    } else if (action === "analyze_passport" || action === "analyze_passport_document_ai") {
      return handleAnalyzePassport(requestData);
    } else {
      return createResponse(false, "Unknown action: " + action);
    }
    
  } catch (error) {
    return createResponse(false, "Request error: " + error.toString());
  }
}

function handleTestConnection() {
  try {
    return createResponse(true, "Service is running", {
      timestamp: new Date().toISOString(),
      status: "OK"
    });
  } catch (error) {
    return createResponse(false, "Test failed");
  }
}

function handleTestDocumentAI(data) {
  try {
    var projectId = data.project_id;
    var processorId = data.processor_id;
    var location = data.location;
    
    if (!location) {
      location = "us";
    }
    
    if (!projectId) {
      return createResponse(false, "Missing project_id");
    }
    
    if (!processorId) {
      return createResponse(false, "Missing processor_id");
    }
    
    var token = getAccessToken();
    if (!token) {
      return createResponse(false, "Cannot get access token");
    }
    
    var url = "https://documentai.googleapis.com/v1/projects/" + projectId + "/locations/" + location + "/processors/" + processorId;
    
    var options = {
      method: "GET",
      headers: {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
      }
    };
    
    var response = UrlFetchApp.fetch(url, options);
    var code = response.getResponseCode();
    
    if (code === 200) {
      var result = JSON.parse(response.getContentText());
      return createResponse(true, "Connection successful", {
        processor_name: result.displayName || "Unknown",
        processor_type: result.type || "Unknown",
        project_id: projectId,
        processor_id: processorId
      });
    } else {
      return createResponse(false, "API error: " + code);
    }
    
  } catch (error) {
    return createResponse(false, "Test error: " + error.toString());
  }
}

function handleAnalyzePassport(data) {
  try {
    var projectId = data.project_id;
    var processorId = data.processor_id;
    var fileContent = data.file_content;
    var filename = data.filename;
    var contentType = data.content_type;
    var location = data.location;
    
    if (!location) {
      location = "us";
    }
    
    if (!filename) {
      filename = "passport";
    }
    
    if (!contentType) {
      contentType = "application/pdf";
    }
    
    if (!projectId || !processorId || !fileContent) {
      return createResponse(false, "Missing required parameters");
    }
    
    var token = getAccessToken();
    if (!token) {
      return createResponse(false, "Cannot get access token");
    }
    
    var url = "https://documentai.googleapis.com/v1/projects/" + projectId + "/locations/" + location + "/processors/" + processorId + ":process";
    
    var requestBody = {
      rawDocument: {
        content: fileContent,
        mimeType: contentType
      }
    };
    
    var options = {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
      },
      payload: JSON.stringify(requestBody)
    };
    
    var response = UrlFetchApp.fetch(url, options);
    var code = response.getResponseCode();
    
    if (code === 200) {
      var result = JSON.parse(response.getContentText());
      var extractedInfo = extractPassportInfo(result);
      
      return createResponse(true, "Analysis completed", {
        analysis: extractedInfo,
        filename: filename
      });
      
    } else {
      return createResponse(false, "Processing failed: " + code);
    }
    
  } catch (error) {
    return createResponse(false, "Analysis error: " + error.toString());
  }
}

function extractPassportInfo(result) {
  var info = {
    full_name: "",
    sex: "",
    date_of_birth: "",
    place_of_birth: "",
    passport_number: "",
    nationality: "",
    confidence_score: 0.7
  };
  
  try {
    if (result.document && result.document.entities) {
      var entities = result.document.entities;
      
      for (var i = 0; i < entities.length; i++) {
        var entity = entities[i];
        var type = entity.type;
        var text = entity.mentionText;
        
        if (!type || !text) {
          continue;
        }
        
        type = type.toLowerCase();
        
        if (type === "person_name" || type === "name") {
          if (!info.full_name) {
            info.full_name = text.trim();
          }
        } else if (type === "sex" || type === "gender") {
          info.sex = text.toUpperCase().charAt(0);
        } else if (type === "date_of_birth") {
          info.date_of_birth = formatDate(text);
        } else if (type === "place_of_birth") {
          info.place_of_birth = text.trim();
        } else if (type === "passport_number" || type === "document_number") {
          info.passport_number = text.trim().replace(/\s/g, "");
        } else if (type === "nationality") {
          info.nationality = text.trim();
        }
      }
    }
    
    return info;
    
  } catch (error) {
    info.error = "Extraction failed";
    return info;
  }
}

function formatDate(dateStr) {
  if (!dateStr) {
    return "";
  }
  
  try {
    var clean = dateStr.replace(/[^\d\/\-\.]/g, "");
    var parts = clean.split(/[\/\-\.]/);
    
    if (parts.length === 3) {
      var day = parts[0];
      var month = parts[1];
      var year = parts[2];
      
      if (day.length === 1) {
        day = "0" + day;
      }
      if (month.length === 1) {
        month = "0" + month;
      }
      
      return year + "-" + month + "-" + day;
    }
    
    return dateStr;
  } catch (error) {
    return dateStr;
  }
}

function getAccessToken() {
  try {
    return ScriptApp.getOAuthToken();
  } catch (error) {
    return null;
  }
}

function createResponse(success, message, data) {
  var response = {
    success: success,
    message: message,
    timestamp: new Date().toISOString()
  };
  
  if (data) {
    if (success) {
      response.data = data;
    } else {
      response.error = data;
    }
  }
  
  return ContentService
    .createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}