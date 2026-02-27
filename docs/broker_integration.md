# Broker Integration Guide

AlphaMind is designed to be extensible with multiple brokers. existing integrations include:

* **Paper** – a built-in simulator used by default in development and testing.
* **Exness** – real money FX broker accessed via REST API.
* **JustMarkets** – similar REST API; packaged alongside Exness in the frontend components.
* **MT5 (MetaTrader 5)** – implemented as an adapter that talks to a bridge or WebSocket API.

## Adding a New Broker

1. **Create a client module** under `backend/app/services/brokers/` carrying the broker-specific logic.
   - Implement methods: `login()`, `place_order()`, `cancel_order()`, `get_positions()`, etc.
   - Follow pattern in `exness_client.py` (see README).  Example stub in README:
     ```python
     class CustomBrokerClient(BaseBrokerClient):
         def __init__(self, api_key: str, base_url: str):
             # initialize HTTP session, headers, etc.

         def place_order(self, symbol: str, volume: float, side: str, **kwargs) -> dict:
             # call the broker API and translate response to internal format

         # additional methods as required by execution layer
     ```
2. **Register the client** in `app/services/execution.py` where the factory selects the appropriate implementation based on `broker_name`.
   ```python
   if broker == "custom":
       from app.services.brokers.custom_client import CustomBrokerClient
       return CustomBrokerClient()
   ```
3. **Update `BrokerAccount` schema and endpoints** if new credentials or fields are needed.
4. **Frontend changes**: add the broker to dropdowns, create a connect component (e.g. `CustomConnect.tsx`), and ensure the API call to `/api/v1/brokers/accounts` includes the right fields.
5. **Testing**: extend `test_all_fixes.py` or write new integration tests that exercise the new broker path using a sandbox or mock service.

## MT5 Integration

MT5 usually requires a gateway process (for example, MetaTrader's Manager API or a third‑party bridge) since there is no direct public REST API.

* **Bridge model**: run a helper service next to the backend that speaks the MT5 protocol (e.g. via MetaTrader5 Python package or a compiled DLL).
* **BrokerAccount** for MT5 contains `server`, `login`, `password`, and optionally `symbol_map`.
* **Example stub**:
  ```python
  class MT5Client(BaseBrokerClient):
      def __init__(self, server: str, login: str, password: str):
          import MetaTrader5 as mt5
          mt5.initialize(login=login, server=server, password=password)

      def place_order(self, symbol, volume, side, **kwargs):
          order_type = mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL
          ticket = mt5.order_send({
              "symbol": symbol,
              "volume": volume,
              "type": order_type,
              # other parameters
          })
          return mt5.order_check(ticket)
  ```

## Exness Integration Notes

* **Environment**: set `EXNESS_API_KEY` and `EXNESS_BASE_URL` before the service starts or when swapping accounts.
* **Sandbox vs Production**: use `api-demo.exness.com` for testing; switch to `api.exness.com` when ready.
* **Order payloads**: clients must send `symbol`, `side`, `volume`, and optional `stop_loss`/`take_profit`.
* **Error handling**: map Exness error codes to HTTP 400/502 to surface to frontend.

## Custom Broker Implementations

If your broker provides gRPC, WebSocket, or FIX:

1. Write an adapter that normalizes messages into the common `ExecutionResult` format used by the backend.
2. Optionally run the adapter as a separate service and communicate over HTTP or message queue (e.g. Redis pub/sub).
3. Update orchestration logic (`app/services/execution.py`) to route to the adapter when `broker == "custom"`.

## Security Considerations

* Never log raw credentials; mask or hash them.
* Store API keys in secrets manager when running in Kubernetes (use `Secret` objects) or in environment variables for Docker Swarm.
* Validate all responses from the broker to avoid executing on stale data.

Refer to `backend/README.md` for more examples and sample code linking to Exness and JustMarkets client modules.