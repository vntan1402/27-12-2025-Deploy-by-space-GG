# 🚀 STEP-BY-STEP Apps Script Deployment

## ⚠️ Syntax Error Fix
The error "Invalid or unexpected token line: 11" is fixed in the clean version.

## 📋 Complete Deployment Steps

### Step 1: Access Google Apps Script
1. Go to **https://script.google.com/**
2. Sign in with your Google account
3. Open your existing project OR create new project

### Step 2: Replace Code Completely
1. **Select ALL existing code** in Code.gs (Ctrl+A)
2. **Delete everything** (Delete key)
3. **Copy the COMPLETE clean code below**:

```javascript
/**
 * Ship Management System - Clean Apps Script v3.1
 * Multi Cert Upload with Correct Folder Structure
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
      return createJsonResponse(true, "Ship Management Apps Script v3.1 is WORKING!", {
        version: "3.1-correct-folder-structure",
        timestamp: new Date().toISOString(),
        supported_actions: [
          "test_connection", 
          "create_complete_ship_structure", 
          "upload_file_with_folder_creation",
          "check_ship_folder_exists"
        ]
      });
    }
    
    var action = requestData.action || "default";
    
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
    return createJsonResponse(false, "Error: " + error.toString());
  }
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

function handleTestConnection(requestData) {
  try {
    var folderId = requestData.folder_id;
    
    if (!folderId) {
      return createJsonResponse(false, "Missing folder_id parameter");
    }
    
    var folder = DriveApp.getFolderById(folderId);
    var folderName = folder.getName();
    
    return createJsonResponse(true, "Connection successful", {
      folder_name: folderName,
      folder_id: folderId,
      test_result: "PASSED"
    });
    
  } catch (error) {
    return createJsonResponse(false, "Connection test failed: " + error.toString());
  }
}

function handleCreateCompleteShipStructure(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    var companyId = requestData.company_id;
    
    if (!parentFolderId || !shipName) {
      return createJsonResponse(false, "Missing required parameters: parent_folder_id, ship_name");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findOrCreateFolder(parentFolder, shipName);
    
    // CORRECT folder structure matching Homepage Sidebar
    var folderStructure = {
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
    
    var subfolderIds = {};
    var totalSubfoldersCreated = 0;
    
    for (var mainCategory in folderStructure) {
      var mainFolder = findOrCreateFolder(shipFolder, mainCategory);
      subfolderIds[mainCategory] = mainFolder.getId();
      
      var subCategories = folderStructure[mainCategory];
      var subcategoryIds = {};
      
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
      structure_type: "homepage_sidebar_compliant",
      company_id: companyId
    });
    
  } catch (error) {
    return createJsonResponse(false, "Folder creation failed: " + error.toString());
  }
}

function handleUploadFileWithFolderCreation(requestData) {
  try {
    var shipName = requestData.ship_name;
    var category = requestData.category;
    var filename = requestData.filename;
    var fileContent = requestData.file_content;
    var contentType = requestData.content_type || 'application/pdf';
    var parentFolderId = requestData.parent_folder_id;
    
    if (!shipName || !category || !filename || !fileContent) {
      return createJsonResponse(false, "Missing required parameters: ship_name, category, filename, file_content");
    }
    
    if (!parentFolderId) {
      return createJsonResponse(false, "Parent folder ID not available");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findFolderByName(parentFolder, shipName);
    
    if (!shipFolder) {
      return createJsonResponse(false, "Ship folder '" + shipName + "' not found. Please create ship first.");
    }
    
    // Categories under Document Portfolio
    var documentPortfolioCategories = [
      "Certificates", "Inspection Records", "Survey Reports", 
      "Drawings & Manuals", "Other Documents"
    ];
    
    var parentCategoryFolder;
    var folderPath;
    
    if (documentPortfolioCategories.indexOf(category) !== -1) {
      // Find Document Portfolio folder
      parentCategoryFolder = findFolderByName(shipFolder, "Document Portfolio");
      if (!parentCategoryFolder) {
        return createJsonResponse(false, "Document Portfolio folder not found in ship '" + shipName + "'");
      }
      folderPath = shipName + "/Document Portfolio/" + category;
    } else {
      // Direct under ship folder
      parentCategoryFolder = shipFolder;
      folderPath = shipName + "/" + category;
    }
    
    // Find target category folder
    var categoryFolder = findFolderByName(parentCategoryFolder, category);
    if (!categoryFolder) {
      return createJsonResponse(false, "Category folder '" + category + "' not found");
    }
    
    // Decode and upload
    var binaryData = Utilities.base64Decode(fileContent);
    var blob = Utilities.newBlob(binaryData, contentType, filename);
    var uploadedFile = categoryFolder.createFile(blob);
    
    return createJsonResponse(true, "File uploaded successfully: " + filename, {
      file_id: uploadedFile.getId(),
      file_name: uploadedFile.getName(),
      file_url: uploadedFile.getUrl(),
      folder_path: folderPath,
      upload_timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    return createJsonResponse(false, "File upload failed: " + error.toString());
  }
}

function handleCheckShipFolderExists(requestData) {
  try {
    var parentFolderId = requestData.parent_folder_id;
    var shipName = requestData.ship_name;
    
    if (!parentFolderId || !shipName) {
      return createJsonResponse(false, "Missing required parameters");
    }
    
    var parentFolder = DriveApp.getFolderById(parentFolderId);
    var shipFolder = findFolderByName(parentFolder, shipName);
    
    if (!shipFolder) {
      return createJsonResponse(true, "Ship folder not found", {
        folder_exists: false,
        ship_name: shipName
      });
    }
    
    var categories = [];
    var subfolders = shipFolder.getFolders();
    while (subfolders.hasNext()) {
      var subfolder = subfolders.next();
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
    return createJsonResponse(false, "Folder check failed: " + error.toString());
  }
}

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
```

### Step 3: Save and Deploy
1. **Save**: Press **Ctrl+S** or click **Save** button
2. **Deploy**: Click **Deploy** → **New deployment**
3. **Configure deployment**:
   - Type: **Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
4. **Click Deploy**
5. **Authorize permissions** (click Allow for all)
6. **Copy the new Web App URL**

### Step 4: Update Ship Management System
1. Login as admin1
2. Go to **System Settings** → **Company Google Drive Configuration**
3. Paste the new Web App URL
4. Click **Test Connection** → should show **PASSED**

## 🎯 Expected Result After Deployment

### ✅ Correct Folder Structure Created:
```
Ship Name/
├── Document Portfolio/          ← Certificates go HERE
│   ├── Certificates/           ← Target for certificate uploads
│   ├── Inspection Records/
│   ├── Survey Reports/
│   ├── Drawings & Manuals/
│   └── Other Documents/
├── Crew Records/
├── ISM Records/
├── ISPS Records/
├── MLC Records/
└── Supplies/
```

### ✅ Certificate Upload Path:
**Certificate files will upload to: `Ship Name/Document Portfolio/Certificates/`**

## 🧪 Quick Test After Deployment
1. Create a new ship
2. Check if **Document Portfolio** folder is created
3. Upload a certificate via Multi Cert Upload
4. Verify file goes to **Ship Name/Document Portfolio/Certificates/**

---

**🚢 This fixes the folder structure to match your Homepage Sidebar exactly!**