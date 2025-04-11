// Google Apps Script to handle folder creation in Google Drive
// This script needs to be deployed as a web app with execute permissions

// Root folder ID where all laboratory folders will be created
const ROOT_FOLDER_ID = "1N3u88Knrz1otgDVykS8iJVO5M5d3eshN";

/**
 * Main function that handles HTTP requests
 */
function doPost(e) {
  try {
    // Parse the request body
    const requestData = JSON.parse(e.postData.contents);
    console.log("Received request: " + JSON.stringify(requestData));
    
    // Get token from script properties
    const secureToken = PropertiesService.getScriptProperties().getProperty('GOOGLE_DRIVE_SECURE_TOKEN');
    console.log("Token from script properties: " + secureToken);
    
    // Validate token - direct comparison
    if (requestData.token !== secureToken) {
      console.error("Token validation failed. Received: " + requestData.token + ", Expected: " + secureToken);
      return createErrorResponse("Invalid security token");
    }      // Handle different actions
    if (requestData.action === "createLabFolders") {
      return handleCreateLabFolders(requestData);
    } else if (requestData.action === "deleteLabFolders") {
      return handleDeleteLabFolders(requestData);
    } else if (requestData.action === "uploadMovimientoDocumento") {
      return handleUploadMovimientoDocumento(requestData);
    } else if (requestData.action === "sendEmail") {
      return handleSendEmail(requestData);
    } else {
      return createErrorResponse("Unknown action");
    }
    
  } catch (error) {
    console.error("Error processing request: " + error);
    return createErrorResponse("Server error: " + error.toString());
  }
}

/**
 * Handles the creation of laboratory folders
 */
function handleCreateLabFolders(data) {
  // Validate required fields
  if (!data.labId || !data.labName) {
    return createErrorResponse("Missing required fields: labId and labName");
  }
  
  try {
    // Get the root folder
    const rootFolder = DriveApp.getFolderById(ROOT_FOLDER_ID);
    if (!rootFolder) {
      return createErrorResponse("Could not access root folder");
    }
    
    // Create main laboratory folder inside the root folder
    const labFolderName = "lab_" + data.labId;
    
    // Check if the folder already exists
    let labFolder = null;
    const existingFolders = rootFolder.getFoldersByName(labFolderName);
    if (existingFolders.hasNext()) {
      labFolder = existingFolders.next();
      console.log("Found existing lab folder: " + labFolderName);
    } else {
      // Create new folder
      labFolder = rootFolder.createFolder(labFolderName);
      console.log("Created new lab folder: " + labFolderName);
    }
    
    // Set description for the lab folder
    labFolder.setDescription(data.labName);
    
    // Create movements subfolder
    const movimientosFolderName = "movimientos_" + data.labId;
    
    // Check if movements subfolder already exists
    let movimientosFolder = null;
    const existingSubfolders = labFolder.getFoldersByName(movimientosFolderName);
    if (existingSubfolders.hasNext()) {
      movimientosFolder = existingSubfolders.next();
      console.log("Found existing movements folder: " + movimientosFolderName);
    } else {
      // Create new movements subfolder
      movimientosFolder = labFolder.createFolder(movimientosFolderName);
      console.log("Created new movements folder: " + movimientosFolderName);
    }
    
    // Return success with folder IDs
    return createSuccessResponse({
      labFolderId: labFolder.getId(),
      movimientosFolderId: movimientosFolder.getId()
    });
    
  } catch (error) {
    console.error("Error creating folders: " + error);
    return createErrorResponse("Error creating folders: " + error.toString());
  }
}

/**
 * Handles the deletion of laboratory folders
 */
function handleDeleteLabFolders(data) {
  // Validate required fields
  if (!data.labFolderId && !data.movimientosFolderId) {
    return createErrorResponse("Missing folder IDs for deletion");
  }
  
  try {
    let deletedFolders = [];
    
    // Delete movements folder first if provided
    if (data.movimientosFolderId) {
      try {
        const movimientosFolder = DriveApp.getFolderById(data.movimientosFolderId);
        movimientosFolder.setTrashed(true);
        deletedFolders.push("movements folder");
        console.log("Successfully deleted movements folder: " + data.movimientosFolderId);
      } catch (error) {
        console.error("Error deleting movements folder: " + error);
        // Continue with main folder deletion even if this fails
      }
    }
    
    // Delete the main laboratory folder if provided
    if (data.labFolderId) {
      try {
        const labFolder = DriveApp.getFolderById(data.labFolderId);
        labFolder.setTrashed(true);
        deletedFolders.push("lab folder");
        console.log("Successfully deleted lab folder: " + data.labFolderId);
      } catch (error) {
        console.error("Error deleting lab folder: " + error);
        // If we already deleted some folders but couldn't delete all, return partial success
        if (deletedFolders.length > 0) {
          return createSuccessResponse({
            message: "Partially deleted folders: " + deletedFolders.join(", ")
          });
        }
        return createErrorResponse("Error deleting lab folder: " + error.toString());
      }
    }
    
    // Return success response
    return createSuccessResponse({
      message: "Successfully deleted folders: " + deletedFolders.join(", ")
    });
    
  } catch (error) {
    console.error("Error in folder deletion: " + error);
    return createErrorResponse("Error in folder deletion: " + error.toString());
  }
}

