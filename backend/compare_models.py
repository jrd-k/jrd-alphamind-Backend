#!/usr/bin/env python3
"""
Compare XGBoost vs LightGBM performance for ML trading.
"""

import asyncio
import sys
import os
import pandas as pd
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def compare_models():
    """Compare XGBoost and LightGBM models."""
    try:
        print("🚀 Comparing XGBoost vs LightGBM for ML Trading")
        print("=" * 60)

        from app.services.ml import MLTradingService, MLDataLoader

        # Initialize services
        ml_service = MLTradingService()
        data_loader = MLDataLoader()

        # Generate sample data
        print("📊 Generating sample data...")
        historical_data = await data_loader.generate_sample_data(
            symbol='EURUSD',
            timeframe='H1',
            days=365
        )

        if historical_data.empty:
            print("❌ No historical data available")
            return

        print(f"✅ Generated {len(historical_data)} data points")

        results = {}

        # Train and evaluate both models
        for model_type in ['xgboost', 'lightgbm']:
            print(f"\n🏃 Training {model_type.upper()} model...")
            try:
                start_time = datetime.now()

                model_result = await ml_service.train_model(
                    historical_data,
                    'EURUSD',
                    force_retrain=True,
                    model_type=model_type
                )

                training_time = datetime.now() - start_time

                f1_score = model_result['training_results']['best_score']
                results[model_type] = {
                    'f1_score': f1_score,
                    'training_time': training_time,
                    'feature_count': model_result['feature_count'],
                    'data_points': model_result['data_points']
                }

                print(f"✅ {model_type.upper()} Results:")
                print(f"   📈 F1 Score: {f1_score:.4f}")
                print(f"   ⏱️  Training time: {training_time}")
                print(f"   🎯 Features used: {model_result['feature_count']}")
                print(f"   📊 Data points: {model_result['data_points']}")

            except Exception as e:
                print(f"❌ {model_type.upper()} training failed: {e}")
                results[model_type] = {'error': str(e)}

        # Compare results
        print("\n" + "=" * 60)
        print("🏆 MODEL COMPARISON RESULTS")
        print("=" * 60)

        if 'xgboost' in results and 'lightgbm' in results:
            if 'error' not in results['xgboost'] and 'error' not in results['lightgbm']:
                xgb_score = results['xgboost']['f1_score']
                lgb_score = results['lightgbm']['f1_score']

                print(f"🏆 XGBoost F1: {xgb_score:.4f}")
                print(f"🏆 LightGBM F1: {lgb_score:.4f}")
                print(f"📊 Difference: {abs(xgb_score - lgb_score):.4f}")
                if xgb_score > lgb_score:
                    print("🏆 WINNER: XGBoost performs better!")
                    improvement = ((xgb_score - lgb_score) / lgb_score) * 100
                    print(f"   XGBoost is {improvement:.1f}% better")
                elif lgb_score > xgb_score:
                    print("🏆 WINNER: LightGBM performs better!")
                    improvement = ((lgb_score - xgb_score) / xgb_score) * 100
                    print(f"   LightGBM is {improvement:.1f}% better")
                else:
                    print("🤝 TIE: Both models perform equally well!")

                # Training time comparison
                xgb_time = results['xgboost']['training_time'].total_seconds()
                lgb_time = results['lightgbm']['training_time'].total_seconds()

                print("\n⏱️  Training Time:")
                print(f"   XGBoost: {xgb_time:.2f} seconds")
                print(f"   LightGBM: {lgb_time:.2f} seconds")
                if xgb_time < lgb_time:
                    print("   XGBoost is faster to train!")
                elif lgb_time < xgb_time:
                    print("   LightGBM is faster to train!")
                else:
                    print("   Similar training times!")

            else:
                print("❌ One or both models failed to train")
        else:
            print("❌ Comparison incomplete")

        print("\n" + "=" * 60)
        print("💡 RECOMMENDATIONS")
        print("=" * 60)

        if 'xgboost' in results and 'lightgbm' in results:
            if 'error' not in results['xgboost'] and 'error' not in results['lightgbm']:
                xgb_score = results['xgboost']['f1_score']
                lgb_score = results['lightgbm']['f1_score']

                if xgb_score > lgb_score:
                    print("• Use XGBoost for better prediction accuracy")
                    print("• Consider LightGBM for faster training on large datasets")
                elif lgb_score > xgb_score:
                    print("• Use LightGBM for better prediction accuracy")
                    print("• LightGBM often handles categorical features better")
                else:
                    print("• Both models perform similarly - choose based on your needs")
                    print("• XGBoost: More mature, better documentation")
                    print("• LightGBM: Faster training, better memory efficiency")

        print("\n🔧 Configuration Tips:")
        print("• Adjust model parameters in MLModelTrainer class")
        print("• Try different feature engineering approaches")
        print("• Experiment with different validation strategies")
        print("• Consider ensemble methods combining both models")

        return results

    except Exception as e:
        print(f"❌ Error during model comparison: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Run the model comparison."""
    results = await compare_models()

    if results:
        print("\n✅ Model comparison completed successfully!")
        return 0
    else:
        print("\n❌ Model comparison failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)