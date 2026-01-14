#!/usr/bin/env python3
"""
Simple XGBoost vs LightGBM comparison for ML trading.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import f1_score
import xgboost as xgb
import lightgbm as lgb
from datetime import datetime
import time

def generate_sample_data(n_samples=1000):
    """Generate sample trading data."""
    np.random.seed(42)

    # Generate OHLCV data
    data = []
    price = 1.0800

    for i in range(n_samples):
        # Random walk with trend
        change = np.random.normal(0, 0.001)
        price += change

        # Generate OHLCV
        high = price + abs(np.random.normal(0, 0.0005))
        low = price - abs(np.random.normal(0, 0.0005))
        open_price = price + np.random.normal(0, 0.0002)
        close = price
        volume = np.random.randint(100, 1000)

        data.append({
            'timestamp': pd.Timestamp('2024-01-01') + pd.Timedelta(hours=i),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df

def create_features(df):
    """Create technical indicators as features."""
    df = df.copy()

    # Price-based features
    df['returns'] = df['close'].pct_change()
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

    # Moving averages
    for period in [5, 10, 20, 50]:
        df[f'sma_{period}'] = df['close'].rolling(period).mean()
        df[f'ema_{period}'] = df['close'].ewm(span=period).mean()

    # Volatility
    df['volatility_10'] = df['returns'].rolling(10).std()
    df['volatility_20'] = df['returns'].rolling(20).std()

    # RSI
    def calculate_rsi(data, period=14):
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    df['rsi'] = calculate_rsi(df['close'])

    # MACD
    ema_12 = df['close'].ewm(span=12).mean()
    ema_26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()

    # Target: 1 if price goes up in next 5 periods, 0 otherwise
    df['target'] = (df['close'].shift(-5) > df['close']).astype(int)

    # Drop NaN values
    df = df.dropna()

    return df

def train_and_evaluate_model(model, X_train, X_test, y_train, y_test, model_name):
    """Train and evaluate a model."""
    start_time = time.time()

    model.fit(X_train, y_train)

    training_time = time.time() - start_time

    # Predict
    if hasattr(model, 'predict_proba'):
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    else:
        y_pred_proba = model.predict(X_test)

    y_pred = (y_pred_proba > 0.5).astype(int)

    # Calculate metrics
    f1 = f1_score(y_test, y_pred)

    return {
        'f1_score': f1,
        'training_time': training_time,
        'predictions': y_pred,
        'actuals': y_test
    }

def main():
    """Compare XGBoost vs LightGBM."""
    print("🚀 Comparing XGBoost vs LightGBM for ML Trading")
    print("=" * 60)

    # Generate sample data
    print("📊 Generating sample data...")
    raw_data = generate_sample_data(2000)
    featured_data = create_features(raw_data)

    print(f"✅ Generated {len(featured_data)} data points with features")

    # Prepare features
    feature_cols = [col for col in featured_data.columns if col not in ['target']]
    X = featured_data[feature_cols]
    y = featured_data['target']

    # Time series split
    tscv = TimeSeriesSplit(n_splits=3)
    results = {'xgboost': [], 'lightgbm': []}

    print("\n🏃 Training models with walk-forward validation...")

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        print(f"\nFold {fold + 1}/3:")

        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        # XGBoost
        xgb_model = xgb.XGBClassifier(
            objective='binary:logistic',
            max_depth=6,
            learning_rate=0.1,
            n_estimators=100,
            random_state=42,
            verbosity=0
        )

        xgb_result = train_and_evaluate_model(xgb_model, X_train, X_test, y_train, y_test, "XGBoost")
        results['xgboost'].append(xgb_result)
        print(f"   XGBoost F1: {xgb_result['f1_score']:.4f}")
        # LightGBM
        lgb_model = lgb.LGBMClassifier(
            objective='binary',
            num_leaves=31,
            learning_rate=0.1,
            n_estimators=100,
            random_state=42,
            verbosity=-1
        )

        lgb_result = train_and_evaluate_model(lgb_model, X_train, X_test, y_train, y_test, "LightGBM")
        results['lightgbm'].append(lgb_result)
        print(f"   LightGBM F1: {lgb_result['f1_score']:.4f}")
    # Aggregate results
    print("\n" + "=" * 60)
    print("🏆 FINAL RESULTS")
    print("=" * 60)

    for model_name in ['xgboost', 'lightgbm']:
        f1_scores = [r['f1_score'] for r in results[model_name]]
        training_times = [r['training_time'] for r in results[model_name]]

        avg_f1 = np.mean(f1_scores)
        avg_time = np.mean(training_times)
        std_f1 = np.std(f1_scores)

        print(f"\n{model_name.upper()}:")
        print(f"   Average F1 Score: {avg_f1:.4f} ± {std_f1:.4f}")
        print(f"   Average Training Time: {avg_time:.4f} seconds")
        print(f"   F1 Scores per fold: {[f'{s:.3f}' for s in f1_scores]}")
    # Determine winner
    xgb_avg_f1 = np.mean([r['f1_score'] for r in results['xgboost']])
    lgb_avg_f1 = np.mean([r['f1_score'] for r in results['lightgbm']])

    print("\n🏆 WINNER:")
    if xgb_avg_f1 > lgb_avg_f1:
        improvement = ((xgb_avg_f1 - lgb_avg_f1) / lgb_avg_f1) * 100
        print(f"   XGBoost performs better by {improvement:.1f}%")
    elif lgb_avg_f1 > xgb_avg_f1:
        improvement = ((lgb_avg_f1 - xgb_avg_f1) / xgb_avg_f1) * 100
        print(f"   LightGBM performs better by {improvement:.1f}%")
    else:
        print("   Tie - both models perform similarly!")

    print("\n💡 RECOMMENDATIONS:")
    print("• XGBoost: More stable, better for smaller datasets")
    print("• LightGBM: Faster training, better for larger datasets")
    print("• Both are excellent gradient boosting algorithms")
    print("• Consider ensemble methods combining both")

if __name__ == "__main__":
    main()