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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    try:
        logger.info("🚀 Starting Ship Management System API V2...")
        
        # Connect to database
        await mongo_db.connect()
        logger.info("✅ Database connected")
        
        # Initialize admin if needed (auto-create from .env)
        from app.utils.init_admin import init_admin_if_needed
        await init_admin_if_needed()
        
        # Setup scheduled jobs
        # Run cleanup job daily at 2:00 AM
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
        logger.error(f"❌ Startup failed: {e}")
        raise

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

# Mount uploads folder (shared with backend-v1)
uploads_path = Path("/app/uploads")
uploads_path.mkdir(exist_ok=True)
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
