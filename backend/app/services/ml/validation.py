"""
ML Model Validation

Implements robust validation techniques:
- Walk-forward validation
- Purged K-fold cross-validation
- Performance metrics calculation
- Risk-adjusted returns analysis
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import roc_auc_score, average_precision_score
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MLValidator:
    """Validate ML trading models with time-series aware techniques."""

    def __init__(self,
                 n_splits: int = 5,
                 embargo_periods: int = 5,
                 purge_periods: int = 10):
        """
        Initialize validator.

        Args:
            n_splits: Number of splits for cross-validation
            embargo_periods: Periods to embargo after test set
            purge_periods: Periods to purge between train/test
        """
        self.n_splits = n_splits
        self.embargo_periods = embargo_periods
        self.purge_periods = purge_periods

    def walk_forward_validation(self,
                               df: pd.DataFrame,
                               predictions: np.ndarray,
                               actual_returns: pd.Series,
                               transaction_cost_pct: float = 0.0005) -> Dict[str, Any]:
        """
        Perform walk-forward validation with trading simulation.

        Args:
            df: DataFrame with features and labels
            predictions: Model predictions (0/1)
            actual_returns: Actual future returns
            transaction_cost_pct: Transaction cost percentage

        Returns:
            Dictionary with validation results
        """
        if len(predictions) != len(actual_returns):
            raise ValueError("Predictions and returns must have same length")

        # Simulate trading
        portfolio_returns = []
        trades = []
        cumulative_return = 1.0

        for i, (pred, ret) in enumerate(zip(predictions, actual_returns)):
            if pred == 1:  # Long signal
                # Apply transaction costs
                net_return = ret - (2 * transaction_cost_pct)  # Round trip cost
                portfolio_returns.append(net_return)
                trades.append({
                    'index': i,
                    'type': 'long',
                    'return': net_return,
                    'gross_return': ret
                })
                cumulative_return *= (1 + net_return)
            else:
                portfolio_returns.append(0.0)  # No trade
                trades.append({
                    'index': i,
                    'type': 'no_trade',
                    'return': 0.0,
                    'gross_return': ret
                })

        # Calculate metrics
        portfolio_returns = np.array(portfolio_returns)
        trades_df = pd.DataFrame(trades)

        results = {
            'total_periods': len(predictions),
            'total_trades': len(trades_df[trades_df['type'] == 'long']),
            'win_rate': (portfolio_returns > 0).mean(),
            'avg_win': portfolio_returns[portfolio_returns > 0].mean() if (portfolio_returns > 0).any() else 0,
            'avg_loss': portfolio_returns[portfolio_returns < 0].mean() if (portfolio_returns < 0).any() else 0,
            'profit_factor': abs(portfolio_returns[portfolio_returns > 0].sum() /
                               portfolio_returns[portfolio_returns < 0].sum()) if (portfolio_returns < 0).any() else np.inf,
            'total_return': cumulative_return - 1.0,
            'annualized_return': (cumulative_return) ** (252 / len(predictions)) - 1 if len(predictions) > 0 else 0,
            'sharpe_ratio': self._calculate_sharpe_ratio(portfolio_returns),
            'max_drawdown': self._calculate_max_drawdown(portfolio_returns),
            'calmar_ratio': self._calculate_calmar_ratio(portfolio_returns),
            'trades': trades_df.to_dict('records')
        }

        return results

    def purged_kfold_validation(self,
                               X: pd.DataFrame,
                               y: pd.Series,
                               predictions: np.ndarray,
                               embargo_pct: float = 0.01) -> Dict[str, Any]:
        """
        Perform purged K-fold cross-validation.

        Args:
            X: Feature DataFrame
            y: Target series
            predictions: Model predictions
            embargo_pct: Embargo percentage

        Returns:
            Dictionary with cross-validation results
        """
        # Time series split with purging
        tscv = TimeSeriesSplit(n_splits=self.n_splits)

        cv_results = []

        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            # Apply purging and embargo
            purged_train_idx = self._apply_purging_embargo(
                train_idx, test_idx, len(X), embargo_pct
            )

            # Get fold data
            y_test = y.iloc[test_idx]
            y_pred = predictions[test_idx]

            # Calculate metrics
            metrics = self._calculate_classification_metrics(y_test, y_pred)

            fold_result = {
                'fold': fold + 1,
                'train_size': len(purged_train_idx),
                'test_size': len(test_idx),
                'metrics': metrics
            }

            cv_results.append(fold_result)

        # Aggregate results
        aggregated = self._aggregate_cv_results(cv_results)

        return {
            'fold_results': cv_results,
            'aggregated': aggregated
        }

    def _apply_purging_embargo(self,
                              train_idx: np.ndarray,
                              test_idx: np.ndarray,
                              total_size: int,
                              embargo_pct: float) -> np.ndarray:
        """Apply purging and embargo to training indices."""
        # Convert to sets for easier manipulation
        train_set = set(train_idx)
        test_set = set(test_idx)

        # Embargo: Remove training samples too close to test set
        embargo_size = int(len(test_idx) * embargo_pct)
        if embargo_size > 0:
            # Remove points before test set
            embargo_start = max(0, min(test_idx) - embargo_size)
            embargo_end = max(test_idx) + embargo_size

            embargo_set = set(range(embargo_start, min(embargo_end + 1, total_size)))
            train_set = train_set - embargo_set

        # Purging: Remove training samples that overlap with test period
        purge_start = max(0, min(test_idx) - self.purge_periods)
        purge_end = min(total_size, max(test_idx) + self.purge_periods)

        purge_set = set(range(purge_start, purge_end + 1))
        train_set = train_set - purge_set

        return np.array(sorted(list(train_set)))

    def _calculate_classification_metrics(self,
                                        y_true: pd.Series,
                                        y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate classification metrics."""
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0),
        }

        # Add AUC if predictions are probabilities
        if y_pred.dtype == float and np.all((y_pred >= 0) & (y_pred <= 1)):
            try:
                metrics['auc'] = roc_auc_score(y_true, y_pred)
                metrics['average_precision'] = average_precision_score(y_true, y_pred)
            except Exception as e:
                logger.warning(f"Could not calculate AUC metrics: {e}")

        return metrics

    def _aggregate_cv_results(self, cv_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate cross-validation results."""
        if not cv_results:
            return {}

        metrics_list = [fold['metrics'] for fold in cv_results]

        aggregated = {}
        for metric in metrics_list[0].keys():
            values = [m[metric] for m in metrics_list if metric in m]
            if values:
                aggregated[f'{metric}_mean'] = np.mean(values)
                aggregated[f'{metric}_std'] = np.std(values)
                aggregated[f'{metric}_min'] = np.min(values)
                aggregated[f'{metric}_max'] = np.max(values)

        return aggregated

    def _calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate
        return np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns)

    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown."""
        if len(returns) == 0:
            return 0.0

        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)

    def _calculate_calmar_ratio(self, returns: np.ndarray) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)."""
        if len(returns) == 0:
            return 0.0

        total_return = np.prod(1 + returns) - 1
        max_dd = self._calculate_max_drawdown(returns)

        if max_dd == 0:
            return np.inf if total_return > 0 else 0.0

        return abs(total_return / max_dd)

    def plot_validation_results(self, results: Dict[str, Any], save_path: Optional[str] = None):
        """Plot validation results."""
        if 'trades' not in results:
            return

        trades_df = pd.DataFrame(results['trades'])

        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # 1. Cumulative returns
        if 'return' in trades_df.columns:
            cumulative = (1 + trades_df['return']).cumprod()
            axes[0, 0].plot(cumulative)
            axes[0, 0].set_title('Cumulative Returns')
            axes[0, 0].set_xlabel('Trade Number')
            axes[0, 0].set_ylabel('Cumulative Return')
            axes[0, 0].grid(True)

        # 2. Trade returns distribution
        winning_trades = trades_df[trades_df['return'] > 0]['return']
        losing_trades = trades_df[trades_df['return'] < 0]['return']

        if not winning_trades.empty:
            axes[0, 1].hist(winning_trades, alpha=0.7, label='Winning Trades', color='green')
        if not losing_trades.empty:
            axes[0, 1].hist(losing_trades, alpha=0.7, label='Losing Trades', color='red')

        axes[0, 1].set_title('Trade Returns Distribution')
        axes[0, 1].set_xlabel('Return')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].legend()
        axes[0, 1].grid(True)

        # 3. Drawdown
        if 'return' in trades_df.columns:
            cumulative = (1 + trades_df['return']).cumprod()
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max

            axes[1, 0].plot(drawdown)
            axes[1, 0].set_title('Drawdown')
            axes[1, 0].set_xlabel('Trade Number')
            axes[1, 0].set_ylabel('Drawdown')
            axes[1, 0].fill_between(range(len(drawdown)), drawdown, 0, alpha=0.3, color='red')
            axes[1, 0].grid(True)

        # 4. Rolling win rate
        if 'return' in trades_df.columns:
            win_rate = (trades_df['return'] > 0).rolling(window=20).mean()
            axes[1, 1].plot(win_rate)
            axes[1, 1].set_title('Rolling Win Rate (20 trades)')
            axes[1, 1].set_xlabel('Trade Number')
            axes[1, 1].set_ylabel('Win Rate')
            axes[1, 1].grid(True)
            axes[1, 1].axhline(y=0.5, color='red', linestyle='--', alpha=0.7)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()

        plt.close()