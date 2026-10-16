import React, { useState, useEffect } from 'react';
import { 
  FileSpreadsheet, 
  Upload, 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  CheckCircle2, 
  Layers,
  ArrowRight
} from 'lucide-react';
import { InvoiceBatchSummary, InvoiceLineItem } from '../types';
import { api } from '../api/client';

interface InvoicesViewProps {
  batches: InvoiceBatchSummary[];
  loading: boolean;
  onUploadInvoices: (file: File, carrierName: string) => Promise<void>;
  onTriggerAudit: (batchId: string) => void;
}

export const InvoicesView: React.FC<InvoicesViewProps> = ({
  batches,
  loading,
  onUploadInvoices,
  onTriggerAudit
}) => {
  const [selectedBatch, setSelectedBatch] = useState<InvoiceBatchSummary | null>(batches[0] || null);
  const [carrierInput, setCarrierInput] = useState('');
  const [uploading, setUploading] = useState(false);
  const [lines, setLines] = useState<InvoiceLineItem[]>([]);
  const [page, setPage] = useState(1);
  const [totalLines, setTotalLines] = useState(0);
  const [loadingLines, setLoadingLines] = useState(false);

  const activeBatch = selectedBatch || batches[0] || null;

  useEffect(() => {
    if (activeBatch) {
      loadLines(activeBatch.id, page);
    }
  }, [activeBatch, page]);

  const loadLines = async (batchId: string, pageNum: number) => {
    setLoadingLines(true);
    try {
      const res = await api.getBatchLines(batchId, pageNum, 25);
      setLines(res.items);
      setTotalLines(res.total);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoadingLines(false);
    }
  };

  const handleUploadSubmit = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setUploading(true);
    try {
      await onUploadInvoices(file, carrierInput);
      setCarrierInput('');
    } catch (err: any) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Upload Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Carrier Invoice Batches</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Ingests raw CSV or PDF invoices into normalized line items ready for mathematical audit.
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
            <span>{uploading ? 'Ingesting Invoices...' : 'Upload Invoices CSV'}</span>
            <input
              type="file"
              accept=".csv,.pdf"
              onChange={handleUploadSubmit}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Main Grid: Batches & Lines Table */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        
        {/* Left Column: Batches List */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Invoice Batches ({batches.length})
          </h3>

          <div className="space-y-2">
            {batches.map((b) => {
              const isSelected = activeBatch?.id === b.id;

              return (
                <div
                  key={b.id}
                  onClick={() => {
                    setSelectedBatch(b);
                    setPage(1);
                  }}
                  className={`cursor-pointer rounded-xl border p-4 transition ${
                    isSelected
                      ? 'border-emerald-500 bg-emerald-50/40 shadow-sm dark:border-emerald-500/50 dark:bg-emerald-950/20'
                      : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-sm text-slate-900 dark:text-white">{b.carrier_name}</h4>
                      <p className="text-xs font-mono text-slate-500 dark:text-slate-400">{b.filename}</p>
                    </div>
                    <span className="text-sm font-bold tabular-nums text-slate-900 dark:text-white">
                      ${b.total_billed_amount}
                    </span>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
                    <span>{b.total_lines} line items</span>
                    <span>{new Date(b.uploaded_at).toLocaleDateString()}</span>
                  </div>
                </div>
              );
            })}

            {batches.length === 0 && (
              <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-xs text-slate-500 dark:border-slate-800">
                No invoice batches uploaded yet.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Line Items Table */}
        <div className="lg:col-span-2 space-y-4">
          {activeBatch ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 space-y-4">
              
              {/* Batch Header */}
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    {activeBatch.carrier_name} — Invoiced Line Items
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {activeBatch.total_lines} lines | Total Billed: <strong className="font-mono">${activeBatch.total_billed_amount}</strong>
                  </p>
                </div>

                <button
                  onClick={() => onTriggerAudit(activeBatch.id)}
                  className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-bold text-white shadow hover:bg-emerald-500"
                >
                  <span>Audit this Batch</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </div>

              {/* Table */}
              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 font-semibold text-slate-600 dark:bg-slate-800/50 dark:text-slate-400">
                    <tr>
                      <th className="px-4 py-2.5">Line ID</th>
                      <th className="px-4 py-2.5">Shipment ID</th>
                      <th className="px-4 py-2.5">Inv #</th>
                      <th className="px-4 py-2.5">Code</th>
                      <th className="px-4 py-2.5">Service</th>
                      <th className="px-4 py-2.5 text-right">Published</th>
                      <th className="px-4 py-2.5 text-right">Billed Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-sans dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                    {lines.map((l) => (
                      <tr key={l.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                        <td className="px-4 py-2 font-mono text-slate-500">{l.line_id}</td>
                        <td className="px-4 py-2 font-mono font-medium text-slate-900 dark:text-white">{l.shipment_id}</td>
                        <td className="px-4 py-2 font-mono text-slate-500">{l.invoice_number}</td>
                        <td className="px-4 py-2">
                          <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                            {l.charge_code}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-slate-500">{l.service_level || 'Standard'}</td>
                        <td className="px-4 py-2 text-right tabular-nums text-slate-500">
                          {l.published_rate ? `$${l.published_rate}` : '-'}
                        </td>
                        <td className="px-4 py-2 text-right font-bold tabular-nums text-slate-900 dark:text-white">
                          ${l.amount_billed}
                        </td>
                      </tr>
                    ))}

                    {lines.length === 0 && (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                          {loadingLines ? 'Loading line items...' : 'No lines in this batch.'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between text-xs text-slate-500 pt-2">
                <span>
                  Showing {Math.min((page - 1) * 25 + 1, totalLines)} - {Math.min(page * 25, totalLines)} of {totalLines}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="rounded p-1 border hover:bg-slate-100 disabled:opacity-40"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setPage(p => p + 1)}
                    disabled={page * 25 >= totalLines}
                    className="rounded p-1 border hover:bg-slate-100 disabled:opacity-40"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center text-slate-500 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              Select an invoice batch on the left to view parsed line items.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
