import {
  ContractSummary,
  ContractDetail,
  ContractRule,
  InvoiceBatchSummary,
  InvoiceLineItem,
  AuditOverview,
  AuditFinding,
  DisputeLetter,
  AmdPanelMetrics
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}: ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export const api = {
  // AMD Telemetry
  getAmdStatus: async (): Promise<AmdPanelMetrics> => {
    const res = await fetch(`${API_BASE}/api/amd-status`);
    return handleResponse<AmdPanelMetrics>(res);
  },

  // Contracts & Rules
  getContracts: async (): Promise<ContractSummary[]> => {
    const res = await fetch(`${API_BASE}/api/contracts`);
    return handleResponse<ContractSummary[]>(res);
  },

  getContractDetail: async (contractId: string): Promise<ContractDetail> => {
    const res = await fetch(`${API_BASE}/api/contracts/${contractId}`);
    return handleResponse<ContractDetail>(res);
  },

  uploadContract: async (file: File, carrierName?: string): Promise<ContractDetail> => {
    const formData = new FormData();
    formData.append('file', file);
    if (carrierName) formData.append('carrier_name', carrierName);

    const res = await fetch(`${API_BASE}/api/contracts/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<ContractDetail>(res);
  },

  updateRule: async (contractId: string, ruleId: string, patch: Partial<ContractRule>): Promise<ContractRule> => {
    const res = await fetch(`${API_BASE}/api/contracts/${contractId}/rules/${ruleId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    });
    return handleResponse<ContractRule>(res);
  },

  batchUpdateRules: async (contractId: string, action: 'approve' | 'reject', ruleIds: string[]): Promise<{ updated_count: number }> => {
    const res = await fetch(`${API_BASE}/api/contracts/${contractId}/rules/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, rule_ids: ruleIds }),
    });
    return handleResponse<{ updated_count: number }>(res);
  },

  // Invoices
  getInvoiceBatches: async (): Promise<InvoiceBatchSummary[]> => {
    const res = await fetch(`${API_BASE}/api/invoices`);
    return handleResponse<InvoiceBatchSummary[]>(res);
  },

  getBatchLines: async (batchId: string, page = 1, limit = 50): Promise<{ items: InvoiceLineItem[]; total: number }> => {
    const res = await fetch(`${API_BASE}/api/invoices/${batchId}/lines?page=${page}&limit=${limit}`);
    return handleResponse<{ items: InvoiceLineItem[]; total: number }>(res);
  },

  uploadInvoices: async (file: File, carrierName?: string): Promise<InvoiceBatchSummary> => {
    const formData = new FormData();
    formData.append('file', file);
    if (carrierName) formData.append('carrier_name', carrierName);

    const res = await fetch(`${API_BASE}/api/invoices/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<InvoiceBatchSummary>(res);
  },

  // Deterministic Audit
  runAudit: async (batchId: string, contractId: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/api/audit/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_id: batchId, contract_id: contractId }),
    });
    return handleResponse<any>(res);
  },

  getFindings: async (filters?: { batchId?: string; carrierName?: string; ruleType?: string }): Promise<AuditOverview> => {
    const params = new URLSearchParams();
    if (filters?.batchId) params.append('batch_id', filters.batchId);
    if (filters?.carrierName) params.append('carrier_name', filters.carrierName);
    if (filters?.ruleType) params.append('rule_type', filters.ruleType);

    const res = await fetch(`${API_BASE}/api/audit/findings?${params.toString()}`);
    return handleResponse<AuditOverview>(res);
  },

  getFindingDetail: async (findingId: string): Promise<AuditFinding> => {
    const res = await fetch(`${API_BASE}/api/audit/findings/${findingId}`);
    return handleResponse<AuditFinding>(res);
  },

  // Disputes
  generateDispute: async (batchId: string, carrierName: string, shipperName?: string): Promise<DisputeLetter> => {
    const res = await fetch(`${API_BASE}/api/disputes/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        batch_id: batchId,
        carrier_name: carrierName,
        shipper_name: shipperName || 'Acme Shipper Operations',
      }),
    });
    return handleResponse<DisputeLetter>(res);
  },

  getDisputes: async (): Promise<DisputeLetter[]> => {
    const res = await fetch(`${API_BASE}/api/disputes`);
    return handleResponse<DisputeLetter[]>(res);
  },

  updateDispute: async (letterId: string, patch: Partial<DisputeLetter>): Promise<DisputeLetter> => {
    const res = await fetch(`${API_BASE}/api/disputes/${letterId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    });
    return handleResponse<DisputeLetter>(res);
  },

  getExportUrl: (letterId: string, format: 'markdown' | 'pdf'): string => {
    return `${API_BASE}/api/disputes/${letterId}/export?format=${format}`;
  }
};
