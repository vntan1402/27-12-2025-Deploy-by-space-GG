/**
 * Ship Management System - Updated Google Apps Script
 * Version: 3.0 - Multi Cert Upload Compatible
 * 
 * DEPLOYMENT INSTRUCTIONS:
 * 1. Go to https://script.google.com/
 * 2. Create new project or open existing
 * 3. Replace Code.gs with this complete code
 * 4. Deploy as Web App:
 *    - Execute as: Me (your account)
 *    - Who has access: Anyone
 * 5. Copy the Web App URL and update in Ship Management System
 */

function doPost(e) {
  return handleRequest(e);
}

function doGet(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  try {
    // Parse request data
    let requestData = {};
    
    if (e && e.postData && e.postData.contents) {
      try {
        requestData = JSON.parse(e.postData.contents);
      } catch (parseError) {
        return createJsonResponse(false, `Invalid JSON: ${parseError.toString()}`);
      }
    } else if (e && e.parameter) {
      requestData = e.parameter;
    } else {
      // Default response - this proves the script is working
      return createJsonResponse(true, "Ship Management Apps Script v3.0 is WORKING!", {
        version: "3.0-multi-cert-compatible",
        timestamp: new Date().toISOString(),
        supported_actions: [
          "test_connection", 
          "create_complete_ship_structure", 
          "upload_file_with_folder_creation",
          "check_ship_folder_exists"
        ]
      });
    }
    
    const action = requestData.action || "default";
    
    // Handle different actions
    switch (action) {
      case 'test_connection':
        return handleTestConnection(requestData);
        
      case 'create_complete_ship_structure':
        return handleCreateCompleteShipStructure(requestData);
        
      case 'upload_file_with_folder_creation':
        return handleUploadFileWithFolderCreation(requestData);
        
      case 'check_ship_folder_exists':
        return handleCheckShipFolderExists(requestData);
        
      default:
        return createJsonResponse(true, "Apps Script working - no action specified", {
          received_action: action,
          available_actions: [
            "test_connection", 
            "create_complete_ship_structure", 
            "upload_file_with_folder_creation",
            "check_ship_folder_exists"
          ]
        });
    }
    
  } catch (error) {
    return createJsonResponse(false, `Error: ${error.toString()}`);
  }
}

/**
 * Create JSON response
 */
