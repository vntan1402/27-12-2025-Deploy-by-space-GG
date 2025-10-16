#!/usr/bin/env python3
"""
Debug passport upload to check parameters sent to Apps Script
"""

import asyncio
import sys
sys.path.append('/app/backend')

from dual_apps_script_manager import create_dual_apps_script_manager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_upload():
    # Use test company ID
    company_id = "cd1951d0-223e-4a09-865b-593047ed8c2d"  # AMCSC
    
    manager = create_dual_apps_script_manager(company_id)
    
    # Create dummy file content
    test_content = b"Test passport content"
    test_filename = "test_passport_debug.pdf"
    test_ship = "BROTHER 36"
    test_summary = "Test summary content"
    
    logger.info("=" * 80)
    logger.info("TESTING PASSPORT UPLOAD WITH DEBUG")
    logger.info("=" * 80)
    logger.info(f"Ship: {test_ship}")
    logger.info(f"Filename: {test_filename}")
    logger.info(f"Summary: {test_summary[:50]}...")
    
    # This will show the actual parameters being sent
    result = await manager.upload_passport_files(
        passport_file_content=test_content,
        passport_filename=test_filename,
        passport_content_type="application/pdf",
        ship_name=test_ship,
        summary_text=test_summary
    )
    
    logger.info("=" * 80)
    logger.info("UPLOAD RESULT:")
    logger.info("=" * 80)
    logger.info(f"Success: {result.get('success')}")
    logger.info(f"Message: {result.get('message')}")
    
    if result.get('uploads'):
        logger.info("\nUPLOAD DETAILS:")
        passport_upload = result['uploads'].get('passport', {})
        logger.info(f"Passport Upload Success: {passport_upload.get('success')}")
        if passport_upload.get('folder_path'):
            logger.info(f"📂 FOLDER PATH: {passport_upload.get('folder_path')}")
        
        summary_upload = result['uploads'].get('summary', {})
        logger.info(f"Summary Upload Success: {summary_upload.get('success')}")
        if summary_upload.get('folder_path'):
            logger.info(f"📂 SUMMARY PATH: {summary_upload.get('folder_path')}")

if __name__ == "__main__":
    asyncio.run(test_upload())
