'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { CheckCircle, XCircle, AlertCircle, Settings, Plus } from 'lucide-react';
import { api } from '@/lib/api';

interface Broker {
  id: number;
  user_id?: number;
  name: string;
  broker_name: string;
  status: 'connected' | 'disconnected' | 'error';
  lastSync?: string;
  account_id?: string;
  api_key?: string;
  api_secret?: string;
  base_url?: string;
  is_active?: number;
  created_at?: string;
  updated_at?: string;
  mt5_path?: string;
  mt5_password?: string;
}

// API functions
const fetchBrokers = async (): Promise<Broker[]> => {
  try {
    const response = await api.get('/api/v1/brokers/accounts');
    return response.data || [];
  } catch (error: any) {
    console.error('Failed to fetch brokers:', error);
    if (error.response?.status === 401) {
      console.warn('User not authenticated - broker features require login');
      return [];
    }
    return [];
  }
};

const createBroker = async (brokerData: Omit<Broker, 'id' | 'created_at' | 'updated_at'>): Promise<Broker | null> => {
  try {
    console.log('createBroker called with:', brokerData);
    const response = await api.post('/api/v1/brokers/accounts', brokerData);
    console.log('createBroker response:', response);
    return response.data;
  } catch (error: any) {
    console.error('Failed to create broker:', error);
    if (error.response?.status === 401) {
      console.warn('User not authenticated - please log in to add brokers');
      alert('Please log in to add broker accounts.');
      return null;
    }
    return null;
  }
};

const updateBroker = async (id: number, brokerData: Partial<Broker>): Promise<Broker | null> => {
  try {
    const response = await api.put(`/api/v1/brokers/accounts/${id}`, brokerData);
    return response.data;
  } catch (error) {
    console.error('Failed to update broker:', error);
    return null;
  }
};

const deleteBroker = async (id: number): Promise<boolean> => {
  try {
    await api.delete(`/api/v1/brokers/accounts/${id}`);
    return true;
  } catch (error) {
    console.error('Failed to delete broker:', error);
    return false;
  }
};

// Available brokers
const AVAILABLE_BROKERS = [
  { 
    id: 'mt5', 
    name: 'MetaTrader 5', 
    description: 'Professional trading platform',
    icon: '📊'
  },
  { 
    id: 'exness', 
    name: 'Exness', 
    description: 'Low-cost forex and CFD broker',
    icon: '💰'
  },
  { 
    id: 'justmarkets', 
    name: 'Just Markets', 
    description: 'Multi-asset broker with MT4/MT5',
    icon: '🌐'
  },
  { 
    id: 'paper', 
    name: 'Paper Trading', 
    description: 'Practice trading without real money',
    icon: '📄'
  },
];

