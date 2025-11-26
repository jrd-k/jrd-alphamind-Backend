try:
    # Try pydantic v1
    from pydantic import BaseSettings  # type: ignore

    class Settings(BaseSettings):
        app_name: str = "jrd-alphamind-backend"
        debug: bool = True
        database_url: str = "sqlite:///./dev.db"
        redis_url: str = "redis://localhost:6379/0"
        # JWT settings
        jwt_secret: str = "change-me-in-production"
        jwt_algorithm: str = "HS256"
        jwt_exp_minutes: int = 60
        # Indicator API key (optional). If empty, indicator endpoints are public.
        indicator_api_key: str = ""
        # Scheduler settings
        scheduler_enabled: bool = True
        scheduler_interval_seconds: int = 60
        scheduler_auto_execute: bool = False
        # CORS: comma-separated list of allowed frontend origins
        frontend_origins: str = "http://localhost:3000,http://localhost:5173"
        # MT5 Configuration (optional)
        mt5_path: str = ""
        mt5_account: str = ""
        mt5_password: str = ""

        class Config:
            env_file = ".env"

    settings = Settings()
except Exception:
    try:
        # pydantic v2: BaseSettings moved to pydantic-settings package
        from pydantic_settings import BaseSettings  # type: ignore

        class Settings(BaseSettings):
            app_name: str = "jrd-alphamind-backend"
            debug: bool = True
            database_url: str = "sqlite:///./dev.db"
            redis_url: str = "redis://localhost:6379/0"
            # DeepSeek AI service
            deepseek_api_key: str = ""
            deepseek_base_url: str = "https://api.deepseek.ai/v1"
            # OpenAI
            openai_api_key: str = ""
            openai_base_url: str = "https://api.openai.com/v1"
            # Trading execution
            enable_live_trading: bool = False
            max_trade_qty: float = 1.0
            # Confirm live trading token - must equal 'CONFIRM-LIVE' to allow live execution
            confirm_live_token: str = ""
            # DeepSeek AI service
            deepseek_api_key: str = ""
            deepseek_base_url: str = "https://api.deepseek.ai/v1"
            # OpenAI
            openai_api_key: str = ""
            openai_base_url: str = "https://api.openai.com/v1"
            # JWT settings
            jwt_secret: str = "change-me-in-production"
            jwt_algorithm: str = "HS256"
            jwt_exp_minutes: int = 60
            # Indicator API key (optional). If empty, indicator endpoints are public.
            indicator_api_key: str = ""
            # Scheduler settings
            scheduler_enabled: bool = True
            scheduler_interval_seconds: int = 60
            scheduler_auto_execute: bool = False
            # CORS: comma-separated list of allowed frontend origins
            frontend_origins: str = "http://localhost:3000,http://localhost:5173"
            # MT5 Configuration (optional)
            mt5_path: str = ""
            mt5_account: str = ""
            mt5_password: str = ""

            class Config:
                env_file = ".env"

        settings = Settings()
    except Exception:
        # Fallback: lightweight settings object that reads from environment
        import os

        class Settings:
            app_name: str = os.getenv("APP_NAME", "jrd-alphamind-backend")
            debug: bool = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")
            database_url: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
            redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            # DeepSeek AI service
            deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
            deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.ai/v1")
            # OpenAI
            openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
            openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            # Trading execution
            enable_live_trading: bool = os.getenv("ENABLE_LIVE_TRADING", "False").lower() in ("1", "true", "yes")
            max_trade_qty: float = float(os.getenv("MAX_TRADE_QTY", "1.0"))
            confirm_live_token: str = os.getenv("CONFIRM_LIVE", "")
            jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
            jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
            jwt_exp_minutes: int = int(os.getenv("JWT_EXP_MINUTES", "60"))
            indicator_api_key: str = os.getenv("INDICATOR_API_KEY", "")
            scheduler_enabled: bool = os.getenv("SCHEDULER_ENABLED", "True").lower() in ("1", "true", "yes")
            scheduler_interval_seconds: int = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "60"))
            scheduler_auto_execute: bool = os.getenv("SCHEDULER_AUTO_EXECUTE", "False").lower() in ("1", "true", "yes")
            # CORS: comma-separated list of allowed frontend origins
            frontend_origins: str = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://localhost:5173")
            # MT5 Configuration (optional)
            mt5_path: str = os.getenv("MT5_PATH", "")
            mt5_account: str = os.getenv("MT5_ACCOUNT", "")
            mt5_password: str = os.getenv("MT5_PASSWORD", "")

        settings = Settings()
