/**
 * Google Apps Script for Document AI Integration - FIXED VERSION
 * Version: Fixed Authentication Scopes
 * Purpose: Handle Document AI API calls with proper OAuth scopes
 * 
 * IMPORTANT: This script requires the following OAuth scopes in appscript.json:
 * - https://www.googleapis.com/auth/cloud-platform
 * - https://www.googleapis.com/auth/documentai
 * - https://www.googleapis.com/auth/script.external_request
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
      return createJsonResponse(true, "Document AI Service (FIXED AUTH) is WORKING!", {
        version: "fixed-auth-v1.0",
        timestamp: new Date().toISOString(),
        service: "Google Document AI Integration - Fixed Authentication",
        oauth_scopes: [
          "https://www.googleapis.com/auth/cloud-platform",
          "https://www.googleapis.com/auth/documentai",
          "https://www.googleapis.com/auth/script.external_request"
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
      case "analyze_passport_document_ai":
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
  return createJsonResponse(true, "Document AI Service with fixed authentication is running successfully", {
    timestamp: new Date().toISOString(),
    version: "fixed-auth-v1.0",
    uptime_check: "OK",
    auth_scopes: "cloud-platform, documentai, external_request"
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

    console.log("🔍 Testing Document AI connection with fixed auth...");
    console.log("   🏗️ Project: " + projectId);
    console.log("   📍 Location: " + location);
    console.log("   ⚙️ Processor: " + processorId);

    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token with required scopes");
    }

    console.log("✅ Access token obtained successfully");

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

    console.log("📡 Making test request to Document AI API...");

    var response = UrlFetchApp.fetch(url, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();

    console.log("📡 Response code: " + responseCode);

    if (responseCode === 200) {
      var info = JSON.parse(responseText);
      console.log("✅ Document AI connection test successful");
      return createJsonResponse(true, "Document AI connection successful with fixed authentication", {
        processor_info: info,
        auth_method: "fixed_oauth_scopes"
      });
    } else {
      console.error("❌ Document AI connection test failed: " + responseText);
      return createJsonResponse(false, "Document AI connection test failed: " + responseText, {
        response_code: responseCode,
        auth_method: "fixed_oauth_scopes"
      });
    }

  } catch (error) {
    console.error("❌ Test connection error: " + error.toString());
    return createJsonResponse(false, "Test failed: " + error.toString());
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
      return createJsonResponse(false, "Missing required parameters: project_id, processor_id, or file_content");
    }

    console.log("🔄 PASSPORT ANALYSIS - Fixed Auth Version");
    console.log("   📄 File: " + filename);
    console.log("   🏗️ Project: " + projectId);
    console.log("   ⚙️ Processor: " + processorId);

    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token with Document AI scopes");
    }

    console.log("✅ Access token obtained with proper scopes");

    var processorName = "projects/" + projectId + "/locations/" + location + "/processors/" + processorId + ":process";
    
    var requestPayload = {
      rawDocument: {
        content: fileContent,
        mimeType: contentType
      }
    };

    var options = {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json"
      },
      payload: JSON.stringify(requestPayload),
      muteHttpExceptions: true
    };

    console.log("📡 Sending request to Document AI API with proper authentication...");
    
    var response = UrlFetchApp.fetch("https://documentai.googleapis.com/v1/" + processorName, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();

    console.log("📡 Document AI response code: " + responseCode);

    if (responseCode === 200) {
      var result = JSON.parse(responseText);
      
      console.log("✅ Document AI processing successful!");
      
      // Debug: Log the structure we received
      console.log("📊 Document AI Response Structure:");
      if (result.document) {
        console.log("   ✅ Has document object");
        if (result.document.text) {
          console.log("   ✅ Has text: " + result.document.text.length + " characters");
        }
        if (result.document.entities && result.document.entities.length > 0) {
          console.log("   ✅ Has entities: " + result.document.entities.length + " found");
          
          // Log first few entities for debugging
          for (var i = 0; i < Math.min(result.document.entities.length, 5); i++) {
            var entity = result.document.entities[i];
            console.log("     Entity " + i + ": type=" + (entity.type || "unknown") + 
                       ", text=" + (entity.mentionText || entity.textAnchor?.content || "no_text") +
                       ", confidence=" + (entity.confidence || "no_confidence"));
          }
        } else {
          console.log("   ❌ No entities found");
        }
      } else {
        console.log("   ❌ No document object in response");
      }
      
      // Extract passport-specific information
      var extractedInfo = extractPassportInformation(result);
      
      console.log("✅ Passport analysis completed successfully");
      console.log("   👤 Extracted Name: '" + extractedInfo.full_name + "'");
      console.log("   📔 Extracted Passport: '" + extractedInfo.passport_number + "'");
      console.log("   🎯 Confidence: " + extractedInfo.confidence_score);
      
      return createJsonResponse(true, "Passport analysis completed successfully", {
        analysis: extractedInfo,
        processing_details: {
          filename: filename,
          content_type: contentType,
          processor_id: processorId,
          auth_method: "fixed_oauth_scopes",
          document_structure: {
            has_document: !!result.document,
            has_text: !!(result.document && result.document.text),
            text_length: result.document && result.document.text ? result.document.text.length : 0,
            has_entities: !!(result.document && result.document.entities && result.document.entities.length > 0),
            entity_count: result.document && result.document.entities ? result.document.entities.length : 0
          }
        }
      });
      
    } else {
      console.error("❌ Document AI processing error: " + responseText);
      return createJsonResponse(false, "Document AI processing failed with code " + responseCode + ": " + responseText, {
        response_code: responseCode,
        auth_method: "fixed_oauth_scopes"
      });
    }

  } catch (error) {
    console.error("❌ Passport analysis error: " + error.toString());
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

// Extract passport-specific information from Document AI result
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
      processing_method: "document_ai_entities",
      debug_info: {
        entities_found: 0,
        entities_processed: 0,
        text_patterns_used: false
      }
    };

    if (!document) {
      extractedInfo.debug_info.error = "No document in response";
      return extractedInfo;
    }

    // Extract from entities if available
    if (document.entities && document.entities.length > 0) {
      extractedInfo.debug_info.entities_found = document.entities.length;
      var confidenceScores = [];

      console.log("🔍 Processing " + document.entities.length + " entities...");

      for (var i = 0; i < document.entities.length; i++) {
        var entity = document.entities[i];
        var entityType = (entity.type || "").toLowerCase();
        var entityText = entity.mentionText || "";
        
        if (entity.textAnchor && entity.textAnchor.content) {
          entityText = entityText || entity.textAnchor.content;
        }
        
        var confidence = entity.confidence || 0;

        console.log("   Entity " + i + ": type='" + entityType + "', text='" + entityText + "', confidence=" + confidence);

        if (confidence > 0) {
          confidenceScores.push(confidence);
        }

        extractedInfo.debug_info.entities_processed++;

        // Map entity types to passport fields with more variations
        var mapped = false;
        switch (entityType) {
          case 'person_name':
          case 'name':
          case 'full_name':
          case 'given_names':
          case 'surname':
          case 'first_name':
          case 'last_name':
            if (!extractedInfo.full_name && entityText.trim()) {
              extractedInfo.full_name = entityText.trim();
              console.log("     ✅ Mapped to full_name: " + entityText);
              mapped = true;
            }
            break;
          case 'sex':
          case 'gender':
            if (entityText.trim()) {
              extractedInfo.sex = entityText.toUpperCase().charAt(0); // M or F
              console.log("     ✅ Mapped to sex: " + entityText);
              mapped = true;
            }
            break;
          case 'date_of_birth':
          case 'birth_date':
          case 'dob':
          case 'birthday':
            if (entityText.trim()) {
              extractedInfo.date_of_birth = formatDate(entityText);
              console.log("     ✅ Mapped to date_of_birth: " + entityText);
              mapped = true;
            }
            break;
          case 'place_of_birth':
          case 'birth_place':
          case 'place_birth':
          case 'birthplace':
            if (entityText.trim()) {
              extractedInfo.place_of_birth = entityText.trim();
              console.log("     ✅ Mapped to place_of_birth: " + entityText);
              mapped = true;
            }
            break;
          case 'passport_number':
          case 'document_number':
          case 'passport_id':
          case 'document_id':
          case 'id_number':
            if (entityText.trim()) {
              extractedInfo.passport_number = entityText.trim().replace(/\s+/g, '');
              console.log("     ✅ Mapped to passport_number: " + entityText);
              mapped = true;
            }
            break;
          case 'nationality':
          case 'country':
          case 'issuing_country':
          case 'citizenship':
            if (entityText.trim()) {
              extractedInfo.nationality = entityText.trim();
              console.log("     ✅ Mapped to nationality: " + entityText);
              mapped = true;
            }
            break;
          case 'issue_date':
          case 'date_of_issue':
          case 'issued_date':
          case 'issuance_date':
            if (entityText.trim()) {
              extractedInfo.issue_date = formatDate(entityText);
              console.log("     ✅ Mapped to issue_date: " + entityText);
              mapped = true;
            }
            break;
          case 'expiry_date':
          case 'expiration_date':
          case 'date_of_expiry':
          case 'expires':
          case 'valid_until':
            if (entityText.trim()) {
              extractedInfo.expiry_date = formatDate(entityText);
              console.log("     ✅ Mapped to expiry_date: " + entityText);
              mapped = true;
            }
            break;
        }
        
        if (!mapped) {
          console.log("     ❌ No mapping for entity type: " + entityType);
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
    } else {
      console.log("❌ No entities found in Document AI response");
    }

    // Fallback: extract from text using patterns if entities didn't provide enough info
    if (document.text && (!extractedInfo.passport_number || !extractedInfo.full_name)) {
      console.log("🔍 Using text pattern extraction as fallback");
      extractedInfo.debug_info.text_patterns_used = true;
      
      var textInfo = extractFromTextPatterns(document.text);

      if (!extractedInfo.full_name && textInfo.full_name) {
        extractedInfo.full_name = textInfo.full_name;
        extractedInfo.processing_method = "text_patterns";
        console.log("     ✅ Text pattern found name: " + textInfo.full_name);
      }
      if (!extractedInfo.passport_number && textInfo.passport_number) {
        extractedInfo.passport_number = textInfo.passport_number;
        extractedInfo.processing_method = "text_patterns";
        console.log("     ✅ Text pattern found passport: " + textInfo.passport_number);
      }
      if (!extractedInfo.date_of_birth && textInfo.date_of_birth) {
        extractedInfo.date_of_birth = textInfo.date_of_birth;
        console.log("     ✅ Text pattern found DOB: " + textInfo.date_of_birth);
      }
    }

    // Set minimum confidence if we extracted some information
    if (extractedInfo.confidence_score === 0.0 && 
        (extractedInfo.full_name || extractedInfo.passport_number)) {
      extractedInfo.confidence_score = 0.7; // Reasonable confidence for pattern matching
    }

    console.log("🎯 Final extraction results:");
    console.log("   Name: '" + extractedInfo.full_name + "'");
    console.log("   Passport: '" + extractedInfo.passport_number + "'");
    console.log("   DOB: '" + extractedInfo.date_of_birth + "'");
    console.log("   Sex: '" + extractedInfo.sex + "'");
    console.log("   Confidence: " + extractedInfo.confidence_score);

    return extractedInfo;

  } catch (error) {
    console.error("❌ Information extraction error: " + error.toString());
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
    console.log("🔍 Text pattern extraction - text length: " + text.length);

    // Enhanced Vietnamese name patterns
    var namePatterns = [
      /(?:họ và tên|tên|name|full name)[:.\s]*([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*)*)/gi,
      /([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]+\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]+\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]+)/g,
      /NGUYEN\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]+\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]+/gi
    ];

    for (var i = 0; i < namePatterns.length; i++) {
      var match = namePatterns[i].exec(text);
      if (match && match[1] && match[1].length > 5) {
        info.full_name = match[1].trim();
        console.log("   ✅ Name pattern match: " + info.full_name);
        break;
      } else if (match && match[0] && match[0].length > 5) {
        info.full_name = match[0].trim();
        console.log("   ✅ Name pattern match (full): " + info.full_name);
        break;
      }
    }

    // Enhanced passport number patterns
    var passportPatterns = [
      /(?:Passport\s*(?:No|Number|#)|Số\s*hộ\s*chiếu)[:.\s]*([A-Z]\d{7,8}|[A-Z]{1,2}\d{6,8})/gi,
      /\b([A-Z]\d{7,8}|[A-Z]{1,2}\d{6,8})\b/g,
      /B\d{7}/gi
    ];

    for (var j = 0; j < passportPatterns.length; j++) {
      var match = passportPatterns[j].exec(text);
      if (match && match[1]) {
        info.passport_number = match[1].replace(/\s+/g, '');
        console.log("   ✅ Passport pattern match: " + info.passport_number);
        break;
      }
    }

    // Date patterns
    var datePatterns = [
      /(?:Date\s*of\s*birth|Ngày\s*sinh|DOB)[:.\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})/gi,
      /\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})\b/g
    ];

    for (var k = 0; k < datePatterns.length; k++) {
      var match = datePatterns[k].exec(text);
      if (match && match[1]) {
        info.date_of_birth = formatDate(match[1]);
        console.log("   ✅ Date pattern match: " + info.date_of_birth);
        break;
      }
    }

    return info;

  } catch (error) {
    console.error("❌ Text pattern extraction error: " + error.toString());
    return info;
  }
}

// Format date to DD/MM/YYYY format (Vietnamese standard)
function formatDate(dateString) {
  if (!dateString) return "";

  try {
    // Clean the date string
    var cleanDate = dateString.replace(/[^\d\/\-\.]/g, "");
    var parts = cleanDate.split(/[\/\-\.]/);

    if (parts.length === 3) {
      var day = parts[0].length === 1 ? '0' + parts[0] : parts[0];
      var month = parts[1].length === 1 ? '0' + parts[1] : parts[1];
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
    console.error("❌ Date formatting error: " + error.toString());
    return dateString;
  }
}

function getDocumentAIAccessToken() {
  try {
    // Use built-in Apps Script token with cloud-platform scope
    // This should now include Document AI access
    return ScriptApp.getOAuthToken();
  } catch (err) {
    console.error("❌ Access token error: " + err.toString());
    return null;
  }
}

function createJsonResponse(success, message, data) {
  var result = {
    success: success,
    message: message,
    timestamp: new Date().toISOString(),
    service: "Document AI Fixed Auth v1.0"
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