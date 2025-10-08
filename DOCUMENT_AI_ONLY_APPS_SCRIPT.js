/**
 * Google Apps Script for Document AI Processing ONLY
 * Version: Document AI Processor v3.0
 * Purpose: Handle Document AI processing without file upload
 * Backend handles all file uploads directly
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
      return createJsonResponse(true, "Document AI Processing Service is WORKING!", {
        version: "document-ai-only-v3.0",
        timestamp: new Date().toISOString(),
        workflow: "Document AI Processing → Summary Generation (NO FILE UPLOAD)",
        supported_documents: [
          "Passport (Hộ chiếu)",
          "Seaman's Book (Sổ thủy thủ)", 
          "Certificate of Competency (Bằng cấp chuyên môn)",
          "STCW Certificates (Chứng chỉ STCW)",
          "Medical Certificate (Giấy khám sức khỏe)",
          "Other Maritime Documents"
        ],
        supported_actions: [
          "test_connection",
          "test_document_ai",
          "analyze_passport_document_ai",
          "analyze_seamans_book_document_ai", 
          "analyze_certificate_document_ai",
          "analyze_medical_document_ai",
          "analyze_maritime_document_ai"
        ],
        note: "File uploads handled by backend directly - not by Apps Script"
      });
    }

    var action = requestData.action || "default";

    switch (action) {
      case "test_connection":
        return handleTestConnection(requestData);
      case "test_document_ai":
        return handleTestDocumentAI(requestData);
      case "analyze_passport_document_ai":
        return handleAnalyzeDocument(requestData, "passport");
      case "analyze_seamans_book_document_ai":
        return handleAnalyzeDocument(requestData, "seamans_book");
      case "analyze_certificate_document_ai":
        return handleAnalyzeDocument(requestData, "certificate");
      case "analyze_medical_document_ai":
        return handleAnalyzeDocument(requestData, "medical");
      case "analyze_maritime_document_ai":
        return handleAnalyzeDocument(requestData, "general_maritime");
      default:
        console.log("❌ UNKNOWN ACTION:", action);
        return createJsonResponse(false, "Unknown action: " + action);
    }

  } catch (error) {
    console.error("Request handling error: " + error.toString());
    return createJsonResponse(false, "Error processing request: " + error.toString());
  }
}

function handleTestConnection(data) {
  return createJsonResponse(true, "Document AI Processing Service is running successfully", {
    timestamp: new Date().toISOString(),
    version: "document-ai-only-v3.0",
    uptime_check: "OK",
    workflow: "Document AI Processing → Summary Generation (Backend handles uploads)",
    document_types_supported: 5
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

    console.log("🔍 Testing Document AI connection...");
    console.log("   🏗️ Project: " + projectId);
    console.log("   📍 Location: " + location);
    console.log("   ⚙️ Processor: " + processorId + " (Universal Processor)");

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
      return createJsonResponse(true, "Document AI connection successful", {
        processor_info: info,
        workflow: "document_ai_processing_only"
      });
    } else {
      return createJsonResponse(false, "Document AI connection failed: " + responseText);
    }

  } catch (error) {
    return createJsonResponse(false, "Test failed: " + error.toString());
  }
}

function handleAnalyzeDocument(data, documentType) {
  try {
    var projectId = data.project_id;
    var location = data.location || 'us';
    var processorId = data.processor_id;
    var fileContent = data.file_content;
    var filename = data.filename || "maritime_document";
    var contentType = data.content_type || "application/pdf";
    
    if (!projectId || !processorId || !fileContent) {
      return createJsonResponse(false, "Missing required parameters: project_id, processor_id, or file_content");
    }

    var documentInfo = getDocumentTypeInfo(documentType);

    console.log("🔄 DOCUMENT AI PROCESSING (NO FILE UPLOAD)");
    console.log("   📄 File: " + filename);
    console.log("   📋 Type: " + documentInfo.name + " (" + documentInfo.name_vn + ")");
    console.log("   🏗️ Project: " + projectId);
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

    console.log("📡 Sending " + documentInfo.name + " to Document AI...");
    
    var response = UrlFetchApp.fetch("https://documentai.googleapis.com/v1/" + processorName, options);
    var responseCode = response.getResponseCode();
    var responseText = response.getContentText();

    console.log("📡 Document AI response code: " + responseCode);

    if (responseCode === 200) {
      var result = JSON.parse(responseText);
      
      console.log("✅ Document AI processing successful!");
      
      // Extract summary from Document AI response
      var documentSummary = extractMaritimeSummary(result, documentType, documentInfo);
      
      console.log("📝 Generated " + documentInfo.name + " summary: " + documentSummary.substring(0, 200) + "...");
      
      return createJsonResponse(true, documentInfo.name + " processing completed successfully", {
        summary: documentSummary,
        document_type: documentType,
        processing_details: {
          filename: filename,
          content_type: contentType,
          processor_id: processorId,
          processor_type: "universal_processor",
          document_category: documentInfo.category,
          document_name: documentInfo.name,
          document_name_vn: documentInfo.name_vn,
          workflow: "document_ai_only",
          note: "File uploads handled by backend"
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
    console.error("❌ Document analysis error: " + error.toString());
    return createJsonResponse(false, "Document analysis failed: " + error.toString());
  }
}

function getDocumentTypeInfo(documentType) {
  var documentTypes = {
    "passport": {
      name: "Passport",
      name_vn: "Hộ chiếu",
      category: "identification",
      key_fields: ["full_name", "passport_number", "date_of_birth", "place_of_birth", "nationality", "sex", "issue_date", "expiry_date"]
    },
    "seamans_book": {
      name: "Seaman's Book", 
      name_vn: "Sổ thủy thủ",
      category: "maritime_qualification",
      key_fields: ["full_name", "book_number", "date_of_birth", "place_of_birth", "nationality", "rank", "issue_date", "expiry_date", "issuing_authority"]
    },
    "certificate": {
      name: "Maritime Certificate",
      name_vn: "Chứng chỉ hàng hải", 
      category: "certification",
      key_fields: ["certificate_name", "certificate_number", "holder_name", "issue_date", "expiry_date", "issuing_authority", "certificate_level", "endorsements"]
    },
    "medical": {
      name: "Medical Certificate",
      name_vn: "Giấy khám sức khỏe",
      category: "medical",
      key_fields: ["patient_name", "certificate_number", "examination_date", "expiry_date", "medical_status", "restrictions", "examining_doctor", "medical_facility"]
    },
    "general_maritime": {
      name: "Maritime Document",
      name_vn: "Tài liệu hàng hải",
      category: "general",
      key_fields: ["document_name", "document_number", "holder_name", "issue_date", "expiry_date", "issuing_authority", "document_type"]
    }
  };
  
  return documentTypes[documentType] || documentTypes["general_maritime"];
}

function extractMaritimeSummary(documentAIResult, documentType, documentInfo) {
  try {
    console.log("📝 Starting summary extraction for " + documentInfo.name);

    if (!documentAIResult || !documentAIResult.document) {
      console.log("❌ No document object in DocumentAI result");
      return "No document content available for summarization.";
    }
    
    var document = documentAIResult.document;

    // Try to get summary from entities first
    if (document.entities && document.entities.length > 0) {
      for (var i = 0; i < document.entities.length; i++) {
        var entity = document.entities[i];
        if (entity.type && entity.type.toLowerCase().includes('summary') && entity.mentionText) {
          console.log("✅ Found summary entity for " + documentInfo.name);
          return createStructuredSummary(entity.mentionText, documentType, documentInfo);
        }
      }
    }

    // Fallback to raw text
    if (document.text) {
      console.log("📝 Creating summary from raw text for " + documentInfo.name);
      return createStructuredSummary(document.text, documentType, documentInfo);
    }

    return "No extractable content found in " + documentInfo.name + ".";
    
  } catch (error) {
    console.error("❌ Summary extraction error: " + error.toString());
    return "Summary extraction failed: " + error.toString();
  }
}

function createStructuredSummary(text, documentType, documentInfo) {
  try {
    var summary = "";

    // Header
    summary += "🧭 MARITIME DOCUMENT ANALYSIS\n";
    summary += "====================================\n";
    summary += "📄 Document Type : " + documentInfo.name + " (" + documentInfo.name_vn + ")\n";
    summary += "📁 Category      : " + documentInfo.category + "\n";
    summary += "🕓 Analysis Date : " + new Date().toISOString() + "\n\n";

    // Expected key fields
    summary += "🔑 EXPECTED KEY FIELDS\n";
    summary += "----------------------\n";
    for (var i = 0; i < documentInfo.key_fields.length; i++) {
      summary += " - " + documentInfo.key_fields[i] + "\n";
    }
    summary += "\n";

    // Document content
    summary += "📘 DOCUMENT CONTENT\n";
    summary += "-------------------\n";
    var cleanText = text.replace(/\s+/g, " ").trim();
    if (cleanText.length > 10000) {
      summary += cleanText.substring(0, 10000) + "... [truncated]\n\n";
    } else {
      summary += cleanText + "\n\n";
    }

    // Processing status
    summary += "✅ PROCESSING STATUS\n";
    summary += "-------------------\n";
    summary += " - Document AI processing: COMPLETED\n";
    summary += " - Text extraction: OK\n";
    summary += " - Structured summary: Generated\n";
    summary += " - Next step: Backend AI field extraction\n";
    summary += " - File upload: Handled by backend\n";

    return summary;

  } catch (error) {
    console.error("❌ Structured summary creation error: " + error.toString());
    return "Summary creation failed: " + error.toString();
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
    service: "Document AI Processing Only v3.0"
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