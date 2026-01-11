"""
ML Trading Service Orchestrator

Main service that coordinates all ML components:
- Feature engineering
- Model training and validation
- Risk management
- Live execution
- Performance monitoring
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime, timedelta
import json
import os

from .feature_engineering import MLFeatureEngineer
from .label_generation import MLLabelGenerator
from .model_training import MLModelTrainer
from .validation import MLValidator
from .risk_management import MLRiskManager
from .execution import MLExecutionEngine

logger = logging.getLogger(__name__)


class MLTradingService:
    """Main ML trading service orchestrator."""

    def __init__(self,
                 brain_service=None,
                 trade_orchestrator=None,
                 config: Dict[str, Any] = None):
        """
        Initialize ML trading service.

        Args:
            brain_service: Brain service instance
            trade_orchestrator: Trade orchestrator instance
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.brain_service = brain_service
        self.trade_orchestrator = trade_orchestrator

        # Initialize components
        self.feature_engineer = MLFeatureEngineer()
        self.label_generator = MLLabelGenerator(
            future_periods=self.config['future_periods'],
            return_threshold=self.config['return_threshold']
        )
        self.model_trainer = MLModelTrainer(
            model_dir=self.config['model_dir']
        )
        self.validator = MLValidator(
            n_splits=self.config['validation_splits']
        )
        self.risk_manager = MLRiskManager(
            max_position_size_pct=self.config['max_position_size_pct'],
            max_portfolio_risk_pct=self.config['max_portfolio_risk_pct']
        )

        # Initialize execution engine if services available
        self.execution_engine = None
        if brain_service and trade_orchestrator:
            self.execution_engine = MLExecutionEngine(
                brain_service=brain_service,
                risk_manager=self.risk_manager,
                trade_orchestrator=trade_orchestrator,
                confidence_threshold=self.config['confidence_threshold']
            )

        # State
        self.trained_models = {}
        self.feature_columns = []
        self.is_live = False

        logger.info("ML Trading Service initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'future_periods': 5,
            'return_threshold': 0.001,
            'validation_splits': 5,
            'max_position_size_pct': 0.01,
            'max_portfolio_risk_pct': 0.02,
            'confidence_threshold': 0.6,
            'model_dir': 'models',
            'training_data_path': 'data/training_data.csv',
            'live_update_interval': 60,  # seconds
        }

    async def train_model(self,
                         historical_data: pd.DataFrame,
                         target_symbol: str = 'EURUSD',
                         force_retrain: bool = False) -> Dict[str, Any]:
        """
        Train ML model on historical data.

        Args:
            historical_data: OHLCV DataFrame with historical data
            target_symbol: Target trading symbol
            force_retrain: Force retraining even if model exists

        Returns:
            Training results dictionary
        """
        try:
            logger.info(f"Starting model training for {target_symbol}")

            # Check if model already exists
            if not force_retrain and target_symbol in self.trained_models:
                logger.info(f"Model for {target_symbol} already exists, skipping training")
                return self.trained_models[target_symbol]

            # Step 1: Feature Engineering
            logger.info("Generating features...")
            featured_data = self.feature_engineer.create_features(historical_data)

            # Step 2: Label Generation
            logger.info("Generating labels...")
            labeled_data = self.label_generator.create_labels(featured_data)
            labeled_data = self.label_generator.filter_valid_labels(labeled_data)

            if labeled_data.empty:
                raise ValueError("No valid labeled data after filtering")

            # Step 3: Prepare training data
            feature_cols = [col for col in labeled_data.columns
                          if col.startswith(('price_', 'trend_', 'momentum_', 'volatility_',
                                           'candle_', 'market_'))]

            self.feature_columns = feature_cols

            # Step 4: Train model
            logger.info(f"Training model with {len(feature_cols)} features...")
            training_results = self.model_trainer.train_walk_forward(
                df=labeled_data,
                feature_cols=feature_cols,
                label_col='label_binary'
            )

            # Step 5: Validate model
            logger.info("Validating model...")
            predictions = []
            actual_returns = []

            for fold in training_results['fold_results']:
                predictions.extend(fold['predictions'])
                actual_returns.extend(fold['actuals'])

            validation_results = self.validator.walk_forward_validation(
                df=labeled_data,
                predictions=np.array(predictions),
                actual_returns=np.array(actual_returns)
            )

            # Step 6: Store results
            model_info = {
                'symbol': target_symbol,
                'training_results': training_results,
                'validation_results': validation_results,
                'feature_columns': feature_cols,
                'trained_at': datetime.now(),
                'data_points': len(labeled_data),
                'feature_count': len(feature_cols)
            }

            self.trained_models[target_symbol] = model_info

            # Save model info
            self._save_model_info(model_info)

            logger.info(f"Model training completed for {target_symbol}")
            return model_info

        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise

    async def start_live_trading(self) -> bool:
        """Start live trading mode."""
        try:
            if not self.execution_engine:
                logger.error("Execution engine not available")
                return False

            if not self.trained_models:
                logger.warning("No trained models available for live trading")
                return False

            self.is_live = True
            logger.info("Live trading started")

            # Start live processing loop
            asyncio.create_task(self._live_processing_loop())

            return True

        except Exception as e:
            logger.error(f"Error starting live trading: {e}")
            return False

    async def stop_live_trading(self) -> bool:
        """Stop live trading mode."""
        try:
            self.is_live = False
            logger.info("Live trading stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping live trading: {e}")
            return False

    async def _live_processing_loop(self):
        """Main live processing loop."""
        while self.is_live:
            try:
                # Get latest market data
                market_data = await self._get_latest_market_data()

                if market_data:
                    # Process through execution engine
                    signal = await self.execution_engine.process_market_data(market_data)

                    if signal:
                        logger.info(f"Generated trading signal: {signal}")

                # Wait for next update
                await asyncio.sleep(self.config['live_update_interval'])

            except Exception as e:
                logger.error(f"Error in live processing loop: {e}")
                await asyncio.sleep(10)  # Brief pause on error

    async def _get_latest_market_data(self) -> Optional[Dict[str, Any]]:
        """Get latest market data for live processing."""
        # This would integrate with market data feed
        # For now, return None (placeholder)
        return None

    async def get_model_performance(self, symbol: str = None) -> Dict[str, Any]:
        """Get model performance metrics."""
        try:
            if symbol and symbol in self.trained_models:
                model_info = self.trained_models[symbol]
                return {
                    'symbol': symbol,
                    'training_metrics': self.model_trainer.get_training_summary(
                        model_info['training_results']
                    ),
                    'validation_metrics': model_info['validation_results'],
                    'last_updated': model_info['trained_at']
                }

            # Aggregate all models
            all_performance = {}
            for sym, model_info in self.trained_models.items():
                all_performance[sym] = await self.get_model_performance(sym)

            return all_performance

        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return {}

    async def predict(self, symbol: str, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get ML prediction for given symbol and features."""
        try:
            if symbol not in self.trained_models:
                logger.warning(f"No trained model available for {symbol}")
                return None

            model_info = self.trained_models[symbol]

            # Load the best model
            model_name = f"best_model_{model_info['trained_at'].strftime('%Y%m%d_%H%M%S')}"
            try:
                model = self.model_trainer.load_model(model_name)
            except FileNotFoundError:
                # Try to find any model file for this symbol
                model_files = [f for f in os.listdir(self.config['model_dir'])
                              if f.startswith('best_model_') and f.endswith('.joblib')]
                if model_files:
                    model = self.model_trainer.load_model(model_files[0].replace('.joblib', ''))
                else:
                    logger.error(f"No model file found for {symbol}")
                    return None

            # Prepare features DataFrame
            feature_df = pd.DataFrame([features])

            # Ensure all required features are present
            required_features = model_info['feature_columns']
            missing_features = [f for f in required_features if f not in feature_df.columns]
            if missing_features:
                logger.warning(f"Missing features for {symbol}: {missing_features}")
                # Fill missing features with 0
                for feature in missing_features:
                    feature_df[feature] = 0.0

            # Make prediction
            prediction_result = self.model_trainer.predict(model, feature_df[required_features])

            # Add metadata
            prediction_result.update({
                'symbol': symbol,
                'model_version': model_info['trained_at'].isoformat(),
                'feature_count': len(required_features),
                'timestamp': datetime.now().isoformat()
            })

            return prediction_result

        except Exception as e:
            logger.error(f"Error getting prediction for {symbol}: {e}")
            return None

    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        try:
            if self.execution_engine:
                return await self.execution_engine.get_execution_stats()
            else:
                return {'status': 'execution_engine_not_available'}

        except Exception as e:
            logger.error(f"Error getting execution stats: {e}")
            return {}

    def _save_model_info(self, model_info: Dict[str, Any]):
        """Save model information to disk."""
        try:
            os.makedirs(self.config['model_dir'], exist_ok=True)

            filename = f"model_info_{model_info['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.config['model_dir'], filename)

            # Convert datetime to string
            model_info_copy = model_info.copy()
            model_info_copy['trained_at'] = model_info_copy['trained_at'].isoformat()

            with open(filepath, 'w') as f:
                json.dump(model_info_copy, f, indent=2, default=str)

            logger.info(f"Model info saved to {filepath}")

        except Exception as e:
            logger.error(f"Error saving model info: {e}")

    async def load_models(self) -> bool:
        """Load saved models from disk."""
        try:
            if not os.path.exists(self.config['model_dir']):
                logger.info("Model directory does not exist")
                return False

            # Find latest model files
            model_files = [f for f in os.listdir(self.config['model_dir'])
                          if f.startswith('model_info_') and f.endswith('.json')]

            if not model_files:
                logger.info("No saved models found")
                return False

            loaded_count = 0
            for filename in model_files:
                try:
                    filepath = os.path.join(self.config['model_dir'], filename)

                    with open(filepath, 'r') as f:
                        model_info = json.load(f)

                    # Convert datetime string back
                    model_info['trained_at'] = datetime.fromisoformat(model_info['trained_at'])

                    symbol = model_info['symbol']
                    self.trained_models[symbol] = model_info
                    loaded_count += 1

                except Exception as e:
                    logger.error(f"Error loading model {filename}: {e}")

            logger.info(f"Loaded {loaded_count} models")
            return loaded_count > 0

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False

    async def update_models(self, new_data: pd.DataFrame) -> Dict[str, Any]:
        """Update models with new data."""
        try:
            update_results = {}

            for symbol in self.trained_models.keys():
                try:
                    # Retrain model with new data
                    result = await self.train_model(new_data, symbol, force_retrain=True)
                    update_results[symbol] = {'status': 'updated', 'result': result}

                except Exception as e:
                    logger.error(f"Error updating model for {symbol}: {e}")
                    update_results[symbol] = {'status': 'error', 'error': str(e)}

            return update_results

        except Exception as e:
            logger.error(f"Error updating models: {e}")
            return {'error': str(e)}

    def get_service_status(self) -> Dict[str, Any]:
        """Get overall service status."""
        return {
            'is_live': self.is_live,
            'trained_models_count': len(self.trained_models),
            'available_symbols': list(self.trained_models.keys()),
            'execution_engine_available': self.execution_engine is not None,
            'feature_engineer_ready': True,
            'last_update': datetime.now()
        }