/**
 * Creates a successful response
 */
function createSuccessResponse(data) {
  return ContentService.createTextOutput(JSON.stringify({
    success: true,
    ...data
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Creates an error response
 */
function createErrorResponse(errorMessage) {
  return ContentService.createTextOutput(JSON.stringify({
    success: false,
    error: errorMessage
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Handles uploading a document for a movement and storing it in a dedicated folder
 */
function handleUploadMovimientoDocumento(data) {
  // Validate required fields
  if (!data.labId || !data.folderName || !data.fileName || !data.fileData || !data.fileType) {
    return createErrorResponse("Missing required fields for document upload");
  }
  
  try {
    // First, get the movements folder for this lab
    const labFolderName = "lab_" + data.labId;
    const movimientosFolderName = "movimientos_" + data.labId;
    
    // Get the root folder
    const rootFolder = DriveApp.getFolderById(ROOT_FOLDER_ID);
    if (!rootFolder) {
      return createErrorResponse("Could not access root folder");
    }
    
    // Find the lab folder
    let labFolder = null;
    const labFolders = rootFolder.getFoldersByName(labFolderName);
    if (labFolders.hasNext()) {
      labFolder = labFolders.next();
    } else {
      return createErrorResponse("Laboratory folder does not exist");
    }
    
    // Find the movements folder
    let movimientosFolder = null;
    const movimientosFolders = labFolder.getFoldersByName(movimientosFolderName);
    if (movimientosFolders.hasNext()) {
      movimientosFolder = movimientosFolders.next();
    } else {
      return createErrorResponse("Movements folder does not exist");
    }
    
    // Create or get the specific movement folder with format "movimiento+fecha"
    let movimientoSpecificFolder = null;
    const specificFolders = movimientosFolder.getFoldersByName(data.folderName);
    
    if (specificFolders.hasNext()) {
      movimientoSpecificFolder = specificFolders.next();
      console.log("Found existing specific movement folder: " + data.folderName);
    } else {
      // Create new specific movement folder
      movimientoSpecificFolder = movimientosFolder.createFolder(data.folderName);
      console.log("Created new specific movement folder: " + data.folderName);
    }
    
    // Process and create the file
    const fileBlob = Utilities.newBlob(
      Utilities.base64Decode(data.fileData),
      data.fileType,
      data.fileName
    );
    
    // Create the file in the specific movement folder
    const file = movimientoSpecificFolder.createFile(fileBlob);
    console.log("Created file: " + file.getName() + " in folder: " + data.folderName);
    
    // Return success with file info
    return createSuccessResponse({
      fileId: file.getId(),
      fileUrl: file.getUrl()
    });
    
  } catch (error) {
    console.error("Error uploading document: " + error);
    return createErrorResponse("Error uploading document: " + error.toString());
  }
}

/**
 * Handles sending emails through Gmail
 */
function handleSendEmail(data) {
  // Validate required fields
  if (!data.to || !data.subject || !data.htmlBody) {
    return createErrorResponse("Missing required email fields: to, subject, and htmlBody");
  }
  
  try {
    // Send the email using GmailApp
    GmailApp.sendEmail(
      data.to,
      data.subject,
      "", // Plain text body (empty because we're using HTML)
      {
        htmlBody: data.htmlBody,
        name: data.senderName || "Sistema de Gestión de Laboratorios CRUB",
        replyTo: data.replyTo || "no-reply@crub.edu.ar"
      }
    );
    
    // Return success
    return createSuccessResponse({
      message: "Email sent successfully to " + data.to
    });
    
  } catch (error) {
    console.error("Error sending email: " + error);
    return createErrorResponse("Error sending email: " + error.toString());
  }
}

/**
 * Handles GET requests - useful for testing
 */
function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "active",
    message: "The Google Drive integration service is running"
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Helper function to set up script properties - Run this once to set up your environment
 * This should be run manually from the Apps Script editor when setting up
 */
function setupEnvironment() {
  const scriptProperties = PropertiesService.getScriptProperties();
  scriptProperties.setProperty("GOOGLE_DRIVE_SECURE_TOKEN", "1250");
  Logger.log("Environment setup complete!");
}