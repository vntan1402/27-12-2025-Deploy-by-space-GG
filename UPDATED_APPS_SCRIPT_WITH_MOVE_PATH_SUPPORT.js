/**
 * UPDATED: MOVE FILE function with folder path support
 * Supports both target_folder_id and target_folder_path
 */

/**
 * MOVE FILE - Updated to support folder path
 */
function handleMoveFile(requestData) {
  try {
    Logger.log("📦 Starting file move operation...");
    
    var fileId = requestData.file_id;
    var targetFolderId = requestData.target_folder_id;
    var targetFolderPath = requestData.target_folder_path;
    var parentFolderId = requestData.parent_folder_id; // Root folder for path resolution
    
    Logger.log("📋 Move parameters:");
    Logger.log("   File ID: " + fileId);
    Logger.log("   Target Folder ID: " + targetFolderId);
    Logger.log("   Target Folder Path: " + targetFolderPath);
    Logger.log("   Parent Folder ID: " + parentFolderId);
    
    if (!fileId) {
      return createResponse(false, "Missing file_id");
    }
    
    if (!targetFolderId && !targetFolderPath) {
      return createResponse(false, "Missing target_folder_id or target_folder_path");
    }
    
    // Get the file
    var file;
    try {
      file = DriveApp.getFileById(fileId);
      Logger.log("✅ File found: " + file.getName());
    } catch (e) {
      Logger.log("❌ File not found: " + fileId);
      return createResponse(false, "File not found: " + fileId);
    }
    
    // Get target folder (either by ID or by creating path)
    var targetFolder;
    
    if (targetFolderId) {
      // Use folder ID directly
      try {
        targetFolder = DriveApp.getFolderById(targetFolderId);
        Logger.log("✅ Target folder found by ID: " + targetFolder.getName());
      } catch (e) {
        Logger.log("❌ Target folder not found: " + targetFolderId);
        return createResponse(false, "Target folder not found: " + targetFolderId);
      }
    } else if (targetFolderPath) {
      // Find or create folder from path
      Logger.log("🔍 Resolving folder path: " + targetFolderPath);
      
      // Get root folder (parent_folder_id or My Drive root)
      var rootFolder;
      if (parentFolderId) {
        try {
          rootFolder = DriveApp.getFolderById(parentFolderId);
          Logger.log("✅ Using parent folder: " + rootFolder.getName());
        } catch (e) {
          Logger.log("❌ Parent folder not found, using My Drive root");
          rootFolder = DriveApp.getRootFolder();
        }
      } else {
        Logger.log("ℹ️ No parent folder specified, using My Drive root");
        rootFolder = DriveApp.getRootFolder();
      }
      
      // Split path and create/find folders
      var pathParts = targetFolderPath.split('/');
      Logger.log("📂 Path parts: " + JSON.stringify(pathParts));
      
      targetFolder = createFolderPathSafe(rootFolder, pathParts);
      
      if (!targetFolder) {
        Logger.log("❌ Failed to create/find target folder path");
        return createResponse(false, "Failed to create/find target folder: " + targetFolderPath);
      }
      
      Logger.log("✅ Target folder ready: " + targetFolder.getName() + " (ID: " + targetFolder.getId() + ")");
    }
    
    // Check if file is already in target folder
    var currentParents = file.getParents();
    var alreadyInTarget = false;
    
    while (currentParents.hasNext()) {
      var parent = currentParents.next();
      if (parent.getId() === targetFolder.getId()) {
        alreadyInTarget = true;
        Logger.log("ℹ️ File is already in target folder");
        break;
      }
    }
    
    if (!alreadyInTarget) {
      // Remove from current parents
      var parents = file.getParents();
      var removedFrom = [];
      
      while (parents.hasNext()) {
        var parent = parents.next();
        removedFrom.push(parent.getName());
        parent.removeFile(file);
      }
      
      Logger.log("📤 Removed file from: " + JSON.stringify(removedFrom));
      
      // Add to target folder
      targetFolder.addFile(file);
      Logger.log("📥 Added file to: " + targetFolder.getName());
    }
    
    Logger.log("✅ File moved successfully!");
    
    return createResponse(true, "File moved successfully", {
      file_id: fileId,
      file_name: file.getName(),
      target_folder_id: targetFolder.getId(),
      target_folder_name: targetFolder.getName(),
      target_folder_path: targetFolderPath || "N/A",
      already_in_target: alreadyInTarget,
      moved_timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    Logger.log("❌ Move failed: " + error.toString());
    Logger.log("Error stack: " + error.stack);
    return createResponse(false, "Move failed: " + error.toString());
  }
}

// Replace the existing handleMoveFile function in your Apps Script with this updated version
