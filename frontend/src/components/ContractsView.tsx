import React, { useState } from 'react';
import { 
  FileText, 
  Upload, 
  Check, 
  X, 
  ShieldAlert, 
  ShieldCheck, 
  Search, 
  Plus, 
  Edit3, 
  CheckCircle2, 
  AlertCircle
} from 'lucide-react';
import { ContractSummary, ContractDetail, ContractRule } from '../types';

interface ContractsViewProps {
  contracts: ContractSummary[];
  selectedContract: ContractDetail | null;
  loading: boolean;
  onSelectContract: (id: string) => void;
  onUploadContract: (file: File, carrierName: string) => Promise<void>;
  onUpdateRuleStatus: (contractId: string, ruleId: string, status: 'approved' | 'rejected') => Promise<void>;
  onBatchApprove: (contractId: string, ruleIds: string[]) => Promise<void>;
}

export const ContractsView: React.FC<ContractsViewProps> = ({
  contracts,
  selectedContract,
  loading,
  onSelectContract,
  onUploadContract,
  onUpdateRuleStatus,
  onBatchApprove
}) => {
  const [carrierInput, setCarrierInput] = useState('');
  const [uploading, setUploading] = useState(false);
  const [filterType, setFilterType] = useState('all');

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setUploading(true);
    try {
      await onUploadContract(file, carrierInput);
      setCarrierInput('');
    } catch (err: any) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const rules = selectedContract?.rules || [];
  const filteredRules = filterType === 'all' 
    ? rules 
    : rules.filter(r => r.status === filterType);

  const pendingProposed = rules.filter(r => r.status === 'proposed');

  return (
    <div className="space-y-6">
      {/* Top Header & Upload Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Carrier Contracts & Commercial Rules</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Rules extracted by Gemma with mandatory verbatim quote verification safeguard.
          </p>
        </div>

        {/* Upload Form */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Carrier Name (optional)"
            value={carrierInput}
            onChange={(e) => setCarrierInput(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          />
          <label className="flex cursor-pointer items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow transition hover:bg-emerald-500">
            <Upload className="h-3.5 w-3.5" />
            <span>{uploading ? 'Extracting with Gemma...' : 'Upload Contract PDF'}</span>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Main Grid: Contracts List & Rules Panel */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        
        {/* Left Column: Contracts Selector */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Uploaded Agreements ({contracts.length})
          </h3>

          <div className="space-y-2">
            {contracts.map((c) => {
              const isSelected = selectedContract?.id === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => onSelectContract(c.id)}
                  className={`cursor-pointer rounded-xl border p-4 transition ${
                    isSelected
                      ? 'border-emerald-500 bg-emerald-50/40 shadow-sm dark:border-emerald-500/50 dark:bg-emerald-950/20'
                      : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-sm text-slate-900 dark:text-white">{c.carrier_name}</h4>
                      <p className="text-xs font-mono text-slate-500 dark:text-slate-400">{c.filename}</p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                      {c.approved_rule_count}/{c.rule_count} approved
                    </span>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Uploaded: {new Date(c.uploaded_at).toLocaleDateString()}</span>
                  </div>
                </div>
              );
            })}

            {contracts.length === 0 && (
              <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-xs text-slate-500 dark:border-slate-800">
                No contracts uploaded yet. Upload a carrier contract PDF above.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Rules Review & Verification */}
        <div className="lg:col-span-2 space-y-4">
          {selectedContract ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              
              {/* Header and Batch Action */}
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    {selectedContract.carrier_name} — Commercial Rules
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {selectedContract.contract_reference || 'Master Agreement'} | Effective: {selectedContract.effective_date || '2026-01-01'}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  {pendingProposed.length > 0 && (
                    <button
                      onClick={() => onBatchApprove(selectedContract.id, pendingProposed.map(r => r.id))}
                      className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-bold text-white shadow hover:bg-emerald-500"
                    >
                      <Check className="h-3.5 w-3.5" />
                      <span>Approve All Proposed ({pendingProposed.length})</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Status Filter Tabs */}
              <div className="flex gap-2 pt-3">
                {['all', 'proposed', 'approved', 'rejected'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setFilterType(st)}
                    className={`rounded-md px-2.5 py-1 text-xs font-semibold capitalize ${
                      filterType === st
                        ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>

              {/* Rules List */}
              <div className="mt-4 space-y-3">
                {filteredRules.map((rule) => {
                  const isRejected = rule.status === 'rejected';
                  const isApproved = rule.status === 'approved';
                  const isProposed = rule.status === 'proposed';

                  return (
                    <div
                      key={rule.id}
                      className={`rounded-xl border p-4 transition ${
                        isRejected
                          ? 'border-rose-200 bg-rose-50/20 dark:border-rose-900/40 dark:bg-rose-950/10'
                          : isApproved
                          ? 'border-emerald-200 bg-emerald-50/20 dark:border-emerald-900/40 dark:bg-emerald-950/10'
                          : 'border-slate-200 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-800/20'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-slate-800 dark:text-slate-200">
                            {rule.id}
                          </span>
                          <span className="rounded bg-slate-200/80 px-2 py-0.5 font-mono text-[10px] font-bold uppercase text-slate-700 dark:bg-slate-700 dark:text-slate-300">
                            {rule.type}
                          </span>
                          <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                            (Page {rule.source_page})
                          </span>
                        </div>

                        {/* Status Badge */}
                        <div className="flex items-center gap-1.5">
                          {isApproved && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                              <CheckCircle2 className="h-3 w-3" /> Approved
                            </span>
                          )}
                          {isRejected && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 text-xs font-bold text-rose-800 dark:bg-rose-950 dark:text-rose-300">
                              <AlertCircle className="h-3 w-3" /> Rejected
                            </span>
                          )}
                          {isProposed && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                              Proposed (Review Needed)
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Rule Description & Parameters */}
                      <p className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">
                        {rule.description}
                      </p>
                      
                      <div className="mt-1 flex flex-wrap gap-2 text-xs font-mono text-slate-600 dark:text-slate-400">
                        {Object.entries(rule.parameters).map(([k, v]) => (
                          <span key={k} className="rounded bg-white/80 px-1.5 py-0.5 border border-slate-200 dark:bg-slate-800 dark:border-slate-700">
                            {k}: <strong>{String(v)}</strong>
                          </span>
                        ))}
                      </div>

                      {/* Verbatim Contract Quote Citation */}
                      <div className="mt-3 rounded-lg border border-slate-200/80 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
                        <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                          Verbatim Contract Clause (Page {rule.source_page}):
                        </p>
                        <blockquote className="mt-1 text-xs italic text-slate-700 dark:text-slate-300 border-l-2 border-emerald-500 pl-2">
                          "{rule.source_quote}"
                        </blockquote>
                      </div>

                      {/* Rejection notice if unverified quote */}
                      {rule.rejection_reason && (
                        <p className="mt-2 text-xs text-rose-600 dark:text-rose-400 font-medium">
                          Safeguard Notice: {rule.rejection_reason}
                        </p>
                      )}

                      {/* Approval Actions */}
                      <div className="mt-3 flex items-center justify-end gap-2 border-t border-slate-200/40 pt-2 dark:border-slate-800/40">
                        {rule.status !== 'approved' && (
                          <button
                            onClick={() => onUpdateRuleStatus(selectedContract.id, rule.id, 'approved')}
                            className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-950/60 dark:text-emerald-400"
                          >
                            <Check className="h-3 w-3" /> Approve Rule
                          </button>
                        )}
                        {rule.status !== 'rejected' && (
                          <button
                            onClick={() => onUpdateRuleStatus(selectedContract.id, rule.id, 'rejected')}
                            className="inline-flex items-center gap-1 rounded-md bg-rose-50 px-2.5 py-1 text-xs font-bold text-rose-700 hover:bg-rose-100 dark:bg-rose-950/60 dark:text-rose-400"
                          >
                            <X className="h-3 w-3" /> Reject Rule
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center text-slate-500 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              Select a contract on the left to inspect its extracted rules and verbatim clause citations.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
