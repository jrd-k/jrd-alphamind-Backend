'use client';

interface QuoteDisplayProps {
  quote: any;
  symbol: string;
}

export function QuoteDisplay({ quote, symbol }: QuoteDisplayProps) {
  if (!quote) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">{symbol} Quote</h3>
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const priceChange = quote.last - quote.previousClose;
  const priceChangePercent = ((priceChange / quote.previousClose) * 100).toFixed(2);

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="text-lg font-semibold mb-4">{symbol} Quote</h3>

      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="text-gray-600">Last Price:</span>
          <span className="font-semibold text-lg">
            ${quote.last?.toFixed(5)}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Bid:</span>
          <span>${quote.bid?.toFixed(5)}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Ask:</span>
          <span>${quote.ask?.toFixed(5)}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Volume:</span>
          <span>{quote.volume?.toLocaleString()}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Change:</span>
          <span className={`font-semibold ${priceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {priceChange >= 0 ? '+' : ''}${priceChange?.toFixed(5)} ({priceChangePercent}%)
          </span>
        </div>
      </div>
    </div>
  );
}