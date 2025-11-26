from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, users, orders, marketdata, trades, instruments, accounts, websockets
from app.core.database import init_db
from app.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(title="jrd-alphamind-backend")

    # Configure CORS
    allowed_origins = [o.strip() for o in settings.frontend_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
    app.include_router(marketdata.router, prefix="/api/v1/marketdata", tags=["marketdata"])
    app.include_router(trades.router, prefix="/api/v1/trades", tags=["trades"])
    app.include_router(instruments.router, prefix="/api/v1/instruments", tags=["instruments"])
    app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["accounts"])
    app.include_router(websockets.router, tags=["websockets"])
    # orchestrator and indicators
    from app.api.v1 import orchestrator, indicators, brain, webhook, economic_calendar

    app.include_router(orchestrator.router, prefix="/api/v1/orchestrator", tags=["orchestrator"])
    app.include_router(indicators.router, prefix="/api/v1/indicators", tags=["indicators"])
    app.include_router(brain.router, prefix="/api/v1/brain", tags=["brain"])
    app.include_router(economic_calendar.router, prefix="/api/v1", tags=["economic-calendar"])
    # webhook.router already defines prefix "/webhook"; include under /api/v1
    app.include_router(webhook.router, prefix="/api/v1")

    # initialize DB in dev
    @app.on_event("startup")
    def on_startup():
        import asyncio
        import logging
        from app.workers.scheduler import get_scheduler

        logger = logging.getLogger(__name__)
        init_db()
        
        # Start scheduler
        scheduler = get_scheduler()
        if scheduler.enabled:
            loop = asyncio.get_event_loop()
            task = loop.create_task(scheduler.start())
            logger.info("Scheduler task created")

    @app.on_event("shutdown")
    def on_shutdown():
        import asyncio
        import logging
        from app.workers.scheduler import get_scheduler

        logger = logging.getLogger(__name__)
        scheduler = get_scheduler()
        try:
            asyncio.run(scheduler.stop())
            logger.info("Scheduler stopped on shutdown")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    return app


app = create_app()

# Ensure DB tables exist when the module is imported (helps tests and dev runs)
try:
    init_db()
except Exception:
    # swallow creation errors here; startup event will also try
    pass

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
