/**
 * Google Apps Script Update for Certificate Move Functionality
 * 
 * Add these functions to your existing Google Apps Script to support 
 * the new certificate move functionality in the Ship Management System.
 * 
 * This file contains the additional code needed to:
 * 1. Get folder structure for a ship
 * 2. Move files between folders
 */

/**
 * Get folder structure for a specific ship
 * @param {string} parentFolderId - The main company folder ID
 * @param {string} shipName - Name of the ship (optional)
 * @returns {Object} - Folder structure with IDs and names
 */
function getFolderStructure(parentFolderId, shipName = '') {
  try {
    Logger.log(`Getting folder structure for parent: ${parentFolderId}, ship: ${shipName}`);
    
    const parentFolder = DriveApp.getFolderById(parentFolderId);
    const folders = [];
    
    if (shipName) {
      // Get specific ship folder structure
      const shipFolders = parentFolder.getFoldersByName(shipName);
      
      if (shipFolders.hasNext()) {
        const shipFolder = shipFolders.next();
        Logger.log(`Found ship folder: ${shipFolder.getName()}`);
        
        // Get all subfolders in the ship folder
        const subFolders = shipFolder.getFolders();
        while (subFolders.hasNext()) {
          const folder = subFolders.next();
          folders.push({
            folder_id: folder.getId(),
            folder_name: folder.getName(),
            folder_path: `${shipName}/${folder.getName()}`,
            parent_id: shipFolder.getId()
          });
        }
        
        // Also add the main ship folder as an option
        folders.unshift({
          folder_id: shipFolder.getId(),
          folder_name: shipName,
          folder_path: shipName,
          parent_id: parentFolderId
        });
      } else {
        Logger.log(`Ship folder "${shipName}" not found`);
        return {
          success: false,
          message: `Ship folder "${shipName}" not found`,
          folders: []
        };
      }
    } else {
      // Get all ship folders
      const allFolders = parentFolder.getFolders();
      while (allFolders.hasNext()) {
        const folder = allFolders.next();
        folders.push({
          folder_id: folder.getId(),
          folder_name: folder.getName(),
          folder_path: folder.getName(),
          parent_id: parentFolderId
        });
        
        // Get subfolders of each ship
        const subFolders = folder.getFolders();
        while (subFolders.hasNext()) {
          const subFolder = subFolders.next();
          folders.push({
            folder_id: subFolder.getId(),
            folder_name: subFolder.getName(),
            folder_path: `${folder.getName()}/${subFolder.getName()}`,
            parent_id: folder.getId()
          });
        }
      }
    }
    
    Logger.log(`Found ${folders.length} folders`);
    return {
      success: true,
      folders: folders,
      total_count: folders.length
    };
    
  } catch (error) {
    Logger.log(`Error getting folder structure: ${error.toString()}`);
    return {
      success: false,
      message: `Error getting folder structure: ${error.toString()}`,
      folders: []
    };
  }
}

/**
 * Move a file to a different folder
 * @param {string} fileId - The ID of the file to move
 * @param {string} targetFolderId - The ID of the destination folder
 * @returns {Object} - Success status and details
 */
function moveFile(fileId, targetFolderId) {
  try {
    Logger.log(`Moving file ${fileId} to folder ${targetFolderId}`);
    
    // Get the file and target folder
    const file = DriveApp.getFileById(fileId);
    const targetFolder = DriveApp.getFolderById(targetFolderId);
    
    // Get current parent folders
    const currentParents = file.getParents();
    
    // Remove file from all current parent folders
    while (currentParents.hasNext()) {
      const currentParent = currentParents.next();
      Logger.log(`Removing file from folder: ${currentParent.getName()}`);
      currentParent.removeFile(file);
    }
    
    // Add file to target folder
    targetFolder.addFile(file);
    Logger.log(`File moved successfully to: ${targetFolder.getName()}`);
    
    return {
      success: true,
      message: `File moved successfully to ${targetFolder.getName()}`,
      file_id: fileId,
      target_folder_id: targetFolderId,
      target_folder_name: targetFolder.getName()
    };
    
  } catch (error) {
    Logger.log(`Error moving file: ${error.toString()}`);
    return {
      success: false,
      message: `Error moving file: ${error.toString()}`,
      file_id: fileId,
      target_folder_id: targetFolderId
    };
  }
}

/**
 * Updated doPost function to handle new actions
 * Add these cases to your existing doPost function
 */
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    Logger.log('Received request:', JSON.stringify(data));
    
    const action = data.action;
    
    // Add these new cases to your existing switch statement
    switch (action) {
      
      case 'get_folder_structure':
        const parentFolderId = data.parent_folder_id;
        const shipName = data.ship_name || '';
        
        if (!parentFolderId) {
          return ContentService
            .createTextOutput(JSON.stringify({
              success: false,
              message: 'parent_folder_id is required'
            }))
            .setMimeType(ContentService.MimeType.JSON);
        }
        
        const folderResult = getFolderStructure(parentFolderId, shipName);
        return ContentService
          .createTextOutput(JSON.stringify(folderResult))
          .setMimeType(ContentService.MimeType.JSON);
      
      case 'move_file':
        const fileId = data.file_id;
        const targetFolderId = data.target_folder_id;
        
        if (!fileId || !targetFolderId) {
          return ContentService
            .createTextOutput(JSON.stringify({
              success: false,
              message: 'file_id and target_folder_id are required'
            }))
            .setMimeType(ContentService.MimeType.JSON);
        }
        
        const moveResult = moveFile(fileId, targetFolderId);
        return ContentService
          .createTextOutput(JSON.stringify(moveResult))
          .setMimeType(ContentService.MimeType.JSON);
      
      // ... your existing cases (test_connection, create_folder_structure, upload_file, etc.)
      
      default:
        return ContentService
          .createTextOutput(JSON.stringify({
            success: false,
            message: 'Unknown action: ' + action
          }))
          .setMimeType(ContentService.MimeType.JSON);
    }
    
  } catch (error) {
    Logger.log('Error in doPost:', error.toString());
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        message: 'Server error: ' + error.toString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Test function to verify the new functionality works
 * You can run this in the Apps Script editor to test
 */
function testNewFunctions() {
  // Replace with your actual folder ID and ship name for testing
  const testParentFolderId = 'YOUR_PARENT_FOLDER_ID';
  const testShipName = 'TEST_SHIP_NAME';
  
  Logger.log('Testing folder structure retrieval...');
  const folderResult = getFolderStructure(testParentFolderId, testShipName);
  Logger.log('Folder result:', JSON.stringify(folderResult));
  
  // Uncomment to test file moving (replace with actual file and folder IDs)
  // const moveResult = moveFile('YOUR_TEST_FILE_ID', 'YOUR_TARGET_FOLDER_ID');
  // Logger.log('Move result:', JSON.stringify(moveResult));
}