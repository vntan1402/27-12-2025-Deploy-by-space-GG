"""
Dual Apps Script Manager
Handles both System Apps Script (Document AI) and Company Apps Script (File Upload)
"""
import base64
import json
import logging
import aiohttp
from typing import Dict, Any, Optional, Tuple
from mongodb_database import mongo_db

logger = logging.getLogger(__name__)

class DualAppsScriptManager:
    """
    Manages calls to both System Apps Script and Company Apps Script
    - System Apps Script: Document AI processing only
    - Company Apps Script: File uploads to Company Google Drive
    """
    
    def __init__(self, company_id: str):
        self.company_id = company_id
        self.system_apps_script_url = None
        self.company_apps_script_url = None
        self.parent_folder_id = None
        # Configuration will be loaded when first needed
    
    async def _load_configuration(self):
        """Load Apps Script URLs from configuration"""
        try:
            # Get Document AI configuration (System Apps Script)
            ai_config = await mongo_db.find_one(
                "ai_config",
                {"id": "system_ai"}
            )
            
            if ai_config and ai_config.get("document_ai", {}).get("enabled"):
                self.system_apps_script_url = ai_config["document_ai"].get("apps_script_url")
                logger.info(f"✅ System Apps Script URL loaded for Document AI")
            
            # Get Company Google Drive configuration (Company Apps Script)
            gdrive_config = await mongo_db.find_one(
                "company_gdrive_config",
                {"company_id": self.company_id}
            )
            
            if gdrive_config:
                # Check for company_apps_script_url first, then fallback to web_app_url
                self.company_apps_script_url = gdrive_config.get("company_apps_script_url") or gdrive_config.get("web_app_url")
                self.parent_folder_id = gdrive_config.get("parent_folder_id") or gdrive_config.get("folder_id")
                if self.company_apps_script_url:
                    logger.info(f"✅ Company Apps Script URL loaded for file upload")
                else:
                    logger.warning("❌ Company Apps Script URL not configured")
                
                if self.parent_folder_id:
                    logger.info(f"✅ Company Google Drive Folder ID loaded: {self.parent_folder_id}")
                else:
                    logger.warning("❌ Company Google Drive Folder ID not configured")
            
        except Exception as e:
            logger.error(f"❌ Error loading Apps Script configuration: {e}")
    
    async def analyze_passport_with_dual_scripts(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str,
        ship_name: str,
        document_ai_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process passport using both Apps Scripts
        
        Args:
            file_content: Passport file content
            filename: File name
            content_type: MIME type
            ship_name: Ship name for folder structure
            document_ai_config: Document AI configuration
            
        Returns:
            dict: Combined results from both Apps Scripts
        """
        try:
            # Load configuration first
            await self._load_configuration()
            
            logger.info(f"🔄 Starting dual Apps Script processing for: {filename}")
            
            # Step 1: Document AI Analysis via System Apps Script
            logger.info("📡 Step 1: Document AI analysis via System Apps Script...")
            ai_result = await self._call_system_apps_script_for_ai(
                file_content, filename, content_type, document_ai_config
            )
            
            if not ai_result.get('success'):
                logger.error(f"❌ Document AI analysis failed: {ai_result.get('message')}")
                return {
                    'success': False,
                    'message': 'Document AI analysis failed',
                    'error': ai_result.get('message'),
                    'step': 'document_ai_analysis'
                }
            
            # Step 2: File Uploads via Company Apps Script
            logger.info("📁 Step 2: File uploads via Company Apps Script...")
            upload_result = await self._upload_files_via_company_script(
                file_content, filename, content_type, ship_name, ai_result
            )
            
            if not upload_result.get('success'):
                logger.error(f"❌ File upload failed: {upload_result.get('message')}")
                return {
                    'success': False,
                    'message': 'File upload failed',
                    'error': upload_result.get('message'),
                    'step': 'file_upload',
                    'ai_result': ai_result  # Still return AI results
                }
            
            # Combine results
            logger.info("✅ Dual Apps Script processing completed successfully")
            return {
                'success': True,
                'message': 'Passport processing completed successfully',
                'ai_analysis': ai_result,
                'file_uploads': upload_result,
                'processing_method': 'dual_apps_script',
                'workflow': 'system_ai_analysis + company_file_upload'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in dual Apps Script processing: {e}")
            return {
                'success': False,
                'message': f'Dual Apps Script processing failed: {str(e)}',
                'error': str(e)
            }
    
    async def _call_system_apps_script_for_ai(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str,
        document_ai_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call System Apps Script for Document AI processing only"""
        try:
            if not self.system_apps_script_url:
                raise ValueError("System Apps Script URL not configured")
            
            # Prepare payload for Document AI analysis only
            payload = {
                "action": "analyze_passport_document_ai",
                "file_content": base64.b64encode(file_content).decode('utf-8'),
                "filename": filename,
                "content_type": content_type,
                "project_id": document_ai_config.get("project_id"),
                "location": document_ai_config.get("location", "us"),
                "processor_id": document_ai_config.get("processor_id")
            }
            
            logger.info(f"📡 Calling System Apps Script for Document AI: {filename}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.system_apps_script_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ System Apps Script (Document AI) completed successfully")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ System Apps Script error: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'message': f'System Apps Script error: {response.status}',
                            'error': error_text
                        }
        
        except Exception as e:
            logger.error(f"❌ Error calling System Apps Script: {e}")
            return {
                'success': False,
                'message': f'System Apps Script call failed: {str(e)}',
                'error': str(e)
            }
    
    async def _upload_files_via_company_script(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str,
        ship_name: str,
        ai_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upload files via Company Apps Script"""
        try:
            if not self.company_apps_script_url:
                raise ValueError("Company Apps Script URL not configured")
            
            if not self.parent_folder_id:
                raise ValueError("Company Google Drive Folder ID not configured")
            
            upload_results = {}
            
            # Upload 1: Passport file to Ship/Crew records (using same method as certificates)
            logger.info(f"📤 Uploading passport file: {ship_name}/Crew records/{filename}")
            passport_upload = await self._call_company_apps_script({
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': self.parent_folder_id,
                'ship_name': ship_name,
                'parent_category': 'Crew Records',
                'category': 'Crew List',  # Use existing Crew List subcategory
                'filename': filename,
                'file_content': base64.b64encode(file_content).decode('utf-8'),
                'content_type': content_type
            })
            upload_results['passport'] = passport_upload
            
            # Upload 2: Summary file to SUMMARY folder
            if ai_result.get('success') and ai_result.get('data', {}).get('summary'):
                summary_content = ai_result['data']['summary']
                base_name = filename.rsplit('.', 1)[0]
                summary_filename = f"{base_name}_Summary.txt"
                
                logger.info(f"📋 Uploading summary file: SUMMARY/{summary_filename}")
                summary_upload = await self._call_company_apps_script({
                    'file_content': base64.b64encode(summary_content.encode('utf-8')).decode('utf-8'),
                    'filename': summary_filename,
                    'folder_path': "SUMMARY",
                    'content_type': 'text/plain',
                    'parent_folder_id': self.parent_folder_id
                })
                upload_results['summary'] = summary_upload
            
            # Check upload results
            passport_success = upload_results.get('passport', {}).get('success', False)
            summary_success = upload_results.get('summary', {}).get('success', False)
            
            if passport_success:
                logger.info("✅ All file uploads completed successfully")
                return {
                    'success': True,
                    'message': 'Files uploaded successfully to Company Google Drive',
                    'uploads': upload_results,
                    'upload_method': 'company_apps_script'
                }
            else:
                logger.error("❌ Passport file upload failed")
                return {
                    'success': False,
                    'message': 'File upload failed',
                    'uploads': upload_results,
                    'error': 'Passport upload failed'
                }
            
        except Exception as e:
            logger.error(f"❌ Error uploading files via Company Apps Script: {e}")
            return {
                'success': False,
                'message': f'Company file upload failed: {str(e)}',
                'error': str(e)
            }
    
    async def _call_company_apps_script(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP call to Company Apps Script"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.company_apps_script_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Company Apps Script error: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'message': f'Company Apps Script error: {response.status}',
                            'error': error_text
                        }
        
        except Exception as e:
            logger.error(f"❌ Error calling Company Apps Script: {e}")
            return {
                'success': False,
                'message': f'Company Apps Script call failed: {str(e)}',
                'error': str(e)
            }
    
    async def test_both_apps_scripts(self) -> Dict[str, Any]:
        """Test connectivity to both Apps Scripts"""
        # Load configuration first
        await self._load_configuration()
        
        results = {}
        
        # Test System Apps Script
        if self.system_apps_script_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self.system_apps_script_url,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results['system_apps_script'] = {
                                'success': True,
                                'url': self.system_apps_script_url,
                                'service': data.get('service', 'Unknown'),
                                'version': data.get('version', 'Unknown')
                            }
                        else:
                            results['system_apps_script'] = {
                                'success': False,
                                'url': self.system_apps_script_url,
                                'error': f"Status {response.status}"
                            }
            except Exception as e:
                results['system_apps_script'] = {
                    'success': False,
                    'url': self.system_apps_script_url,
                    'error': str(e)
                }
        else:
            results['system_apps_script'] = {
                'success': False,
                'error': 'URL not configured'
            }
        
        # Test Company Apps Script
        if self.company_apps_script_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self.company_apps_script_url,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results['company_apps_script'] = {
                                'success': True,
                                'url': self.company_apps_script_url,
                                'service': data.get('service', 'Unknown'),
                                'version': data.get('version', 'Unknown')
                            }
                        else:
                            results['company_apps_script'] = {
                                'success': False,
                                'url': self.company_apps_script_url,
                                'error': f"Status {response.status}"
                            }
            except Exception as e:
                results['company_apps_script'] = {
                    'success': False,
                    'url': self.company_apps_script_url,
                    'error': str(e)
                }
        else:
            results['company_apps_script'] = {
                'success': False,
                'error': 'URL not configured'
            }
        
        return results


def create_dual_apps_script_manager(company_id: str) -> DualAppsScriptManager:
    """Factory function to create DualAppsScriptManager"""
    return DualAppsScriptManager(company_id)