function createJsonResponse(success, message, data = null) {
  const response = {
    success: success,
    message: message,
    timestamp: new Date().toISOString()
  };
  
  if (data) {
    Object.assign(response, data);
  }
  
  return ContentService
    .createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Test connection to ensure Apps Script is working
 */
function handleTestConnection(requestData) {
  try {
    const folderId = requestData.folder_id;
    
    if (!folderId) {
      return createJsonResponse(false, "Missing folder_id parameter");
    }
    
    // Try to access the folder
    const folder = DriveApp.getFolderById(folderId);
    const folderName = folder.getName();
    
    return createJsonResponse(true, "Connection successful", {
      folder_name: folderName,
      folder_id: folderId,
      test_result: "PASSED"
    });
    
  } catch (error) {
    return createJsonResponse(false, `Connection test failed: ${error.toString()}`);
  }
}

/**
 * Create complete dynamic ship folder structure
 */
function handleCreateCompleteShipStructure(requestData) {
  try {
    const parentFolderId = requestData.parent_folder_id;
    const shipName = requestData.ship_name;
    const companyId = requestData.company_id;
    
    if (!parentFolderId || !shipName) {
      return createJsonResponse(false, "Missing required parameters: parent_folder_id, ship_name");
    }
    
    // Get parent folder
    const parentFolder = DriveApp.getFolderById(parentFolderId);
    
    // Create ship folder
    const shipFolder = findOrCreateFolder(parentFolder, shipName);
    
    // Define complete folder structure (matching Homepage Sidebar EXACTLY)
    const folderStructure = {
      "Document Portfolio": [
        "Certificates",
        "Inspection Records",
        "Survey Reports", 
        "Drawings & Manuals",
        "Other Documents"
      ],
      "Crew Records": [
        "Crew List",
        "Crew Certificates",
        "Medical Records"
      ],
      "ISM Records": [
        "ISM Certificate",
        "Safety Procedures", 
        "Audit Reports"
      ],
      "ISPS Records": [
        "ISPS Certificate",
        "Security Plan",
        "Security Assessments"
      ],
      "MLC Records": [
        "MLC Certificate",
        "Labor Conditions",
        "Accommodation Reports"
      ],
      "Supplies": [
        "Inventory",
        "Purchase Orders",
        "Spare Parts"
      ]
    };
    
    // Create folders and track IDs
    let subfolderIds = {};
    let totalSubfoldersCreated = 0;
    
    for (const [mainCategory, subCategories] of Object.entries(folderStructure)) {
      // Create main category folder
      const mainFolder = findOrCreateFolder(shipFolder, mainCategory);
      subfolderIds[mainCategory] = mainFolder.getId();
      
      // Create subcategories
      const subcategoryIds = {};
      for (const subCategory of subCategories) {
        const subFolder = findOrCreateFolder(mainFolder, subCategory);
        subcategoryIds[subCategory] = subFolder.getId();
        totalSubfoldersCreated++;
      }
      
      // Store subcategory IDs
      subfolderIds[`${mainCategory}_subcategories`] = subcategoryIds;
    }
    
    return createJsonResponse(true, `Complete folder structure created: ${shipName}`, {
      ship_folder_id: shipFolder.getId(),
      ship_folder_name: shipFolder.getName(),
      subfolder_ids: subfolderIds,
      categories_created: Object.keys(folderStructure).length,
      total_subfolders_created: totalSubfoldersCreated,
      structure_type: "dynamic",
      company_id: companyId
    });
    
  } catch (error) {
    return createJsonResponse(false, `Dynamic folder creation failed: ${error.toString()}`);
  }
}

/**
 * Upload file with folder creation (Multi Cert Upload compatible)
 */
function handleUploadFileWithFolderCreation(requestData) {
  try {
    // Extract parameters (compatible with backend Multi Cert Upload)
    const shipName = requestData.ship_name;
    const category = requestData.category; // "Certificates", "Survey Reports", etc.
    const filename = requestData.filename;
    const fileContent = requestData.file_content; // base64
    const contentType = requestData.content_type || 'application/pdf';
    const parentFolderId = requestData.parent_folder_id;
    
    if (!shipName || !category || !filename || !fileContent) {
      return createJsonResponse(false, "Missing required parameters: ship_name, category, filename, file_content");
    }
    
    if (!parentFolderId) {
      return createJsonResponse(false, "Parent folder ID not available. Please configure Google Drive settings.");
    }
    
    // Get parent folder
    const parentFolder = DriveApp.getFolderById(parentFolderId);
    
    // Find ship folder (should exist from ship creation)
    const shipFolder = findFolderByName(parentFolder, shipName);
    if (!shipFolder) {
      return createJsonResponse(false, `Ship folder '${shipName}' not found. Please create ship first using 'Add New Ship'.`);
    }
    
    // Map category to correct parent folder based on Homepage Sidebar structure
    let parentCategoryFolder;
    let targetCategory = category;
    
    // Categories that belong under "Document Portfolio"
    const documentPortfolioCategories = [
      "Certificates", "Inspection Records", "Survey Reports", 
      "Drawings & Manuals", "Other Documents"
    ];
    
    if (documentPortfolioCategories.includes(category)) {
      // Find Document Portfolio folder
      parentCategoryFolder = findFolderByName(shipFolder, "Document Portfolio");
      if (!parentCategoryFolder) {
        return createJsonResponse(false, `Document Portfolio folder not found in ship '${shipName}'. Please ensure ship folder structure is created properly.`);
      }
    } else {
      // For other categories (Crew Records, ISM Records, etc.), they're direct under ship folder
      parentCategoryFolder = shipFolder;
    }
    
    // Find target category folder within the parent category folder
    const categoryFolder = findFolderByName(parentCategoryFolder, targetCategory);
    if (!categoryFolder) {
      return createJsonResponse(false, `Category folder '${targetCategory}' not found in the expected location. Please check folder structure.`);
    }
    
    // Decode base64 file content
    let binaryData;
    try {
      binaryData = Utilities.base64Decode(fileContent);
    } catch (decodeError) {
      return createJsonResponse(false, `Failed to decode file content: ${decodeError.toString()}`);
    }
    
    // Create blob and upload file
    const blob = Utilities.newBlob(binaryData, contentType, filename);
    const uploadedFile = categoryFolder.createFile(blob);
    
    // Return the correct folder path based on structure
    const folderPath = documentPortfolioCategories.includes(category) 
      ? `${shipName}/Document Portfolio/${category}`
      : `${shipName}/${category}`;
    
    return createJsonResponse(true, `File uploaded successfully: ${filename}`, {
      file_id: uploadedFile.getId(),
      file_name: uploadedFile.getName(),
      file_url: uploadedFile.getUrl(),
      folder_path: folderPath,
      upload_timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    return createJsonResponse(false, `File upload failed: ${error.toString()}`);
  }
}

/**
 * Check if ship folder structure exists
 */
function handleCheckShipFolderExists(requestData) {
  try {
    const parentFolderId = requestData.parent_folder_id;
    const shipName = requestData.ship_name;
    
    if (!parentFolderId || !shipName) {
      return createJsonResponse(false, "Missing required parameters: parent_folder_id, ship_name");
    }
    
    // Get parent folder
    const parentFolder = DriveApp.getFolderById(parentFolderId);
    
    // Check if ship folder exists
    const shipFolder = findFolderByName(parentFolder, shipName);
    
    if (!shipFolder) {
      return createJsonResponse(true, "Ship folder not found", {
        folder_exists: false,
        ship_name: shipName
      });
    }
    
    // Get available categories
    const categories = [];
    const subfolders = shipFolder.getFolders();
    while (subfolders.hasNext()) {
      const subfolder = subfolders.next();
      categories.push(subfolder.getName());
    }
    
    return createJsonResponse(true, "Ship folder structure found", {
      folder_exists: true,
      ship_folder_id: shipFolder.getId(),
      ship_name: shipName,
      available_categories: categories,
      subfolder_count: categories.length
    });
    
  } catch (error) {
    return createJsonResponse(false, `Folder check failed: ${error.toString()}`);
  }
}

/**
 * Helper: Find or create folder
 */
function findOrCreateFolder(parentFolder, folderName) {
  // First try to find existing folder
  const existingFolder = findFolderByName(parentFolder, folderName);
  if (existingFolder) {
    return existingFolder;
  }
  
  // Create new folder if not found
  return parentFolder.createFolder(folderName);
}

/**
 * Helper: Find folder by name
 */
function findFolderByName(parentFolder, folderName) {
  const folders = parentFolder.getFoldersByName(folderName);
  return folders.hasNext() ? folders.next() : null;
}

/**
 * Helper: Get default parent folder ID (fallback)
 * In production, this should be configurable
 */
function getDefaultParentFolderId() {
  // This would need to be configured based on your Google Drive setup
  // For now, return null to force explicit configuration
  return null;
}

/**
 * Utility: Test all functions (for debugging)
 */
function testAllFunctions() {
  console.log("Testing Apps Script functions...");
  
  // Test connection
  const testConn = handleTestConnection({folder_id: "your-folder-id-here"});
  console.log("Test Connection:", testConn);
  
  // Test folder creation
  const testCreate = handleCreateCompleteShipStructure({
    parent_folder_id: "your-folder-id-here",
    ship_name: "TEST SHIP",
    company_id: "test-company"
  });
  console.log("Test Creation:", testCreate);
  
  console.log("All tests completed!");
}