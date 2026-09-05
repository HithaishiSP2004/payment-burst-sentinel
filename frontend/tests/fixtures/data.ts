import type { Overview, InvestigationsResponse, InvestigationEvent, EvaluationData, MerchantRhythm, TimelineDay } from "@/types/api";

/* ─── Overview ───────────────────────────────────────────── */

export const mockOverview: Overview = {
  merchants_monitored: 693,
  total_merchant_days_analyzed: 337151,
  total_flagged_events: 42665,
  elevated_events: 12825,
  high_events: 29840,
  test_period: { merchant_days: 126574, flagged: 7123, flagged_pct: 5.63 },
  enrichment: { vs_overall: 4.01, vs_normal: 7.13 },
  anomaly_types: { velocity: 4520, amount: 24319, combined: 13826 },
  risk_distribution: { normal: 294486, elevated: 12825, high: 29840 },
};

/* ─── Investigation Events ───────────────────────────────── */

export const mockHighAmountEvent: InvestigationEvent = {
  merchant: "Kovacek Ltd",
  date: "2020-12-27",
  risk_level: "high",
  anomaly_type: "amount_anomaly",
  transaction_count: 5,
  expected_tx_count: 2,
  total_amount: 19364.91,
  expected_total_amount: 10.75,
  velocity_deviation: 0.8,
  amount_deviation: 1935.4,
  composite_deviation: 1935.4,
  fraud_count: 0,
  evidence: ["Amount deviation: +1935.4 MADs"],
};

export const mockElevatedCombinedEvent: InvestigationEvent = {
  merchant: "Test Merchant B",
  date: "2020-11-15",
  risk_level: "elevated",
  anomaly_type: "combined_anomaly",
  transaction_count: 8,
  expected_tx_count: 2,
  total_amount: 5000,
  expected_total_amount: 500,
  velocity_deviation: 4.2,
  amount_deviation: 6.8,
  composite_deviation: 8.0,
  fraud_count: 1,
  evidence: [],
};

export const mockHighVolumeEvent: InvestigationEvent = {
  merchant: "Volume Corp",
  date: "2020-10-01",
  risk_level: "high",
  anomaly_type: "velocity_anomaly",
  transaction_count: 50,
  expected_tx_count: 5,
  total_amount: 200,
  expected_total_amount: 180,
  velocity_deviation: 12.5,
  amount_deviation: 0.3,
  composite_deviation: 12.5,
  fraud_count: 0,
  evidence: [],
};

export const mockInvestigations: InvestigationsResponse = {
  total: 3,
  events: [mockHighAmountEvent, mockElevatedCombinedEvent, mockHighVolumeEvent],
};

export const mockEmptyInvestigations: InvestigationsResponse = {
  total: 0,
  events: [],
};

/* ─── Merchant Rhythm ────────────────────────────────────── */

const makeDay = (date: string, amount: number, expected: number, anomaly: string): TimelineDay => ({
  date,
  total_amount: amount,
  expected_total_amount: expected,
  transaction_count: 3,
  expected_tx_count: 2,
  amount_deviation: anomaly !== "normal" && anomaly !== "not_scored" ? 5.2 : 0,
  velocity_deviation: 0.5,
  anomaly_type: anomaly,
});

export const mockMerchantRhythm: MerchantRhythm = {
  merchant: "Kovacek Ltd",
  total_days: 90,
  anomaly_days: 18,
  avg_daily_tx: 2.3,
  avg_daily_amount: 45.5,
  timeline: [
    makeDay("2020-10-01", 50, 45, "normal"),
    makeDay("2020-10-02", 200, 45, "amount_anomaly"),
    makeDay("2020-10-03", 40, 45, "normal"),
    makeDay("2020-10-04", 60, 45, "not_scored"),
    makeDay("2020-10-05", 300, 45, "combined_anomaly"),
  ],
};

export const mockMerchantNoDeviations: MerchantRhythm = {
  merchant: "Clean Corp",
  total_days: 60,
  anomaly_days: 0,
  avg_daily_tx: 5,
  avg_daily_amount: 100,
  timeline: [
    makeDay("2020-10-01", 100, 95, "normal"),
    makeDay("2020-10-02", 110, 95, "normal"),
  ],
};

/* ─── Evaluation ─────────────────────────────────────────── */

export const mockEvaluation: EvaluationData = {
  methodology: {
    detection_unit: "merchant-day",
    proxy_ground_truth: "Merchant-day containing at least one fraud-tagged transaction",
    thresholds: { elevated: 4, high: 5 },
  },
  primary_results: {
    flagged_vs_normal: {
      flagged_count: 7123,
      normal_count: 119451,
      enrichment_vs_normal: 7.13,
      enrichment_vs_overall: 4.01,
    },
    risk_levels: {
      normal: { count: 119451, fraud_days: 1038, fraud_rate: 0.932, enrichment: 0.56 },
      elevated: { count: 4977, fraud_days: 152, fraud_rate: 3.054, enrichment: 1.84 },
      high: { count: 11113, fraud_days: 917, fraud_rate: 8.252, enrichment: 4.98 },
    },
  },
  confusion_matrix: {
    tp: 1069,
    fp: 15021,
    fn: 1030,
    tn: 109454,
    unit: "merchant-day",
    positive_definition: "Merchant-day with fraud_count > 0",
  },
  proxy_metrics: {
    proxy_precision_pct: 6.64,
    proxy_recall_pct: 50.93,
    proxy_f1_pct: 11.75,
    methodology_note: "These metrics use fraud-containing merchant-days as proxy ground truth.",
  },
  alert_efficiency: {
    total_eligible_merchant_days: 126574,
    total_alerts: 16090,
    alert_rate_pct: 12.71,
    proxy_fraud_days_captured: 1069,
    total_proxy_fraud_days: 2099,
    proxy_capture_rate_pct: 50.93,
    alerts_per_proxy_positive: 15.05,
  },
  signal_analysis: {},
  baseline_comparison: {
    volume_only: { enrichment_vs_normal: 1.83 },
  },
  verdict: "meaningful_enrichment",
  limitations: [
    "Behavioral anomaly ≠ fraud — the system detects behavioral deviation, not fraud",
    "Merchant-day is the detection unit; proxy ground truth is fraud-containing merchant-day",
    "Daily resolution only — sub-daily patterns not detected",
  ],
};

/* ─── Investigation Detail ────────────────────────────────── */

export const mockInvestigationDetail = {
  merchant: "Kovacek Ltd",
  date: "2020-11-27",
  risk_level: "high",
  anomaly_type: "amount_anomaly",
  composite_deviation: 396.48,
  primary_evidence: {
    signal: "Payment Value Deviation",
    role: "PRIMARY" as const,
    observed: 3998.66,
    expected: 10.75,
    variability: 10.06,
    deviation_mads: 396.48,
  },
  behavioral_context: {
    signal: "Transaction Volume Shift",
    role: "CONTEXT" as const,
    observed: 3,
    expected: 2.0,
    variability: 1.0,
    deviation_mads: 1.0,
  },
  evidence_statements: [
    "Total payment value ($3998.66) was significantly above the expected range (expected ~$10.75, variability ±$10.06).",
    "Daily transaction count (3) was above expected (~2).",
    "This system identifies unusual behavior. Investigation is required to determine the cause.",
  ],
  baseline_info: {
    historical_days_used: 90,
    baseline_window_days: 90,
    baseline_status: "sufficient_history",
    day_of_week: 5,
  },
  metadata: {
    fraud_count: 0,
  },
};