export function BrokerIntegration() {
  const [brokers, setBrokers] = useState<Broker[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [showCredentialModal, setShowCredentialModal] = useState(false);
  const [showBrokerSelection, setShowBrokerSelection] = useState(false);
  const [modalBrokerId, setModalBrokerId] = useState<string | null>(null);
  const [selectedAvailableBroker, setSelectedAvailableBroker] = useState<string | null>(null);
  const [newBrokerName, setNewBrokerName] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');

  useEffect(() => {
    const loadBrokers = async () => {
      setLoading(true);
      try {
        const brokers = await fetchBrokers();
        setBrokers(brokers);
      } catch (error) {
        console.error('Failed to load brokers:', error);
        // Keep empty array if API fails
      } finally {
        setLoading(false);
      }
    };

    loadBrokers();
  }, []);

  const connectBroker = async (brokerId: string) => {
    const broker = brokers.find(b => b.id === parseInt(brokerId));
    if (broker && (!broker.api_key || !broker.api_secret)) {
      openCredentialModal(brokerId);
      return;
    }

    setConnecting(brokerId);
    try {
      // Update broker status to connected
      await updateBroker(parseInt(brokerId), { status: 'connected' });
      setBrokers(prev => prev.map(b =>
        b.id === parseInt(brokerId)
          ? { ...b, status: 'connected', lastSync: new Date().toISOString() }
          : b
      ));
    } catch (error) {
      setBrokers(prev => prev.map(b =>
        b.id === parseInt(brokerId)
          ? { ...b, status: 'error' }
          : b
      ));
    } finally {
      setConnecting(null);
    }
  };

  const openCredentialModal = (brokerId?: string) => {
    if (brokerId) {
      setModalBrokerId(brokerId);
      const existing = brokers.find(b => b.id === parseInt(brokerId));
      setApiKey(existing?.api_key || '');
      setApiSecret(existing?.api_secret || '');
      setSelectedAvailableBroker(null);
    } else {
      setModalBrokerId(null);
      setNewBrokerName('');
      setApiKey('');
      setApiSecret('');
      setSelectedAvailableBroker(null);
    }
    setShowCredentialModal(true);
  };

  const selectBrokerToAdd = (brokerId: string) => {
    const broker = AVAILABLE_BROKERS.find(b => b.id === brokerId);
    if (broker) {
      setSelectedAvailableBroker(brokerId);
      setNewBrokerName(broker.name);
      setShowBrokerSelection(false);
      setShowCredentialModal(true);
    }
  };

  const saveCredentials = async () => {
    console.log('saveCredentials called', { modalBrokerId, newBrokerName, apiKey: apiKey ? '***' : '', apiSecret: apiSecret ? '***' : '' });

    if (modalBrokerId) {
      // Update existing broker
      console.log('Updating existing broker:', modalBrokerId);
      const updatedBroker = await updateBroker(parseInt(modalBrokerId), {
        api_key: apiKey,
        api_secret: apiSecret
      });
      console.log('Update result:', updatedBroker);
      if (updatedBroker) {
        setBrokers(prev => prev.map(b =>
          b.id === parseInt(modalBrokerId) ? updatedBroker : b
        ));
        console.log('Broker updated in state');
      }
    } else {
      // Create new broker
      const brokerName = selectedAvailableBroker || newBrokerName;
      console.log('Creating new broker:', brokerName);
      const newBroker = await createBroker({
        name: brokerName,
        broker_name: brokerName,
        status: 'disconnected',
        api_key: apiKey,
        api_secret: apiSecret
      });
      console.log('Create result:', newBroker);
      if (newBroker) {
        console.log('Adding broker to state:', newBroker);
        setBrokers(prev => {
          const updated = [...prev, newBroker];
          console.log('Updated brokers list:', updated);
          return updated;
        });
        console.log('New broker added to state:', newBroker);
      } else {
        console.error('Failed to create broker - no response from API');
        alert('Failed to create broker. Check console for details.');
      }
    }
    setShowCredentialModal(false);
    // Clear form
    setNewBrokerName('');
    setApiKey('');
    setApiSecret('');
    setSelectedAvailableBroker(null);
    setModalBrokerId(null);
  };
  const disconnectBroker = async (brokerId: string) => {
    try {
      await updateBroker(parseInt(brokerId), { status: 'disconnected' });
      setBrokers(prev => prev.map(broker =>
        broker.id === parseInt(brokerId)
          ? { ...broker, status: 'disconnected' }
          : broker
      ));
    } catch (error) {
      console.error('Failed to disconnect broker:', error);
    }
  };

  // determine whether credential modal save button should be enabled
  const canSaveCredentials = () => {
    const hasKeys = apiKey.trim() && apiSecret.trim();
    if (modalBrokerId) {
      return Boolean(hasKeys);
    }
    return Boolean(newBrokerName.trim() && hasKeys);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'error':
        return 'Connection Error';
      default:
        return 'Disconnected';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-4">Broker Integration</h2>
        <p className="text-gray-600 mb-6">
          Connect your trading accounts to enable automated order execution and synchronization.
        </p>

        <div className="mb-6">
          <Button onClick={() => setShowBrokerSelection(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Broker
          </Button>
        </div>

        {/* Broker selection section */}
        <Modal
          isOpen={showBrokerSelection}
          onClose={() => setShowBrokerSelection(false)}
          title="Select a Broker"
          size="lg"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {AVAILABLE_BROKERS.map((broker) => (
              <button
                key={broker.id}
                onClick={() => selectBrokerToAdd(broker.id)}
                className="border-2 border-gray-300 rounded-2xl p-6 cursor-pointer hover:bg-blue-50 hover:border-blue-500 active:bg-blue-100 transition-all text-left"
              >
                <div className="text-5xl mb-3">{broker.icon}</div>
                <h3 className="font-bold text-lg text-gray-900">{broker.name}</h3>
                <p className="text-sm text-gray-600 mt-2">{broker.description}</p>
                <div className="mt-4 pt-4 border-t-2 border-gray-200">
                  <span className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold text-sm">
                    Select Broker
                  </span>
                </div>
              </button>
            ))}
          </div>
        </Modal>

        {/* credential modal for adding/editing brokers */}
        <Modal
          isOpen={showCredentialModal}
          onClose={() => setShowCredentialModal(false)}
          title={modalBrokerId ? 'Edit Broker Credentials' : `Add ${newBrokerName || 'Broker'}`}
          size="md"
        >
          <div className="space-y-4">
            {!modalBrokerId && !selectedAvailableBroker && (
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">Broker Name</label>
                <input
                  type="text"
                  value={newBrokerName}
                  onChange={e => setNewBrokerName(e.target.value)}
                  placeholder="Enter broker name"
                  className="w-full border-2 border-gray-300 rounded-xl shadow-sm p-4 text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">API Key</label>
              <input
                type="text"
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                className="w-full border-2 border-gray-300 rounded-xl shadow-sm p-4 text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">API Secret</label>
              <input
                type="password"
                value={apiSecret}
                onChange={e => setApiSecret(e.target.value)}
                placeholder="Enter your API secret"
                className="w-full border-2 border-gray-300 rounded-xl shadow-sm p-4 text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>

            <div className="flex flex-col-reverse sm:flex-row gap-3 pt-4">
              <Button variant="outline" onClick={() => setShowCredentialModal(false)} className="flex-1">
                Cancel
              </Button>
              <Button onClick={saveCredentials} disabled={!canSaveCredentials()} className="flex-1">
                Save Broker
              </Button>
            </div>
          </div>
        </Modal>

        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading brokers...</p>
            </div>
          ) : brokers.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">No brokers configured yet.</p>
              <p className="text-sm text-gray-500 mb-4">
                You need to be logged in to add and manage broker accounts.
              </p>
              <Button onClick={() => openCredentialModal()} className="mr-4">
                <Plus className="h-4 w-4 mr-2" />
                Add Broker
              </Button>
              <Button variant="outline" onClick={() => window.location.href = '/auth/login'}>
                Log In
              </Button>
            </div>
          ) : (
            brokers.map((broker) => (
              <div key={broker.id} className="bg-white p-6 rounded-lg shadow-md">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {getStatusIcon(broker.status)}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">{broker.name || broker.broker_name || 'Unknown Broker'}</h3>
                      <p className="text-sm text-gray-500">
                        Status: {getStatusText(broker.status)}
                        {broker.lastSync && (
                          <span className="ml-2">
                            • Last sync: {new Date(broker.lastSync).toLocaleString()}
                          </span>
                        )}
                        {broker.api_key && broker.api_secret ? (
                          <span className="ml-2 text-green-600">
                            • Credentials saved
                          </span>
                        ) : (
                          <span className="ml-2 text-red-600">
                            • No credentials
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    {broker.status === 'connected' ? (
                      <>
                        <Button variant="outline" size="sm" onClick={() => openCredentialModal(broker.id.toString())}>
                          <Settings className="h-4 w-4 mr-2" />
                          Configure
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => disconnectBroker(broker.id.toString())}
                        >
                          Disconnect
                        </Button>
                      </>
                    ) : (
                      <Button
                        onClick={() => connectBroker(broker.id.toString())}
                        disabled={connecting === broker.id.toString()}
                        size="sm"
                      >
                        {connecting === broker.id.toString() ? 'Connecting...' : 'Connect'}
                      </Button>
                    )}
                  </div>
                </div>

              {broker.status === 'connected' && (
                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
                  <div className="flex">
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-green-800">
                        Successfully Connected
                      </h4>
                      <div className="mt-2 text-sm text-green-700">
                        <p>
                          Your {broker.name} account is now connected. Orders will be automatically synchronized.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {broker.status === 'error' && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex">
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-red-800">
                        Connection Failed
                      </h4>
                      <div className="mt-2 text-sm text-red-700">
                        <p>
                          Unable to connect to {broker.name}. Please check your credentials and try again.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))
          )}
        </div>

        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                Need Help?
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  We support MetaTrader 5, OANDA, Interactive Brokers, Exness, Just Markets, FP Markets, and many more.
                  Use the "Add Broker" button to register a new provider and enter your API credentials. Configure an existing broker to update keys.
                  Don't see your broker? Contact support to request integration with additional brokers.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}