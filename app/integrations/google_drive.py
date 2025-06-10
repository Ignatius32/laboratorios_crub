import requests
import json
import os
from flask import current_app

class GoogleDriveIntegration:
    """
    Class to handle Google Drive integration via Google Apps Script
    """
    
    def __init__(self):
        # Get Google Apps Script deployment URL from environment variables or config
        self.script_url = os.environ.get('GOOGLE_SCRIPT_URL')
        self.secure_token = os.environ.get('GOOGLE_DRIVE_SECURE_TOKEN', '1250')  # Use the same env var name as in Google Apps Script
        
        if not self.script_url:
            # Fallback or development URL if not set in environment
            self.script_url = current_app.config.get('GOOGLE_SCRIPT_URL', '')
    
    def create_laboratory_folders(self, lab_id, lab_name):
        """
        Creates folders in Google Drive for a laboratory
        
        Args:
            lab_id (str): The laboratory ID
            lab_name (str): The laboratory name
            
        Returns:
            dict: Dictionary with folder IDs or None if there was an error
        """
        if not self.script_url:
            current_app.logger.error("Google Script URL not configured")
            return None
            
        try:
            # Prepare the request data
            data = {
                'action': 'createLabFolders',
                'token': str(self.secure_token),  # Ensure token is a string
                'labId': lab_id,
                'labName': lab_name
            }
            
            # Log the request for debugging
            current_app.logger.info(f"Sending request to Google Script: {data}")
            
            # Send request to Google Apps Script
            response = requests.post(
                self.script_url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return {
                        'lab_folder_id': result.get('labFolderId'),
                        'movimientos_folder_id': result.get('movimientosFolderId')
                    }
                else:
                    current_app.logger.error(f"Drive API Error: {result.get('error')}")
                    return None
            else:
                current_app.logger.error(f"HTTP Error: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            current_app.logger.error(f"Exception in Google Drive integration: {str(e)}")
            return None
            
    def delete_laboratory_folders(self, folder_ids):
        """
        Deletes laboratory folders from Google Drive
        
        Args:
            folder_ids (dict): Dictionary containing folder IDs to delete
                - lab_folder_id: ID of the main laboratory folder
                - movimientos_folder_id: ID of the movements folder
                
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self.script_url:
            current_app.logger.error("Google Script URL not configured")
            return False
            
        # If folder IDs are None or empty, return True (nothing to delete)
        if not folder_ids or (not folder_ids.get('lab_folder_id') and not folder_ids.get('movimientos_folder_id')):
            current_app.logger.info("No folder IDs provided for deletion")
            return True
            
        try:
            # Prepare the request data
            data = {
                'action': 'deleteLabFolders',
                'token': str(self.secure_token),
                'labFolderId': folder_ids.get('lab_folder_id'),
                'movimientosFolderId': folder_ids.get('movimientos_folder_id')
            }
            
            # Log the request for debugging
            current_app.logger.info(f"Sending folder deletion request to Google Script: {data}")
            
            # Send request to Google Apps Script
            response = requests.post(
                self.script_url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    current_app.logger.info("Folders successfully deleted from Google Drive")
                    return True
                else:
                    current_app.logger.error(f"Drive API Error: {result.get('error')}")
                    return False
            else:                
                current_app.logger.error(f"HTTP Error: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Exception in Google Drive folder deletion: {str(e)}")
            return False
            
    def upload_movimiento_documento(self, lab_id, movimiento_id, file_data, file_name, file_type):
        """
        Uploads a document for a movement to Google Drive
        
        Args:
            lab_id (str): The laboratory ID
            movimiento_id (str): The movement ID
            file_data (str): Base64 encoded file data
            file_name (str): Original file name
            file_type (str): MIME type of the file
            
        Returns:
            dict: Dictionary with file ID and URL or None if there was an error
        """
        if not self.script_url:
            current_app.logger.error("Google Script URL not configured")
            return None
            
        try:
            # Get current date for folder name
            from datetime import datetime
            current_date = datetime.now().strftime('%Y-%m-%d')
            folder_name = f"{movimiento_id}_{current_date}"
            
            # Prepare the request data
            data = {
                'action': 'uploadMovimientoDocumento',
                'token': str(self.secure_token),
                'labId': lab_id,
                'folderName': folder_name,
                'fileName': file_name,
                'fileData': file_data,
                'fileType': file_type
            }
            
            # Log the request for debugging (excluding file data)
            log_data = {k: v for k, v in data.items() if k != 'fileData'}
            current_app.logger.info(f"Sending document upload request to Google Script: {log_data}")
            
            # Send request to Google Apps Script
            response = requests.post(
                self.script_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=60  # Longer timeout for file uploads
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return {
                        'file_id': result.get('fileId'),
                        'file_url': result.get('fileUrl')
                    }
                else:
                    current_app.logger.error(f"Drive API Error: {result.get('error')}")
                    return None
            else:
                current_app.logger.error(f"HTTP Error: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            current_app.logger.error(f"Exception in Google Drive document upload: {str(e)}")
            return None
            
    def send_email(self, to, subject, html_body, sender_name=None, reply_to=None):
        """
        Sends an email using the Google Apps Script
        
        Args:
            to (str): Recipient email address
            subject (str): Email subject
            html_body (str): HTML content of the email
            sender_name (str, optional): Name of the sender
            reply_to (str, optional): Reply-to email address
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.script_url:
            current_app.logger.error("Google Script URL not configured")
            return False
            
        try:
            # Prepare the request data
            data = {
                'action': 'sendEmail',
                'token': str(self.secure_token),
                'to': to,
                'subject': subject,
                'htmlBody': html_body
            }
            
            # Add optional parameters if provided
            if sender_name:
                data['senderName'] = sender_name
            if reply_to:
                data['replyTo'] = reply_to
            
            # Log the request for debugging
            current_app.logger.info(f"Sending email request to Google Script: {to}, subject: {subject}")
            
            # Send request to Google Apps Script
            response = requests.post(
                self.script_url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
              # Check response
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    current_app.logger.info(f"Email sent successfully to {to}")
                    return True
                else:
                    current_app.logger.error(f"Google Script Error: {result.get('error')}")
                    return False
            else:
                current_app.logger.error(f"HTTP Error: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Exception in email sending: {str(e)}")
            return False
            
    def upload_ficha_seguridad(self, producto_id, file_data, file_extension):
        """
        Uploads a safety datasheet file to Google Drive
        
        Args:
            producto_id (str): The product ID
            file_data (str): Base64 encoded file data
            file_extension (str): File extension (pdf, jpg, png, etc.)
            
        Returns:
            dict: Dictionary with file ID and URL or None if there was an error
        """
        if not self.script_url:
            current_app.logger.error("Google Script URL not configured")
            return None
            
        try:
            # Prepare the request data
            file_name = f"ficha_seg_{producto_id}.{file_extension}"
            
            data = {
                'action': 'uploadFichaSeguridad',
                'token': str(self.secure_token),
                'fileName': file_name,
                'fileData': file_data,
                'fileExtension': file_extension
            }
            
            # Log the request for debugging (excluding file data)
            log_data = {k: v for k, v in data.items() if k != 'fileData'}
            current_app.logger.info(f"Sending ficha seguridad upload request to Google Script: {log_data}")
            
            # Send request to Google Apps Script
            response = requests.post(
                self.script_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=60  # Longer timeout for file uploads
            )            # Check response
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    current_app.logger.info(f"Ficha de seguridad uploaded successfully: {file_name}")
                    return {
                        'file_id': result.get('fileId'),
                        'file_url': result.get('fileUrl')
                    }
                else:
                    error_msg = result.get('error', 'Unknown error')
                    current_app.logger.error(f"Drive API Error: {error_msg}")
                    return {'error': error_msg}
            else:
                error_msg = f"HTTP Error: {response.status_code}, Response: {response.text}"
                current_app.logger.error(error_msg)
                return {'error': error_msg}
                
        except Exception as e:
            error_msg = f"Exception in ficha seguridad upload: {str(e)}"
            current_app.logger.error(error_msg)
            return {'error': error_msg}
        
    def download_file(self, file_id):
        """
        Downloads a file from Google Drive using the Google Apps Script
        
        Args:
            file_id (str): The Google Drive file ID
            
        Returns:
            dict: Dictionary with file data and metadata or None if there was an error
        """
        if not self.script_url:
            current_app.logger.error("Google Script URL not configured")
            return None
            
        try:
            # Prepare the request data
            data = {
                'action': 'downloadFile',
                'token': str(self.secure_token),
                'fileId': file_id
            }
            
            # Log the request for debugging
            current_app.logger.info(f"Sending file download request to Google Script: {data}")
            
            # Send request to Google Apps Script
            response = requests.post(
                self.script_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=60  # Longer timeout for file downloads
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    current_app.logger.info(f"File downloaded successfully: {file_id}")
                    return {
                        'file_data': result.get('fileData'),  # Base64 encoded file data
                        'file_name': result.get('fileName'),
                        'mime_type': result.get('mimeType'),
                        'file_size': result.get('fileSize')
                    }
                else:
                    error_msg = result.get('error', 'Unknown error')
                    current_app.logger.error(f"Drive API Error: {error_msg}")
                    return {'error': error_msg}
            else:
                error_msg = f"HTTP Error: {response.status_code}, Response: {response.text}"
                current_app.logger.error(error_msg)
                return {'error': error_msg}
                
        except Exception as e:
            error_msg = f"Exception in file download: {str(e)}"
            current_app.logger.error(error_msg)
            return {'error': error_msg}

    def get_file_stream_url(self, file_id):
        """
        Gets a streaming URL for a file from Google Drive for direct embedding
        
        Args:
            file_id (str): The Google Drive file ID
            
        Returns:
            dict: Dictionary with streaming URL or None if there was an error
        """
        if not self.script_url:
            current_app.logger.error("Google Script URL not configured")
            return None
            
        try:
            # Prepare the request data
            data = {
                'action': 'getFileStreamUrl',
                'token': str(self.secure_token),
                'fileId': file_id
            }
            
            # Log the request for debugging
            current_app.logger.info(f"Sending file stream URL request to Google Script: {data}")
            
            # Send request to Google Apps Script
            response = requests.post(
                self.script_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    current_app.logger.info(f"File stream URL obtained successfully: {file_id}")
                    return {
                        'stream_url': result.get('streamUrl'),
                        'file_name': result.get('fileName'),
                        'mime_type': result.get('mimeType')
                    }
                else:
                    error_msg = result.get('error', 'Unknown error')
                    current_app.logger.error(f"Drive API Error: {error_msg}")
                    return {'error': error_msg}
            else:
                error_msg = f"HTTP Error: {response.status_code}, Response: {response.text}"
                current_app.logger.error(error_msg)
                return {'error': error_msg}
                
        except Exception as e:
            error_msg = f"Exception in getting file stream URL: {str(e)}"
            current_app.logger.error(error_msg)
            return {'error': error_msg}

# Create a singleton instance
drive_integration = GoogleDriveIntegration()