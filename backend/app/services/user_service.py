import uuid
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from app.models.user import UserCreate, UserUpdate, UserResponse, UserRole
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token

logger = logging.getLogger(__name__)

class UserService:
    """Business logic for user management"""
    
    @staticmethod
    def get_audit_log_service():
        """Get audit log service instance"""
        from app.db.mongodb import mongo_db
        from app.services.crew_audit_log_service import CrewAuditLogService
        from app.repositories.crew_audit_log_repository import CrewAuditLogRepository
        return CrewAuditLogService(CrewAuditLogRepository(mongo_db.database))
    
    @staticmethod
    async def authenticate(username: str, password: str, remember_me: bool = False) -> Tuple[str, UserResponse]:
        """
        Authenticate user and return access token
        Returns: (access_token, user)
        """
        logger.info(f"🔐 Authentication attempt for: {username}")
        
        # Find user
        user = await UserRepository.find_by_username(username)
        if not user:
            logger.warning(f"❌ User not found: {username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        logger.info(f"✅ User found: {user.get('username')}")
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            logger.warning(f"❌ Invalid password for: {username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        logger.info(f"✅ Password verified for: {username}")
        
        # Check if active
        if not user.get("is_active", True):
            logger.warning(f"❌ Account disabled: {username}")
            raise HTTPException(status_code=401, detail="Account is disabled")
        
        # Create token
        token_expires = timedelta(days=30) if remember_me else timedelta(hours=24)
        token_data = {
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"],
            "company": user.get("company"),
            "full_name": user.get("full_name", user["username"])
        }
        access_token = create_access_token(data=token_data, expires_delta=token_expires)
        
        logger.info(f"✅ Token created for: {username} (remember_me: {remember_me})")
        
        # Remove password hash
        user.pop("password_hash", None)
        
        return access_token, UserResponse(**user)
    
    @staticmethod
    async def get_all_users(current_user: UserResponse) -> List[UserResponse]:
        """Get users based on current user's role"""
        users = await UserRepository.find_all()
        
        # Filter based on role
        if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SUPER_ADMIN]:
            filtered = users
        elif current_user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            filtered = [u for u in users if u.get('company') == current_user.company]
        else:
            filtered = [u for u in users if u.get('id') == current_user.id]
        
        # Remove password hashes
        for user in filtered:
            user.pop("password_hash", None)
        
        return [UserResponse(**u) for u in filtered]
    
    @staticmethod
    async def create_user(user_data: UserCreate, current_user: UserResponse) -> UserResponse:
        """Create new user"""
        # Check if username exists
        existing = await UserRepository.find_by_username(user_data.username)
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check email if provided
        if user_data.email:
            existing_email = await UserRepository.find_by_email(user_data.email)
            if existing_email:
                raise HTTPException(status_code=400, detail="Email already exists")
        
        # Create user dict
        user_dict = user_data.dict()
        password = user_dict.pop("password")
        user_dict["password_hash"] = hash_password(password)
        user_dict["id"] = str(uuid.uuid4())
        user_dict["created_at"] = datetime.now(timezone.utc)
        user_dict["permissions"] = {}
        
        # Create in database
        await UserRepository.create(user_dict)
        
        # Log audit (before removing password_hash)
        try:
            audit_service = UserService.get_audit_log_service()
            performed_by_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            # Create a copy without password_hash for logging
            log_user_dict = {k: v for k, v in user_dict.items() if k != 'password_hash'}
            await audit_service.log_user_create(
                user_data=log_user_dict,
                performed_by_user=performed_by_dict
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        logger.info(f"✅ User created: {user_data.username}")
        
        # Return user without password
        user_dict.pop("password_hash")
        return UserResponse(**user_dict)
    
    @staticmethod
    async def update_user(user_id: str, update_data: UserUpdate, current_user: UserResponse) -> UserResponse:
        """Update user"""
        # Find user
        user = await UserRepository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Keep old user data for audit (before update)
        old_user_for_audit = {k: v for k, v in user.items() if k != 'password_hash'}
        
        # Prepare update dict
        update_dict = update_data.dict(exclude_unset=True)
        
        # Handle password update
        if "password" in update_dict and update_dict["password"]:
            update_dict["password_hash"] = hash_password(update_dict.pop("password"))
        
        # Update
        await UserRepository.update(user_id, update_dict)
        
        logger.info(f"✅ User updated: {user_id}")
        
        # Get updated user
        updated_user = await UserRepository.find_by_id(user_id)
        
        # Log audit (before removing password_hash)
        try:
            audit_service = UserService.get_audit_log_service()
            performed_by_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            new_user_for_audit = {k: v for k, v in updated_user.items() if k != 'password_hash'}
            await audit_service.log_user_update(
                old_user=old_user_for_audit,
                new_user=new_user_for_audit,
                performed_by_user=performed_by_dict
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        updated_user.pop("password_hash", None)
        return UserResponse(**updated_user)
    
    @staticmethod
    async def delete_user(user_id: str, current_user: UserResponse) -> dict:
        """Delete user"""
        user = await UserRepository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await UserRepository.delete(user_id)
        
        # Log audit
        try:
            audit_service = UserService.get_audit_log_service()
            performed_by_dict = {
                'id': current_user.id,
                'username': current_user.username,
                'full_name': current_user.full_name,
                'company': current_user.company
            }
            user_for_audit = {k: v for k, v in user.items() if k != 'password_hash'}
            await audit_service.log_user_delete(
                user_data=user_for_audit,
                performed_by_user=performed_by_dict
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
        
        logger.info(f"✅ User deleted: {user_id}")
        
        return {"message": "User deleted successfully"}

    @staticmethod
    async def upload_signature(
        user_id: str, 
        file_content: bytes, 
        filename: str, 
        current_user: UserResponse
    ) -> dict:
        """
        Upload and process user signature
        - Process image to remove background
        - Upload to Google Drive: COMPANY DOCUMENT/User Signature
        - Update user record with signature URL
        
        Uses the standard upload_file_with_folder_creation action that is supported by Apps Script
        """
        import base64
        import aiohttp
        from app.db.mongodb import mongo_db
        from app.utils.signature_processor import process_signature_for_upload
        
        logger.info(f"🖊️ Processing signature for user: {user_id}")
        
        # Verify user exists
        user = await UserRepository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get company ID
        company_id = user.get('company') or current_user.company
        if not company_id:
            raise HTTPException(status_code=400, detail="Company not found for user")
        
        try:
            # Get GDrive config
            config = await mongo_db.find_one("company_gdrive_config", {"company_id": company_id})
            if not config:
                raise HTTPException(status_code=404, detail="Google Drive not configured for this company")
            
            apps_script_url = config.get("web_app_url") or config.get("apps_script_url")
            parent_folder_id = config.get("folder_id")
            
            if not apps_script_url:
                raise HTTPException(status_code=400, detail="Apps Script URL not configured")
            if not parent_folder_id:
                raise HTTPException(status_code=400, detail="Root folder ID not configured")
            
            # Process signature image (remove background)
            processed_bytes, new_filename = process_signature_for_upload(file_content, filename)
            
            # Generate unique filename with username
            username = user.get('username', 'user')
            final_filename = f"{username}_{new_filename}"
            
            # Encode file to base64
            file_base64 = base64.b64encode(processed_bytes).decode('utf-8')
            
            # Use upload_file_with_folder_creation action - the standard approach
            # Apps Script structure: ship_name folder must exist first, then it creates nested folders
            # For signature: root_folder / "COMPANY DOCUMENT" (as ship_name) / "User Signature" (as category)
            # 
            # The Apps Script looks for ship_name folder first, then creates parent_category/category inside it
            # Since we want: COMPANY DOCUMENT / User Signature
            # We set: ship_name = "COMPANY DOCUMENT", category = "User Signature", parent_category = empty
            # This will create: COMPANY DOCUMENT / User Signature / file
            
            logger.info(f"📤 Uploading signature file: {final_filename}")
            logger.info(f"   Target path: COMPANY DOCUMENT / User Signature")
            
            payload = {
                "action": "upload_file_with_folder_creation",
                "parent_folder_id": parent_folder_id,
                "ship_name": "COMPANY DOCUMENT",  # The parent folder (must exist or be created manually)
                "parent_category": "User Signature",  # Will be created as subfolder
                "category": "",  # Empty - file goes directly in User Signature
                "filename": final_filename,
                "file_content": file_base64,
                "content_type": "image/png"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    apps_script_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    response_text = await response.text()
                    logger.info(f"📡 Apps Script response status: {response.status}")
                    
                    if response.status == 200:
                        try:
                            result = await response.json()
                        except:
                            # Try parsing from text
                            import json
                            result = json.loads(response_text)
                        
                        if result.get("success"):
                            file_id = result.get("file_id")
                            
                            # Get viewable URL
                            signature_url = f"https://drive.google.com/uc?id={file_id}"
                            
                            # Update user record
                            await UserRepository.update(user_id, {
                                'signature_file_id': file_id,
                                'signature_url': signature_url
                            })
                            
                            logger.info(f"✅ Signature uploaded successfully for user {user_id}: {file_id}")
                            
                            return {
                                'success': True,
                                'message': 'Signature uploaded successfully',
                                'file_id': file_id,
                                'signature_url': signature_url,
                                'filename': final_filename
                            }
                        else:
                            error_msg = result.get("message", "Unknown error")
                            logger.error(f"❌ Upload failed: {error_msg}")
                            logger.error(f"   Full response: {result}")
                            raise HTTPException(status_code=500, detail=f"Upload failed: {error_msg}")
                    else:
                        logger.error(f"❌ Request failed: {response.status}")
                        logger.error(f"   Response: {response_text[:500]}")
                        raise HTTPException(status_code=500, detail=f"Upload request failed: {response.status}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error uploading signature: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to process signature: {str(e)}")

    @staticmethod
    async def _find_or_create_folder(apps_script_url: str, parent_folder_id: str, folder_name: str) -> str:
        """Helper to find or create a folder in Google Drive"""
        import aiohttp
        
        # First try to find existing folder
        find_payload = {
            "action": "find_subfolder",
            "parent_folder_id": parent_folder_id,
            "folder_name": folder_name
        }
        
        async with aiohttp.ClientSession() as session:
            # Try to find
            async with session.post(
                apps_script_url,
                json=find_payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success") and result.get("folder_id"):
                        logger.info(f"   ✓ Found existing folder: {folder_name}")
                        return result["folder_id"]
            
            # Not found, create new
            create_payload = {
                "action": "create_folder",
                "parent_folder_id": parent_folder_id,
                "folder_name": folder_name
            }
            
            async with session.post(
                apps_script_url,
                json=create_payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success") and result.get("folder_id"):
                        logger.info(f"   ✓ Created new folder: {folder_name}")
                        return result["folder_id"]
        
        return None

