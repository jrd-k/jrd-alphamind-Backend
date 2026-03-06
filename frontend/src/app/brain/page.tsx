'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { BrainDecision } from '@/types';
import { Button } from '@/components/ui/Button';
import { BrainDecisionCard } from '@/components/brain/BrainDecisionCard';
import { BrainAnalysisForm } from '@/components/brain/BrainAnalysisForm';
import { Brain, Zap, TrendingUp, Activity, Sparkles, Target } from 'lucide-react';

export default function BrainPage() {
  const [decisions, setDecisions] = useState<BrainDecision[]>([
    {
      id: 1,
      symbol: 'EURUSD',
      decision: 'BUY',
      confidence: 0.92,
      reasoning: 'Strong bullish divergence detected on 4H chart. RSI oversold recovery pattern confirmed.',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
      targetPrice: 1.0950,
      stopLoss: 1.0750,
      indicators: {},
      created_at: new Date().toISOString(),
    },
    {
      id: 2,
      symbol: 'GBPUSD',
      decision: 'SELL',
      confidence: 0.87,
      reasoning: 'Resistance level broken with high volume. AI predicts correction incoming.',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      targetPrice: 1.2600,
      stopLoss: 1.2950,
      indicators: {},
      created_at: new Date().toISOString(),
    },
    {
      id: 3,
      symbol: 'USDJPY',
      decision: 'HOLD',
      confidence: 0.78,
      reasoning: 'Consolidation pattern detected. Wait for breakout confirmation.',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      targetPrice: 110.80,
      stopLoss: 110.20,
      indicators: {},
      created_at: new Date().toISOString(),
    },
  ]);  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [showAnalysisForm, setShowAnalysisForm] = useState(false);

  const mockStats = {
    totalAnalyzed: 45,
    buySignals: 18,
    sellSignals: 16,
    holdSignals: 11,
    avgConfidence: 0.85,
    accuracy: 78,
  };

  const handleAnalysisRequest = async (symbol: string) => {
    setAnalyzing(true);
    try {
      await api.post('/api/v1/brain/decide', { symbol });
    } catch (error) {
      console.error('Failed to analyze:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision.toUpperCase()) {
      case 'BUY':
        return 'from-green-500 to-emerald-500';
      case 'SELL':
        return 'from-red-500 to-pink-500';
      default:
        return 'from-yellow-500 to-orange-500';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
            🧠 AI Brain
          </h1>
          <p className="text-slate-400">Machine Learning Decision Engine</p>
        </div>
        <Button
          onClick={() => setShowAnalysisForm(!showAnalysisForm)}
          className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500"
        >
          <Sparkles className="h-4 w-4 mr-2" />
          New Analysis
        </Button>
      </div>

      {showAnalysisForm && (
        <div className="premium-card p-8 rounded-xl border border-purple-500/20">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Brain className="h-6 w-6 text-purple-400" />
            Request AI Analysis
          </h2>
          <BrainAnalysisForm onSubmit={handleAnalysisRequest} loading={analyzing} />
        </div>
      )}

      {/* Key Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="premium-card p-6 rounded-lg border border-blue-500/20">
          <p className="text-xs font-semibold text-slate-400 mb-2">TOTAL ANALYZED</p>
          <p className="text-3xl font-bold text-blue-400">{mockStats.totalAnalyzed}</p>
        </div>

        <div className="premium-card p-6 rounded-lg border border-green-500/20">
          <p className="text-xs font-semibold text-slate-400 mb-2">BUY SIGNALS</p>
          <p className="text-3xl font-bold text-green-400">{mockStats.buySignals}</p>
        </div>

        <div className="premium-card p-6 rounded-lg border border-red-500/20">
          <p className="text-xs font-semibold text-slate-400 mb-2">SELL SIGNALS</p>
          <p className="text-3xl font-bold text-red-400">{mockStats.sellSignals}</p>
        </div>

        <div className="premium-card p-6 rounded-lg border border-yellow-500/20">
          <p className="text-xs font-semibold text-slate-400 mb-2">HOLD SIGNALS</p>
          <p className="text-3xl font-bold text-yellow-400">{mockStats.holdSignals}</p>
        </div>

        <div className="premium-card p-6 rounded-lg border border-purple-500/20">
          <p className="text-xs font-semibold text-slate-400 mb-2">AVG CONFIDENCE</p>
          <p className="text-3xl font-bold text-purple-400">{(mockStats.avgConfidence * 100).toFixed(0)}%</p>
        </div>

        <div className="premium-card p-6 rounded-lg border border-pink-500/20">
          <p className="text-xs font-semibold text-slate-400 mb-2">ACCURACY</p>
          <p className="text-3xl font-bold text-pink-400">{mockStats.accuracy}%</p>
        </div>
      </div>

      {/* AI Decision Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 premium-card p-8 rounded-xl border border-purple-500/20">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Activity className="h-6 w-6 text-purple-400" />
            Latest AI Decisions
          </h2>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
            </div>
          ) : decisions.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              No brain decisions found. Request an analysis to get started.
            </div>
          ) : (
            <div className="space-y-4">
              {decisions.map((decision) => (
                <div
                  key={decision.id}
                  className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-6 hover:border-purple-500/50 transition-all"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-4 flex-1">
                      <div className={`px-4 py-2 rounded-lg bg-gradient-to-r ${getDecisionColor(decision.decision)} text-white font-bold text-lg`}>
                        {decision.decision}
                      </div>
                      <div>
                        <p className="text-lg font-bold text-white">{decision.symbol}</p>
                        <p className="text-sm text-slate-400">{decision.timestamp ? new Date(decision.timestamp).toLocaleString() : '-'}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-transparent bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text">
                        {(decision.confidence * 100).toFixed(0)}%
                      </p>
                      <p className="text-xs text-slate-400">Confidence</p>
                    </div>
                  </div>

                  <div className="mb-4 p-4 bg-slate-900/30 rounded-lg border border-slate-700/30">
                    <p className="text-slate-300 text-sm leading-relaxed">{decision.reasoning}</p>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-3 bg-slate-900/20 rounded-lg border border-slate-700/30">
                      <p className="text-xs text-slate-400 mb-1">TARGET</p>
                      <p className="text-lg font-bold text-green-400">${decision.targetPrice?.toFixed(4)}</p>
                    </div>
                    <div className="p-3 bg-slate-900/20 rounded-lg border border-slate-700/30">
                      <p className="text-xs text-slate-400 mb-1">STOP LOSS</p>
                      <p className="text-lg font-bold text-red-400">${decision.stopLoss?.toFixed(4)}</p>
                    </div>
                    <div className="p-3 bg-slate-900/20 rounded-lg border border-slate-700/30">
                      <p className="text-xs text-slate-400 mb-1">RATIO</p>
                      <p className="text-lg font-bold text-blue-400">
                        {((decision.targetPrice! - decision.symbol.charCodeAt(0) / 100) / (decision.symbol.charCodeAt(0) / 100 - decision.stopLoss!)).toFixed(2)}:1
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Decision Summary */}
        <div className="premium-card p-8 rounded-xl border border-pink-500/20">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Target className="h-6 w-6 text-pink-400" />
            Decision Summary
          </h2>

          <div className="space-y-6">
            {/* Buy Distribution */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-slate-400">Buy Signals</span>
                <span className="text-sm font-bold text-green-400">{Math.round((mockStats.buySignals / mockStats.totalAnalyzed) * 100)}%</span>
              </div>
              <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-green-400 to-emerald-400" style={{ width: `${(mockStats.buySignals / mockStats.totalAnalyzed) * 100}%` }}></div>
              </div>
            </div>

            {/* Sell Distribution */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-slate-400">Sell Signals</span>
                <span className="text-sm font-bold text-red-400">{Math.round((mockStats.sellSignals / mockStats.totalAnalyzed) * 100)}%</span>
              </div>
              <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-red-400 to-pink-400" style={{ width: `${(mockStats.sellSignals / mockStats.totalAnalyzed) * 100}%` }}></div>
              </div>
            </div>

            {/* Hold Distribution */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-slate-400">Hold Signals</span>
                <span className="text-sm font-bold text-yellow-400">{Math.round((mockStats.holdSignals / mockStats.totalAnalyzed) * 100)}%</span>
              </div>
              <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-yellow-400 to-orange-400" style={{ width: `${(mockStats.holdSignals / mockStats.totalAnalyzed) * 100}%` }}></div>
              </div>
            </div>

            <div className="border-t border-slate-700/50 pt-6">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-400">ML Model</span>
                  <span className="text-white font-semibold">LightGBM v3</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Features</span>
                  <span className="text-white font-semibold">156</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Training Data</span>
                  <span className="text-white font-semibold">5Y history</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Last Update</span>
                  <span className="text-white font-semibold">2h ago</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}