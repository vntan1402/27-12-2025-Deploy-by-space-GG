/**
 * FIX for handleUploadFixed function
 * Replace the "Step 3: Determine target folder" section with this code
 */

// FIND THIS SECTION IN YOUR APPS SCRIPT (around line 125-165):
/*
    // Step 3: Determine target folder based on category structure
    var targetFolder;
    var folderPath;
    
    if (parentCategory && category) {
      // Nested structure: Ship/ParentCategory/Category
      Logger.log("📁 Creating nested structure: " + shipName + "/" + parentCategory + "/" + category);
      targetFolder = createFolderPathSafe(shipFolder, [parentCategory, category]);
      folderPath = shipName + "/" + parentCategory + "/" + category;
    }
*/

// REPLACE WITH THIS CODE:
// ============================================
// Step 3: Determine target folder based on category structure
var targetFolder;
var folderPath;

if (parentCategory && category) {
  // ✅ FIXED: Split parent_category by "/" to handle nested paths
  // Example: "Class & Flag Cert/Other Documents" → ["Class & Flag Cert", "Other Documents"]
  var parentCategoryParts = parentCategory.split('/').map(function(part) {
    return part.trim();
  }).filter(function(part) {
    return part.length > 0;
  });
  
  Logger.log("📁 Creating nested structure: " + shipName + "/" + parentCategory + "/" + category);
  Logger.log("   Parent parts: " + JSON.stringify(parentCategoryParts));
  
  // Combine parent parts with category
  var allParts = parentCategoryParts.concat([category]);
  Logger.log("   All folder parts: " + JSON.stringify(allParts));
  
  targetFolder = createFolderPathSafe(shipFolder, allParts);
  folderPath = shipName + "/" + parentCategory + "/" + category;
  
} else if (category) {
  // Single level: Ship/Category
  // IMPORTANT: Crew Records should upload directly to Ship/Crew Records, NOT Ship/Class & Flag Cert/Crew Records
  if (category === "Crew Records") {
    // Create direct path: Ship/Crew Records
    Logger.log("📁 Creating Crew Records: " + shipName + "/Crew Records");
    targetFolder = createFolderPathSafe(shipFolder, [category]);
    folderPath = shipName + "/Crew Records";
  } else if (category && !parentCategory) {
    // For other categories, try to find "Class & Flag Cert" parent category first (legacy compatibility)
    var classFlagFolder = findFolderByNameSafe(shipFolder, "Class & Flag Cert");
    if (classFlagFolder) {
      Logger.log("📁 Using Class & Flag Cert structure: " + shipName + "/Class & Flag Cert/" + category);
      targetFolder = findOrCreateFolderSafe(classFlagFolder, category);
      folderPath = shipName + "/Class & Flag Cert/" + category;
    } else {
      // Create direct single level
      Logger.log("📁 Creating single level: " + shipName + "/" + category);
      targetFolder = createFolderPathSafe(shipFolder, [category]);
      folderPath = shipName + "/" + category;
    }
  } else {
    Logger.log("📁 Creating single level: " + shipName + "/" + category);
    targetFolder = createFolderPathSafe(shipFolder, [category]);
    folderPath = shipName + "/" + category;
  }
} else {
  // Direct to ship folder
  Logger.log("📁 Using ship folder directly: " + shipName);
  targetFolder = shipFolder;
  folderPath = shipName;
}
// ============================================
