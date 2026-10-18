import React, { useState } from 'react';
import { Cpu, Activity, Clock, Zap, Server, CheckCircle2, AlertCircle, Play, X } from 'lucide-react';
import { AmdPanelMetrics } from '../types';
import { api } from '../api/client';

interface AmdPanelProps {
  metrics: AmdPanelMetrics | null;
  loading: boolean;
  onRefresh: () => void;
}

export const AmdPanel: React.FC<AmdPanelProps> = ({ metrics, loading, onRefresh }) => {
  const [testingLive, setTestingLive] = useState(false);
  const [liveTestResult, setLiveTestResult] = useState<any>(null);

  if (loading && !metrics) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-rose-500 border-t-transparent" />
      </div>
    );
  }

  const isConnected = metrics?.is_connected ?? true;
  const mode = metrics?.mode ?? 'replay';
  const lastLiveTs = metrics?.last_live_call_timestamp 
    ? new Date(metrics.last_live_call_timestamp).toLocaleString()
    : null;

  const handleRunLiveTest = async () => {
    setTestingLive(true);
    try {
      const res = await api.runLiveTestCall();
      setLiveTestResult(res);
      onRefresh();
    } catch (err) {
      console.error('Failed to run live test call:', err);
    } finally {
      setTestingLive(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-zinc-900 to-neutral-900 p-6 text-white shadow-xl border border-slate-800">
        <div className="relative z-10 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-rose-600 text-white font-black text-xs">
                AMD
              </span>
              <h2 className="text-xl font-bold tracking-tight text-white">AMD Inference Telemetry Engine</h2>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                mode === 'live' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              }`}>
                {mode === 'live' ? 'LIVE ROCm/vLLM' : 'REPLAY (recorded from AMD endpoint)'}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-300">
              Live operational metrics for legal rule extraction powered by Google Gemma on AMD Developer Cloud / ROCm infrastructure.
            </p>
            <p className="mt-1 font-mono text-xs text-slate-400">
              Last Successful Live Call: {lastLiveTs ? <strong className="text-emerald-400">{lastLiveTs}</strong> : <span className="text-amber-400">No live call recorded in session (REPLAY active)</span>}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleRunLiveTest}
              disabled={testingLive}
              className="inline-flex items-center gap-1.5 rounded-lg bg-rose-600 px-3.5 py-2 text-xs font-bold text-white shadow-md hover:bg-rose-500 disabled:opacity-50 transition"
            >
              <Zap className={`h-3.5 w-3.5 ${testingLive ? 'animate-pulse' : ''}`} />
              <span>{testingLive ? 'Running Live Call...' : 'Run Live Extraction Test'}</span>
            </button>

            <button
              onClick={onRefresh}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-200 transition hover:bg-slate-700"
            >
              Refresh Telemetry
            </button>
          </div>
        </div>
      </div>

      {/* Live Test Result Callout Modal */}
      {liveTestResult && (
        <div className="rounded-2xl border border-rose-500/40 bg-slate-900 p-6 text-white shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-rose-400" />
              <h3 className="font-bold text-sm">Live Extraction Verification Test Results</h3>
              <span className="rounded bg-rose-500/20 px-2 py-0.5 font-mono text-[11px] font-semibold text-rose-300">
                Mode: {liveTestResult.mode?.toUpperCase()}
              </span>
            </div>
            <button
              onClick={() => setLiveTestResult(null)}
              className="rounded p-1 text-slate-400 hover:bg-slate-800"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4 font-mono text-xs">
            <div className="rounded-lg bg-slate-800/60 p-3">
              <span className="text-slate-400 text-[10px] block uppercase">Raw Latency</span>
              <span className="text-base font-bold text-white">{liveTestResult.latency_ms} ms</span>
            </div>
            <div className="rounded-lg bg-slate-800/60 p-3">
              <span className="text-slate-400 text-[10px] block uppercase">Throughput</span>
              <span className="text-base font-bold text-rose-400">{liveTestResult.tokens_per_second} tps</span>
            </div>
            <div className="rounded-lg bg-slate-800/60 p-3">
              <span className="text-slate-400 text-[10px] block uppercase">Tokens (In / Out)</span>
              <span className="text-base font-bold text-white">{liveTestResult.prompt_tokens} / {liveTestResult.completion_tokens}</span>
            </div>
            <div className="rounded-lg bg-slate-800/60 p-3">
              <span className="text-slate-400 text-[10px] block uppercase">Inference Host</span>
              <span className="text-xs font-bold text-white truncate block">{liveTestResult.endpoint_host}</span>
            </div>
          </div>

          <div className="mt-4 rounded-lg bg-slate-950 p-4 font-mono text-xs text-slate-300 overflow-x-auto">
            <p className="text-[10px] font-bold uppercase text-slate-400 mb-1">Parsed Rule Output from Gemma on AMD:</p>
            <pre>{JSON.stringify(liveTestResult.extracted_data, null, 2)}</pre>
          </div>
        </div>
      )}

      {/* Primary KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Model Identifier */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-rose-50 p-2.5 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Model Architecture</p>
              <p className="font-mono text-sm font-bold text-slate-900 dark:text-white">
                {metrics?.model_name || 'google/gemma-2-9b-it'}
              </p>
            </div>
          </div>
        </div>

        {/* Endpoint Host */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-emerald-50 p-2.5 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400">
              <Server className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Inference Host</p>
              <div className="flex items-center gap-1.5">
                <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                <p className="font-mono text-xs font-bold text-slate-900 dark:text-white">
                  {metrics?.endpoint_host || 'notebooks.amd.com'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Average Latency */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-blue-50 p-2.5 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400">
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Average Latency</p>
              <p className="text-lg font-bold tabular-nums text-slate-900 dark:text-white">
                {metrics?.average_latency_ms !== undefined ? `${metrics.average_latency_ms.toFixed(1)} ms` : '-'}
              </p>
            </div>
          </div>
        </div>

        {/* Throughput */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-amber-50 p-2.5 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Tokens / Second</p>
              <p className="text-lg font-bold tabular-nums text-slate-900 dark:text-white">
                {metrics?.average_tokens_per_second !== undefined ? `~${metrics.average_tokens_per_second.toFixed(1)} tps` : '-'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Session Activity and Non-Negotiable Principle Notice */}
      <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-4 text-xs text-emerald-900 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300">
        <div className="flex items-start gap-2.5">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <div>
            <p className="font-bold">Architectural Principle: LLM Never Computes Money</p>
            <p className="mt-0.5 text-emerald-800 dark:text-emerald-400">
              Gemma on AMD is dedicated solely to legal language parsing, rule schema extraction, and quote verification. All money, percentages, comparisons, and claim totals are calculated deterministically using pure Python <code className="font-mono font-semibold">Decimal</code> arithmetic.
            </p>
          </div>
        </div>
      </div>

      {/* Call History Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Recent AMD Inference Logs</h3>
          <span className="text-xs text-slate-500 dark:text-slate-400">Total Calls: {metrics?.total_calls ?? 0}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 font-semibold text-slate-600 dark:bg-slate-800/50 dark:text-slate-400">
              <tr>
                <th className="px-6 py-3">Timestamp</th>
                <th className="px-6 py-3">Operation</th>
                <th className="px-6 py-3">Mode</th>
                <th className="px-6 py-3 text-right">Prompt Tokens</th>
                <th className="px-6 py-3 text-right">Completion</th>
                <th className="px-6 py-3 text-right">Latency</th>
                <th className="px-6 py-3 text-right">Throughput</th>
                <th className="px-6 py-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-slate-700 dark:divide-slate-800 dark:text-slate-300">
              {(metrics?.recent_calls && metrics.recent_calls.length > 0) ? (
                metrics.recent_calls.map((call) => (
                  <tr key={call.call_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/50">
                    <td className="px-6 py-3">{new Date(call.timestamp).toLocaleTimeString()}</td>
                    <td className="px-6 py-3 font-sans font-medium">{call.operation}</td>
                    <td className="px-6 py-3">
                      <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                        call.mode === 'live' ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300' : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                      }`}>
                        {call.mode}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-right tabular-nums">{call.prompt_tokens}</td>
                    <td className="px-6 py-3 text-right tabular-nums">{call.completion_tokens}</td>
                    <td className="px-6 py-3 text-right tabular-nums">{call.latency_ms.toFixed(1)} ms</td>
                    <td className="px-6 py-3 text-right tabular-nums">{call.tokens_per_second.toFixed(1)} tps</td>
                    <td className="px-6 py-3 text-center">
                      <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400">
                        {call.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-slate-500 font-sans">
                    No calls recorded yet in this session.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
