from fastapi import FastAPI

from app.api.v1 import auth, users, orders, marketdata, trades
from app.core.database import init_db

def create_app() -> FastAPI:
    app = FastAPI(title="jrd-alphamind-backend")

    # include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
    app.include_router(marketdata.router, prefix="/api/v1/marketdata", tags=["marketdata"])
    app.include_router(trades.router, prefix="/api/v1/trades", tags=["trades"])
    app.include_router(
        __import__("app.api.v1.instruments", fromlist=["router"]).router,
        prefix="/api/v1/instruments",
        tags=["instruments"],
    )
    # include orders router (we had a placeholder earlier)
    app.include_router(
        __import__("app.api.v1.orders", fromlist=["router"]).router,
        prefix="/api/v1/orders",
        tags=["orders"],
    )

    # initialize DB in dev
    @app.on_event("startup")
    def on_startup():
        init_db()

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
