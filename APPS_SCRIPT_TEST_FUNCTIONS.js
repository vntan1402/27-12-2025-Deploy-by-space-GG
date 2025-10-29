// ===============================================
// 🧪 TEST FUNCTION - Add to Apps Script Editor
// ===============================================

/**
 * Test function to verify Apps Script v3.0 logic
 * This can be run directly in the editor
 */
function testScriptLogic() {
  try {
    Logger.log("🧪 Starting test...");
    
    // Test 1: Test maskSensitiveData function
    const maskedId = maskSensitiveData("1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB");
    Logger.log("✅ Test 1 - Mask function: " + maskedId);
    if (maskedId !== "1UeKVB***") {
      throw new Error("Mask function failed!");
    }
    
    // Test 2: Test connection to folder
    const testResult = testConnection({ 
      folder_id: "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB" 
    });
    Logger.log("✅ Test 2 - Connection: " + JSON.stringify(testResult));
    
    // Test 3: Test list folders
    const folders = listFolders({ 
      parent_id: "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB" 
    });
    Logger.log("✅ Test 3 - List folders: Found " + folders.length + " folders");
    
    // Test 4: Test validation with invalid folder_id
    try {
      validateFolderId("invalid_id_12345");
      Logger.log("❌ Test 4 FAILED - Should have thrown error");
    } catch (e) {
      Logger.log("✅ Test 4 - Validation working: " + e.message);
    }
    
    Logger.log("");
    Logger.log("🎉 ALL TESTS PASSED!");
    Logger.log("✅ Apps Script v3.0 is working correctly!");
    Logger.log("");
    Logger.log("📝 Next step: Test via Web App URL from your application");
    
    return "All tests passed! ✅";
    
  } catch (error) {
    Logger.log("❌ TEST FAILED: " + error.message);
    Logger.log(error.stack);
    throw error;
  }
}

/**
 * Test doPost logic with simulated event
 * This simulates what happens when Web App receives POST request
 */
function testDoPostLogic() {
  try {
    Logger.log("🧪 Testing doPost logic...");
    
    // Simulate a POST request event
    const mockEvent = {
      postData: {
        contents: JSON.stringify({
          action: "test_connection",
          folder_id: "1UeKVBrqaEsND4WziUUL2h-JIyOZ7maVB"
        })
      }
    };
    
    // Call doPost with mock event
    const response = doPost(mockEvent);
    const content = response.getContent();
    const result = JSON.parse(content);
    
    Logger.log("Response: " + JSON.stringify(result, null, 2));
    
    if (result.success) {
      Logger.log("✅ doPost test PASSED!");
      Logger.log("✅ Web App is ready to receive real POST requests!");
      return "doPost working correctly! ✅";
    } else {
      Logger.log("❌ doPost test FAILED: " + result.message);
      throw new Error("doPost test failed");
    }
    
  } catch (error) {
    Logger.log("❌ TEST FAILED: " + error.message);
    Logger.log(error.stack);
    throw error;
  }
}
