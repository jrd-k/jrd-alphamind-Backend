# TradingView / WebSocket Integration Example

This document shows a minimal example to connect a frontend to the backend `/ws/trades` WebSocket and plot simple markers on a TradingView chart (or Lightweight Charts).

1) Connect to the WebSocket and receive trade messages (JSON):

```js
// plain browser JS example
const ws = new WebSocket('ws://localhost:8000/ws/trades');

ws.onopen = () => console.log('ws open');
ws.onmessage = (evt) => {
  try {
    const trade = JSON.parse(evt.data);
    console.log('trade', trade);
    // forward to charting code (see below)
  } catch (e) {
    console.warn('invalid message', evt.data);
  }
};

ws.onclose = () => console.log('ws closed');
```

2) Example using Lightweight-Charts (open-source) to add markers for received trades:

```js
import { createChart } from 'lightweight-charts';

const chart = createChart(document.getElementById('chart'), { width: 800, height: 400 });
const series = chart.addLineSeries();

// initialize series with some data (your real data source will be different)
series.setData([
  { time: '2025-11-17', value: 1.0 },
  { time: '2025-11-18', value: 1.01 },
]);

const ws = new WebSocket('ws://localhost:8000/ws/trades');
ws.onmessage = (evt) => {
  const trade = JSON.parse(evt.data);
  // add a marker
  const mark = {
    time: trade.timestamp.split('T')[0],
    position: trade.side === 'buy' ? 'belowBar' : 'aboveBar',
    color: trade.side === 'buy' ? 'green' : 'red',
    shape: 'arrowUp',
    text: `${trade.side} ${trade.qty}@${trade.price}`,
  };
  series.setMarkers([mark]);
};
```

3) Notes
- The backend publishes JSON trade messages to `/ws/trades` with the following fields: id, symbol, side, price, qty, timestamp, order_id, user_id, metadata.
- For production use with TradingView's full widget, you will need to implement a timeseries REST datafeed or use the Charting Library. The above is a simple demonstration using Lightweight-Charts.
