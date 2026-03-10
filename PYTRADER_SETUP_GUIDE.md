# PyTrader EA Setup Guide for MT4/MT5
# Complete installation and configuration instructions

## Prerequisites
- MT4 or MT5 terminal installed
- Active trading account
- PyTrader EA file (download from your fork)

## Step 1: Download PyTrader EA

1. Go to your GitHub fork of PyTrader
2. Download the latest EA file: `Pytrader_API_V4_01.ex4` (for MT4) or `Pytrader_API_V4_01.ex5` (for MT5)
3. Save it to your MT4/MT5 Experts folder

## Step 2: Install EA in Terminal

### For MT4:
```
1. Open MT4 Terminal
2. Go to File → Open Data Folder
3. Navigate to MQL4 → Experts
4. Copy Pytrader_API_V4_01.ex4 to this folder
5. Restart MT4 Terminal
```

### For MT5:
```
1. Open MT5 Terminal
2. Go to File → Open Data Folder
3. Navigate to MQL5 → Experts
4. Copy Pytrader_API_V4_01.ex5 to this folder
5. Restart MT5 Terminal
```

## Step 3: Configure EA Parameters

1. In MT4/MT5 Navigator, right-click on Pytrader_API_V4_01
2. Select "Attach to Chart"
3. Configure the following parameters:

### Required Parameters:
```
Port: 1122 (default TCP port for PyTrader)
Host: localhost (or 127.0.0.1)
Magic Number: 12345 (matches our bot configuration)
```

### Optional Parameters:
```
Log Level: 1 (for debugging)
Max Orders: 100
Slippage: 10
```

## Step 4: Enable Automated Trading

1. Make sure "Algo Trading" button is enabled (green) in MT4/MT5 toolbar
2. Check that the EA is attached to a chart (green play button)

## Step 5: Test Connection

1. Start your backend server
2. Run the PyTrader integration test:
```bash
cd backend
python test_pytrader_integration.py
```

3. Check MT4/MT5 Experts tab for connection messages

## Step 6: Configure Environment Variables

Create a `.env` file in your project root:

```bash
# MT5/PyTrader Configuration
MT5_ACCOUNT=your_mt5_account_number
MT5_API_KEY=your_pytrader_api_key
MT5_API_SECRET=your_pytrader_secret
MT5_SERVER=your_mt5_server

# Trading Configuration
ENABLE_LIVE_TRADING=false  # Set to true for live trading
CONFIRM_LIVE_TOKEN=CONFIRM-LIVE
```

## Step 7: Test Trading Operations

### Test Balance Check:
```python
from app.services.brokers.mt5_client import PyTraderClient
import asyncio

async def test_balance():
    client = PyTraderClient(
        account_id="your_account",
        api_key="your_key",
        api_secret="your_secret",
        server="your_server"
    )

    balance = await client.get_balance()
    print(f"Balance: {balance}")

asyncio.run(test_balance())
```

### Test Market Order:
```python
async def test_order():
    client = PyTraderClient(
        account_id="your_account",
        api_key="your_key",
        api_secret="your_secret",
        server="your_server"
    )

    result = await client.place_order(
        symbol="EURUSD",
        side="buy",
        qty=0.01,
        order_type="market"
    )
    print(f"Order result: {result}")

asyncio.run(test_order())
```

## Step 8: Start AI Trading Bot

```bash
# Set environment variables
export MT5_ACCOUNT=your_account
export MT5_API_KEY=your_key
export MT5_API_SECRET=your_secret
export MT5_SERVER=your_server

# Run the bot
python scripts/ai_trading_bot.py
```

## Troubleshooting

### Connection Issues:
1. Check that EA is attached to chart and running (green play button)
2. Verify port 1122 is not blocked by firewall
3. Check MT4/MT5 Experts tab for error messages
4. Ensure MT4/MT5 terminal has internet connection

### Trading Issues:
1. Verify account has sufficient balance
2. Check that symbol is available and not disabled
3. Ensure market is open for the symbol
4. Check spread and commission settings

### Common Errors:
- "Connection refused": EA not running or port blocked
- "Invalid symbol": Symbol not supported by broker
- "No permission": Algo trading disabled or account restrictions
- "Insufficient funds": Account balance too low

## Security Notes

1. Never share your API keys or account credentials
2. Use demo account first to test all functionality
3. Enable live trading only after thorough testing
4. Monitor positions regularly, especially when using leverage
5. Set appropriate stop-loss levels to limit risk

## Supported Symbols

The system supports all major market instruments:
- Forex: EURUSD, GBPUSD, USDJPY, etc.
- Commodities: XAUUSD (Gold), XAGUSD (Silver), etc.
- Indices: SPX500, US30, NAS100, etc.
- Crypto: BTCUSD, ETHUSD, etc.
- Bonds: US10Y, etc.

## Next Steps

1. Test with demo account first
2. Paper trade to verify strategies
3. Start with small position sizes
4. Gradually increase as confidence grows
5. Monitor and adjust risk parameters

## Support

If you encounter issues:
1. Check the logs in MT4/MT5 Experts tab
2. Review backend logs: `tail -f logs/backend.log`
3. Test individual components before running full bot
4. Join PyTrader community for EA-specific issues