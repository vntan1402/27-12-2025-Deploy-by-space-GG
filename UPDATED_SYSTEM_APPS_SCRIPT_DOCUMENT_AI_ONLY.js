/**
 * Google Apps Script for Maritime Document AI Integration
 * Version: Maritime Documents Universal Processor v3.0 - Document AI Only
 * Purpose: Handle ALL maritime crew documents - Document AI processing only
 * Workflow: Document AI → Summary → Backend handles file uploads
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
      return createJsonResponse(true, "Maritime Document AI Service is WORKING!", {
        version: "maritime-docs-v3.0-document-ai-only",
        timestamp: new Date().toISOString(),
        workflow: "Document AI → Summary → Backend File Upload",
        supported_documents: [
          "Passport (Hộ chiếu)",
          "Seaman's Book (Sổ thủy thủ)", 
          "Certificate of Competency (Bằng cấp chuyên môn)",
          "STCW Certificates (Chứng chỉ STCW)",
          "Medical Certificate (Giấy khám sức khỏe)",
          "Visa Documents (Thị thực)",
          "National ID (CCCD/CMND)",
          "Training Certificates (Chứng chỉ đào tạo)",
          "Work Permits (Giấy phép lao động)",
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
        note: "File uploads are handled by backend via Company Apps Script - this script only processes Document AI"
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
  return createJsonResponse(true, "Maritime Document AI Service is running successfully", {
    timestamp: new Date().toISOString(),
    version: "maritime-docs-v3.0-document-ai-only",
    uptime_check: "OK",
    workflow: "Document AI → Summary → Backend File Upload",
    document_types_supported: 10,
    file_upload: "Handled by backend via Company Apps Script"
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

    console.log("🔍 Testing Maritime Document AI connection...");
    console.log("   🏗️ Project: " + projectId);
    console.log("   📍 Location: " + location);
    console.log("   ⚙️ Processor: " + processorId + " (Universal Summarizer)");

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
      return createJsonResponse(true, "Maritime Document AI connection successful", {
        processor_info: info,
        workflow: "maritime_document_ai_only"
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

    console.log("🔄 MARITIME DOCUMENT AI ANALYSIS (NO FILE UPLOAD)");
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
      
      // Extract summary from Document AI response with document type context
      var documentSummary = extractMaritimeSummary(result, documentType, documentInfo);
      
      console.log("📝 Generated " + documentInfo.name + " summary: " + documentSummary.substring(0, 200) + "...");
      
      return createJsonResponse(true, documentInfo.name + " summary generated successfully", {
        summary: documentSummary,
        document_type: documentType,
        processing_details: {
          filename: filename,
          content_type: contentType,
          processor_id: processorId,
          processor_type: "universal_summarizer",
          document_category: documentInfo.category,
          document_name: documentInfo.name,
          document_name_vn: documentInfo.name_vn,
          workflow: "document_ai_only",
          next_step: "backend_field_extraction_and_file_upload"
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
    console.error("❌ Maritime document analysis error: " + error.toString());
    return createJsonResponse(false, "Maritime document analysis failed: " + error.toString());
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
    console.log("📝 Starting maritime summary extraction");
    console.log("📊 DocumentAI Result:", JSON.stringify(documentAIResult));

    // SAFE CHECK for document object
    if (!documentAIResult || !documentAIResult.document) {
      console.log("❌ No document object in DocumentAI result");
      return "No document content available for summarization. DocumentAI may have failed to process the file.";
    }
    
    var document = documentAIResult.document;
    
    if (!document) {
      return "No document content available for summarization.";
    }

    // First, try to get summary from entities (if it's a summarizer processor)
    if (document.entities && document.entities.length > 0) {
      for (var i = 0; i < document.entities.length; i++) {
        var entity = document.entities[i];
        if (entity.type && entity.type.toLowerCase().includes('summary') && entity.mentionText) {
          console.log("✅ Found summary entity for " + documentInfo.name);
          return createStructuredSummary(entity.mentionText, documentType, documentInfo);
        }
      }
    }

    // Fallback: create structured summary from raw text
    if (document.text) {
      console.log("📝 Creating structured summary from raw text for " + documentInfo.name);
      var rawText = document.text;
      
      return createStructuredSummary(rawText, documentType, documentInfo);
    }

    return "No extractable content found in " + documentInfo.name + ".";
    
  } catch (error) {
    console.error("❌ Maritime summary extraction error: " + error.toString());
    return "Summary extraction failed: " + error.toString();
  }
}

function createStructuredSummary(text, documentType, documentInfo) {
  try {
    var summary = "";

    // ===== HEADER =====
    summary += "🧭 MARITIME DOCUMENT ANALYSIS\n";
    summary += "====================================\n";
    summary += "📄 Document Type : " + documentInfo.name + " (" + documentInfo.name_vn + ")\n";
    summary += "📁 Category      : " + documentInfo.category + "\n";
    summary += "🕓 Analysis Date : " + new Date().toISOString() + "\n\n";

    // ===== EXPECTED KEY FIELDS =====
    summary += "🔑 EXPECTED KEY FIELDS\n";
    summary += "----------------------\n";
    for (var i = 0; i < documentInfo.key_fields.length; i++) {
      summary += " - " + documentInfo.key_fields[i] + "\n";
    }
    summary += "\n";

    // ===== DOCUMENT CONTENT =====
    summary += "📘 DOCUMENT CONTENT\n";
    summary += "-------------------\n";
    var cleanText = text.replace(/\s+/g, " ").trim();
    if (cleanText.length > 10000) {
      summary += cleanText.substring(0, 10000) + "... [truncated]\n\n";
    } else {
      summary += cleanText + "\n\n";
    }

    // ===== IDENTIFIED PATTERNS =====
    summary += "📊 IDENTIFIED PATTERNS\n";
    summary += "----------------------\n";
    var patterns = extractPatterns(cleanText, documentType);
    if (patterns.length > 0) {
      for (var j = 0; j < patterns.length; j++) {
        summary += " - " + patterns[j] + "\n";
      }
    } else {
      summary += " (No patterns identified)\n";
    }
    summary += "\n";

    // ===== DOCUMENT SPECIFIC ANALYSIS =====
    summary += "🧩 DOCUMENT SPECIFIC ANALYSIS\n";
    summary += "-----------------------------\n";
    summary += getDocumentSpecificAnalysis(cleanText, documentType, documentInfo) + "\n\n";

    // ===== SUMMARY FOOTER =====
    summary += "✅ PROCESSING STATUS\n";
    summary += "-------------------\n";
    summary += " - Text extraction: OK\n";
    summary += " - Structured summary: Completed\n";
    summary += " - Next step: Backend field extraction and file upload\n";

    return summary;

  } catch (error) {
    console.error("❌ Structured summary creation error: " + error.toString());
    return "Summary creation failed: " + error.toString();
  }
}

function extractPatterns(text, documentType) {
  var patterns = [];
  
  try {
    // Common patterns for all maritime documents
    
    // Names (Vietnamese and English)
    var nameMatches = text.match(/([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ][a-zàáạảãâầấậẩẫăằắặẳẵ]*)/g);
    if (nameMatches && nameMatches.length > 0) {
      patterns.push("Names found: " + nameMatches.slice(0, 3).join(", "));
    }
    
    // Numbers (certificate numbers, passport numbers, etc.)
    var numberMatches = text.match(/([A-Z]{1,3}\d{6,10}|\d{8,12})/g);
    if (numberMatches && numberMatches.length > 0) {
      patterns.push("Document numbers: " + numberMatches.slice(0, 3).join(", "));
    }
    
    // Dates
    var dateMatches = text.match(/(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})/g);
    if (dateMatches && dateMatches.length > 0) {
      patterns.push("Dates found: " + dateMatches.slice(0, 3).join(", "));
    }
    
    // Document type specific patterns
    switch (documentType) {
      case "passport":
        // Passport specific patterns
        if (text.toLowerCase().includes("passport") || text.toLowerCase().includes("hộ chiếu")) {
          patterns.push("Passport document confirmed");
        }
        if (text.match(/nationality|quốc tịch/i)) {
          patterns.push("Nationality information present");
        }
        break;
        
      case "seamans_book":
        // Seaman's book patterns
        if (text.toLowerCase().includes("seaman") || text.toLowerCase().includes("thủy thủ")) {
          patterns.push("Seaman's book document confirmed");
        }
        var rankMatches = text.match(/(captain|chief officer|second officer|third officer|engineer|bosun|able seaman|ordinary seaman)/gi);
        if (rankMatches) {
          patterns.push("Maritime ranks found: " + rankMatches.slice(0, 2).join(", "));
        }
        break;
        
      case "certificate":
        // Certificate patterns
        if (text.match(/certificate|chứng chỉ|bằng cấp/i)) {
          patterns.push("Certificate document confirmed");
        }
        var certMatches = text.match(/(STCW|COC|COP|GMDSS|Basic Safety|Advanced Fire|Medical First Aid)/gi);
        if (certMatches) {
          patterns.push("Certificate types: " + certMatches.slice(0, 3).join(", "));
        }
        break;
        
      case "medical":
        // Medical certificate patterns
        if (text.match(/medical|y tế|sức khỏe/i)) {
          patterns.push("Medical document confirmed");
        }
        if (text.match(/fit|unfit|restricted|không hạn chế|hạn chế/i)) {
          patterns.push("Medical fitness status present");
        }
        break;
    }
    
  } catch (error) {
    patterns.push("Pattern extraction error: " + error.toString());
  }
  
  return patterns;
}

function getDocumentSpecificAnalysis(text, documentType, documentInfo) {
  var analysis = "";
  
  try {
    analysis += documentInfo.name.toUpperCase() + " SPECIFIC ANALYSIS:\n";
    analysis += "=" + "=".repeat(documentInfo.name.length + 19) + "\n";
    
    switch (documentType) {
      case "passport":
        analysis += "Passport Analysis:\n";
        analysis += "- Looking for: Personal identification information\n";
        analysis += "- Key elements: Full name, passport number, nationality, dates\n";
        analysis += "- Format: International travel document\n";
        break;
        
      case "seamans_book":
        analysis += "Seaman's Book Analysis:\n";
        analysis += "- Looking for: Maritime qualification and service record\n"; 
        analysis += "- Key elements: Maritime rank, vessel service history, endorsements\n";
        analysis += "- Format: Official maritime service document\n";
        break;
        
      case "certificate":
        analysis += "Maritime Certificate Analysis:\n";
        analysis += "- Looking for: Professional maritime qualifications\n";
        analysis += "- Key elements: Certificate type, competency level, validity period\n";
        analysis += "- Format: Training/competency certification\n";
        break;
        
      case "medical":
        analysis += "Medical Certificate Analysis:\n";
        analysis += "- Looking for: Maritime medical fitness assessment\n";
        analysis += "- Key elements: Medical status, restrictions, examination details\n";
        analysis += "- Format: Health certification for maritime service\n";
        break;
        
      default:
        analysis += "General Maritime Document Analysis:\n";
        analysis += "- Looking for: Maritime-related information and credentials\n";
        analysis += "- Key elements: Document identification, validity, authority\n";
        analysis += "- Format: Official maritime documentation\n";
    }
    
    analysis += "Document Processing Summary:\n";
    analysis += "- Content successfully extracted and structured\n";
    analysis += "- Ready for AI field extraction using system AI\n";
    analysis += "- File upload handled by backend via Company Apps Script\n";
    
  } catch (error) {
    analysis += "Document analysis error: " + error.toString();
  }
  
  return analysis;
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
    service: "Maritime Document AI v3.0 - Document AI Only"
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