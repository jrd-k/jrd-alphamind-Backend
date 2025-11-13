from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Iterator

from app.core.config import settings


connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # import models Base to create tables
    from app.models.orm_models import Base, Instrument
    import time
    from sqlalchemy.exc import OperationalError

    # Try creating tables, retry if DB not ready (useful when Postgres container starts)
    attempts = 0
    while True:
        try:
            Base.metadata.create_all(bind=engine)
            # seed some instruments if none
            Session = sessionmaker(bind=engine)
            s = Session()
            try:
                count = s.query(Instrument).count()
                if count == 0:
                    seeds = [
                        Instrument(symbol="EURUSD", name="EUR / USD"),
                        Instrument(symbol="BTCUSD", name="BTC / USD"),
                        Instrument(symbol="AAPL", name="Apple Inc."),
                    ]
                    s.add_all(seeds)
                    s.commit()
            finally:
                s.close()
            break
        except OperationalError:
            attempts += 1
            if attempts > 10:
                raise
            time.sleep(1)
