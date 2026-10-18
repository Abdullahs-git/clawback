import React, { useState } from 'react';
import { 
  AlertTriangle, 
  Search, 
  Filter, 
  ArrowUpDown, 
  Calendar, 
  CheckCircle2, 
  FileText, 
  Play, 
  X,
  Clock,
  ShieldCheck
} from 'lucide-react';
import { AuditFinding, ContractSummary, InvoiceBatchSummary } from '../types';

interface AuditViewProps {
  findings: AuditFinding[];
  contracts: ContractSummary[];
  batches: InvoiceBatchSummary[];
  loading: boolean;
  onRunAudit: (batchId: string, contractId: string) => Promise<void>;
  onSelectFinding: (finding: AuditFinding) => void;
  selectedFinding: AuditFinding | null;
  onCloseDrilldown: () => void;
}

export const AuditView: React.FC<AuditViewProps> = ({
  findings,
  contracts,
  batches,
  loading,
  onRunAudit,
  onSelectFinding,
  selectedFinding,
  onCloseDrilldown
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [carrierFilter, setCarrierFilter] = useState('all');
  const [ruleTypeFilter, setRuleTypeFilter] = useState('all');
  const [selectedBatchId, setSelectedBatchId] = useState('');
  const [selectedContractId, setSelectedContractId] = useState('');
  const [isAuditing, setIsAuditing] = useState(false);

  const carriers = Array.from(new Set(findings.map(f => f.carrier_name)));
  const ruleTypes = Array.from(new Set(findings.map(f => f.rule_type)));

  const filteredFindings = findings.filter(f => {
    const matchesSearch = 
      f.shipment_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.invoice_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.charge_code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCarrier = carrierFilter === 'all' || f.carrier_name === carrierFilter;
    const matchesRule = ruleTypeFilter === 'all' || f.rule_type === ruleTypeFilter;
    return matchesSearch && matchesCarrier && matchesRule;
  });

  const handleRunAuditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBatchId || !selectedContractId) {
      alert('Please select both an invoice batch and a contract.');
      return;
    }
    setIsAuditing(true);
    try {
      await onRunAudit(selectedBatchId, selectedContractId);
    } catch (err: any) {
      alert(`Audit failed: ${err.message}`);
    } finally {
      setIsAuditing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Quick Audit Runner */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Deterministic Audit Engine</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Evaluates every invoice line against approved contract rules using 100% Decimal arithmetic.
            </p>
          </div>

          {/* Quick Audit Bar */}
          <form onSubmit={handleRunAuditSubmit} className="flex flex-wrap items-center gap-2">
            <select
              value={selectedBatchId}
              onChange={(e) => setSelectedBatchId(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-900 focus:border-emerald-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="">Select Invoice Batch...</option>
              {batches.map(b => (
                <option key={b.id} value={b.id}>{b.carrier_name} ({b.total_lines} lines)</option>
              ))}
            </select>

            <select
              value={selectedContractId}
              onChange={(e) => setSelectedContractId(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-900 focus:border-emerald-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="">Select Contract Rules...</option>
              {contracts.map(c => (
                <option key={c.id} value={c.id}>{c.carrier_name} ({c.approved_rule_count} approved)</option>
              ))}
            </select>

            <button
              type="submit"
              disabled={isAuditing}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-bold text-white shadow transition hover:bg-emerald-500 disabled:opacity-50"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>{isAuditing ? 'Auditing with Decimal...' : 'Run Audit'}</span>
            </button>
          </form>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search shipment ID, invoice #..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-64 rounded-lg border border-slate-300 bg-white pl-8 pr-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>

          {/* Carrier Filter */}
          <select
            value={carrierFilter}
            onChange={(e) => setCarrierFilter(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-900 focus:border-emerald-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            <option value="all">All Carriers</option>
            {carriers.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          {/* Rule Type Filter */}
          <select
            value={ruleTypeFilter}
            onChange={(e) => setRuleTypeFilter(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-900 focus:border-emerald-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            <option value="all">All Rule Types</option>
            {ruleTypes.map(rt => <option key={rt} value={rt}>{rt}</option>)}
          </select>
        </div>

        <span className="text-xs text-slate-500 dark:text-slate-400">
          Showing <strong>{filteredFindings.length}</strong> of {findings.length} findings
        </span>
      </div>

      {/* Findings Table */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 font-semibold text-slate-600 dark:bg-slate-800/50 dark:text-slate-400">
              <tr>
                <th className="px-5 py-3.5">Shipment ID</th>
                <th className="px-5 py-3.5">Invoice #</th>
                <th className="px-5 py-3.5">Carrier</th>
                <th className="px-5 py-3.5">Charge Code</th>
                <th className="px-5 py-3.5">Triggered Rule</th>
                <th className="px-5 py-3.5 text-right">Expected</th>
                <th className="px-5 py-3.5 text-right">Billed</th>
                <th className="px-5 py-3.5 text-right font-bold text-slate-900 dark:text-white">Overcharge</th>
                <th className="px-5 py-3.5 text-center">Claim Deadline</th>
                <th className="px-5 py-3.5 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-sans">
              {filteredFindings.map((f) => (
                <tr 
                  key={f.finding_id} 
                  className="hover:bg-slate-50/70 dark:hover:bg-slate-800/50 transition cursor-pointer"
                  onClick={() => onSelectFinding(f)}
                >
                  <td className="px-5 py-3 font-mono font-medium text-slate-900 dark:text-white">
                    {f.shipment_id}
                  </td>
                  <td className="px-5 py-3 font-mono text-slate-600 dark:text-slate-400">
                    {f.invoice_number}
                  </td>
                  <td className="px-5 py-3 font-medium text-slate-800 dark:text-slate-200">
                    {f.carrier_name}
                  </td>
                  <td className="px-5 py-3">
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                      {f.charge_code}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-slate-600 dark:text-slate-400 max-w-[200px] truncate" title={f.rule_description}>
                    {f.rule_description}
                  </td>
                  <td className="px-5 py-3 text-right tabular-nums text-slate-500">
                    ${f.expected_amount}
                  </td>
                  <td className="px-5 py-3 text-right tabular-nums text-slate-600 dark:text-slate-400">
                    ${f.billed_amount}
                  </td>
                  <td className="px-5 py-3 text-right font-bold tabular-nums text-emerald-600 dark:text-emerald-400">
                    +${f.overcharge_amount}
                  </td>
                  <td className="px-5 py-3 text-center">
                    {f.claim_deadline_date ? (
                      <span className="inline-flex items-center gap-1 rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                        <Clock className="h-3 w-3" />
                        {f.claim_deadline_date}
                      </span>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectFinding(f);
                      }}
                      className="rounded bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                    >
                      Proof & Drilldown
                    </button>
                  </td>
                </tr>
              ))}

              {filteredFindings.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-5 py-12 text-center text-slate-500">
                    No audit findings match your current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Drilldown Traceability Side Panel (Non-blocking slide-over) */}
      {selectedFinding && (
        <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-4xl flex-col bg-white shadow-2xl dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 transition-all duration-300">
          {/* Panel Header */}
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded bg-emerald-100 px-2 py-0.5 text-[10px] font-bold uppercase text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                  Audit Proof
                </span>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Finding {selectedFinding.finding_id.slice(0, 8)}: Shipment {selectedFinding.shipment_id}
                </h3>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Carrier: <strong className="text-slate-700 dark:text-slate-300">{selectedFinding.carrier_name}</strong> | Invoice: <strong className="font-mono text-slate-700 dark:text-slate-300">{selectedFinding.invoice_number}</strong>
              </p>
            </div>
            <button
              onClick={onCloseDrilldown}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              title="Close side panel"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Overcharge Summary Banner */}
          <div className="flex items-center justify-between bg-emerald-50 px-6 py-3 border-b border-emerald-100 dark:bg-emerald-950/30 dark:border-emerald-900/50">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
                Net Overcharge Claimed
              </span>
              <div className="text-2xl font-black tabular-nums text-emerald-800 dark:text-emerald-300">
                +${selectedFinding.overcharge_amount} USD
              </div>
            </div>
            <div className="text-right text-xs">
              <span className="text-slate-500 dark:text-slate-400">Claim Window: </span>
              <strong className="text-slate-900 dark:text-white font-mono">
                {selectedFinding.days_remaining_to_claim !== null && selectedFinding.days_remaining_to_claim !== undefined
                  ? `${selectedFinding.days_remaining_to_claim} days remaining`
                  : 'Contract standard (180d)'}
              </strong>
              {selectedFinding.claim_deadline_date && (
                <p className="text-[11px] text-slate-400">Deadline: {selectedFinding.claim_deadline_date}</p>
              )}
            </div>
          </div>

          {/* 3-Column Proof Body */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs">
              
              {/* Column 1: The Invoice Line */}
              <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-800/30 space-y-3">
                <div className="flex items-center gap-1.5 font-bold text-slate-900 dark:text-white border-b border-slate-200 pb-2 dark:border-slate-700">
                  <FileText className="h-4 w-4 text-slate-500" />
                  <span>1. The Invoice Line</span>
                </div>
                <div className="space-y-2">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Billed Charge Code:</span>
                    <span className="font-mono font-bold text-slate-900 dark:text-white rounded bg-slate-200/60 dark:bg-slate-700 px-1.5 py-0.5">
                      {selectedFinding.charge_code}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Amount Billed:</span>
                    <span className="text-base font-bold tabular-nums text-slate-900 dark:text-white">
                      ${selectedFinding.billed_amount}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Shipment Reference:</span>
                    <span className="font-mono text-slate-700 dark:text-slate-300">{selectedFinding.shipment_id}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Invoice Number:</span>
                    <span className="font-mono text-slate-700 dark:text-slate-300">{selectedFinding.invoice_number}</span>
                  </div>
                </div>
              </div>

              {/* Column 2: The Contract Quote & Citation */}
              <div className="rounded-xl border border-blue-200 bg-blue-50/30 p-4 dark:border-blue-900/40 dark:bg-blue-950/20 space-y-3">
                <div className="flex items-center gap-1.5 font-bold text-slate-900 dark:text-white border-b border-blue-200 pb-2 dark:border-blue-800/60">
                  <ShieldCheck className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <span>2. Contract Quote Citation</span>
                </div>
                <div className="space-y-2">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Governing Rule:</span>
                    <span className="font-bold text-blue-700 dark:text-blue-300">{selectedFinding.rule_description}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Contract Page:</span>
                    <span className="font-mono font-semibold text-slate-700 dark:text-slate-300">Page {selectedFinding.contract_page}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Verbatim Contract Clause:</span>
                    <blockquote className="italic border-l-2 border-blue-500 pl-2 text-slate-700 dark:text-slate-300 bg-white/70 dark:bg-slate-800/60 p-2 rounded text-[11px] mt-1">
                      "{selectedFinding.contract_clause_quote}"
                    </blockquote>
                  </div>
                </div>
              </div>

              {/* Column 3: The Arithmetic Proof */}
              <div className="rounded-xl border border-emerald-200 bg-emerald-50/30 p-4 dark:border-emerald-900/40 dark:bg-emerald-950/20 space-y-3">
                <div className="flex items-center gap-1.5 font-bold text-slate-900 dark:text-white border-b border-emerald-200 pb-2 dark:border-emerald-800/60">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  <span>3. Arithmetic Calculation</span>
                </div>
                <div className="space-y-2">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Contract Expected:</span>
                    <span className="text-base font-bold tabular-nums text-slate-900 dark:text-white">
                      ${selectedFinding.expected_amount}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Overcharge Amount:</span>
                    <span className="text-base font-black tabular-nums text-emerald-700 dark:text-emerald-400">
                      ${selectedFinding.overcharge_amount}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Step-by-Step Formula:</span>
                    <div className="font-mono text-[11px] bg-white/80 dark:bg-slate-800/80 p-2 rounded border border-emerald-200 dark:border-emerald-800/50 text-slate-800 dark:text-slate-200">
                      {selectedFinding.calculation_math}
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>

          {/* Panel Footer */}
          <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-6 py-3 dark:border-slate-800 dark:bg-slate-800/40">
            <span className="text-xs text-slate-500">
              Deterministic Python Decimal calculation • Zero LLM math
            </span>
            <button
              onClick={onCloseDrilldown}
              className="rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900"
            >
              Close Side Panel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
