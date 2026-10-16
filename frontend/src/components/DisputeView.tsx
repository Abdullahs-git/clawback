import React, { useState } from 'react';
import { 
  Mail, 
  Download, 
  Check, 
  FileText, 
  Plus, 
  Clock, 
  ShieldCheck, 
  ExternalLink,
  Edit3
} from 'lucide-react';
import { DisputeLetter, InvoiceBatchSummary } from '../types';
import { api } from '../api/client';

interface DisputeViewProps {
  disputes: DisputeLetter[];
  batches: InvoiceBatchSummary[];
  loading: boolean;
  onGenerateDispute: (batchId: string, carrierName: string) => Promise<void>;
  onApproveDispute: (letterId: string) => Promise<void>;
  onRefresh: () => void;
}

export const DisputeView: React.FC<DisputeViewProps> = ({
  disputes,
  batches,
  loading,
  onGenerateDispute,
  onApproveDispute,
  onRefresh
}) => {
  const [selectedLetter, setSelectedLetter] = useState<DisputeLetter | null>(disputes[0] || null);
  const [selectedBatchId, setSelectedBatchId] = useState('');
  const [generating, setGenerating] = useState(false);

  const activeLetter = selectedLetter || disputes[0] || null;

  const handleGenerateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBatchId) {
      alert('Please select an invoice batch to generate a dispute letter for.');
      return;
    }
    const batch = batches.find(b => b.id === selectedBatchId);
    if (!batch) return;

    setGenerating(true);
    try {
      await onGenerateDispute(batch.id, batch.carrier_name);
      setSelectedBatchId('');
    } catch (err: any) {
      alert(`Error generating dispute: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Dispute Generator Bar */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Carrier Dispute Letters & Recovery Packets</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Deterministic evidence packages with itemized contract clauses. Human approval mandatory before export.
            </p>
          </div>

          <form onSubmit={handleGenerateSubmit} className="flex items-center gap-2">
            <select
              value={selectedBatchId}
              onChange={(e) => setSelectedBatchId(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-900 focus:border-emerald-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="">Select Carrier Invoice Batch...</option>
              {batches.map(b => (
                <option key={b.id} value={b.id}>{b.carrier_name} ({b.total_lines} lines)</option>
              ))}
            </select>
            <button
              type="submit"
              disabled={generating}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-bold text-white shadow hover:bg-emerald-500 disabled:opacity-50"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>{generating ? 'Drafting Letter...' : 'Draft Dispute Letter'}</span>
            </button>
          </form>
        </div>
      </div>

      {/* Main Grid: Letter Selector & Letter Preview / Export */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        
        {/* Left Column: Existing Dispute Letters */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Dispute Letters ({disputes.length})
          </h3>

          <div className="space-y-2">
            {disputes.map((l) => {
              const isSelected = activeLetter?.id === l.id;
              const isApproved = l.status === 'approved';

              return (
                <div
                  key={l.id}
                  onClick={() => setSelectedLetter(l)}
                  className={`cursor-pointer rounded-xl border p-4 transition ${
                    isSelected
                      ? 'border-emerald-500 bg-emerald-50/40 shadow-sm dark:border-emerald-500/50 dark:bg-emerald-950/20'
                      : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-sm text-slate-900 dark:text-white">{l.carrier_name}</h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Date: {l.date_generated}
                      </p>
                    </div>
                    <span className="text-sm font-black tabular-nums text-emerald-600 dark:text-emerald-400">
                      ${l.total_claim_amount}
                    </span>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">{l.total_disputed_items} disputed lines</span>
                    <span className={`rounded-full px-2 py-0.5 font-bold uppercase text-[10px] ${
                      isApproved 
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                        : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                    }`}>
                      {l.status}
                    </span>
                  </div>
                </div>
              );
            })}

            {disputes.length === 0 && (
              <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-xs text-slate-500 dark:border-slate-800">
                No dispute letters drafted yet. Select an invoice batch above to draft your first letter.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Dispute Letter Preview & Export */}
        <div className="lg:col-span-2 space-y-4">
          {activeLetter ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 space-y-5">
              
              {/* Header and Approval Actions */}
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">
                      Dispute Claim for {activeLetter.carrier_name}
                    </h3>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                      activeLetter.status === 'approved' 
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                        : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                    }`}>
                      {activeLetter.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Total Claim: <strong className="font-bold text-emerald-600 dark:text-emerald-400">${activeLetter.total_claim_amount} USD</strong> ({activeLetter.total_disputed_items} items)
                  </p>
                </div>

                {/* Export & Approval Buttons */}
                <div className="flex items-center gap-2">
                  {activeLetter.status !== 'approved' && (
                    <button
                      onClick={() => onApproveDispute(activeLetter.id)}
                      className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-bold text-white shadow hover:bg-emerald-500"
                    >
                      <Check className="h-3.5 w-3.5" />
                      <span>Approve Letter</span>
                    </button>
                  )}

                  <a
                    href={api.getExportUrl(activeLetter.id, 'pdf')}
                    download
                    className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  >
                    <Download className="h-3.5 w-3.5 text-rose-500" />
                    <span>Download PDF</span>
                  </a>

                  <a
                    href={api.getExportUrl(activeLetter.id, 'markdown')}
                    download
                    className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  >
                    <Download className="h-3.5 w-3.5 text-blue-500" />
                    <span>Markdown</span>
                  </a>
                </div>
              </div>

              {/* Letter Markdown Body Display */}
              <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-5 font-mono text-xs text-slate-800 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
                {activeLetter.body_markdown}
              </div>

              {/* Schedule A Evidence Table */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                  Schedule A: Itemized Evidence ({activeLetter.evidence_table?.length || 0} entries)
                </h4>

                <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 font-semibold text-slate-600 dark:bg-slate-800/50 dark:text-slate-400">
                      <tr>
                        <th className="px-4 py-2.5">Shipment ID</th>
                        <th className="px-4 py-2.5">Inv #</th>
                        <th className="px-4 py-2.5">Code</th>
                        <th className="px-4 py-2.5">Contract Citation</th>
                        <th className="px-4 py-2.5 text-right">Billed</th>
                        <th className="px-4 py-2.5 text-right">Expected</th>
                        <th className="px-4 py-2.5 text-right font-bold">Claim</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-sans dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                      {activeLetter.evidence_table?.slice(0, 15).map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                          <td className="px-4 py-2 font-mono font-medium">{row.shipment_id}</td>
                          <td className="px-4 py-2 font-mono text-slate-500">{row.invoice_number}</td>
                          <td className="px-4 py-2 font-mono font-bold text-slate-800 dark:text-slate-200">{row.charge_code}</td>
                          <td className="px-4 py-2 italic text-slate-500 max-w-[220px] truncate" title={row.contract_clause_reference}>
                            p.{row.contract_page}: "{row.contract_clause_reference}"
                          </td>
                          <td className="px-4 py-2 text-right tabular-nums">${row.billed_amount}</td>
                          <td className="px-4 py-2 text-right tabular-nums">${row.expected_amount}</td>
                          <td className="px-4 py-2 text-right tabular-nums font-bold text-emerald-600 dark:text-emerald-400">
                            ${row.claim_amount}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center text-slate-500 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              Select or draft a dispute letter on the left to preview evidence and export.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
