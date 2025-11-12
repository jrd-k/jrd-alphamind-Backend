from fastapi import FastAPI

from app.api.v1 import auth, users, orders, marketdata

def create_app() -> FastAPI:
    app = FastAPI(title="jrd-alphamind-backend")

    # include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
    app.include_router(marketdata.router, prefix="/api/v1/marketdata", tags=["marketdata"])

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
