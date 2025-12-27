# Entry point for uvicorn - imports from app.main
from app.main import app

# Re-export app for uvicorn
__all__ = ["app"]
