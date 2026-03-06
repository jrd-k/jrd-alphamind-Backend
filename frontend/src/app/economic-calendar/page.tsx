'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { EconomicEvent } from '@/types';
import { Button } from '@/components/ui/Button';
import { EconomicEventCard } from '@/components/economic-calendar/EconomicEventCard';

export default function EconomicCalendarPage() {
  const [events, setEvents] = useState<EconomicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    impact: 'all', // all, high, medium, low
    country: 'all',
    upcoming: true,
  });

  const fetchEvents = async () => {
    try {
      const params: any = {};
      params.hours_ahead = 168; // 1 week default
      if (filter.impact !== 'all') params.min_impact = filter.impact;
      if (filter.country !== 'all') params.currencies = filter.country;
      if (filter.upcoming) params.upcoming = true;

      const response = await api.get('/api/v1/economic-calendar/upcoming', { params });
      setEvents(response.data.items || response.data);
    } catch (error) {
      console.error('Failed to fetch economic events:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [filter]);

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

  const countries = ['all', ...Array.from(new Set(events.map(e => e.country)))];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Economic Calendar</h1>
        <Button onClick={fetchEvents} variant="outline">
          Refresh
        </Button>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Filters</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Impact Level
            </label>
            <select
              value={filter.impact}
              onChange={(e) => setFilter(prev => ({ ...prev, impact: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Impacts</option>
              <option value="high">High Impact</option>
              <option value="medium">Medium Impact</option>
              <option value="low">Low Impact</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Country
            </label>
            <select
              value={filter.country}
              onChange={(e) => setFilter(prev => ({ ...prev, country: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {countries.map((country) => (
                <option key={country} value={country}>
                  {country === 'all' ? 'All Countries' : country}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="upcoming"
              checked={filter.upcoming}
              onChange={(e) => setFilter(prev => ({ ...prev, upcoming: e.target.checked }))}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="upcoming" className="ml-2 text-sm font-medium text-gray-700">
              Show Only Upcoming Events
            </label>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Economic Events</h2>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No economic events found with current filters.
          </div>
        ) : (
          <div className="space-y-4">
            {events.map((event) => (
              <EconomicEventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}