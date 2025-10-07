/**
 * SIMPLE TEST Apps Script - Debug Version
 */

function doPost(e) {
  return handleRequest(e);
}

function doGet(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  try {
    console.log("🔄 REQUEST RECEIVED");
    
    var requestData = {};
    var method = "GET";

    if (e && e.postData && e.postData.contents) {
      method = "POST";
      console.log("📥 POST DATA DETECTED");
      console.log("Raw contents:", e.postData.contents.substring(0, 500) + "...");
      
      try {
        requestData = JSON.parse(e.postData.contents);
        console.log("✅ JSON PARSED SUCCESS");
        console.log("Action:", requestData.action);
        console.log("Filename:", requestData.filename);
      } catch (parseError) {
        console.log("❌ JSON PARSE ERROR:", parseError.toString());
        return createJsonResponse(false, "Invalid JSON: " + parseError.toString());
      }
    } else {
      console.log("📥 GET REQUEST - Returning test response");
      return createJsonResponse(true, "Simple Test Apps Script is WORKING!", {
        version: "simple-test-v1.0",
        timestamp: new Date().toISOString(),
        method: method
      });
    }

    var action = requestData.action || "default";
    console.log("🎯 ACTION TO EXECUTE:", action);

    // Simple action handling
    switch (action) {
      case "analyze_passport_document_ai":
        return handleSimplePassportAnalysis(requestData);
      case "upload_file":
        return handleSimpleUpload(requestData);
      default:
        console.log("❌ UNKNOWN ACTION:", action);
        return createJsonResponse(false, "Unknown action: " + action);
    }

  } catch (error) {
    console.error("❌ REQUEST ERROR:", error.toString());
    return createJsonResponse(false, "Request handling error: " + error.toString());
  }
}

function handleSimplePassportAnalysis(data) {
  try {
    console.log("🔄 SIMPLE PASSPORT ANALYSIS");
    
    // Safe access to data
    var filename = (data && data.filename) || "no_filename";
    var fileContent = (data && data.file_content) || "";
    var projectId = (data && data.project_id) || "no_project";
    var processorId = (data && data.processor_id) || "no_processor";
    
    console.log("📄 File:", filename);
    console.log("🏗️ Project:", projectId);
    console.log("⚙️ Processor:", processorId);
    console.log("📊 Content length:", fileContent.length);
    
    // Mock successful response for now
    return createJsonResponse(true, "Simple passport analysis test completed", {
      summary: "MOCK SUMMARY: This is a test passport document analysis. The file " + filename + " was processed successfully for testing purposes.",
      processing_details: {
        filename: filename,
        processor_id: processorId,
        project_id: projectId,
        test_mode: true
      }
    });
    
  } catch (error) {
    console.error("❌ SIMPLE ANALYSIS ERROR:", error.toString());
    return createJsonResponse(false, "Simple analysis failed: " + error.toString());
  }
}

function handleSimpleUpload(data) {
  try {
    console.log("📁 SIMPLE UPLOAD");
    
    // Safe access to data  
    var filename = (data && data.filename) || "no_filename";
    var folderPath = (data && data.folder_path) || "no_folder";
    
    console.log("📄 File:", filename);
    console.log("📁 Folder:", folderPath);
    
    // Mock successful upload
    return createJsonResponse(true, "Simple upload test completed", {
      file_id: "test_file_" + new Date().getTime(),
      filename: filename,
      folder_path: folderPath,
      test_mode: true
    });
    
  } catch (error) {
    console.error("❌ SIMPLE UPLOAD ERROR:", error.toString());
    return createJsonResponse(false, "Simple upload failed: " + error.toString());
  }
}

function createJsonResponse(success, message, data) {
  var result = {
    success: success,
    message: message,
    timestamp: new Date().toISOString(),
    service: "Simple Test Apps Script v1.0"
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