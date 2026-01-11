# Entry point for Google Cloud Buildpacks
# This file imports the FastAPI app from app.main
from app.main import app

# For local development with: python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
