'use client';

import { EconomicEvent } from '@/types';

interface EconomicEventCardProps {
  event: EconomicEvent;
}

export function EconomicEventCard({ event }: EconomicEventCardProps) {
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'high':
        return '🔴';
      case 'medium':
        return '🟡';
      case 'low':
        return '🟢';
      default:
        return '⚪';
    }
  };

  const eventDate = new Date(event.date);
  const now = new Date();
  const timeUntil = eventDate.getTime() - now.getTime();
  const hoursUntil = Math.floor(timeUntil / (1000 * 60 * 60));
  const minutesUntil = Math.floor((timeUntil % (1000 * 60 * 60)) / (1000 * 60));

  const isUpcoming = timeUntil > 0;
  const isLive = timeUntil <= 0 && timeUntil > -3600000; // Within last hour

  return (
    <div className={`border rounded-lg p-6 ${
      isLive ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-200'
    }`}>
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">{event.title}</h3>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getImpactColor(event.impact)}`}>
              {getImpactIcon(event.impact)} {event.impact.toUpperCase()}
            </span>
          </div>

          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>📍 {event.country}</span>
            <span>🕐 {eventDate.toLocaleString()}</span>
            {isUpcoming && (
              <span className="text-blue-600 font-medium">
                ⏰ {hoursUntil}h {minutesUntil}m
              </span>
            )}
            {isLive && (
              <span className="text-red-600 font-medium animate-pulse">
                🔴 LIVE
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <div className="bg-gray-50 p-3 rounded-md">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Previous</p>
          <p className="text-lg font-semibold text-gray-900">
            {event.previous !== undefined ? event.previous : 'N/A'}
          </p>
        </div>

        <div className="bg-blue-50 p-3 rounded-md">
          <p className="text-xs text-blue-600 uppercase tracking-wide">Forecast</p>
          <p className="text-lg font-semibold text-blue-900">
            {event.forecast !== undefined ? event.forecast : 'N/A'}
          </p>
        </div>

        <div className={`p-3 rounded-md ${
          event.actual !== undefined ? 'bg-green-50' : 'bg-gray-50'
        }`}>
          <p className={`text-xs uppercase tracking-wide ${
            event.actual !== undefined ? 'text-green-600' : 'text-gray-500'
          }`}>
            Actual
          </p>
          <p className={`text-lg font-semibold ${
            event.actual !== undefined ? 'text-green-900' : 'text-gray-400'
          }`}>
            {event.actual !== undefined ? event.actual : 'Pending'}
          </p>
        </div>
      </div>

      {event.actual !== undefined && event.forecast !== undefined && (
        <div className="mt-4 p-3 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-600">
            <span className="font-medium">Impact:</span>{' '}
            {event.actual > event.forecast ? (
              <span className="text-green-600">📈 Better than expected</span>
            ) : event.actual < event.forecast ? (
              <span className="text-red-600">📉 Worse than expected</span>
            ) : (
              <span className="text-gray-600">➡️ As expected</span>
            )}
          </p>
        </div>
      )}
    </div>
  );
}