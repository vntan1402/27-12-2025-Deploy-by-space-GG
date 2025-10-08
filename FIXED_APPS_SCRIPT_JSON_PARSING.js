function doPost(e) {
  return handleRequest(e);
}

function doGet(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  try {
    console.log("🔄 REQUEST RECEIVED");
    console.log("Request object type:", typeof e);
    console.log("Request object keys:", Object.keys(e || {}));
    
    var requestData = {};
    var method = "GET";

    // DEBUG: Log the full request object structure
    if (e) {
      console.log("📊 Full request structure:");
      console.log("- e.postData:", !!e.postData);
      console.log("- e.parameter:", !!e.parameter);
      console.log("- e.parameters:", !!e.parameters);
      
      if (e.postData) {
        console.log("- e.postData.contents:", !!e.postData.contents);
        console.log("- e.postData.type:", e.postData.type);
      }
    }

    if (e && e.postData && e.postData.contents) {
      method = "POST";
      console.log("📥 POST DATA DETECTED");
      console.log("Content-Type:", e.postData.type);
      console.log("Raw contents length:", e.postData.contents.length);
      console.log("First 500 chars:", e.postData.contents.substring(0, 500));
      
      try {
        requestData = JSON.parse(e.postData.contents);
        console.log("✅ JSON PARSED SUCCESS");
        console.log("Parsed data keys:", Object.keys(requestData || {}));
        console.log("Action:", requestData.action);
        console.log("Filename:", requestData.filename);
        console.log("Has file_content:", !!requestData.file_content);
      } catch (parseError) {
        console.log("❌ JSON PARSE ERROR:", parseError.toString());
        console.log("Raw content causing error:", e.postData.contents);
        return createJsonResponse(false, "Invalid JSON: " + parseError.toString(), {
          raw_content: e.postData.contents.substring(0, 1000)
        });
      }
    } else if (e && e.parameter) {
      method = "GET";
      console.log("📥 PARAMETER DATA DETECTED");
      requestData = e.parameter;
      console.log("Parameter keys:", Object.keys(requestData || {}));
    } else {
      console.log("📥 NO DATA - Returning test response");
      return createJsonResponse(true, "Fixed JSON Parsing Apps Script is WORKING!", {
        version: "json-fix-v1.0",
        timestamp: new Date().toISOString(),
        method: method,
        debug_info: {
          has_e: !!e,
          has_postData: !!(e && e.postData),
          has_parameter: !!(e && e.parameter)
        }
      });
    }

    var action = requestData.action || "default";
    console.log("🎯 ACTION TO EXECUTE:", action);

    // Handle actions
    switch (action) {
      case "analyze_passport_document_ai":
        return handlePassportAnalysis(requestData);
      case "upload_file":
        return handleFileUpload(requestData);
      default:
        console.log("❌ UNKNOWN ACTION:", action);
        return createJsonResponse(false, "Unknown action: " + action, {
          available_actions: ["analyze_passport_document_ai", "upload_file"],
          received_action: action
        });
    }

  } catch (error) {
    console.error("❌ REQUEST HANDLING ERROR:", error.toString());
    console.error("Error stack:", error.stack);
    return createJsonResponse(false, "Request handling error: " + error.toString(), {
      error_stack: error.stack
    });
  }
}

function handlePassportAnalysis(data) {
  try {
    console.log("🔄 PASSPORT ANALYSIS STARTED");
    console.log("📊 Analysis data keys:", Object.keys(data || {}));
    
    // Safe access with detailed logging
    var filename = (data && data.filename) || "no_filename";
    var fileContent = (data && data.file_content) || "";
    var projectId = (data && data.project_id) || "no_project";
    var processorId = (data && data.processor_id) || "no_processor";
    var location = (data && data.location) || "us";
    
    console.log("📄 File:", filename);
    console.log("🏗️ Project:", projectId);
    console.log("📍 Location:", location);
    console.log("⚙️ Processor:", processorId);
    console.log("📊 Content length:", fileContent.length);
    
    if (!projectId || projectId === "no_project") {
      return createJsonResponse(false, "Missing project_id parameter");
    }
    
    if (!processorId || processorId === "no_processor") {
      return createJsonResponse(false, "Missing processor_id parameter");
    }
    
    if (!fileContent) {
      return createJsonResponse(false, "Missing file_content parameter");
    }
    
    // For now, return mock success to test data flow
    console.log("✅ All parameters validated, returning mock success");
    
    return createJsonResponse(true, "Passport analysis test completed", {
      summary: "MOCK ANALYSIS: Vietnamese passport detected. File: " + filename + ". Project: " + projectId + ". Processor: " + processorId + ". Content size: " + fileContent.length + " chars. This is a test response to verify data flow.",
      processing_details: {
        filename: filename,
        processor_id: processorId,
        project_id: projectId,
        location: location,
        content_size: fileContent.length,
        test_mode: true
      }
    });
    
  } catch (error) {
    console.error("❌ PASSPORT ANALYSIS ERROR:", error.toString());
    return createJsonResponse(false, "Passport analysis failed: " + error.toString());
  }
}

function handleFileUpload(data) {
  try {
    console.log("📁 FILE UPLOAD STARTED");
    console.log("📊 Upload data keys:", Object.keys(data || {}));
    
    // Safe access with detailed logging  
    var filename = (data && data.filename) || "no_filename";
    var folderPath = (data && data.folder_path) || "no_folder";
    var fileContent = (data && data.file_content) || "";
    
    console.log("📄 File:", filename);
    console.log("📁 Folder:", folderPath);
    console.log("📊 Size:", fileContent.length, "chars");
    
    // Mock successful upload
    console.log("✅ Upload parameters validated, returning mock success");
    
    return createJsonResponse(true, "File upload test completed", {
      file_id: "test_upload_" + new Date().getTime(),
      filename: filename,
      folder_path: folderPath,
      size: fileContent.length,
      test_mode: true
    });
    
  } catch (error) {
    console.error("❌ FILE UPLOAD ERROR:", error.toString());
    return createJsonResponse(false, "File upload failed: " + error.toString());
  }
}

function createJsonResponse(success, message, data) {
  var result = {
    success: success,
    message: message,
    timestamp: new Date().toISOString(),
    service: "JSON Fix Apps Script v1.0"
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