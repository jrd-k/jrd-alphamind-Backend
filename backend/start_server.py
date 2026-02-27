#!/usr/bin/env python3
"""
AlphaMind Backend Server Startup Script
Handles PYTHONPATH and proper server initialization
"""
import sys
import os
from contextlib import asynccontextmanager

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from app.main import create_app
from app.core.database import init_db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan event handler"""
    # Startup
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

    yield

    # Shutdown
    logger.info("Application shutting down...")

def create_production_app():
    """Create app with proper lifespan management"""
    app = create_app()

    # Override the lifespan if needed
    # For now, we'll keep the existing startup event but add proper error handling

    return app

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting AlphaMind Backend Server...")

    try:
        app = create_production_app()
        logger.info("Application created successfully")

        # Start server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)