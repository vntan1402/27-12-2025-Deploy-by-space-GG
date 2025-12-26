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
from app.core.security import get_current_user
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
            
            # Check both possible field names for document_ai
            doc_ai = ai_config.get("document_ai") or ai_config.get("document_ai_config", {})
            result["details"]["document_ai_enabled"] = doc_ai.get("enabled", False) if doc_ai else False
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
        
        # Check both possible field names: document_ai and document_ai_config
        doc_ai_config = ai_config.get("document_ai") or ai_config.get("document_ai_config", {})
        
        if not doc_ai_config:
            result["status"] = "unhealthy"
            result["message"] = "Document AI not configured in AI settings"
            return result
        
        # Check if Document AI is enabled
        if not doc_ai_config.get("enabled", False):
            result["status"] = "unhealthy"
            result["message"] = "Document AI is disabled"
            result["details"]["enabled"] = False
            return result
        
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
                result["details"]["processor_id"] = processor_id[:8] + "..." if processor_id else "N/A"
                
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


@router.get("/production-diagnostic")
async def production_diagnostic(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Advanced production diagnostic test.
    
    Runs multiple ping tests to calculate average latency and detect
    intermittent connectivity issues.
    """
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": current_user.username,
        "test_type": "production_diagnostic",
        "ping_tests": [],
        "summary": {
            "total_pings": 3,
            "successful_pings": 0,
            "avg_latency_ms": 0,
            "min_latency_ms": None,
            "max_latency_ms": None,
            "latency_variance": None,
            "stability_rating": "unknown"
        }
    }
    
    # Get AI config
    ai_config = await get_ai_config()
    if not ai_config:
        results["error"] = "AI configuration not found"
        return results
    
    doc_ai_config = ai_config.get("document_ai") or ai_config.get("document_ai_config", {})
    apps_script_url = doc_ai_config.get("apps_script_url") if doc_ai_config else None
    
    if not apps_script_url:
        results["error"] = "Apps Script URL not configured"
        return results
    
    # Run 3 ping tests
    latencies = []
    for i in range(3):
        ping_result = {
            "ping_number": i + 1,
            "latency_ms": None,
            "status": "unknown"
        }
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    apps_script_url,
                    json={"action": "ping"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    elapsed_ms = (time.time() - start_time) * 1000
                    
                    ping_result["latency_ms"] = round(elapsed_ms, 2)
                    ping_result["http_status"] = response.status
                    
                    if response.status == 200:
                        ping_result["status"] = "success"
                        results["summary"]["successful_pings"] += 1
                        latencies.append(elapsed_ms)
                    else:
                        ping_result["status"] = "degraded"
                        
        except asyncio.TimeoutError:
            ping_result["status"] = "timeout"
            ping_result["error"] = "Timed out (>30s)"
            
        except Exception as e:
            ping_result["status"] = "error"
            ping_result["error"] = str(e)
        
        results["ping_tests"].append(ping_result)
        
        # Wait 1 second between pings
        if i < 2:
            await asyncio.sleep(1)
    
    # Calculate statistics
    if latencies:
        results["summary"]["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2)
        results["summary"]["min_latency_ms"] = round(min(latencies), 2)
        results["summary"]["max_latency_ms"] = round(max(latencies), 2)
        
        if len(latencies) > 1:
            avg = results["summary"]["avg_latency_ms"]
            variance = sum((x - avg) ** 2 for x in latencies) / len(latencies)
            results["summary"]["latency_variance"] = round(variance, 2)
        
        # Stability rating
        if results["summary"]["successful_pings"] == 3:
            if results["summary"]["avg_latency_ms"] < 2000:
                results["summary"]["stability_rating"] = "excellent"
            elif results["summary"]["avg_latency_ms"] < 5000:
                results["summary"]["stability_rating"] = "good"
            else:
                results["summary"]["stability_rating"] = "slow"
        elif results["summary"]["successful_pings"] >= 2:
            results["summary"]["stability_rating"] = "unstable"
        else:
            results["summary"]["stability_rating"] = "poor"
    
    return results


@router.post("/bandwidth-test")
async def bandwidth_test(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test bandwidth to Google Apps Script with various payload sizes.
    
    Sends payloads of different sizes and measures upload/download speed.
    Helps diagnose network performance issues between server and external services.
    """
    import base64
    import string
    import random
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": current_user.username,
        "test_type": "bandwidth_test",
        "tests": [],
        "summary": {
            "total_tests": 0,
            "successful_tests": 0,
            "avg_upload_speed_mbps": 0,
            "avg_download_speed_mbps": 0,
            "bandwidth_rating": "unknown"
        },
        "benchmark": {
            "100KB": {"expected_seconds": 1.5, "description": "Small payload"},
            "500KB": {"expected_seconds": 2.5, "description": "Medium payload"},
            "1MB": {"expected_seconds": 4.0, "description": "Large payload"},
            "2MB": {"expected_seconds": 7.0, "description": "Very large payload"},
            "3MB": {"expected_seconds": 10.0, "description": "Maximum test payload"}
        }
    }
    
    # Get AI config for Apps Script URL
    ai_config = await get_ai_config()
    if not ai_config:
        results["error"] = "AI configuration not found"
        return results
    
    doc_ai_config = ai_config.get("document_ai") or ai_config.get("document_ai_config", {})
    apps_script_url = doc_ai_config.get("apps_script_url") if doc_ai_config else None
    
    if not apps_script_url:
        results["error"] = "Apps Script URL not configured"
        return results
    
    # Test payload sizes in bytes
    test_sizes = [
        ("100KB", 100 * 1024),
        ("500KB", 500 * 1024),
        ("1MB", 1 * 1024 * 1024),
        ("2MB", 2 * 1024 * 1024),
        ("3MB", 3 * 1024 * 1024)
    ]
    
    upload_speeds = []
    
    for size_label, size_bytes in test_sizes:
        test_result = {
            "payload_size": size_label,
            "payload_bytes": size_bytes,
            "status": "pending",
            "upload_time_seconds": None,
            "upload_speed_mbps": None,
            "rating": "unknown",
            "vs_benchmark": None
        }
        
        try:
            # Generate random payload (simulating file content)
            # Use base64-encoded random bytes to simulate PDF upload
            random_data = ''.join(random.choices(string.ascii_letters + string.digits, k=size_bytes))
            
            # Create payload similar to document upload
            payload = {
                "action": "bandwidth_test",
                "test_data": random_data,
                "size_label": size_label,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    apps_script_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout for large payloads
                ) as response:
                    # Read response to measure full round-trip
                    await response.text()
                    
                    elapsed_seconds = time.time() - start_time
                    
                    test_result["upload_time_seconds"] = round(elapsed_seconds, 2)
                    test_result["http_status"] = response.status
                    
                    # Calculate upload speed in Mbps (megabits per second)
                    # size_bytes * 8 = bits, / 1_000_000 = megabits
                    upload_speed_mbps = (size_bytes * 8 / 1_000_000) / elapsed_seconds
                    test_result["upload_speed_mbps"] = round(upload_speed_mbps, 2)
                    
                    if response.status == 200:
                        test_result["status"] = "success"
                        results["summary"]["successful_tests"] += 1
                        upload_speeds.append(upload_speed_mbps)
                        
                        # Compare with benchmark
                        expected = results["benchmark"][size_label]["expected_seconds"]
                        ratio = elapsed_seconds / expected
                        test_result["vs_benchmark"] = f"{ratio:.1f}x"
                        
                        if ratio <= 1.5:
                            test_result["rating"] = "excellent"
                        elif ratio <= 2.5:
                            test_result["rating"] = "good"
                        elif ratio <= 4.0:
                            test_result["rating"] = "slow"
                        else:
                            test_result["rating"] = "very_slow"
                    else:
                        test_result["status"] = "error"
                        test_result["error"] = f"HTTP {response.status}"
                        
        except asyncio.TimeoutError:
            test_result["status"] = "timeout"
            test_result["error"] = "Request timed out (>120s)"
            
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
        
        results["tests"].append(test_result)
        results["summary"]["total_tests"] += 1
        
        # Small delay between tests to avoid rate limiting
        await asyncio.sleep(0.5)
    
    # Calculate summary statistics
    if upload_speeds:
        results["summary"]["avg_upload_speed_mbps"] = round(sum(upload_speeds) / len(upload_speeds), 2)
        results["summary"]["min_upload_speed_mbps"] = round(min(upload_speeds), 2)
        results["summary"]["max_upload_speed_mbps"] = round(max(upload_speeds), 2)
        
        # Overall bandwidth rating
        avg_speed = results["summary"]["avg_upload_speed_mbps"]
        if avg_speed >= 5.0:
            results["summary"]["bandwidth_rating"] = "excellent"
        elif avg_speed >= 2.0:
            results["summary"]["bandwidth_rating"] = "good"
        elif avg_speed >= 1.0:
            results["summary"]["bandwidth_rating"] = "acceptable"
        elif avg_speed >= 0.5:
            results["summary"]["bandwidth_rating"] = "slow"
        else:
            results["summary"]["bandwidth_rating"] = "very_slow"
    
    return results

