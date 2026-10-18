import React from 'react';
import { 
  ShieldCheck, 
  Cpu, 
  FileText, 
  FileSpreadsheet, 
  AlertTriangle, 
  Mail, 
  LayoutDashboard,
  Sun,
  Moon,
  Sparkles,
  RefreshCw
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  mode: 'live' | 'replay';
  modelName: string;
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  openFindingsCount: number;
  onSeedDemo?: () => void;
  seeding?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  mode,
  modelName,
  darkMode,
  setDarkMode,
  openFindingsCount,
  onSeedDemo,
  seeding = false,
}) => {
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Sparkles },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'findings', label: 'Audit Findings', icon: AlertTriangle, badge: openFindingsCount },
    { id: 'contracts', label: 'Contracts & Rules', icon: FileText },
    { id: 'invoices', label: 'Invoice Batches', icon: FileSpreadsheet },
    { id: 'disputes', label: 'Dispute Letters', icon: Mail },
    { id: 'amd', label: 'AMD Telemetry', icon: Cpu },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        
        {/* Brand & Badges */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-md shadow-emerald-500/20">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">Clawback</span>
              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                synthetic demo data
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Deterministic Contract Audit & Recovery Engine
            </p>
          </div>
        </div>

        {/* AMD Status Badge (Judges element) */}
        <div className="hidden lg:flex items-center gap-2">
          <div className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold shadow-sm ${
            mode === 'live' 
              ? 'bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/60 dark:text-rose-400 dark:border-rose-800'
              : 'bg-amber-50 text-amber-800 border border-amber-200 dark:bg-amber-950/60 dark:text-amber-400 dark:border-amber-800'
          }`}>
            <span className={`h-2 w-2 rounded-full ${mode === 'live' ? 'bg-rose-500 animate-pulse' : 'bg-amber-500'}`} />
            <span>{mode === 'live' ? 'LIVE (AMD ROCm)' : 'REPLAY (recorded from AMD endpoint)'}</span>
          </div>
          <span className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 font-mono text-[11px] text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
            {modelName}
          </span>
        </div>

        {/* Controls: Seed Demo & Dark Mode */}
        <div className="flex items-center gap-2">
          {onSeedDemo && (
            <button
              onClick={onSeedDemo}
              disabled={seeding}
              className="hidden sm:inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 disabled:opacity-50 transition"
              title="Reset database and load synthetic demo workspace"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${seeding ? 'animate-spin text-emerald-500' : 'text-slate-500'}`} />
              <span>{seeding ? 'Seeding...' : 'Reset Demo Data'}</span>
            </button>
          )}
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
            title="Toggle theme"
          >
            {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="mx-auto flex max-w-7xl overflow-x-auto px-4 sm:px-6">
        <nav className="flex space-x-1" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 border-b-2 px-3 py-2.5 text-xs font-semibold transition-colors sm:text-sm ${
                  isActive
                    ? 'border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400'
                    : 'border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-900 dark:text-slate-400 dark:hover:border-slate-700 dark:hover:text-slate-200'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
                {Boolean(tab.badge && tab.badge > 0) && (
                  <span className="rounded-full bg-emerald-100 px-1.5 py-0.2 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400">
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
