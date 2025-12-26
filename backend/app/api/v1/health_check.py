"""
Health Check & Connectivity Testing API
Tests connectivity to external services and measures latency
"""
import logging
import time
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from app.models.user import UserResponse
from app.api.deps import get_current_user
from app.repositories.gdrive_config_repository import GDriveConfigRepository
from app.repositories.ai_config_repository import AIConfigRepository
from app.utils.ai_config_helper import get_ai_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health Check"])


@router.get("/connectivity")
async def check_connectivity(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Check connectivity to all external services and measure latency.
    
    Tests:
    - Google Apps Script (GDrive)
    - Google Document AI (via Apps Script)
    - MongoDB connection
    - AI Configuration
    
    Returns detailed timing information for each service.
    """
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": current_user.username,
        "company": current_user.company,
        "services": {},
        "summary": {
            "total_services": 0,
            "healthy": 0,
            "unhealthy": 0,
            "avg_latency_ms": 0
        }
    }
    
    latencies = []
    
    # Test 1: Google Apps Script (GDrive) connectivity
    gdrive_result = await _test_gdrive_connectivity(current_user.company)
    results["services"]["google_apps_script"] = gdrive_result
    if gdrive_result["status"] == "healthy":
        results["summary"]["healthy"] += 1
        if gdrive_result.get("latency_ms"):
            latencies.append(gdrive_result["latency_ms"])
    else:
        results["summary"]["unhealthy"] += 1
    results["summary"]["total_services"] += 1
    
    # Test 2: AI Configuration
    ai_config_result = await _test_ai_config()
    results["services"]["ai_config"] = ai_config_result
    if ai_config_result["status"] == "healthy":
        results["summary"]["healthy"] += 1
        if ai_config_result.get("latency_ms"):
            latencies.append(ai_config_result["latency_ms"])
    else:
        results["summary"]["unhealthy"] += 1
    results["summary"]["total_services"] += 1
    
    # Test 3: Document AI (via Apps Script)
    doc_ai_result = await _test_document_ai_connectivity(current_user.company)
    results["services"]["document_ai"] = doc_ai_result
    if doc_ai_result["status"] == "healthy":
        results["summary"]["healthy"] += 1
        if doc_ai_result.get("latency_ms"):
            latencies.append(doc_ai_result["latency_ms"])
    else:
        results["summary"]["unhealthy"] += 1
    results["summary"]["total_services"] += 1
    
    # Calculate average latency
    if latencies:
        results["summary"]["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2)
    
    # Overall health status
    if results["summary"]["unhealthy"] == 0:
        results["overall_status"] = "healthy"
    elif results["summary"]["healthy"] > results["summary"]["unhealthy"]:
        results["overall_status"] = "degraded"
    else:
        results["overall_status"] = "unhealthy"
    
    return results


@router.get("/ping-apps-script")
async def ping_apps_script(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Simple ping test to Google Apps Script.
    Returns latency in milliseconds.
    """
    return await _test_gdrive_connectivity(current_user.company)


@router.get("/ping-document-ai")
async def ping_document_ai(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Simple ping test to Document AI via Apps Script.
    Returns latency in milliseconds.
    """
    return await _test_document_ai_connectivity(current_user.company)


async def _test_gdrive_connectivity(company_id: str) -> Dict[str, Any]:
    """Test Google Apps Script connectivity"""
    result = {
        "service": "Google Apps Script (GDrive)",
        "status": "unknown",
        "latency_ms": None,
        "message": "",
        "details": {}
    }
    
    try:
        # Get GDrive config
        config = await GDriveConfigRepository.get_by_company(company_id)
        
        if not config:
            result["status"] = "unhealthy"
            result["message"] = "GDrive not configured for this company"
            return result
        
        apps_script_url = config.get("web_app_url") or config.get("apps_script_url")
        if not apps_script_url:
            result["status"] = "unhealthy"
            result["message"] = "Apps Script URL not configured"
            return result
        
        # Simple ping payload
        payload = {
            "action": "ping"
        }
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                apps_script_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                elapsed_ms = (time.time() - start_time) * 1000
                
                result["latency_ms"] = round(elapsed_ms, 2)
                result["details"]["http_status"] = response.status
                result["details"]["url"] = apps_script_url[:50] + "..."
                
                if response.status == 200:
                    result["status"] = "healthy"
                    result["message"] = f"Connected successfully in {elapsed_ms:.0f}ms"
                else:
                    result["status"] = "unhealthy"
                    result["message"] = f"HTTP {response.status} response"
                    
    except asyncio.TimeoutError:
        result["status"] = "unhealthy"
        result["message"] = "Connection timed out (>30s)"
        result["details"]["error"] = "TimeoutError"
        
    except aiohttp.ClientError as e:
        result["status"] = "unhealthy"
        result["message"] = f"Network error: {str(e)}"
        result["details"]["error"] = str(e)
        
    except Exception as e:
        result["status"] = "unhealthy"
        result["message"] = f"Error: {str(e)}"
        result["details"]["error"] = str(e)
    
    return result


async def _test_ai_config() -> Dict[str, Any]:
    """Test AI Configuration availability"""
    result = {
        "service": "AI Configuration",
        "status": "unknown",
        "latency_ms": None,
        "message": "",
        "details": {}
    }
    
    try:
        start_time = time.time()
        
        ai_config = await get_ai_config()
        
        elapsed_ms = (time.time() - start_time) * 1000
        result["latency_ms"] = round(elapsed_ms, 2)
        
        if ai_config:
            result["status"] = "healthy"
            result["message"] = f"AI config found in {elapsed_ms:.0f}ms"
            result["details"]["provider"] = ai_config.get("provider", "unknown")
            result["details"]["model"] = ai_config.get("model", "unknown")
            result["details"]["document_ai_enabled"] = bool(ai_config.get("document_ai_config", {}).get("project_id"))
        else:
            result["status"] = "unhealthy"
            result["message"] = "AI configuration not found"
            
    except Exception as e:
        result["status"] = "unhealthy"
        result["message"] = f"Error: {str(e)}"
        result["details"]["error"] = str(e)
    
    return result


async def _test_document_ai_connectivity(company_id: str) -> Dict[str, Any]:
    """Test Document AI connectivity via Apps Script"""
    result = {
        "service": "Google Document AI",
        "status": "unknown",
        "latency_ms": None,
        "message": "",
        "details": {}
    }
    
    try:
        # Get AI config for Document AI settings
        ai_config = await get_ai_config()
        
        if not ai_config:
            result["status"] = "unhealthy"
            result["message"] = "AI configuration not found"
            return result
        
        doc_ai_config = ai_config.get("document_ai_config", {})
        apps_script_url = doc_ai_config.get("apps_script_url")
        project_id = doc_ai_config.get("project_id")
        processor_id = doc_ai_config.get("processor_id")
        
        if not apps_script_url:
            result["status"] = "unhealthy"
            result["message"] = "Document AI Apps Script URL not configured"
            return result
        
        if not project_id or not processor_id:
            result["status"] = "unhealthy"
            result["message"] = "Document AI project/processor not configured"
            result["details"]["project_id"] = project_id or "missing"
            result["details"]["processor_id"] = processor_id or "missing"
            return result
        
        # Test payload - minimal request
        payload = {
            "action": "ping",
            "project_id": project_id,
            "processor_id": processor_id
        }
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                apps_script_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                elapsed_ms = (time.time() - start_time) * 1000
                
                result["latency_ms"] = round(elapsed_ms, 2)
                result["details"]["http_status"] = response.status
                result["details"]["project_id"] = project_id
                result["details"]["processor_id"] = processor_id[:8] + "..."
                
                if response.status == 200:
                    result["status"] = "healthy"
                    result["message"] = f"Connected successfully in {elapsed_ms:.0f}ms"
                else:
                    result["status"] = "degraded"
                    result["message"] = f"HTTP {response.status} response (may still work)"
                    
    except asyncio.TimeoutError:
        result["status"] = "unhealthy"
        result["message"] = "Connection timed out (>30s)"
        result["details"]["error"] = "TimeoutError"
        
    except aiohttp.ClientError as e:
        result["status"] = "unhealthy"
        result["message"] = f"Network error: {str(e)}"
        result["details"]["error"] = str(e)
        
    except Exception as e:
        result["status"] = "unhealthy"
        result["message"] = f"Error: {str(e)}"
        result["details"]["error"] = str(e)
    
    return result
