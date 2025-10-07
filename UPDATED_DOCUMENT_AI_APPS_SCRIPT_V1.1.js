/**
 * Google Apps Script for Document AI Integration
 * Version 1.1 - Complete with Passport Analysis and Cache Busting
 * Purpose: Handle Document AI API calls for Ship Management System
 */

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
      return createJsonResponse(true, "Document AI Service v1.1 is WORKING!", {
        version: "1.1-complete-with-passport",
        timestamp: new Date().toISOString(),
        service: "Google Document AI Integration",
        supported_actions: [
          "test_connection",
          "test_document_ai",
          "analyze_passport",
          "analyze_passport_document_ai",
          "analyze_document"
        ]
      });
    }

    var action = requestData.action || "default";

    switch (action) {
      case "test_connection":
        return handleTestConnection(requestData);
      case "test_document_ai":
        return handleTestDocumentAI(requestData);
      case "analyze_passport":
      case "analyze_passport_document_ai":  // Handle backend call
        return handleAnalyzePassport(requestData);
      case "analyze_document":
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
  return createJsonResponse(true, "Document AI Service is running successfully", {
    timestamp: new Date().toISOString(),
    version: "1.1-complete",
    uptime_check: "OK"
  });
}

function handleTestDocumentAI(data) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;

    if (!projectId || !processorId) {
      return createJsonResponse(false, "Missing required parameters: project_id or processor_id");
    }

    var accessToken = getDocumentAIAccessToken();
    var processorName = "projects/" + projectId + "/locations/" + location + "/processors/" + processorId;
    var url = "https://documentai.googleapis.com/v1/" + processorName;

    var options = {
      method: "GET",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json"
      },
      muteHttpExceptions: true
    };

    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();

    if (responseCode === 200) {
      var info = JSON.parse(responseText);
      return createJsonResponse(true, "Document AI connection successful", info);
    } else {
      return createJsonResponse(false, "Document AI error: " + responseText);
    }

  } catch (error) {
    return createJsonResponse(false, "Test failed: " + error.toString());
  }
}

