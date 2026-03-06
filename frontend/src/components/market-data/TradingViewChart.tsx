'use client';

import { useEffect, useRef } from 'react';

interface TradingViewChartProps {
  symbol: string;
  timeframe?: string;
  width?: string;
  height?: string;
}

export function TradingViewChart({ symbol, timeframe = '1h', width = '100%', height = '400px' }: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Map timeframe to TradingView interval
  const getInterval = (tf: string) => {
    switch (tf) {
      case '1m': return '1';
      case '5m': return '5';
      case '15m': return '15';
      case '1h': return '60';
      case '4h': return '240';
      case '1d': return 'D';
      default: return '60';
    }
  };

  useEffect(() => {
    if (!containerRef.current) return;

    // Clear any existing content
    containerRef.current.innerHTML = '';

    // Create script element for TradingView widget
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;

    script.onload = () => {
      if (window.TradingView && containerRef.current) {
        new window.TradingView.widget({
          container_id: containerRef.current.id,
          symbol: `FX_IDC:${symbol}`,
          interval: getInterval(timeframe),
          timezone: 'Etc/UTC',
          theme: 'dark',
          style: '1',
          locale: 'en',
          toolbar_bg: '#f1f3f6',
          enable_publishing: false,
          allow_symbol_change: true,
          save_image: false,
          studies: [
            'MASimple@tv-basicstudies',
            'RSI@tv-basicstudies',
            'MACD@tv-basicstudies'
          ],
          show_popup_button: true,
          popup_width: '1000',
          popup_height: '650',
          no_replay: true,
          hide_side_toolbar: false,
          hide_top_toolbar: false,
          autosize: true,
          backgroundColor: 'rgba(17, 24, 39, 1)',
          gridColor: 'rgba(55, 65, 81, 1)',
          textColor: 'rgba(156, 163, 175, 1)',
          upColor: 'rgba(34, 197, 94, 1)',
          downColor: 'rgba(239, 68, 68, 1)',
        });
      }
    };

    // Append script to container
    containerRef.current.appendChild(script);

    // Cleanup function
    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [symbol]);

  return (
    <div
      id={`tradingview-${symbol}-${Date.now()}`}
      ref={containerRef}
      style={{ width, height }}
      className="rounded-lg overflow-hidden"
    />
  );
}

// Extend window interface for TradingView
declare global {
  interface Window {
    TradingView: {
      widget: new (config: any) => any;
    };
  }
}