"""
ML Model Training Pipeline

Implements XGBoost-based trading model with:
- Walk-forward validation
- Purged K-fold cross-validation
- Feature importance analysis
- Model persistence and loading
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MLModelTrainer:
    """Train and validate ML trading models."""

    def __init__(self,
                 model_dir: str = "models",
                 n_splits: int = 5,
                 test_size: int = 0.2,
                 random_state: int = 42):
        """
        Initialize model trainer.

        Args:
            model_dir: Directory to save trained models
            n_splits: Number of splits for time series validation
            test_size: Size of test set
            random_state: Random state for reproducibility
        """
        self.model_dir = model_dir
        self.n_splits = n_splits
        self.test_size = test_size
        self.random_state = random_state

        # Create model directory
        os.makedirs(self.model_dir, exist_ok=True)

        # XGBoost parameters
        self.xgb_params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': self.random_state,
            'verbosity': 1
        }

    def train_walk_forward(self,
                          df: pd.DataFrame,
                          feature_cols: List[str],
                          label_col: str = 'label_binary',
                          purge_periods: int = 5) -> Dict[str, Any]:
        """
        Train model using walk-forward validation.

        Args:
            df: DataFrame with features and labels
            feature_cols: List of feature column names
            label_col: Target label column
            purge_periods: Periods to purge between train/test

        Returns:
            Dictionary with training results and metrics
        """
        if df.empty or not all(col in df.columns for col in feature_cols + [label_col]):
            raise ValueError("Missing required columns in DataFrame")

        # Sort by time
        df = df.sort_index()

        # Prepare data
        X = df[feature_cols]
        y = df[label_col]

        # Walk-forward validation
        tscv = TimeSeriesSplit(n_splits=self.n_splits, test_size=int(len(df) * self.test_size))

        results = {
            'fold_results': [],
            'feature_importance': None,
            'best_model': None,
            'best_score': 0,
            'predictions': [],
            'actuals': []
        }

        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            logger.info(f"Training fold {fold + 1}/{self.n_splits}")

            # Get train/test data
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            # Purge overlapping periods
            if purge_periods > 0:
                X_train, y_train = self._purge_data(X_train, y_train, X_test, purge_periods)

            # Train model
            model = xgb.XGBClassifier(**self.xgb_params)
            model.fit(X_train, y_train)

            # Predict
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            y_pred = (y_pred_proba > 0.5).astype(int)

            # Calculate metrics
            metrics = self._calculate_metrics(y_test, y_pred, y_pred_proba)

            # Store results
            fold_result = {
                'fold': fold + 1,
                'train_size': len(X_train),
                'test_size': len(X_test),
                'metrics': metrics,
                'predictions': y_pred.tolist(),
                'actuals': y_test.tolist(),
                'probabilities': y_pred_proba.tolist()
            }

            results['fold_results'].append(fold_result)

            # Track best model
            if metrics['f1_score'] > results['best_score']:
                results['best_score'] = metrics['f1_score']
                results['best_model'] = model
                results['feature_importance'] = dict(zip(feature_cols, model.feature_importances_))

            results['predictions'].extend(y_pred.tolist())
            results['actuals'].extend(y_test.tolist())

        # Save best model
        if results['best_model']:
            self._save_model(results['best_model'], f"best_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        return results

    def _purge_data(self,
                   X_train: pd.DataFrame,
                   y_train: pd.Series,
                   X_test: pd.DataFrame,
                   purge_periods: int) -> Tuple[pd.DataFrame, pd.Series]:
        """Remove data points too close to test set."""
        # Simple purging: remove points within purge_periods of test start
        if len(X_test) > 0:
            test_start_idx = X_test.index[0]
            purge_end_idx = X_test.index[min(purge_periods, len(X_test) - 1)]

            # Remove training data that overlaps with purge period
            purge_mask = (X_train.index >= test_start_idx) & (X_train.index <= purge_end_idx)
            X_train = X_train[~purge_mask]
            y_train = y_train[~purge_mask]

        return X_train, y_train

    def _calculate_metrics(self,
                          y_true: pd.Series,
                          y_pred: np.ndarray,
                          y_proba: Optional[np.ndarray] = None) -> Dict[str, float]:
        """Calculate comprehensive metrics."""
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0),
        }

        if y_proba is not None:
            # Additional probability-based metrics
            metrics.update({
                'avg_probability': np.mean(y_proba),
                'probability_std': np.std(y_proba),
                'confidence_ratio': np.mean(y_proba > 0.6),  # High confidence predictions
            })

        return metrics

    def plot_feature_importance(self, feature_importance: Dict[str, float], top_n: int = 20):
        """Plot feature importance."""
        if not feature_importance:
            return

        # Sort features by importance
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        features, importance = zip(*sorted_features[:top_n])

        plt.figure(figsize=(12, 8))
        sns.barplot(x=list(importance), y=list(features))
        plt.title(f'Top {top_n} Feature Importance')
        plt.xlabel('Importance')
        plt.tight_layout()
        plt.savefig(os.path.join(self.model_dir, 'feature_importance.png'))
        plt.close()

    def plot_confusion_matrix(self, y_true: List[int], y_pred: List[int]):
        """Plot confusion matrix."""
        cm = confusion_matrix(y_true, y_pred)

        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=['No Trade', 'Trade'],
                   yticklabels=['No Trade', 'Trade'])
        plt.title('Confusion Matrix')
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.tight_layout()
        plt.savefig(os.path.join(self.model_dir, 'confusion_matrix.png'))
        plt.close()

    def _save_model(self, model: xgb.XGBClassifier, model_name: str):
        """Save trained model."""
        model_path = os.path.join(self.model_dir, f"{model_name}.joblib")
        joblib.dump(model, model_path)
        logger.info(f"Model saved to {model_path}")

    def load_model(self, model_name: str) -> xgb.XGBClassifier:
        """Load trained model."""
        model_path = os.path.join(self.model_dir, f"{model_name}.joblib")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model {model_name} not found")
        return joblib.load(model_path)

    def predict(self, model: xgb.XGBClassifier, features: pd.DataFrame) -> Dict[str, Any]:
        """Make predictions using trained model."""
        try:
            # Ensure features are in correct format
            if isinstance(features, dict):
                features = pd.DataFrame([features])

            # Make prediction
            probabilities = model.predict_proba(features)[:, 1]
            predictions = (probabilities > 0.5).astype(int)

            # Calculate confidence based on probability distance from 0.5
            confidence = np.abs(probabilities - 0.5) * 2  # Scale to 0-1 range

            return {
                'prediction': int(predictions[0]),
                'probability': float(probabilities[0]),
                'confidence': float(confidence[0]),
                'signal': 'BUY' if predictions[0] == 1 else 'SELL'
            }

        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {
                'prediction': 0,
                'probability': 0.5,
                'confidence': 0.0,
                'signal': 'HOLD',
                'error': str(e)
            }

    def get_training_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate training summary."""
        if not results['fold_results']:
            return {}

        fold_metrics = [fold['metrics'] for fold in results['fold_results']]

        summary = {
            'total_folds': len(results['fold_results']),
            'avg_accuracy': np.mean([m['accuracy'] for m in fold_metrics]),
            'avg_precision': np.mean([m['precision'] for m in fold_metrics]),
            'avg_recall': np.mean([m['recall'] for m in fold_metrics]),
            'avg_f1': np.mean([m['f1_score'] for m in fold_metrics]),
            'best_fold': np.argmax([m['f1_score'] for m in fold_metrics]) + 1,
            'overall_predictions': len(results['predictions']),
            'positive_predictions': sum(results['predictions']),
            'positive_ratio': sum(results['predictions']) / len(results['predictions']),
        }

        return summary