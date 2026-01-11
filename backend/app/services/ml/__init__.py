"""
ML Trading Service

Comprehensive ML-based trading system with:
- Feature engineering from market data
- Label generation for supervised learning
- XGBoost model training with walk-forward validation
- Risk management and position sizing
- Live execution engine
- Data loading and preprocessing
"""

from .feature_engineering import MLFeatureEngineer
from .label_generation import MLLabelGenerator
from .model_training import MLModelTrainer
from .validation import MLValidator
from .risk_management import MLRiskManager
from .execution import MLExecutionEngine
from .data_loader import MLDataLoader
from .ml_service import MLTradingService

__all__ = [
    'MLFeatureEngineer',
    'MLLabelGenerator',
    'MLModelTrainer',
    'MLValidator',
    'MLRiskManager',
    'MLExecutionEngine',
    'MLDataLoader',
    'MLTradingService'
]