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
        version: "1.1-cache-busted",
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
    
    // Generate unique identifiers for cache busting
    var timestamp = new Date().getTime();
    var uniqueId = Math.random().toString(36).substring(2, 15);
    var cacheKey = timestamp + "_" + uniqueId + "_" + filename.replace(/[^a-zA-Z0-9]/g, '');
    
    console.log("🔄 CACHE BUSTING - Starting fresh passport analysis");
    console.log("   📄 File: " + filename);
    console.log("   🔑 Cache Key: " + cacheKey);
    console.log("   ⏰ Timestamp: " + timestamp);
    
    var token = getAccessToken();
    if (!token) {
      return createResponse(false, "Cannot get access token");
    }
    
    var url = "https://documentai.googleapis.com/v1/projects/" + projectId + "/locations/" + location + "/processors/" + processorId + ":process";
    
    // Add cache busting to the request body - modify content to make it unique
    var requestBody = {
      rawDocument: {
        content: fileContent,
        mimeType: contentType
      },
      // Add unique processing metadata to prevent caching
      processOptions: {
        individualPageSelector: {
          pages: [1]  // Process first page to ensure unique request
        }
      },
      // Add unique field extraction hint with timestamp
      fieldMask: {
        paths: ["text", "entities", "pages"]
      },
      // Custom labels for cache busting
      labels: {
        "processing_id": cacheKey,
        "timestamp": timestamp.toString(),
        "filename": filename,
        "cache_version": "v1.1"
      }
    };
    
    var options = {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        // Add unique headers for cache busting
        "X-Processing-ID": cacheKey,
        "X-Timestamp": timestamp.toString(),
        "X-Cache-Bust": "true"
      },
      payload: JSON.stringify(requestBody)
    };
    
    console.log("📡 Sending unique request to Document AI API with cache busting");
    
    var response = UrlFetchApp.fetch(url, options);
    var code = response.getResponseCode();
    
    if (code === 200) {
      var result = JSON.parse(response.getContentText());
      var extractedInfo = extractPassportInfo(result);
      
      // Add cache busting info to response
      extractedInfo.cache_info = {
        cache_key: cacheKey,
        timestamp: timestamp,
        processing_method: "cache_busted_v1.1"
      };
      
      console.log("✅ Fresh analysis completed with cache busting");
      console.log("   👤 Extracted Name: " + extractedInfo.full_name);
      console.log("   📔 Extracted Passport: " + extractedInfo.passport_number);
      
      return createResponse(true, "Analysis completed", {
        analysis: extractedInfo,
        filename: filename,
        cache_info: {
          cache_key: cacheKey,
          timestamp: timestamp,
          fresh_analysis: true
        }
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
    
    // If no entities found, try text extraction as fallback
    if (result.document && result.document.text && (!info.full_name || !info.passport_number)) {
      console.log("🔍 Using text extraction fallback for missing data");
      var textInfo = extractFromText(result.document.text);
      
      if (!info.full_name && textInfo.full_name) {
        info.full_name = textInfo.full_name;
      }
      if (!info.passport_number && textInfo.passport_number) {
        info.passport_number = textInfo.passport_number;
      }
    }
    
    return info;
    
  } catch (error) {
    info.error = "Extraction failed";
    return info;
  }
}

function extractFromText(text) {
  var info = {
    full_name: "",
    passport_number: ""
  };
  
  try {
    // Look for name patterns (Vietnamese names)
    var namePatterns = [
      /(?:họ và tên|tên|name)[:.\s]*([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*)*)/gi,
      /([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*)/g
    ];
    
    for (var i = 0; i < namePatterns.length; i++) {
      var match = namePatterns[i].exec(text);
      if (match && match[1] && match[1].length > 5) {
        info.full_name = match[1].trim();
        break;
      }
    }
    
    // Look for passport number patterns
    var passportPatterns = [
      /(?:passport\s*(?:no|number|#)|số\s*hộ\s*chiếu)[:.\s]*([A-Z]\d{7,8}|[A-Z]{1,2}\d{6,8})/gi,
      /\b([A-Z]\d{7,8}|[A-Z]{1,2}\d{6,8})\b/g
    ];
    
    for (var j = 0; j < passportPatterns.length; j++) {
      var match = passportPatterns[j].exec(text);
      if (match && match[1]) {
        info.passport_number = match[1].trim();
        break;
      }
    }
    
    return info;
    
  } catch (error) {
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