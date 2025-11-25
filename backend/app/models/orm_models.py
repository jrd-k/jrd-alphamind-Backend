from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import registry
from datetime import datetime

# Use SQLAlchemy 2.0 registry / modern declarative mapping
mapper_registry = registry()
Base = mapper_registry.generate_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    symbol = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    status = Column(String, default="new")
    created_at = Column(DateTime, default=datetime.utcnow)


class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)


# Trade model for executed trades
class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False)  # 'buy' or 'sell'
    price = Column(Float, nullable=False)
    qty = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    order_id = Column(String, nullable=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    # 'metadata' is a reserved attribute name on the declarative base; store
    # the JSON in a different attribute name that maps to the DB column 'metadata'
    metadata_json = Column('metadata', JSON, nullable=True)


# Indicator signal model: stores outputs from external indicator engines (e.g., TradingView alerts)
class IndicatorSignal(Base):
    __tablename__ = "indicator_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    source = Column(String, nullable=False, default="supertrend_ai")
    signal = Column(String, nullable=True)
    value = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class BrainDecision(Base):
    __tablename__ = "brain_decisions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    decision = Column(String, nullable=False)
    indicator = Column(JSON, nullable=True)
    deepseek = Column(JSON, nullable=True)
    openai = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Expose a property named `metadata` on the mapped class after mapping has been
# constructed. Declaring a class-level attribute named `metadata` conflicts with
# SQLAlchemy's declarative internals, so we attach a property dynamically.
def _trade_get_metadata(self):
    return getattr(self, "metadata_json", None)


def _trade_set_metadata(self, value):
    setattr(self, "metadata_json", value)


setattr(Trade, "metadata", property(_trade_get_metadata, _trade_set_metadata))
