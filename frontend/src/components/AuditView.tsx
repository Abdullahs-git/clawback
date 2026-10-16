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

      {/* Drilldown Traceability Modal */}
      {selectedFinding && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4 dark:border-slate-800">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Audit Discrepancy Evidence & Mathematical Proof
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Shipment: <strong className="font-mono text-slate-800 dark:text-slate-200">{selectedFinding.shipment_id}</strong> | Finding ID: {selectedFinding.finding_id.slice(0, 8)}
                </p>
              </div>
              <button
                onClick={onCloseDrilldown}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-5 text-xs text-slate-700 dark:text-slate-300">
              
              {/* Overcharge Banner */}
              <div className="flex items-center justify-between rounded-xl bg-emerald-50 p-4 border border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-800">
                <div>
                  <span className="text-[11px] font-bold uppercase text-emerald-800 dark:text-emerald-300">
                    Calculated Overcharge Claim
                  </span>
                  <div className="text-2xl font-black tabular-nums text-emerald-700 dark:text-emerald-400">
                    +${selectedFinding.overcharge_amount} USD
                  </div>
                </div>
                <div className="text-right text-xs">
                  <p>Billed: <strong>${selectedFinding.billed_amount}</strong></p>
                  <p>Contract Expected: <strong>${selectedFinding.expected_amount}</strong></p>
                </div>
              </div>

              {/* Step-by-Step Math Proof */}
              <div>
                <h4 className="font-bold text-slate-900 dark:text-white mb-1.5 flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  Deterministic Calculation Proof:
                </h4>
                <div className="rounded-lg bg-slate-50 p-3 font-mono text-xs border border-slate-200 dark:bg-slate-800 dark:border-slate-700 text-slate-800 dark:text-slate-200">
                  {selectedFinding.calculation_math}
                </div>
              </div>

              {/* Verbatim Contract Clause Citation */}
              <div>
                <h4 className="font-bold text-slate-900 dark:text-white mb-1.5 flex items-center gap-1.5">
                  <FileText className="h-4 w-4 text-blue-600" />
                  Governing Contract Clause (Page {selectedFinding.contract_page}):
                </h4>
                <blockquote className="rounded-lg bg-slate-50 p-3 text-xs italic border-l-4 border-blue-500 border border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:border-l-blue-500">
                  "{selectedFinding.contract_clause_quote}"
                </blockquote>
              </div>

              {/* Metadata Grid */}
              <div className="grid grid-cols-2 gap-3 text-xs pt-2 border-t border-slate-100 dark:border-slate-800">
                <div>
                  <span className="text-slate-400">Carrier:</span> <strong className="text-slate-800 dark:text-slate-200">{selectedFinding.carrier_name}</strong>
                </div>
                <div>
                  <span className="text-slate-400">Invoice Number:</span> <strong className="font-mono text-slate-800 dark:text-slate-200">{selectedFinding.invoice_number}</strong>
                </div>
                <div>
                  <span className="text-slate-400">Charge Code:</span> <strong className="font-mono text-slate-800 dark:text-slate-200">{selectedFinding.charge_code}</strong>
                </div>
                <div>
                  <span className="text-slate-400">Claim Window:</span> <strong className="text-slate-800 dark:text-slate-200">{selectedFinding.days_remaining_to_claim ?? 180} days remaining</strong>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end border-t border-slate-100 bg-slate-50 px-6 py-3 dark:border-slate-800 dark:bg-slate-800/40">
              <button
                onClick={onCloseDrilldown}
                className="rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900"
              >
                Close Traceability Proof
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
