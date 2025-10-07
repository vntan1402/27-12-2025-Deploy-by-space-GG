/**
 * DEBUG Google Apps Script for Document AI Integration
 * Purpose: Debug what Document AI is actually returning
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
      return createJsonResponse(true, "Debug Document AI Service is WORKING!", {
        version: "debug-1.0",
        timestamp: new Date().toISOString()
      });
    }

    var action = requestData.action || "default";

    switch (action) {
      case "analyze_passport_document_ai":
        return handleDebugAnalyzePassport(requestData);
      default:
        return createJsonResponse(false, "Unknown action: " + action);
    }

  } catch (error) {
    console.error("Request handling error: " + error.toString());
    return createJsonResponse(false, "Error processing request: " + error.toString());
  }
}

function handleDebugAnalyzePassport(data) {
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

    console.log("🔍 DEBUG PASSPORT ANALYSIS STARTED");
    console.log("   📄 File: " + filename);
    console.log("   🏗️ Project: " + projectId);
    console.log("   📍 Location: " + location);
    console.log("   ⚙️ Processor: " + processorId);

    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token");
    }

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

    console.log("📡 Sending request to Document AI API");
    
    var response = UrlFetchApp.fetch("https://documentai.googleapis.com/v1/" + processorName, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();

    if (responseCode === 200) {
      var result = JSON.parse(responseText);
      
      // DEBUG: Log the complete Document AI response structure
      console.log("✅ Document AI Response Structure:");
      
      var debugInfo = {
        response_code: responseCode,
        has_document: !!result.document,
        document_structure: {},
        entities_found: 0,
        text_length: 0,
        raw_entities: [],
        processor_info: {
          processor_name: processorName,
          project_id: projectId,
          processor_id: processorId,
          location: location
        }
      };

      if (result.document) {
        var doc = result.document;
        
        // Document structure analysis
        debugInfo.document_structure = {
          has_text: !!doc.text,
          has_entities: !!(doc.entities && doc.entities.length > 0),
          has_pages: !!(doc.pages && doc.pages.length > 0),
          has_textAnchor: false
        };
        
        if (doc.text) {
          debugInfo.text_length = doc.text.length;
          console.log("📝 Document Text Length: " + doc.text.length);
          console.log("📝 First 200 chars: " + doc.text.substring(0, 200));
        }
        
        if (doc.entities && doc.entities.length > 0) {
          debugInfo.entities_found = doc.entities.length;
          console.log("🏷️ Found " + doc.entities.length + " entities");
          
          for (var i = 0; i < Math.min(doc.entities.length, 10); i++) {  // Show first 10 entities
            var entity = doc.entities[i];
            var entityInfo = {
              type: entity.type || "unknown",
              mention_text: entity.mentionText || "no_mention",
              confidence: entity.confidence || 0,
              text_anchor_content: ""
            };
            
            if (entity.textAnchor && entity.textAnchor.content) {
              entityInfo.text_anchor_content = entity.textAnchor.content;
              debugInfo.document_structure.has_textAnchor = true;
            }
            
            debugInfo.raw_entities.push(entityInfo);
            console.log("   Entity " + i + ": " + JSON.stringify(entityInfo));
          }
        } else {
          console.log("❌ No entities found in Document AI response");
        }
      } else {
        console.log("❌ No document object in Document AI response");
      }
      
      // Try to extract passport info with debugging
      var extractedInfo = debugExtractPassportInformation(result);
      
      return createJsonResponse(true, "Debug analysis completed", {
        debug_info: debugInfo,
        extracted_analysis: extractedInfo,
        raw_response_keys: Object.keys(result || {})
      });
      
    } else {
      console.error("Document AI processing error: " + responseText);
      return createJsonResponse(false, "Document AI processing failed with code " + responseCode + ": " + responseText);
    }

  } catch (error) {
    console.error("Debug passport analysis error: " + error.toString());
    return createJsonResponse(false, "Debug passport analysis failed: " + error.toString());
  }
}

function debugExtractPassportInformation(documentAIResult) {
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
      processing_method: "debug_extraction",
      debug_details: {
        entities_processed: 0,
        entities_matched: 0,
        text_patterns_tried: false,
        patterns_matched: 0
      }
    };

    if (!document) {
      extractedInfo.debug_details.error = "No document in response";
      return extractedInfo;
    }

    console.log("🔍 DEBUGGING EXTRACTION PROCESS");

    // Process entities with detailed logging
    if (document.entities && document.entities.length > 0) {
      extractedInfo.debug_details.entities_processed = document.entities.length;
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

        console.log("🏷️ Processing entity " + i + ": type='" + entityType + "', text='" + entityText + "', confidence=" + confidence);

        // Try to match entity types with detailed logging
        var matched = false;
        
        switch (entityType) {
          case 'person_name':
          case 'name':
          case 'full_name':
          case 'given_names':
          case 'surname':
            if (!extractedInfo.full_name && entityText.trim()) {
              extractedInfo.full_name = entityText.trim();
              matched = true;
              console.log("   ✅ Matched as full_name: " + entityText);
            }
            break;
          case 'sex':
          case 'gender':
            if (entityText.trim()) {
              extractedInfo.sex = entityText.toUpperCase().charAt(0);
              matched = true;
              console.log("   ✅ Matched as sex: " + entityText);
            }
            break;
          case 'date_of_birth':
          case 'birth_date':
          case 'dob':
            if (entityText.trim()) {
              extractedInfo.date_of_birth = entityText.trim();
              matched = true;
              console.log("   ✅ Matched as date_of_birth: " + entityText);
            }
            break;
          case 'passport_number':
          case 'document_number':
          case 'passport_id':
          case 'document_id':
            if (entityText.trim()) {
              extractedInfo.passport_number = entityText.trim().replace(/\s+/g, '');
              matched = true;
              console.log("   ✅ Matched as passport_number: " + entityText);
            }
            break;
        }
        
        if (matched) {
          extractedInfo.debug_details.entities_matched++;
        } else {
          console.log("   ❌ No match for entity type: " + entityType);
        }
      }

      // Calculate confidence
      if (confidenceScores.length > 0) {
        var sum = 0;
        for (var j = 0; j < confidenceScores.length; j++) {
          sum += confidenceScores[j];
        }
        extractedInfo.confidence_score = sum / confidenceScores.length;
      }
    }

    // Try text pattern extraction if entities didn't work
    if (document.text && (!extractedInfo.passport_number || !extractedInfo.full_name)) {
      console.log("🔍 Trying text pattern extraction as fallback");
      extractedInfo.debug_details.text_patterns_tried = true;
      
      var textInfo = debugExtractFromTextPatterns(document.text);
      
      if (!extractedInfo.full_name && textInfo.full_name) {
        extractedInfo.full_name = textInfo.full_name;
        extractedInfo.processing_method = "text_patterns";
        extractedInfo.debug_details.patterns_matched++;
      }
      if (!extractedInfo.passport_number && textInfo.passport_number) {
        extractedInfo.passport_number = textInfo.passport_number;
        extractedInfo.processing_method = "text_patterns";
        extractedInfo.debug_details.patterns_matched++;
      }
    }

    console.log("🎯 Final extraction results:");
    console.log("   Name: '" + extractedInfo.full_name + "'");
    console.log("   Passport: '" + extractedInfo.passport_number + "'");
    console.log("   Confidence: " + extractedInfo.confidence_score);
    console.log("   Entities matched: " + extractedInfo.debug_details.entities_matched + "/" + extractedInfo.debug_details.entities_processed);

    return extractedInfo;

  } catch (error) {
    console.error("Debug extraction error: " + error.toString());
    return {
      error: "Debug extraction failed: " + error.toString(),
      confidence_score: 0.0,
      processing_method: "debug_error"
    };
  }
}

function debugExtractFromTextPatterns(text) {
  var info = {
    full_name: "",
    passport_number: "",
    date_of_birth: ""
  };

  try {
    console.log("🔍 DEBUG TEXT PATTERNS - Text length: " + text.length);
    console.log("🔍 First 500 chars: " + text.substring(0, 500));

    // Vietnamese name patterns
    var namePatterns = [
      /(?:họ và tên|tên|name)[:.\s]*([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*)*)/gi,
      /([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*)/g
    ];

    for (var i = 0; i < namePatterns.length; i++) {
      var matches = text.match(namePatterns[i]);
      if (matches && matches.length > 0) {
        console.log("🔍 Name pattern " + i + " matches: " + JSON.stringify(matches));
        var match = namePatterns[i].exec(text);
        if (match && match[1] && match[1].length > 5) {
          info.full_name = match[1].trim();
          console.log("   ✅ Extracted name: " + info.full_name);
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
        console.log("   ✅ Extracted passport: " + info.passport_number);
        break;
      }
    }

    return info;

  } catch (error) {
    console.error("Text pattern debug error: " + error.toString());
    return info;
  }
}

function getDocumentAIAccessToken() {
  try {
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
    service: "Debug Document AI v1.0"
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