// NEW: Handle passport analysis with cache busting
function handleAnalyzePassport(data) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;
    var fileContent = data.file_content;
    var filename = data.filename || "passport_document";
    var contentType = data.content_type || "application/pdf";
    
    // Cache busting parameters from backend
    var cacheKey = data.cache_key;
    var timestamp = data.timestamp;
    var uniqueId = data.unique_id;
    
    if (!projectId || !processorId || !fileContent) {
      return createJsonResponse(false, "Missing required parameters: project_id, processor_id, or file_content");
    }

    console.log("🔄 PASSPORT ANALYSIS - Cache Busting Active");
    console.log("   📄 File: " + filename);
    console.log("   🔑 Cache Key: " + cacheKey);
    console.log("   ⏰ Timestamp: " + timestamp);

    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token");
    }

    var processorName = "projects/" + projectId + "/locations/" + location + "/processors/" + processorId + ":process";
    
    // Create unique request payload with cache busting
    var requestPayload = {
      rawDocument: {
        content: fileContent,
        mimeType: contentType
      }
    };
    
    // Add cache busting metadata to prevent cached responses
    if (cacheKey) {
      requestPayload.labels = {
        "cache_key": cacheKey,
        "timestamp": timestamp.toString(),
        "filename": filename,
        "processing_version": "v1.1"
      };
    }

    var options = {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
        // Cache busting headers
        "X-Processing-ID": cacheKey || "default",
        "X-Timestamp": timestamp ? timestamp.toString() : new Date().getTime().toString(),
        "X-Cache-Version": "v1.1"
      },
      payload: JSON.stringify(requestPayload),
      muteHttpExceptions: true
    };

    console.log("📡 Sending request to Document AI API with cache busting");
    
    var response = UrlFetchApp.fetch("https://documentai.googleapis.com/v1/" + processorName, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();

    if (responseCode === 200) {
      var result = JSON.parse(responseText);
      
      // Extract passport-specific information
      var extractedInfo = extractPassportInformation(result);
      
      console.log("✅ Passport analysis completed successfully");
      console.log("   👤 Extracted Name: " + extractedInfo.full_name);
      console.log("   📔 Extracted Passport: " + extractedInfo.passport_number);
      
      return createJsonResponse(true, "Passport analysis completed successfully", {
        analysis: extractedInfo,
        processing_details: {
          filename: filename,
          content_type: contentType,
          processor_id: processorId,
          cache_info: {
            cache_key: cacheKey,
            timestamp: timestamp,
            fresh_analysis: true
          }
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

function handleAnalyzeDocument(data) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;
    var fileContent = data.file_content;
    var contentType = data.content_type || "application/pdf";

    if (!projectId || !processorId || !fileContent) {
      return createJsonResponse(false, "Missing required parameters");
    }

    var accessToken = getDocumentAIAccessToken();
    var processorName = "projects/" + projectId + "/locations/" + location + "/processors/" + processorId + ":process";

    var payload = JSON.stringify({
      rawDocument: {
        content: fileContent,
        mimeType: contentType
      }
    });

    var options = {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json"
      },
      payload: payload,
      muteHttpExceptions: true
    };

    var response = UrlFetchApp.fetch("https://documentai.googleapis.com/v1/" + processorName, options);
    var text = response.getContentText();
    var code = response.getResponseCode();

    if (code === 200) {
      var result = JSON.parse(text);
      return createJsonResponse(true, "Document processed successfully", result);
    } else {
      return createJsonResponse(false, "Document AI error: " + text);
    }

  } catch (error) {
    return createJsonResponse(false, "Analyze document failed: " + error.toString());
  }
}

// NEW: Extract passport-specific information from Document AI result
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
      }

      // Calculate average confidence
      if (confidenceScores.length > 0) {
        var sum = 0;
        for (var j = 0; j < confidenceScores.length; j++) {
          sum += confidenceScores[j];
        }
        extractedInfo.confidence_score = sum / confidenceScores.length;
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

// Extract passport information from text using patterns (fallback method)
function extractFromTextPatterns(text) {
  var info = {
    full_name: "",
    passport_number: "",
    date_of_birth: ""
  };

  try {
    // Vietnamese name patterns
    var namePatterns = [
      /(?:họ và tên|tên|name)[:.\s]*([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*)*)/gi,
      /([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*)/g
    ];

    for (var i = 0; i < namePatterns.length; i++) {
      var matches = text.match(namePatterns[i]);
      if (matches && matches.length > 0) {
        var match = namePatterns[i].exec(text);
        if (match && match[1] && match[1].length > 5) {
          info.full_name = match[1].trim();
          break;
        }
      }
    }

    // Passport number patterns
    var passportPatterns = [
      /(?:Passport\s*(?:No|Number|#)|Số\s*hộ\s*chiếu)[:.\s]*([A-Z]\d{7,8}|[A-Z]{1,2}\d{6,8})/gi,
      /\b([A-Z]\d{7,8}|[A-Z]{1,2}\d{6,8})\b/g
    ];

    for (var j = 0; j < passportPatterns.length; j++) {
      var match = passportPatterns[j].exec(text);
      if (match && match[1]) {
        info.passport_number = match[1].replace(/\s+/g, '');
        break;
      }
    }

    // Date patterns
    var datePatterns = [
      /(?:Date\s*of\s*birth|Ngày\s*sinh)[:.\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})/gi,
      /\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})\b/g
    ];

    for (var k = 0; k < datePatterns.length; k++) {
      var match = datePatterns[k].exec(text);
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

// Format date to YYYY-MM-DD format
function formatDate(dateString) {
  if (!dateString) return "";

  try {
    // Clean the date string
    var cleanDate = dateString.replace(/[^\d\/\-\.]/g, "");
    var parts = cleanDate.split(/[\/\-\.]/);

    if (parts.length === 3) {
      var day = parts[0].padStart ? parts[0].padStart(2, '0') : (parts[0].length === 1 ? '0' + parts[0] : parts[0]);
      var month = parts[1].padStart ? parts[1].padStart(2, '0') : (parts[1].length === 1 ? '0' + parts[1] : parts[1]);
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

      // Return in DD/MM/YYYY format (Vietnamese standard)
      return day + "/" + month + "/" + year;
    }

    return dateString;
  } catch (error) {
    console.error("Date formatting error: " + error.toString());
    return dateString;
  }
}

function getDocumentAIAccessToken() {
  try {
    // Use built-in Apps Script token (covers cloud-platform scope)
    return ScriptApp.getOAuthToken();
  } catch (err) {
    console.error("Access token error: " + err.toString());
    return null;
  }
}

function createJsonResponse(success, message, data) {
  var result = {
    success: success,
    message: message,
    timestamp: new Date().toISOString(),
    service: "Document AI Complete v1.1"
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