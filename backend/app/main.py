from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.mongodb import mongo_db
from app.api.v1 import api_router
from app.services.cleanup_service import CleanupService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = AsyncIOScheduler()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Ship Management System API - V2 Clean Architecture"
)

# CORS middleware - Enhanced for production
# Note: When backend times out or errors before responding, CORS headers won't be sent
# This can cause "CORS blocked" errors even though the real issue is timeout/error
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        "https://quanlytau.com",
        "https://www.quanlytau.com",
        "https://nautical-records.emergent.host",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Cleanup job function
async def scheduled_cleanup_job():
    """Scheduled job to generate cleanup reports"""
    try:
        logger.info("🧹 Running scheduled cleanup job...")
        result = await CleanupService.generate_cleanup_report()
        if result.get("success"):
            logger.info("✅ Cleanup job completed successfully")
            logger.info(f"📊 Report: {result.get('report')}")
        else:
            logger.error(f"❌ Cleanup job failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"❌ Cleanup job error: {e}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    import os
    is_cloud_run = os.path.exists("/workspace")
    
    try:
        logger.info("🚀 Starting Ship Management System API V2...")
        
        # Debug: Log environment info
        mongo_url = os.environ.get('MONGO_URL', 'NOT SET')
        if mongo_url != 'NOT SET' and '@' in mongo_url:
            # Mask password for logging
            parts = mongo_url.split('@')
            host_part = parts[1] if len(parts) > 1 else 'unknown'
            logger.info(f"🔗 MONGO_URL host: {host_part[:50]}...")
        else:
            logger.warning(f"⚠️ MONGO_URL status: {mongo_url[:20] if mongo_url else 'NOT SET'}...")
        
        logger.info(f"🌐 Is Cloud Run: {is_cloud_run}")
        logger.info(f"📁 /workspace exists: {os.path.exists('/workspace')}")
        
        # Connect to database with retry (reduced retries for cloud)
        max_retries = 2 if is_cloud_run else 3
        for attempt in range(max_retries):
            try:
                await mongo_db.connect()
                logger.info("✅ Database connected")
                break
            except Exception as db_error:
                logger.warning(f"⚠️ Database connection attempt {attempt + 1}/{max_retries} failed: {db_error}")
                if attempt == max_retries - 1:
                    logger.error("❌ Could not connect to database after all retries")
                else:
                    import asyncio
                    await asyncio.sleep(1)  # Shorter wait
        
        # Initialize admin if needed (skip on cloud for faster startup)
        if mongo_db.connected and not is_cloud_run:
            try:
                from app.utils.init_admin import init_admin_if_needed
                await init_admin_if_needed()
            except Exception as admin_error:
                logger.warning(f"⚠️ Admin initialization skipped: {admin_error}")
        
        # Setup scheduled jobs (skip on cloud for faster startup)
        if not is_cloud_run:
            scheduler.add_job(
                scheduled_cleanup_job,
                CronTrigger(hour=2, minute=0),
                id="cleanup_job",
                name="Daily Cleanup Report",
                replace_existing=True
            )
            scheduler.start()
            logger.info("✅ Scheduler started - Cleanup job scheduled for 2:00 AM daily")
        
        logger.info(f"✅ {settings.PROJECT_NAME} v{settings.VERSION} is ready!")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        # Don't raise - let the app start anyway for health checks

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        # Shutdown scheduler
        scheduler.shutdown()
        logger.info("✅ Scheduler shut down")
        
        # Disconnect database
        await mongo_db.disconnect()
        logger.info("✅ Database disconnected")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

# Mount uploads folder (use relative path for cloud deployment)
import os
# Use /tmp for Cloud Run (writable) or fallback to local path
if os.path.exists("/workspace"):
    # Running on Cloud Run
    uploads_path = Path("/tmp/uploads")
else:
    # Running locally
    uploads_path = Path("/app/uploads")
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Include API router
app.include_router(api_router, prefix="/api")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": "connected" if mongo_db.connected else "disconnected"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Ship Management System API V2",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }
