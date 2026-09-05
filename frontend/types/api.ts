/* ─── API Response Types ─────────────────────────────────── */

export interface Overview {
  merchants_monitored: number;
  total_merchant_days_analyzed: number;
  total_flagged_events: number;
  elevated_events: number;
  high_events: number;
  test_period: { merchant_days: number; flagged: number; flagged_pct: number };
  enrichment: { vs_overall: number; vs_normal: number };
  anomaly_types: { velocity: number; amount: number; combined: number };
  risk_distribution: { normal: number; elevated: number; high: number };
}

export interface InvestigationEvent {
  merchant: string;
  date: string;
  risk_level: string;
  anomaly_type: string;
  transaction_count: number;
  expected_tx_count: number;
  total_amount: number;
  expected_total_amount: number;
  velocity_deviation: number;
  amount_deviation: number;
  composite_deviation: number;
  fraud_count: number;
  evidence: string[];
}

export interface InvestigationsResponse {
  total: number;
  events: InvestigationEvent[];
}

export interface EvidenceSignal {
  signal: string;
  role: "PRIMARY" | "CONTEXT";
  observed: number;
  expected: number;
  variability: number;
  deviation_mads: number;
}

export interface BaselineInfo {
  historical_days_used: number;
  baseline_window_days: number;
  baseline_status: string;
  day_of_week: number;
}

export interface InvestigationDetail {
  merchant: string;
  date: string;
  risk_level: string;
  anomaly_type: string;
  composite_deviation: number;
  primary_evidence: EvidenceSignal;
  behavioral_context: EvidenceSignal;
  evidence_statements: string[];
  baseline_info: BaselineInfo;
  metadata: {
    fraud_count: number;
  };
}

export interface ConfusionMatrix {
  tp: number;
  fp: number;
  fn: number;
  tn: number;
  unit: string;
  positive_definition: string;
}

export interface ProxyMetrics {
  proxy_precision_pct: number;
  proxy_recall_pct: number;
  proxy_f1_pct: number;
  methodology_note: string;
}

export interface AlertEfficiency {
  total_eligible_merchant_days: number;
  total_alerts: number;
  alert_rate_pct: number;
  proxy_fraud_days_captured: number;
  total_proxy_fraud_days: number;
  proxy_capture_rate_pct: number;
  alerts_per_proxy_positive: number;
}

export interface EvaluationData {
  methodology: {
    detection_unit?: string;
    proxy_ground_truth?: string;
    thresholds?: { elevated: number; high: number };
    [key: string]: unknown;
  };
  primary_results: {
    flagged_vs_normal?: {
      flagged_count: number;
      normal_count: number;
      enrichment_vs_normal: number;
      enrichment_vs_overall: number;
    };
    risk_levels?: Record<string, {
      count: number;
      fraud_days: number;
      fraud_rate: number;
      enrichment: number;
    }>;
    [key: string]: unknown;
  };
  confusion_matrix: ConfusionMatrix;
  proxy_metrics: ProxyMetrics;
  alert_efficiency: AlertEfficiency;
  signal_analysis: unknown;
  baseline_comparison: {
    volume_only?: {
      enrichment_vs_normal: number;
    };
  };
  verdict: string;
  limitations: string[];
}

export interface CostModelScenario {
  name: string;
  review_minutes: number;
  analyst_hourly_cost: number;
  total_alerts: number;
  proxy_true_positives: number;
  estimated_false_positive_alerts: number;
  proxy_precision_pct: number;
  estimated_review_hours: number;
  scenario_based_review_cost: number;
  alerts_per_proxy_positive: number;
}

export interface CostModelPolicyEntry {
  label: string;
  enrichment_vs_normal: number;
  total_alerts: number;
  proxy_true_positives: number;
  estimated_false_positive_alerts: number;
  proxy_precision_pct: number;
  estimated_review_hours: number;
  scenario_based_review_cost: number;
  alerts_per_proxy_positive: number;
  proxy_recall_pct: number;
}

export interface CostModelResponse {
  assumptions: {
    review_minutes: number;
    analyst_hourly_cost: number;
    currency: string;
    policy: string;
    source: string;
    disclaimer: string;
  };
  results: {
    total_alerts: number;
    proxy_true_positives: number;
    estimated_false_positive_alerts: number;
    proxy_precision_pct: number;
    estimated_review_hours: number;
    scenario_based_review_cost: number;
    alerts_per_proxy_positive: number;
    proxy_recall_pct: number;
  };
  scenarios: CostModelScenario[];
  policy_comparison: Record<string, CostModelPolicyEntry>;
}

export interface MerchantRhythm {
  merchant: string;
  total_days: number;
  anomaly_days: number;
  avg_daily_tx: number;
  avg_daily_amount: number;
  timeline: TimelineDay[];
}

export interface TimelineDay {
  date: string;
  total_amount: number;
  expected_total_amount: number;
  transaction_count: number;
  expected_tx_count: number;
  amount_deviation: number;
  velocity_deviation: number;
  anomaly_type: string;
}

/* ─── AI Investigation Intelligence Types (Phase 15) ──── */

export interface EvidenceClaim {
  statement: string;
  evidence_ids: string[];
}

export interface KeyEvidenceExplanation {
  evidence_id: string;
  observation: string;
  why_it_matters: string;
}

export interface InvestigationBriefData {
  headline: string;
  summary: string;
  what_changed: EvidenceClaim[];
  key_evidence: KeyEvidenceExplanation[];
  investigate_next: string[];
  what_remains_unknown: string[];
  safety_note: string;
}

export interface AIBriefResponse {
  status: "available" | "unavailable" | "error";
  cached: boolean;
  generated_at?: string;
  provider?: string;
  model?: string;
  reason?: string;
  brief?: InvestigationBriefData;
}

/* ─── Integration Types (Phase 16) ───────────────────────── */

export interface IntegrationReadiness {
  provider_abstraction: boolean;
  canonical_normalization: boolean;
  payload_validation: boolean;
  idempotency_boundary: boolean;
}

export interface ProviderStatus {
  available?: boolean;
  adapter_ready?: boolean;
  configured?: boolean;
  connected?: boolean;
}

export interface IntegrationStatus {
  current_data_mode: string;
  integration_readiness: IntegrationReadiness;
  providers: Record<string, ProviderStatus>;
}

export interface PipelineStatus {
  payload_validated: boolean;
  canonical_event_created: boolean;
  historical_aggregation: string;
  detection_execution: string;
  ai_analysis: string;
}

export interface CanonicalEvent {
  event_id: string;
  source: string;
  source_event_id: string;
  merchant_id: string;
  merchant_name?: string;
  timestamp: string;
  amount: string;
  currency: string;
  normalized_status: string;
  provider_status?: string;
  payment_method?: string;
  event_type: string;
  source_metadata: Record<string, unknown>;
  received_at: string;
  schema_version: string;
}

export interface DemoIngestionResult {
  event_id?: string;
  status: "accepted" | "duplicate" | "rejected";
  canonical_event?: CanonicalEvent;
  validation_errors: string[];
  pipeline_status: PipelineStatus;
  duplicate_of?: string;
}

/* ─── Application Types ──────────────────────────────────── */

export type Page = "monitor" | "investigations" | "merchant" | "evaluation" | "integration";
