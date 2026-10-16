import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardView } from './components/DashboardView';
import { ContractsView } from './components/ContractsView';
import { InvoicesView } from './components/InvoicesView';
import { AuditView } from './components/AuditView';
import { DisputeView } from './components/DisputeView';
import { AmdPanel } from './components/AmdPanel';
import { 
  ContractSummary, 
  ContractDetail, 
  InvoiceBatchSummary, 
  AuditOverview, 
  AuditFinding, 
  DisputeLetter, 
  AmdPanelMetrics 
} from './types';
import { api } from './api/client';

export function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [darkMode, setDarkMode] = useState(false);
  const [loading, setLoading] = useState(true);

  // Data states
  const [amdMetrics, setAmdMetrics] = useState<AmdPanelMetrics | null>(null);
  const [contracts, setContracts] = useState<ContractSummary[]>([]);
  const [selectedContract, setSelectedContract] = useState<ContractDetail | null>(null);
  const [batches, setBatches] = useState<InvoiceBatchSummary[]>([]);
  const [overview, setOverview] = useState<AuditOverview | null>(null);
  const [disputes, setDisputes] = useState<DisputeLetter[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<AuditFinding | null>(null);

  // Sync dark mode class
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Load all data on mount
  useEffect(() => {
    refreshAllData();
  }, []);

  const refreshAllData = async () => {
    setLoading(true);
    try {
      const [amdRes, contractsRes, batchesRes, findingsRes, disputesRes] = await Promise.allSettled([
        api.getAmdStatus(),
        api.getContracts(),
        api.getInvoiceBatches(),
        api.getFindings(),
        api.getDisputes(),
      ]);

      if (amdRes.status === 'fulfilled') setAmdMetrics(amdRes.value);
      if (contractsRes.status === 'fulfilled') {
        setContracts(contractsRes.value);
        if (contractsRes.value.length > 0 && !selectedContract) {
          loadContractDetail(contractsRes.value[0].id);
        }
      }
      if (batchesRes.status === 'fulfilled') setBatches(batchesRes.value);
      if (findingsRes.status === 'fulfilled') setOverview(findingsRes.value);
      if (disputesRes.status === 'fulfilled') setDisputes(disputesRes.value);
    } catch (err) {
      console.error('Failed to load initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadContractDetail = async (contractId: string) => {
    try {
      const detail = await api.getContractDetail(contractId);
      setSelectedContract(detail);
    } catch (err) {
      console.error(err);
    }
  };

  const handleUploadContract = async (file: File, carrierName: string) => {
    const detail = await api.uploadContract(file, carrierName);
    setSelectedContract(detail);
    await refreshAllData();
  };

  const handleUpdateRuleStatus = async (contractId: string, ruleId: string, status: 'approved' | 'rejected') => {
    await api.updateRule(contractId, ruleId, { status });
    await loadContractDetail(contractId);
    const contractsRes = await api.getContracts();
    setContracts(contractsRes);
  };

  const handleBatchApprove = async (contractId: string, ruleIds: string[]) => {
    await api.batchUpdateRules(contractId, 'approve', ruleIds);
    await loadContractDetail(contractId);
    const contractsRes = await api.getContracts();
    setContracts(contractsRes);
  };

  const handleUploadInvoices = async (file: File, carrierName: string) => {
    await api.uploadInvoices(file, carrierName);
    await refreshAllData();
  };

  const handleRunAudit = async (batchId: string, contractId: string) => {
    await api.runAudit(batchId, contractId);
    const findingsRes = await api.getFindings();
    setOverview(findingsRes);
    setActiveTab('findings');
  };

  const handleGenerateDispute = async (batchId: string, carrierName: string) => {
    const letter = await api.generateDispute(batchId, carrierName);
    const disputesRes = await api.getDisputes();
    setDisputes(disputesRes);
  };

  const handleApproveDispute = async (letterId: string) => {
    await api.updateDispute(letterId, { status: 'approved' });
    const disputesRes = await api.getDisputes();
    setDisputes(disputesRes);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        mode={amdMetrics?.mode || 'replay'}
        modelName={amdMetrics?.model_name || 'google/gemma-2-9b-it'}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        openFindingsCount={overview?.total_findings_count || 0}
      />

      <main className="flex-1 mx-auto max-w-7xl px-4 py-8 sm:px-6 w-full">
        {activeTab === 'dashboard' && (
          <DashboardView
            overview={overview}
            loading={loading}
            onNavigate={setActiveTab}
            onSelectFinding={(f) => {
              setSelectedFinding(f);
              setActiveTab('findings');
            }}
            onRunQuickAudit={() => setActiveTab('findings')}
          />
        )}

        {activeTab === 'findings' && (
          <AuditView
            findings={overview?.findings || []}
            contracts={contracts}
            batches={batches}
            loading={loading}
            onRunAudit={handleRunAudit}
            onSelectFinding={setSelectedFinding}
            selectedFinding={selectedFinding}
            onCloseDrilldown={() => setSelectedFinding(null)}
          />
        )}

        {activeTab === 'contracts' && (
          <ContractsView
            contracts={contracts}
            selectedContract={selectedContract}
            loading={loading}
            onSelectContract={loadContractDetail}
            onUploadContract={handleUploadContract}
            onUpdateRuleStatus={handleUpdateRuleStatus}
            onBatchApprove={handleBatchApprove}
          />
        )}

        {activeTab === 'invoices' && (
          <InvoicesView
            batches={batches}
            loading={loading}
            onUploadInvoices={handleUploadInvoices}
            onTriggerAudit={(batchId) => {
              setActiveTab('findings');
            }}
          />
        )}

        {activeTab === 'disputes' && (
          <DisputeView
            disputes={disputes}
            batches={batches}
            loading={loading}
            onGenerateDispute={handleGenerateDispute}
            onApproveDispute={handleApproveDispute}
            onRefresh={refreshAllData}
          />
        )}

        {activeTab === 'amd' && (
          <AmdPanel
            metrics={amdMetrics}
            loading={loading}
            onRefresh={async () => {
              const res = await api.getAmdStatus();
              setAmdMetrics(res);
            }}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 dark:border-slate-800 dark:bg-slate-900 text-xs text-slate-500">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-700 dark:text-slate-300">Clawback</span>
            <span>—</span>
            <span>AMD Developer Hackathon: ACT III Submission</span>
          </div>
          <div className="flex items-center gap-4">
            <span>Model: <strong className="font-mono text-slate-700 dark:text-slate-300">Gemma-2-9B</strong> on AMD ROCm</span>
            <span>MIT License</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
