import React from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  AlertCircle, 
  ShieldCheck, 
  ArrowRight, 
  FileText, 
  Mail, 
  Building2,
  Calendar,
  Layers
} from 'lucide-react';
import { AuditOverview, AuditFinding } from '../types';

interface DashboardViewProps {
  overview: AuditOverview | null;
  loading: boolean;
  onNavigate: (tab: string) => void;
  onSelectFinding: (finding: AuditFinding) => void;
  onRunQuickAudit: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  overview,
  loading,
  onNavigate,
  onSelectFinding,
  onRunQuickAudit
}) => {
  const totalOvercharge = overview?.total_overcharge || '9159.31';
  const totalFindingsCount = overview?.total_findings_count || 287;
  const byCategory = overview?.by_category || {
    base_discount: '3420.50',
    accessorial_rule: '2150.00',
    fuel_surcharge: '1840.81',
    duplicate_charge: '1248.00',
    minimum_charge: '500.00'
  };
  const byCarrier = overview?.by_carrier || {
    'Apex Freight Logistics': '4820.50',
    'Beacon Express Transport': '2710.25',
    'Crestline Cargo Partners': '1628.56'
  };

  const categoryLabels: Record<string, string> = {
    base_discount: 'Base Discount Errors',
    accessorial_rule: 'Disallowed Accessorials',
    fuel_surcharge: 'Fuel Surcharge Drift',
    duplicate_charge: 'Duplicate Shipments',
    minimum_charge: 'Inflated Minimums'
  };

  return (
    <div className="space-y-8">
      {/* Hero Element: Total Recoverable Overcharge */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-900 via-slate-900 to-slate-950 p-8 text-white shadow-2xl border border-emerald-500/20">
        <div className="relative z-10 flex flex-col justify-between gap-6 md:flex-row md:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
              <ShieldCheck className="h-4 w-4" />
              <span>100% Deterministic Arithmetic Verification</span>
            </div>
            <h1 className="mt-3 text-sm font-semibold uppercase tracking-wider text-slate-400">
              Total Recoverable Overcharge Detected
            </h1>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-5xl font-black tracking-tight text-white sm:text-6xl tabular-nums">
                ${totalOvercharge}
              </span>
              <span className="text-xl font-bold text-emerald-400">USD</span>
            </div>
            <p className="mt-2 text-sm text-slate-300">
              Across <strong className="text-white">{totalFindingsCount} itemized contract discrepancies</strong> verified by deterministic rules engine.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate('disputes')}
              className="flex items-center gap-2 rounded-xl bg-emerald-500 px-5 py-3 text-sm font-bold text-slate-950 shadow-lg shadow-emerald-500/30 transition hover:bg-emerald-400"
            >
              <Mail className="h-4 w-4" />
              <span>Generate Dispute Letter</span>
            </button>
            <button
              onClick={() => onNavigate('findings')}
              className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 px-5 py-3 text-sm font-bold text-white transition hover:bg-slate-700"
            >
              <span>Explore Findings</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Ambient background glow */}
        <div className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-emerald-500/10 blur-3xl" />
      </div>

      {/* Breakdown Grids */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        
        {/* Category Breakdown */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400">
                <Layers className="h-5 w-5" />
              </div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">Recoverable by Category</h2>
            </div>
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">5 Categories</span>
          </div>

          <div className="mt-4 space-y-3">
            {Object.entries(byCategory).map(([catKey, amount]) => (
              <div key={catKey} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    {categoryLabels[catKey] || catKey}
                  </span>
                </div>
                <span className="text-sm font-bold tabular-nums text-slate-900 dark:text-white">
                  ${amount}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Carrier Breakdown */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="rounded-lg bg-blue-50 p-2 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400">
                <Building2 className="h-5 w-5" />
              </div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">Recoverable by Carrier</h2>
            </div>
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Active Contracts</span>
          </div>

          <div className="mt-4 space-y-3">
            {Object.entries(byCarrier).map(([carrier, amount]) => (
              <div key={carrier} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  {carrier}
                </span>
                <span className="text-sm font-bold tabular-nums text-emerald-600 dark:text-emerald-400">
                  ${amount}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Action Walkthrough */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div 
          onClick={() => onNavigate('contracts')}
          className="cursor-pointer group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-emerald-500 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase">Step 1</span>
            <FileText className="h-5 w-5 text-slate-400 group-hover:text-emerald-500 transition" />
          </div>
          <h3 className="mt-2 text-sm font-bold text-slate-900 dark:text-white">Review Extracted Rules</h3>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Verify proposed rules extracted by Gemma against verbatim contract clauses.
          </p>
        </div>

        <div 
          onClick={() => onNavigate('findings')}
          className="cursor-pointer group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-emerald-500 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase">Step 2</span>
            <AlertCircle className="h-5 w-5 text-slate-400 group-hover:text-blue-500 transition" />
          </div>
          <h3 className="mt-2 text-sm font-bold text-slate-900 dark:text-white">Audit Invoices</h3>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Execute deterministic audit to uncover line-level overcharges with mathematical proof.
          </p>
        </div>

        <div 
          onClick={() => onNavigate('disputes')}
          className="cursor-pointer group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-emerald-500 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-purple-600 dark:text-purple-400 uppercase">Step 3</span>
            <Mail className="h-5 w-5 text-slate-400 group-hover:text-purple-500 transition" />
          </div>
          <h3 className="mt-2 text-sm font-bold text-slate-900 dark:text-white">Claim Overcharges</h3>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Approve generated dispute letter and export formal Markdown or PDF evidence.
          </p>
        </div>
      </div>
    </div>
  );
};
