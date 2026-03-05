from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, users, orders, marketdata, trades, instruments, accounts, websockets, ml, general
from app.api.v1 import orchestrator, indicators, brain, webhook, economic_calendar, position_sizing, risk_management
from app.api.v1 import broker_accounts, websockets_secure
from app.core.database import init_db
from app.core.config import settings

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    import logging

    logger = logging.getLogger(__name__)
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    logger.info("Application startup complete")
    yield
    # shutdown
    import asyncio, logging

    logger = logging.getLogger(__name__)
    # scheduler shutdown logic could go here if needed


def create_app() -> FastAPI:
    app = FastAPI(title="jrd-alphamind-backend", lifespan=lifespan)

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
    app.include_router(marketdata.router, prefix="/api/stocks", tags=["marketdata"])  # Frontend compatibility - for chart data
    app.include_router(marketdata.router, prefix="/api/v1/marketdata", tags=["marketdata"])
    app.include_router(trades.router, prefix="/api/v1/trades", tags=["trades"])
    app.include_router(instruments.router, prefix="/api/v1/instruments", tags=["instruments"])
    app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["accounts"])
    app.include_router(ml.router, prefix="/api/v1/ml", tags=["ml"])
    app.include_router(orchestrator.router, prefix="/api/v1/orchestrator", tags=["orchestrator"])
    app.include_router(indicators.router, prefix="/api/v1/indicators", tags=["indicators"])
    app.include_router(brain.router, prefix="/api/v1/brain", tags=["brain"])
    app.include_router(economic_calendar.router, prefix="/api/v1", tags=["economic-calendar"])
    app.include_router(position_sizing.router, prefix="/api/v1/position-sizing", tags=["position-sizing"])
    app.include_router(risk_management.router, prefix="/api/v1/risk", tags=["risk-management"])
    app.include_router(broker_accounts.router, prefix="/api/v1", tags=["broker-accounts"])
    # webhook.router already defines prefix "/webhook"; include under /api/v1
    app.include_router(webhook.router, prefix="/api/v1")

    # Secure WebSocket endpoints
    app.websocket("/ws/trades")(websockets_secure.websocket_trades)
    app.websocket("/ws/market-data")(websockets_secure.websocket_market_data)


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
