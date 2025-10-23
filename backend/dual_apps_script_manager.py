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
                logger.info(f"   URL: {self.system_apps_script_url}")
            
            # Get Company Google Drive configuration (Company Apps Script)
            gdrive_config = await mongo_db.find_one(
                "company_gdrive_config",
                {"company_id": self.company_id}
            )
            
            if gdrive_config:
                # Check for web_app_url first (frontend saves here), then fallback to company_apps_script_url
                self.company_apps_script_url = gdrive_config.get("web_app_url") or gdrive_config.get("company_apps_script_url")
                self.parent_folder_id = gdrive_config.get("parent_folder_id") or gdrive_config.get("folder_id")
                if self.company_apps_script_url:
                    logger.info(f"✅ Company Apps Script URL loaded for file upload")
                    logger.info(f"   URL: {self.company_apps_script_url}")
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
        document_ai_config: Dict[str, Any],
        action: str = "analyze_passport_document_ai"  # Default to passport for backward compatibility
    ) -> Dict[str, Any]:
        """
        Call System Apps Script for Document AI processing only
        
        Args:
            action: Apps Script action to call
                - "analyze_passport_document_ai" for passports
                - "analyze_maritime_document_ai" for survey reports / maritime documents
        """
        try:
            if not self.system_apps_script_url:
                raise ValueError("System Apps Script URL not configured")
            
            # Prepare payload for Document AI analysis only
            payload = {
                "action": action,  # Use dynamic action instead of hardcoded
                "file_content": base64.b64encode(file_content).decode('utf-8'),
                "filename": filename,
                "content_type": content_type,
                "project_id": document_ai_config.get("project_id"),
                "location": document_ai_config.get("location", "us"),
                "processor_id": document_ai_config.get("processor_id")
            }
            
            logger.info(f"📡 Calling System Apps Script for Document AI: {filename} (action: {action})")
            
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
            
            # Upload 1: Passport file to Ship/Crew Records (direct, no subcategory)
            logger.info(f"📤 Uploading passport file: {ship_name}/Crew Records/{filename}")
            passport_upload = await self._call_company_apps_script({
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': self.parent_folder_id,
                'ship_name': ship_name,
                'category': 'Crew Records',  # Upload directly to Crew Records (no parent_category)
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
                
                logger.info(f"📋 Uploading summary file: SUMMARY/Crew Records/{summary_filename}")
                # For summary, upload to SUMMARY/Crew Records folder
                summary_upload = await self._call_company_apps_script({
                    'action': 'upload_file_with_folder_creation',
                    'parent_folder_id': self.parent_folder_id,
                    'ship_name': 'SUMMARY',  # Use SUMMARY as "ship_name" to create root-level SUMMARY folder
                    'category': 'Crew Records',  # Create Crew Records subfolder inside SUMMARY
                    'filename': summary_filename,
                    'file_content': base64.b64encode(summary_content.encode('utf-8')).decode('utf-8'),
                    'content_type': 'text/plain'
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
            logger.info(f"🌐 Calling Company Apps Script: action={payload.get('action')}")
            logger.info(f"   URL: {self.company_apps_script_url}")
            logger.info(f"   Ship Name: {payload.get('ship_name')}")
            logger.info(f"   Category: {payload.get('category')}")
            logger.info(f"   Filename: {payload.get('filename')}")
            logger.info(f"   Parent Folder ID: {payload.get('parent_folder_id')}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.company_apps_script_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Company Apps Script response: success={result.get('success')}, message={result.get('message', 'N/A')[:100]}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Company Apps Script HTTP error: {response.status} - {error_text[:200]}")
                        return {
                            'success': False,
                            'message': f'Company Apps Script error: {response.status}',
                            'error': error_text
                        }
        
        except Exception as e:
            logger.error(f"❌ Error calling Company Apps Script: {e}")
            logger.error(f"   Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
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
    
    async def analyze_certificate_with_dual_scripts(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        ship_name: str,
        document_ai_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process crew certificate using both Apps Scripts
        Similar to passport but for certificates
        
        Args:
            file_content: Certificate file content
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
            
            logger.info(f"🔄 Starting dual Apps Script processing for certificate: {filename}")
            
            # Step 1: Document AI Analysis via System Apps Script
            logger.info("📡 Step 1: Certificate analysis via System Apps Script...")
            ai_result = await self._call_system_apps_script_for_certificate_ai(
                file_content, filename, content_type, document_ai_config
            )
            
            if not ai_result.get('success'):
                logger.error(f"❌ Certificate Document AI analysis failed: {ai_result.get('message')}")
                return {
                    'success': False,
                    'message': 'Certificate Document AI analysis failed',
                    'error': ai_result.get('message'),
                    'step': 'document_ai_analysis'
                }
            
            # Step 2: File Upload via Company Apps Script
            logger.info("📁 Step 2: Certificate file upload via Company Apps Script...")
            upload_result = await self._upload_certificate_via_company_script(
                file_content, filename, content_type, ship_name, ai_result  # Pass ai_result for summary
            )
            
            if not upload_result.get('success'):
                logger.error(f"❌ Certificate file upload failed: {upload_result.get('message')}")
                return {
                    'success': False,
                    'message': 'Certificate file upload failed',
                    'error': upload_result.get('message'),
                    'step': 'file_upload',
                    'ai_result': ai_result  # Still return AI results
                }
            
            # Combine results
            logger.info("✅ Dual Apps Script processing completed successfully for certificate")
            return {
                'success': True,
                'message': 'Certificate processing completed successfully',
                'ai_analysis': ai_result,
                'file_uploads': upload_result,
                'processing_method': 'dual_apps_script',
                'workflow': 'system_ai_analysis + company_file_upload'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in dual Apps Script processing for certificate: {e}")
            return {
                'success': False,
                'message': f'Dual Apps Script processing failed: {str(e)}',
                'error': str(e)
            }
    
    async def _call_system_apps_script_for_certificate_ai(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        document_ai_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call System Apps Script for Certificate Document AI processing"""
        try:
            if not self.system_apps_script_url:
                raise ValueError("System Apps Script URL not configured")
            
            # Prepare payload for Document AI analysis (certificate)
            payload = {
                "action": "analyze_certificate_document_ai",  # ✅ Use certificate action
                "file_content": base64.b64encode(file_content).decode('utf-8'),
                "filename": filename,
                "content_type": content_type,
                "project_id": document_ai_config.get("project_id"),
                "location": document_ai_config.get("location", "us"),
                "processor_id": document_ai_config.get("processor_id")
            }
            
            logger.info(f"📡 Calling System Apps Script for Certificate Document AI: {filename}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.system_apps_script_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ System Apps Script (Certificate Document AI) completed successfully")
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
            logger.error(f"❌ Error calling System Apps Script for certificate: {e}")
            return {
                'success': False,
                'message': f'System Apps Script call failed: {str(e)}',
                'error': str(e)
            }
    
    async def _upload_certificate_via_company_script(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        ship_name: str,
        ai_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upload certificate file and summary via Company Apps Script (same as passport)"""
        try:
            if not self.company_apps_script_url:
                raise ValueError("Company Apps Script URL not configured")
            
            if not self.parent_folder_id:
                raise ValueError("Company Google Drive Folder ID not configured")
            
            upload_results = {}
            
            # Upload 1: Certificate file to Ship/Crew Records
            logger.info(f"📤 Uploading certificate file: {ship_name}/Crew Records/{filename}")
            cert_upload = await self._call_company_apps_script({
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': self.parent_folder_id,
                'ship_name': ship_name,
                'category': 'Crew Records',  # Upload directly to Crew Records
                'filename': filename,
                'file_content': base64.b64encode(file_content).decode('utf-8'),
                'content_type': content_type
            })
            upload_results['certificate'] = cert_upload
            
            # Upload 2: Summary file to SUMMARY folder (same as passport)
            if ai_result.get('success') and ai_result.get('data', {}).get('summary'):
                summary_content = ai_result['data']['summary']
                base_name = filename.rsplit('.', 1)[0]
                summary_filename = f"{base_name}_Summary.txt"
                
                logger.info(f"📋 Uploading certificate summary file: SUMMARY/Crew Records/{summary_filename}")
                # For summary, upload to SUMMARY/Crew Records folder
                summary_upload = await self._call_company_apps_script({
                    'action': 'upload_file_with_folder_creation',
                    'parent_folder_id': self.parent_folder_id,
                    'ship_name': 'SUMMARY',  # Use SUMMARY as "ship_name" to create root-level SUMMARY folder
                    'category': 'Crew Records',  # Create Crew Records subfolder inside SUMMARY
                    'filename': summary_filename,
                    'file_content': base64.b64encode(summary_content.encode('utf-8')).decode('utf-8'),
                    'content_type': 'text/plain'
                })
                upload_results['summary'] = summary_upload
            
            # Check upload results
            cert_success = upload_results.get('certificate', {}).get('success', False)
            summary_success = upload_results.get('summary', {}).get('success', False)
            
            if cert_success:
                logger.info("✅ All certificate file uploads completed successfully")
                return {
                    'success': True,
                    'message': 'Certificate files uploaded successfully to Company Google Drive',
                    'uploads': upload_results,
                    'upload_method': 'company_apps_script'
                }
            else:
                logger.error("❌ Certificate file upload failed")
                return {
                    'success': False,
                    'message': 'Certificate file upload failed',
                    'uploads': upload_results,
                    'error': 'Certificate upload failed'
                }
            
        except Exception as e:
            logger.error(f"❌ Error uploading certificate via Company Apps Script: {e}")
            return {
                'success': False,
                'message': f'Company file upload failed: {str(e)}',
                'error': str(e)
            }


    async def analyze_certificate_only(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        document_ai_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze certificate using Document AI WITHOUT uploading to Drive
        Used for batch processing where upload happens only after successful DB save
        
        Args:
            file_content: Certificate file content
            filename: File name
            content_type: MIME type
            document_ai_config: Document AI configuration
            
        Returns:
            dict: Analysis results only (no file IDs)
        """
        try:
            # Load configuration first
            await self._load_configuration()
            
            logger.info(f"🔄 Analyzing certificate (no upload): {filename}")
            
            # Document AI Analysis via System Apps Script ONLY
            logger.info("📡 Certificate analysis via System Apps Script...")
            ai_result = await self._call_system_apps_script_for_certificate_ai(
                file_content, filename, content_type, document_ai_config
            )
            
            if not ai_result.get('success'):
                logger.error(f"❌ Certificate Document AI analysis failed: {ai_result.get('message')}")
                return {
                    'success': False,
                    'message': 'Certificate Document AI analysis failed',
                    'error': ai_result.get('message'),
                    'step': 'document_ai_analysis'
                }
            
            logger.info("✅ Certificate analysis completed successfully (no upload)")
            return {
                'success': True,
                'message': 'Certificate analysis completed successfully',
                'ai_analysis': ai_result,
                'processing_method': 'analysis_only',
                'workflow': 'system_ai_analysis_without_upload'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in certificate analysis: {e}")
            return {
                'success': False,
                'message': f'Certificate analysis failed: {str(e)}',
                'error': str(e)
            }
    
    async def analyze_survey_report_only(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        document_ai_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze survey report using Document AI WITHOUT uploading to Drive
        Used for batch processing where upload happens only after successful DB save
        
        Args:
            file_content: Survey report file content
            filename: File name
            content_type: MIME type
            document_ai_config: Document AI configuration
            
        Returns:
            dict: Analysis results only (no file IDs)
        """
        try:
            # Load configuration first
            await self._load_configuration()
            
            logger.info(f"🔄 Analyzing survey report (no upload): {filename}")
            
            # Document AI Analysis via System Apps Script ONLY
            logger.info("📡 Survey report analysis via System Apps Script...")
            ai_result = await self._call_system_apps_script_for_ai(
                file_content=file_content,
                filename=filename,
                content_type=content_type,
                document_ai_config=document_ai_config,
                action="analyze_maritime_document_ai"  # Use maritime document action for survey reports
            )
            
            if not ai_result.get('success'):
                logger.error(f"❌ Survey Report Document AI analysis failed: {ai_result.get('message')}")
                return {
                    'success': False,
                    'message': 'Survey Report Document AI analysis failed',
                    'error': ai_result.get('message'),
                    'step': 'document_ai_analysis'
                }
            
            logger.info("✅ Survey report analysis completed successfully (no upload)")
            return {
                'success': True,
                'message': 'Survey report analysis completed successfully',
                'ai_analysis': ai_result,
                'processing_method': 'analysis_only',
                'workflow': 'system_ai_analysis_without_upload'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in survey report analysis: {e}")
            return {
                'success': False,
                'message': f'Survey report analysis failed: {str(e)}',
                'error': str(e)
            }
    


    # ========== TEST REPORT METHODS (NEW) ==========
    
    async def analyze_test_report_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = 'application/pdf',
        document_ai_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze test report file using Document AI
        Full workflow: analyze file and return extracted data
        """
        try:
            await self._load_configuration()
            
            logger.info(f"🔄 Analyzing test report: {filename}")
            
            # Use provided config or fallback to stored config
            if document_ai_config:
                doc_ai_config = document_ai_config
            else:
                doc_ai_config = self.config.get('document_ai_config', {})
            
            if not doc_ai_config or not doc_ai_config.get('project_id'):
                raise ValueError("Document AI configuration not found")
            
            # Determine content type
            content_type = 'application/pdf' if filename.lower().endswith('.pdf') else 'image/jpeg'
            
            # Call System Apps Script for Document AI analysis
            ai_result = await self._call_system_apps_script_for_ai(
                file_content=file_content,
                filename=filename,
                content_type=content_type,
                document_ai_config=doc_ai_config,
                action="analyze_maritime_document_ai"  # Use maritime document action
            )
            
            if not ai_result.get('success'):
                logger.error(f"❌ Test Report Document AI analysis failed")
                return {}
            
            # Extract summary text and other fields
            # DEBUG: Log the full ai_result structure
            logger.info(f"📋 Document AI result keys: {list(ai_result.keys())}")
            if 'ai_analysis' in ai_result:
                logger.info(f"📋 ai_analysis keys: {list(ai_result['ai_analysis'].keys())}")
            
            summary_text = ai_result.get('data', {}).get('summary', '')
            
            if not summary_text:
                logger.warning(f"⚠️ No summary_text in response. Full ai_result: {json.dumps(ai_result, indent=2)[:500]}")
            
            logger.info("✅ Test report analysis completed successfully")
            return {
                'summary_text': summary_text,
                'confidence_score': ai_result.get('ai_analysis', {}).get('confidence_score', 0.0)
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing test report: {e}")
            raise
    
    async def analyze_test_report_only(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = 'application/pdf',
        document_ai_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze test report using Document AI WITHOUT uploading to Drive
        Used for batch processing (PDF splitting)
        
        Args:
            file_content: Test report file content
            filename: File name
            content_type: Content type (default: application/pdf)
            document_ai_config: Document AI configuration dict (optional)
            
        Returns:
            dict: Analysis results only (no file IDs)
        """
        try:
            await self._load_configuration()
            
            logger.info(f"🔄 Analyzing test report (no upload): {filename}")
            
            # Use provided config or fallback to stored config
            if document_ai_config:
                doc_ai_config = document_ai_config
            else:
                doc_ai_config = self.config.get('document_ai_config', {})
            
            if not doc_ai_config or not doc_ai_config.get('project_id'):
                raise ValueError("Document AI configuration not found")
            
            # Determine content type
            content_type = 'application/pdf' if filename.lower().endswith('.pdf') else 'image/jpeg'
            
            # Document AI Analysis via System Apps Script ONLY
            logger.info("📡 Test report analysis via System Apps Script...")
            ai_result = await self._call_system_apps_script_for_ai(
                file_content=file_content,
                filename=filename,
                content_type=content_type,
                document_ai_config=doc_ai_config,
                action="analyze_maritime_document_ai"  # Use maritime document action
            )
            
            if not ai_result.get('success'):
                logger.error(f"❌ Test Report Document AI analysis failed: {ai_result.get('message')}")
                return {
                    'success': False,
                    'message': 'Test Report Document AI analysis failed',
                    'error': ai_result.get('message'),
                    'step': 'document_ai_analysis'
                }
            
            logger.info("✅ Test report analysis completed successfully (no upload)")
            return {
                'success': True,
                'message': 'Test report analysis completed successfully',
                'summary_text': ai_result.get('data', {}).get('summary', ''),
                'confidence_score': ai_result.get('ai_analysis', {}).get('confidence_score', 0.0),
                'processing_method': 'analysis_only',
                'workflow': 'system_ai_analysis_without_upload'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in test report analysis: {e}")
            return {
                'success': False,
                'message': f'Test report analysis failed: {str(e)}',
                'error': str(e)
            }
    
    async def upload_test_report_file(
        self,
        file_content: bytes,
        filename: str,
        ship_name: str,
        summary_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload test report files to Google Drive
        Path: Shipname > Class & Flag Cert > Test Report (original)
        Path: SUMMARY > Class & Flag Document (summary)
        
        Args:
            file_content: Test report file content
            filename: Test report filename
            ship_name: Ship name for folder structure
            summary_text: Summary text (optional)
            
        Returns:
            dict: Upload results with file IDs
        """
        try:
            await self._load_configuration()
            
            logger.info(f"📤 Uploading test report files to Google Drive: {filename}")
            
            # Determine content type
            content_type = 'application/pdf' if filename.lower().endswith('.pdf') else 'image/jpeg'
            
            # Call Company Apps Script for test report upload
            # Path structure: Shipname > Class & Flag Cert > Test Report
            upload_result = await self._call_apps_script_for_test_report_upload(
                file_content=file_content,
                filename=filename,
                content_type=content_type,
                ship_name=ship_name,
                summary_text=summary_text
            )
            
            if not upload_result.get('success'):
                logger.error(f"❌ Test report file upload failed")
                return upload_result
            
            # Extract file ID from Apps Script response
            file_id = upload_result.get('file_id')
            logger.info("✅ Test report files uploaded successfully")
            logger.info(f"   File ID: {file_id}")
            logger.info(f"   Path: {upload_result.get('folder_path', 'N/A')}")
            
            # Upload summary file if summary_text is provided
            summary_file_id = None
            summary_error = None
            if summary_text and summary_text.strip():
                try:
                    summary_filename = filename.rsplit('.', 1)[0] + '_Summary.txt'
                    summary_result = await self.upload_test_report_summary(
                        summary_text=summary_text,
                        filename=summary_filename,
                        ship_name=ship_name
                    )
                    if summary_result.get('success'):
                        summary_file_id = summary_result.get('test_report_summary_file_id')
                        logger.info(f"✅ Test report summary uploaded successfully: {summary_file_id}")
                    else:
                        summary_error = summary_result.get('message', 'Summary upload failed')
                        logger.warning(f"⚠️ Test report summary upload failed (non-critical): {summary_error}")
                except Exception as e:
                    summary_error = str(e)
                    logger.warning(f"⚠️ Test report summary upload failed (non-critical): {e}")
            
            # Return structured response with mapped field names
            return {
                'success': True,
                'message': 'Test report files uploaded successfully',
                'original_file_id': file_id,  # Map file_id to original_file_id for server.py
                'summary_file_id': summary_file_id,  # Summary file ID if uploaded
                'summary_error': summary_error,  # Summary error if any (non-critical)
                'file_path': upload_result.get('folder_path'),
                'upload_details': upload_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error uploading test report files: {e}")
            return {
                'success': False,
                'message': f'Test report file upload failed: {str(e)}',
                'error': str(e)
            }
    
    async def upload_drawings_manuals_file(
        self,
        file_content: bytes,
        filename: str,
        ship_name: str,
        summary_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload drawings & manuals files to Google Drive
        Path: Shipname > Class & Flag Cert > Drawings & Manuals (original)
        Path: SUMMARY > Class & Flag Document (summary)
        
        Args:
            file_content: Drawing/manual file content
            filename: Drawing/manual filename
            ship_name: Ship name for folder structure
            summary_text: Summary text (optional)
            
        Returns:
            dict: Upload results with file IDs
        """
        try:
            await self._load_configuration()
            
            logger.info(f"📐 Uploading drawings & manuals files to Google Drive: {filename}")
            
            # Determine content type
            content_type = 'application/pdf' if filename.lower().endswith('.pdf') else 'image/jpeg'
            
            # Call Company Apps Script for drawings & manuals upload
            # Path structure: Shipname > Class & Flag Cert > Drawings & Manuals
            upload_result = await self._call_company_apps_script(
                file_content=file_content,
                filename=filename,
                content_type=content_type,
                ship_name=ship_name,
                folder_path="Class & Flag Cert/Drawings & Manuals",
                action="upload_drawings_manuals"
            )
            
            if not upload_result.get('success'):
                logger.error(f"❌ Drawings & manuals file upload failed: {upload_result.get('message')}")
                return upload_result
            
            file_id = upload_result.get('file_id')
            logger.info(f"✅ Drawings & manuals file uploaded successfully: {file_id}")
            
            # Upload summary if provided (non-critical)
            summary_file_id = None
            summary_error = None
            if summary_text:
                try:
                    summary_filename = filename.replace('.pdf', '_Summary.txt')
                    summary_result = await self.upload_drawings_manuals_summary(
                        summary_text=summary_text,
                        filename=summary_filename,
                        ship_name=ship_name
                    )
                    if summary_result.get('success'):
                        summary_file_id = summary_result.get('drawings_manuals_summary_file_id')
                        logger.info(f"✅ Drawings & manuals summary uploaded successfully: {summary_file_id}")
                    else:
                        summary_error = summary_result.get('message', 'Summary upload failed')
                        logger.warning(f"⚠️ Drawings & manuals summary upload failed (non-critical): {summary_error}")
                except Exception as e:
                    summary_error = str(e)
                    logger.warning(f"⚠️ Drawings & manuals summary upload failed (non-critical): {e}")
            
            # Return structured response
            return {
                'success': True,
                'message': 'Drawings & manuals files uploaded successfully',
                'original_file_id': file_id,
                'summary_file_id': summary_file_id,
                'summary_error': summary_error,
                'file_path': upload_result.get('folder_path'),
                'upload_details': upload_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error uploading drawings & manuals files: {e}")
            return {
                'success': False,
                'message': f'Drawings & manuals file upload failed: {str(e)}',
                'error': str(e)
            }
    
    async def upload_drawings_manuals_summary(
        self,
        summary_text: str,
        filename: str,
        ship_name: str
    ) -> Dict[str, Any]:
        """
        Upload drawings & manuals summary text file to Google Drive
        Path: SUMMARY/Class & Flag Document/
        
        Args:
            summary_text: Summary text content
            filename: Summary filename (e.g., "GA_Plan_Summary.txt")
            ship_name: Ship name (for logging only)
            
        Returns:
            dict: Upload results with file ID
        """
        try:
            # Load configuration first
            await self._load_configuration()
            
            if not self.company_apps_script_url:
                raise ValueError("Company Apps Script URL not configured")
            
            if not self.parent_folder_id:
                raise ValueError("Company Google Drive Folder ID not configured")
            
            logger.info(f"📋 Uploading drawings & manuals summary to Drive: {filename}")
            logger.info(f"   Ship: {ship_name}")
            logger.info(f"   Target Path: SUMMARY/Class & Flag Document/")
            
            # Call Company Apps Script
            payload = {
                "action": "upload_drawings_manuals_summary",
                "summary_text": summary_text,
                "filename": filename,
                "parent_folder_id": self.parent_folder_id
            }
            
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    self.company_apps_script_url,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
            
            if result.get('success'):
                logger.info(f"✅ Drawings & manuals summary uploaded successfully")
                return result
            else:
                logger.error(f"❌ Drawings & manuals summary upload failed: {result.get('message')}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Error uploading drawings & manuals summary: {e}")
            return {
                'success': False,
                'message': f'Drawings & manuals summary upload failed: {str(e)}',
                'error': str(e)
            }

    async def upload_test_report_summary(
        self,
        summary_text: str,
        filename: str,
        ship_name: str
    ) -> Dict[str, Any]:
        """
        Upload test report summary text file to Google Drive
        Path: SUMMARY/Class & Flag Document/
        
        Args:
            summary_text: Summary text content
            filename: Summary filename (e.g., "Chemical_Suit_Summary.txt")
            ship_name: Ship name (for logging only)
            
        Returns:
            dict: Upload results with file ID
        """
        try:
            # Load configuration first
            await self._load_configuration()
            
            if not self.company_apps_script_url:
                raise ValueError("Company Apps Script URL not configured")
            
            if not self.parent_folder_id:
                raise ValueError("Company Google Drive Folder ID not configured")
            
            logger.info(f"📋 Uploading test report summary to Drive: {filename}")
            logger.info(f"   Ship: {ship_name}")
            logger.info(f"   Target Path: SUMMARY/Class & Flag Document/")
            
            # Upload summary file to: SUMMARY/Class & Flag Document/
            # Using upload_file_with_folder_creation action
            # This will create: ROOT/SUMMARY/Class & Flag Document/
            
            summary_upload = await self._call_company_apps_script({
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': self.parent_folder_id,  # ROOT folder
                'ship_name': 'SUMMARY',  # Creates/finds SUMMARY folder
                'category': 'Class & Flag Document',  # Creates/finds Class & Flag Document subfolder
                'filename': filename,
                'file_content': base64.b64encode(summary_text.encode('utf-8')).decode('utf-8'),
                'content_type': 'text/plain'
            })
            
            if summary_upload.get('success'):
                file_id = summary_upload.get('file_id')
                logger.info(f"✅ Test report summary uploaded successfully")
                logger.info(f"   File ID: {file_id}")
                logger.info(f"   Path: {summary_upload.get('file_path', 'N/A')}")
                
                return {
                    'success': True,
                    'message': 'Test report summary uploaded successfully',
                    'test_report_summary_file_id': file_id,
                    'file_path': summary_upload.get('file_path'),
                    'upload_details': summary_upload
                }
            else:
                logger.error(f"❌ Test report summary upload failed: {summary_upload.get('message')}")
                return {
                    'success': False,
                    'message': 'Test report summary upload failed',
                    'error': summary_upload.get('message', 'Unknown error'),
                    'upload_details': summary_upload
                }
                
        except Exception as e:
            logger.error(f"❌ Error uploading test report summary: {e}")
            return {
                'success': False,
                'message': f'Summary upload failed: {str(e)}',
                'error': str(e)
            }
    
    async def _call_apps_script_for_test_report_upload(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        ship_name: str,
        summary_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call Company Apps Script to upload test report files
        """
        try:
            if not self.company_apps_script_url:
                raise ValueError("Company Apps Script URL not configured")
            
            logger.info(f"📡 Calling Company Apps Script for test report upload...")
            
            # Encode file content
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # Prepare payload
            payload = {
                "action": "upload_file_with_folder_creation",
                "parent_folder_id": self.parent_folder_id,
                "ship_name": ship_name,
                "parent_category": "Class & Flag Cert",  # First level folder under ShipName
                "category": "Test Report",  # Second level folder under Class & Flag Cert
                "filename": filename,
                "file_content": file_base64,
                "content_type": content_type
            }
            
            # Call Apps Script
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.company_apps_script_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    result = await response.json()
            
            logger.info(f"✅ Company Apps Script response received")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error calling Company Apps Script for test report: {e}")
            return {
                'success': False,
                'message': f'Apps Script call failed: {str(e)}',
                'error': str(e)
            }


    async def upload_certificate_files(
        self,
        cert_file_content: bytes,
        cert_filename: str,
        cert_content_type: str,
        ship_name: Optional[str],
        is_standby: bool = False,
        summary_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload certificate files to Drive AFTER successful database save
        
        Args:
            cert_file_content: Certificate file content
            cert_filename: Certificate filename
            cert_content_type: Certificate MIME type
            ship_name: Ship name for folder structure (None if standby)
            is_standby: If True, upload to COMPANY DOCUMENT/Standby Crew folder
            summary_text: Summary text (optional)
            
        Returns:
            dict: Upload results with file IDs
        """
        try:
            # Load configuration first
            await self._load_configuration()
            
            if not self.company_apps_script_url:
                raise ValueError("Company Apps Script URL not configured")
            
            if not self.parent_folder_id:
                raise ValueError("Company Google Drive Folder ID not configured")
            
            logger.info(f"📤 Uploading certificate files to Drive: {cert_filename}")
            
            upload_results = {}
            
            # Determine upload folder based on is_standby flag
            if is_standby:
                # Upload to COMPANY DOCUMENT/Standby Crew
                # Use upload_file_with_folder_creation with ROOT as parent
                # and "COMPANY DOCUMENT" as ship_name to create the hierarchy
                
                logger.info(f"📤 Uploading certificate to COMPANY DOCUMENT/Standby Crew: {cert_filename}")
                
                # Use ROOT folder as parent, "COMPANY DOCUMENT" as ship_name
                # Apps Script will create: ROOT/COMPANY DOCUMENT/Standby Crew
                cert_upload = await self._call_company_apps_script({
                    'action': 'upload_file_with_folder_creation',
                    'parent_folder_id': self.parent_folder_id,  # ROOT folder
                    'ship_name': 'COMPANY DOCUMENT',  # Creates/finds COMPANY DOCUMENT folder
                    'category': 'Standby Crew',  # Creates/finds Standby Crew subfolder
                    'filename': cert_filename,
                    'file_content': base64.b64encode(cert_file_content).decode('utf-8'),
                    'content_type': cert_content_type
                })
                upload_results['certificate'] = cert_upload
                
            else:
                # Upload to Ship/Crew Records (existing logic)
                logger.info(f"📤 Uploading certificate file: {ship_name}/Crew Records/{cert_filename}")
                cert_upload = await self._call_company_apps_script({
                    'action': 'upload_file_with_folder_creation',
                    'parent_folder_id': self.parent_folder_id,
                    'ship_name': ship_name,
                    'category': 'Crew Records',
                    'filename': cert_filename,
                    'file_content': base64.b64encode(cert_file_content).decode('utf-8'),
                    'content_type': cert_content_type
                })
                upload_results['certificate'] = cert_upload
            
            # Upload 2: Summary file to SUMMARY folder (if provided)
            if summary_text:
                base_name = cert_filename.rsplit('.', 1)[0]
                summary_filename = f"{base_name}_Summary.txt"
                
                logger.info(f"📋 Uploading certificate summary file: SUMMARY/Crew Records/{summary_filename}")
                summary_upload = await self._call_company_apps_script({
                    'action': 'upload_file_with_folder_creation',
                    'parent_folder_id': self.parent_folder_id,
                    'ship_name': 'SUMMARY',
                    'category': 'Crew Records',
                    'filename': summary_filename,
                    'file_content': base64.b64encode(summary_text.encode('utf-8')).decode('utf-8'),
                    'content_type': 'text/plain'
                })
                upload_results['summary'] = summary_upload
            
            # Check upload results
            cert_success = upload_results.get('certificate', {}).get('success', False)
            
            if cert_success:
                logger.info("✅ Certificate file uploads completed successfully")
                return {
                    'success': True,
                    'message': 'Certificate files uploaded successfully',
                    'uploads': upload_results
                }
            else:
                logger.error("❌ Certificate file upload failed")
                return {
                    'success': False,
                    'message': 'Certificate file upload failed',
                    'uploads': upload_results,
                    'error': 'Certificate upload failed'
                }
            
        except Exception as e:
            logger.error(f"❌ Error uploading certificate files: {e}")
            return {
                'success': False,
                'message': f'File upload failed: {str(e)}',
                'error': str(e)
            }


    async def analyze_passport_only(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        document_ai_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze passport using Document AI WITHOUT uploading to Drive
        Upload happens only after successful crew creation
        
        Args:
            file_content: Passport file content
            filename: File name
            content_type: MIME type
            document_ai_config: Document AI configuration
            
        Returns:
            dict: Analysis results only (no file IDs)
        """
        try:
            await self._load_configuration()
            
            logger.info(f"🔄 Analyzing passport (no upload): {filename}")
            
            # Document AI Analysis via System Apps Script ONLY
            logger.info("📡 Passport analysis via System Apps Script...")
            ai_result = await self._call_system_apps_script_for_ai(
                file_content, filename, content_type, document_ai_config
            )
            
            if not ai_result.get('success'):
                logger.error(f"❌ Passport Document AI analysis failed: {ai_result.get('message')}")
                return {
                    'success': False,
                    'message': 'Passport Document AI analysis failed',
                    'error': ai_result.get('message'),
                    'step': 'document_ai_analysis'
                }
            
            logger.info("✅ Passport analysis completed successfully (no upload)")
            return {
                'success': True,
                'message': 'Passport analysis completed successfully',
                'ai_analysis': ai_result,
                'processing_method': 'analysis_only',
                'workflow': 'system_ai_analysis_without_upload'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in passport analysis: {e}")
            return {
                'success': False,
                'message': f'Passport analysis failed: {str(e)}',
                'error': str(e)
            }
    
    async def upload_passport_files(
        self,
        passport_file_content: bytes,
        passport_filename: str,
        passport_content_type: str,
        ship_name: str,
        summary_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload passport files to Drive AFTER successful crew creation
        
        Args:
            passport_file_content: Passport file content
            passport_filename: Passport filename
            passport_content_type: Passport MIME type
            ship_name: Ship name for folder structure
            summary_text: Summary text (optional)
            
        Returns:
            dict: Upload results with file IDs
        """
        try:
            await self._load_configuration()
            
            if not self.company_apps_script_url:
                raise ValueError("Company Apps Script URL not configured")
            
            if not self.parent_folder_id:
                raise ValueError("Company Google Drive Folder ID not configured")
            
            logger.info(f"📤 Uploading passport files to Drive: {passport_filename}")
            
            upload_results = {}
            
            # Determine target folder based on ship_name
            # If ship_name is "-", upload to COMPANY DOCUMENT > Standby Crew
            # Otherwise, upload to Ship Name > Crew Records
            if ship_name == "-":
                target_ship = "COMPANY DOCUMENT"
                target_category = "Standby Crew"
                logger.info(f"📤 Uploading passport file (Standby): {target_ship}/{target_category}/{passport_filename}")
            else:
                target_ship = ship_name
                target_category = "Crew Records"
                logger.info(f"📤 Uploading passport file (Normal): {target_ship}/{target_category}/{passport_filename}")
            
            # Upload 1: Passport file
            passport_upload = await self._call_company_apps_script({
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': self.parent_folder_id,
                'ship_name': target_ship,
                'category': target_category,
                'filename': passport_filename,
                'file_content': base64.b64encode(passport_file_content).decode('utf-8'),
                'content_type': passport_content_type
            })
            upload_results['passport'] = passport_upload
            
            # Upload 2: Summary file to SUMMARY folder (if provided)
            if summary_text:
                base_name = passport_filename.rsplit('.', 1)[0]
                summary_filename = f"{base_name}_Summary.txt"
                
                logger.info(f"📋 Uploading passport summary file: SUMMARY/Crew Records/{summary_filename}")
                summary_upload = await self._call_company_apps_script({
                    'action': 'upload_file_with_folder_creation',
                    'parent_folder_id': self.parent_folder_id,
                    'ship_name': 'SUMMARY',
                    'category': 'Crew Records',
                    'filename': summary_filename,
                    'file_content': base64.b64encode(summary_text.encode('utf-8')).decode('utf-8'),
                    'content_type': 'text/plain'
                })
                upload_results['summary'] = summary_upload
            
            # Check upload results
            passport_success = upload_results.get('passport', {}).get('success', False)
            
            if passport_success:
                logger.info("✅ Passport file uploads completed successfully")
                return {
                    'success': True,
                    'message': 'Passport files uploaded successfully',
                    'uploads': upload_results
                }
            else:
                logger.error("❌ Passport file upload failed")
                logger.error(f"   Passport upload response: {upload_results.get('passport', {})}")
                logger.error(f"   Summary upload response: {upload_results.get('summary', {})}")
                return {
                    'success': False,
                    'message': 'Passport file upload failed',
                    'uploads': upload_results,
                    'error': upload_results.get('passport', {}).get('error', 'Passport upload failed')
                }
            
        except Exception as e:
            logger.error(f"❌ Error uploading passport files: {e}")
            return {
                'success': False,
                'message': f'File upload failed: {str(e)}',
                'error': str(e)
            }

    async def upload_survey_report_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        ship_name: str,
        survey_report_name: str
    ) -> Dict[str, Any]:
        """
        Upload survey report file to Google Drive
        Path: ShipName/Class & Flag Cert/Class Survey Report/
        
        Args:
            file_content: Survey report file content
            filename: File name
            content_type: MIME type
            ship_name: Ship name for folder structure
            survey_report_name: Survey report name (for logging)
            
        Returns:
            dict: Upload results with file ID
        """
        try:
            # Load configuration first
            await self._load_configuration()
            
            if not self.company_apps_script_url:
                raise ValueError("Company Apps Script URL not configured")
            
            if not self.parent_folder_id:
                raise ValueError("Company Google Drive Folder ID not configured")
            
            logger.info(f"📤 Uploading survey report file to Drive: {filename}")
            logger.info(f"   Ship: {ship_name}")
            logger.info(f"   Survey Type: {survey_report_name}")
            logger.info(f"   Target Path: {ship_name}/Class & Flag Cert/Class Survey Report/")
            
            # Upload original file to: ShipName/Class & Flag Cert/Class Survey Report/
            # Using upload_file_with_folder_creation action with nested path
            # Use parent_category and category to create proper nested structure
            
            survey_report_upload = await self._call_company_apps_script({
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': self.parent_folder_id,  # ROOT folder
                'ship_name': ship_name,  # Creates/finds ShipName folder
                'parent_category': 'Class & Flag Cert',  # First level folder under ShipName
                'category': 'Class Survey Report',  # Second level folder under Class & Flag Cert
                'filename': filename,
                'file_content': base64.b64encode(file_content).decode('utf-8'),
                'content_type': content_type
            })
            
            if survey_report_upload.get('success'):
                file_id = survey_report_upload.get('file_id')
                logger.info(f"✅ Survey report file uploaded successfully")
                logger.info(f"   File ID: {file_id}")
                logger.info(f"   Path: {survey_report_upload.get('file_path', 'N/A')}")
                
                return {
                    'success': True,
                    'message': 'Survey report file uploaded successfully',
                    'survey_report_file_id': file_id,
                    'file_path': survey_report_upload.get('file_path'),
                    'upload_details': survey_report_upload
                }
            else:
                logger.error(f"❌ Survey report file upload failed: {survey_report_upload.get('message')}")
                return {
                    'success': False,
                    'message': 'Survey report file upload failed',
                    'error': survey_report_upload.get('message', 'Unknown error'),
                    'upload_details': survey_report_upload
                }
                
        except Exception as e:
            logger.error(f"❌ Error uploading survey report file: {e}")
            return {
                'success': False,
                'message': f'File upload failed: {str(e)}',
                'error': str(e)
            }

    async def upload_survey_report_summary(
        self,
        summary_text: str,
        filename: str,
        ship_name: str
    ) -> Dict[str, Any]:
        """
        Upload survey report summary text file to Google Drive
        Path: SUMMARY/Class & Flag Document/
        
        Args:
            summary_text: Summary text content
            filename: Summary filename (e.g., "Annual_Survey_Summary.txt")
            ship_name: Ship name (for logging only)
            
        Returns:
            dict: Upload results with file ID
        """
        try:
            # Load configuration first
            await self._load_configuration()
            
            if not self.company_apps_script_url:
                raise ValueError("Company Apps Script URL not configured")
            
            if not self.parent_folder_id:
                raise ValueError("Company Google Drive Folder ID not configured")
            
            logger.info(f"📋 Uploading survey report summary to Drive: {filename}")
            logger.info(f"   Ship: {ship_name}")
            logger.info(f"   Target Path: SUMMARY/Class & Flag Document/")
            
            # Upload summary file to: SUMMARY/Class & Flag Document/
            # Using upload_file_with_folder_creation action
            # This will create: ROOT/SUMMARY/Class & Flag Document/
            
            summary_upload = await self._call_company_apps_script({
                'action': 'upload_file_with_folder_creation',
                'parent_folder_id': self.parent_folder_id,  # ROOT folder
                'ship_name': 'SUMMARY',  # Creates/finds SUMMARY folder
                'category': 'Class & Flag Document',  # Creates/finds Class & Flag Document subfolder
                'filename': filename,
                'file_content': base64.b64encode(summary_text.encode('utf-8')).decode('utf-8'),
                'content_type': 'text/plain'
            })
            
            if summary_upload.get('success'):
                file_id = summary_upload.get('file_id')
                logger.info(f"✅ Survey report summary uploaded successfully")
                logger.info(f"   File ID: {file_id}")
                logger.info(f"   Path: {summary_upload.get('file_path', 'N/A')}")
                
                return {
                    'success': True,
                    'message': 'Survey report summary uploaded successfully',
                    'summary_file_id': file_id,
                    'file_path': summary_upload.get('file_path'),
                    'upload_details': summary_upload
                }
            else:
                logger.error(f"❌ Survey report summary upload failed: {summary_upload.get('message')}")
                return {
                    'success': False,
                    'message': 'Survey report summary upload failed',
                    'error': summary_upload.get('message', 'Unknown error'),
                    'upload_details': summary_upload
                }
                
        except Exception as e:
            logger.error(f"❌ Error uploading survey report summary: {e}")
            return {
                'success': False,
                'message': f'Summary upload failed: {str(e)}',
                'error': str(e)
            }


def create_dual_apps_script_manager(company_id: str) -> DualAppsScriptManager:
    """Factory function to create DualAppsScriptManager"""
    return DualAppsScriptManager(company_id)