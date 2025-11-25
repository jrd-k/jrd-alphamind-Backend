"""Validate required environment variables for running the trading system.

Usage:
    python scripts/validate_env.py

This script checks for broker credentials, AI keys, and webhook secret and
prints any missing items with guidance for setting them locally or in GitHub
Actions secrets.
"""
import os
import sys

required = [
    "DATABASE_URL",
    "REDIS_URL",
    "JWT_SECRET",
]

optional_ai = ["OPENAI_API_KEY", "DEEPSEEK_API_KEY"]

broker = os.getenv("BROKER", "paper").lower()

broker_vars = []
if broker == "exness":
    broker_vars = ["EXNESS_API_KEY", "EXNESS_BASE_URL"]
elif broker == "justmarkets":
    broker_vars = ["JUSTMARKETS_API_KEY", "JUSTMARKETS_BASE_URL"]
else:
    broker_vars = []

missing = []
for v in required + broker_vars:
    if not os.getenv(v):
        missing.append(v)

missing_ai = [v for v in optional_ai if not os.getenv(v)]

print(f"Broker selected: {broker}")
if missing:
    print("\nMissing required environment variables:")
    for m in missing:
        print(f" - {m}")
    print("\nSet them locally in backend/.env or export them in your shell.")
else:
    print("All required environment variables present.")

if missing_ai:
    print("\nOptional AI keys not set (system will run without external AI):")
    for m in missing_ai:
        print(f" - {m}")
    print("Add them to enable AI features. Do NOT paste keys into public repos.")

if not os.getenv("TRADINGVIEW_WEBHOOK_SECRET"):
    print("\nWarning: TRADINGVIEW_WEBHOOK_SECRET not set. If you plan to use TradingView webhooks, set this secret.")

if os.getenv("ENABLE_LIVE_TRADING", "False").lower() in ("1", "true", "yes") and os.getenv("CONFIRM_LIVE") != "CONFIRM-LIVE":
    print("\nWARNING: ENABLE_LIVE_TRADING is set but CONFIRM_LIVE is not 'CONFIRM-LIVE'. Live trading will be blocked until CONFIRM_LIVE=CONFIRM-LIVE is set.")

print("\nTo set GitHub Actions secrets (example using gh CLI):")
print("  gh secret set OPENAI_API_KEY --body 'sk-...'")
print("  gh secret set DEEPSEEK_API_KEY --body 'sk-...'\n")

sys.exit(0)
