'use client';

import { BrainDecision } from '@/types';

interface BrainDecisionCardProps {
  decision: BrainDecision;
}

export function BrainDecisionCard({ decision }: BrainDecisionCardProps) {
  const getDecisionColor = (decision: string) => {
    switch (decision.toLowerCase()) {
      case 'buy':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'sell':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'hold':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{decision.symbol}</h3>
          <p className="text-sm text-gray-500">
            {new Date(decision.created_at).toLocaleString()}
          </p>
        </div>
        <div className="text-right">
          <span className={`inline-block px-3 py-1 text-sm font-semibold rounded-full border ${getDecisionColor(decision.decision)}`}>
            {decision.decision.toUpperCase()}
          </span>
          <p className={`text-sm font-medium mt-1 ${getConfidenceColor(decision.confidence)}`}>
            {(decision.confidence * 100).toFixed(1)}% confidence
          </p>
        </div>
      </div>

      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Technical Indicators</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          {decision.indicators && Object.entries(decision.indicators).map(([key, value]) => (
            <div key={key} className="bg-gray-50 p-2 rounded">
              <span className="font-medium text-gray-600">{key}:</span>
              <span className="ml-1 text-gray-900">
                {typeof value === 'number' ? value.toFixed(4) : String(value)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                decision.confidence >= 0.8 ? 'bg-green-500' :
                decision.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${decision.confidence * 100}%` }}
            ></div>
          </div>
        </div>
        <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
          View Details
        </button>
      </div>
    </div>
  );
}