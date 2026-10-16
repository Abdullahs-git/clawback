export type RuleStatus = 'proposed' | 'approved' | 'rejected';
export type DisputeStatus = 'draft' | 'approved' | 'exported';

export interface ContractRule {
  id: string;
  contract_id: string;
  type: string;
  description: string;
  parameters: Record<string, any>;
  source_page: number;
  source_quote: string;
  confidence: number;
  status: RuleStatus;
  rejection_reason?: string | null;
  created_at?: string;
}

export interface ContractSummary {
  id: string;
  carrier_name: string;
  filename: string;
  uploaded_at: string;
  rule_count: number;
  approved_rule_count: number;
}

export interface ContractDetail {
  id: string;
  carrier_name: string;
  filename: string;
  contract_reference?: string | null;
  effective_date?: string | null;
  expiration_date?: string | null;
  uploaded_at: string;
  rules: ContractRule[];
}

export interface InvoiceLineItem {
  id: string;
  line_id: string;
  batch_id: string;
  invoice_number: string;
  invoice_date: string;
  shipment_id: string;
  charge_code: string;
  charge_description?: string | null;
  service_level?: string | null;
  published_rate?: string | null;
  discount_applied_percent?: string | null;
  fuel_surcharge_percent?: string | null;
  amount_billed: string;
}

export interface InvoiceBatchSummary {
  id: string;
  carrier_name: string;
  filename: string;
  uploaded_at: string;
  total_lines: number;
  total_billed_amount: string;
}

export interface AuditFinding {
  finding_id: string;
  batch_id: string;
  contract_id: string;
  carrier_name: string;
  invoice_number: string;
  invoice_date: string;
  line_id: string;
  shipment_id: string;
  charge_code: string;
  rule_id: string;
  rule_type: string;
  rule_description: string;
  contract_page: number;
  contract_clause_quote: string;
  expected_amount: string;
  billed_amount: string;
  overcharge_amount: string;
  calculation_math: string;
  claim_deadline_date?: string | null;
  days_remaining_to_claim?: number | null;
  status: string;
  created_at: string;
}

export interface AuditOverview {
  total_overcharge: string;
  total_findings_count: number;
  by_category: Record<string, string>;
  by_carrier: Record<string, string>;
  findings: AuditFinding[];
}

export interface DisputeLetter {
  id: string;
  batch_id: string;
  carrier_name: string;
  carrier_contact_email?: string | null;
  shipper_name: string;
  shipper_contact_name?: string | null;
  shipper_contact_email?: string | null;
  date_generated: string;
  earliest_deadline_date?: string | null;
  total_claim_amount: string;
  total_disputed_items: number;
  subject_line: string;
  body_markdown: string;
  evidence_table: Array<{
    finding_id: string;
    shipment_id: string;
    invoice_number: string;
    charge_code: string;
    contract_page: number;
    contract_clause_reference: string;
    billed_amount: string;
    expected_amount: string;
    claim_amount: string;
    explanation: string;
  }>;
  status: DisputeStatus;
  approved_by?: string | null;
  approved_at?: string | null;
  created_at: string;
}

export interface AmdRecentCall {
  call_id: string;
  timestamp: string;
  operation: string;
  latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  tokens_per_second: number;
  mode: 'live' | 'replay';
  status: string;
}

export interface AmdPanelMetrics {
  model_name: string;
  endpoint_host: string;
  mode: 'live' | 'replay';
  is_connected: boolean;
  total_calls: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  average_latency_ms: number;
  average_tokens_per_second: number;
  recent_calls: AmdRecentCall[];
}
