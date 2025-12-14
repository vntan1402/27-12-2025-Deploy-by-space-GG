/**
 * Dynamic Folder Structure Function
 * Fetches structure from backend API, falls back to Sidebar Main Categories
 */

function getFolderStructure(backendApiUrl) {
  // TRY: Call backend API to get dynamic structure
  if (backendApiUrl) {
    try {
      var response = UrlFetchApp.fetch(backendApiUrl + "/api/sidebar-structure", {
        method: 'GET',
        muteHttpExceptions: true,
        timeout: 10
      });
      
      if (response.getResponseCode() === 200) {
        var result = JSON.parse(response.getContentText());
        if (result.success && result.structure) {
          Logger.log("✅ Using dynamic structure from backend API");
          return result.structure;
        }
      }
    } catch (error) {
      Logger.log("⚠️ Failed to fetch dynamic structure: " + error.toString());
      // Fall through to default structure
    }
  }
  
  // FALLBACK: Default structure based on current Sidebar Main Categories
  // Matches MAIN_CATEGORIES from /app/frontend/src/utils/constants.js
  Logger.log("📁 Using fallback structure (Sidebar Main Categories)");
  return {
    "Class & Flag Cert": [],
    "Crew Records": [],
    "ISM - ISPS - MLC": [],
    "Safety Management System": [],
    "Technical Infor": [],
    "Supplies": []
  };
}

/**
 * Example usage in handleCreateCompleteShipStructure:
 */
function handleCreateCompleteShipStructure(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    var backendApiUrl = requestData.backend_api_url;
    
    if (!parentFolderId || !shipName) {
      return createJsonResponse(false, "Missing required parameters: parent_folder_id, ship_name");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findOrCreateFolder(parentFolder, shipName);
    
    // Get dynamic folder structure
    var folderStructure = getFolderStructure(backendApiUrl);
    
    var subfolderIds = {};
    var totalSubfoldersCreated = 0;
    
    // Create main category folders
    for (var mainCategory in folderStructure) {
      var mainFolder = findOrCreateFolder(shipFolder, mainCategory);
      subfolderIds[mainCategory] = mainFolder.getId();
      
      var subCategories = folderStructure[mainCategory];
      var subcategoryIds = {};
      
      // Create subcategory folders (if any)
      for (var i = 0; i < subCategories.length; i++) {
        var subCategory = subCategories[i];
        var subFolder = findOrCreateFolder(mainFolder, subCategory);
        subcategoryIds[subCategory] = subFolder.getId();
        totalSubfoldersCreated++;
      }
      
      subfolderIds[mainCategory + "_subcategories"] = subcategoryIds;
    }
    
    return createJsonResponse(true, "Complete folder structure created: " + shipName, {
      ship_folder_id: shipFolder.getId(),
      ship_folder_name: shipFolder.getName(),
      subfolder_ids: subfolderIds,
      categories_created: Object.keys(folderStructure).length,
      total_subfolders_created: totalSubfoldersCreated,
      structure_type: "sidebar_main_categories",
      backend_api_used: !!backendApiUrl
    });
    
  } catch (error) {
    return createJsonResponse(false, "Folder creation failed: " + error.toString());
  }
}

// Helper functions
function findOrCreateFolder(parentFolder, folderName) {
  var existingFolder = findFolderByName(parentFolder, folderName);
  if (existingFolder) {
    return existingFolder;
  }
  return parentFolder.createFolder(folderName);
}

function findFolderByName(parentFolder, folderName) {
  var folders = parentFolder.getFoldersByName(folderName);
  return folders.hasNext() ? folders.next() : null;
}

function createJsonResponse(success, message, data) {
  var response = {
    success: success,
    message: message,
    timestamp: new Date().toISOString()
  };
  
  if (data) {
    for (var key in data) {
      response[key] = data[key];
    }
  }
  
  return ContentService
    .createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}
