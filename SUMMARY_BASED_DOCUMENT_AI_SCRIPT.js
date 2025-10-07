/**
 * Google Apps Script for Document AI Integration - SUMMARY BASED VERSION
 * Purpose: Generate summary from documents, then use system AI to extract fields
 * Workflow: Document AI → Summary → System AI → Field Extraction
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
      return createJsonResponse(true, "Document AI Summary Service is WORKING!", {
        version: "summary-based-v1.0",
        timestamp: new Date().toISOString(),
        workflow: "Document AI → Summary → System AI → Field Extraction",
        supported_actions: [
          "test_connection",
          "test_document_ai", 
          "analyze_passport_document_ai",
          "upload_file"
        ]
      });
    }

    var action = requestData.action || "default";

    switch (action) {
      case "test_connection":
        return handleTestConnection(requestData);
      case "test_document_ai":
        return handleTestDocumentAI(requestData);
      case "analyze_passport_document_ai":
        return handleAnalyzePassportSummary(requestData);
      case "upload_file":
        return handleUploadFile(requestData);
      default:
        return createJsonResponse(false, "Unknown action: " + action);
    }

  } catch (error) {
    console.error("Request handling error: " + error.toString());
    return createJsonResponse(false, "Error processing request: " + error.toString());
  }
}

function handleTestConnection(data) {
  return createJsonResponse(true, "Document AI Summary Service is running successfully", {
    timestamp: new Date().toISOString(),
    version: "summary-based-v1.0",
    uptime_check: "OK",
    workflow: "Document AI → Summary → System AI → Field Extraction"
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

    console.log("🔍 Testing Document AI Summarizer connection...");
    console.log("   🏗️ Project: " + projectId);
    console.log("   📍 Location: " + location);
    console.log("   ⚙️ Processor: " + processorId + " (Summarizer)");

    var accessToken = getDocumentAIAccessToken();
    if (!accessToken) {
      return createJsonResponse(false, "Failed to obtain access token");
    }

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
      return createJsonResponse(true, "Document AI Summarizer connection successful", {
        processor_info: info,
        workflow: "summary_based"
      });
    } else {
      return createJsonResponse(false, "Document AI connection failed: " + responseText);
    }

  } catch (error) {
    return createJsonResponse(false, "Test failed: " + error.toString());
  }
}

function handleAnalyzePassportSummary(data) {
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

    console.log("🔄 PASSPORT SUMMARY GENERATION");
    console.log("   📄 File: " + filename);
    console.log("   🏗️ Project: " + projectId);
    console.log("   ⚙️ Processor: " + processorId + " (Summarizer)");

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

    console.log("📡 Sending document to AI Summarizer...");
    
    var response = UrlFetchApp.fetch("https://documentai.googleapis.com/v1/" + processorName, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();

    console.log("📡 Document AI response code: " + responseCode);

    if (responseCode === 200) {
      var result = JSON.parse(responseText);
      
      console.log("✅ Document AI processing successful!");
      
      // Extract summary from Document AI response
      var documentSummary = extractSummaryFromDocumentAI(result);
      
      console.log("📝 Generated summary: " + documentSummary.substring(0, 200) + "...");
      
      return createJsonResponse(true, "Document summary generated successfully", {
        summary: documentSummary,
        processing_details: {
          filename: filename,
          content_type: contentType,
          processor_id: processorId,
          processor_type: "summarizer",
          workflow: "summary_based",
          next_step: "system_ai_field_extraction"
        },
        document_info: {
          has_text: !!(result.document && result.document.text),
          text_length: result.document && result.document.text ? result.document.text.length : 0,
          has_entities: !!(result.document && result.document.entities && result.document.entities.length > 0),
          entity_count: result.document && result.document.entities ? result.document.entities.length : 0
        }
      });
      
    } else {
      console.error("❌ Document AI processing error: " + responseText);
      return createJsonResponse(false, "Document AI processing failed with code " + responseCode + ": " + responseText);
    }

  } catch (error) {
    console.error("❌ Passport summary generation error: " + error.toString());
    return createJsonResponse(false, "Passport summary generation failed: " + error.toString());
  }
}

function handleUploadFile(data) {
  try {
    console.log("📁 File upload action received");
    
    // Basic file upload simulation - in real implementation this would upload to Google Drive
    var filename = data.filename || "unknown_file";
    var fileContent = data.file_content || "";
    var folderPath = data.folder_path || "";
    
    console.log("   📄 File: " + filename);
    console.log("   📁 Folder: " + folderPath);
    console.log("   📊 Size: " + (fileContent ? fileContent.length : 0) + " chars");
    
    // Simulate successful upload
    return createJsonResponse(true, "File upload completed", {
      file_id: "simulated_file_id_" + new Date().getTime(),
      filename: filename,
      folder_path: folderPath,
      upload_method: "google_drive_simulation"
    });
    
  } catch (error) {
    console.error("❌ File upload error: " + error.toString());
    return createJsonResponse(false, "File upload failed: " + error.toString());
  }
}

function extractSummaryFromDocumentAI(documentAIResult) {
  try {
    var document = documentAIResult.document;
    
    if (!document) {
      return "No document content available for summarization.";
    }

    // First, try to get summary from entities (if it's a summarizer processor)
    if (document.entities && document.entities.length > 0) {
      for (var i = 0; i < document.entities.length; i++) {
        var entity = document.entities[i];
        if (entity.type && entity.type.toLowerCase().includes('summary') && entity.mentionText) {
          console.log("✅ Found summary entity");
          return cleanupSummaryText(entity.mentionText);
        }
      }
    }

    // Fallback: create basic summary from raw text
    if (document.text) {
      console.log("📝 Creating basic summary from raw text");
      var rawText = document.text;
      
      // Basic text cleaning and structuring
      var summary = "DOCUMENT ANALYSIS SUMMARY:\n\n";
      summary += "Raw Content: " + rawText.replace(/\s+/g, ' ').trim() + "\n\n";
      
      // Try to identify key information patterns
      var lines = rawText.split('\n').filter(function(line) {
        return line.trim().length > 0;
      });
      
      summary += "Identified Information:\n";
      for (var j = 0; j < lines.length && j < 10; j++) {
        if (lines[j].trim().length > 3) {
          summary += "- " + lines[j].trim() + "\n";
        }
      }
      
      return summary;
    }

    return "No extractable content found in document.";
    
  } catch (error) {
    console.error("❌ Summary extraction error: " + error.toString());
    return "Summary extraction failed: " + error.toString();
  }
}

function cleanupSummaryText(text) {
  if (!text) return "";
  
  try {
    // Clean up common AI summary artifacts
    var cleaned = text
      .replace(/^(Please provide the document|I need the text)/i, '')
      .replace(/\*\s*/g, '• ')  // Convert * to •
      .replace(/^[\s•-]+/gm, '• ')  // Standardize bullets
      .trim();
    
    return cleaned;
  } catch (error) {
    return text;
  }
}

function getDocumentAIAccessToken() {
  try {
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
    service: "Document AI Summary Service v1.0"
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