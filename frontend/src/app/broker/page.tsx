'use client';

import { BrokerIntegration } from '@/components/broker/BrokerIntegration';

export default function BrokerPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Broker Integration</h1>
      </div>

      <BrokerIntegration />
    </div>
  );
}