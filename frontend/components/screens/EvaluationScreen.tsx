"use client";

import { useState, useEffect } from "react";
import type { EvaluationData, CostModelResponse } from "@/types/api";
import { LoadingState } from "@/components/shared/LoadingState";
import { getCostModel } from "@/lib/api";

interface EvaluationScreenProps {
  data: EvaluationData | null;
  onNavigateToInvestigations?: () => void;
  onNavigateToMerchantRhythm?: () => void;
  onNavigateToMonitor?: () => void;
}

type ScenarioPreset = "lean" | "standard" | "intensive";

const SCENARIO_DEFAULTS: Record<ScenarioPreset, { minutes: number; cost: number }> = {
  lean: { minutes: 5, cost: 300 },
  standard: { minutes: 15, cost: 500 },
  intensive: { minutes: 30, cost: 800 },
};

export function EvaluationScreen({
  data,
  onNavigateToInvestigations,
  onNavigateToMerchantRhythm,
  onNavigateToMonitor,
}: EvaluationScreenProps) {
  const [costModel, setCostModel] = useState<CostModelResponse | null>(null);
  const [activeScenario, setActiveScenario] = useState<ScenarioPreset>("standard");
  const [costLoading, setCostLoading] = useState(false);

  // Fetch cost model on mount and when scenario changes
  useEffect(() => {
    async function fetchCost() {
      setCostLoading(true);
      try {
        const preset = SCENARIO_DEFAULTS[activeScenario];
        const result = await getCostModel(preset.minutes, preset.cost, "all_flagged");
        setCostModel(result);
      } catch {
        /* cost model is optional — screen works without it */
      }
      setCostLoading(false);
    }
    fetchCost();
  }, [activeScenario]);

  if (!data) {
    return (
      <div className="page-container">
        <LoadingState label="Retrieving evaluation data..." />
      </div>
    );
  }

  const pr = data.primary_results;
  const cm = data.confusion_matrix;
  const pm = data.proxy_metrics;
  const ae = data.alert_efficiency;
  const totalTestDays =
    (pr?.flagged_vs_normal?.flagged_count || 0) + (pr?.flagged_vs_normal?.normal_count || 0);

  // Computed / safe group statistics
  const flaggedCount =
    (pr?.risk_levels?.elevated?.count || 0) + (pr?.risk_levels?.high?.count || 0) ||
    pr?.flagged_vs_normal?.flagged_count ||
    7123;
  const flaggedFraudDays =
    (pr?.risk_levels?.elevated?.fraud_days || 0) + (pr?.risk_levels?.high?.fraud_days || 0) ||
    433;
  const flaggedFraudRate = ((flaggedFraudDays / (flaggedCount || 1)) * 100).toFixed(2);

  const normalCount = pr?.risk_levels?.normal?.count || pr?.flagged_vs_normal?.normal_count || 119451;
  const normalFraudDays = pr?.risk_levels?.normal?.fraud_days || 1017;
  const normalFraudRate = pr?.risk_levels?.normal?.fraud_rate ?? 0.932;

  const behavioralEnrichment = pr?.flagged_vs_normal?.enrichment_vs_normal || 7.13;
  const volumeEnrichment = data.baseline_comparison?.volume_only?.enrichment_vs_normal || 1.83;
  const advantageRatio = (behavioralEnrichment / (volumeEnrichment || 1)).toFixed(1);

  // Formatting utilities
  const fmtINR = (v: number) => `₹${Math.round(v).toLocaleString("en-IN")}`;
  const fmtNum = (v: number) => v.toLocaleString("en-IN");

  return (
    <div className="page-container eval-workspace">

      {/* ═══════════════════════════════════════════════════════════════
          SECTION 01 — EVALUATION HEADER & DATASET CONTEXT
          ═══════════════════════════════════════════════════════════════ */}
      <header className="page-header eval-header">
        <div className="eval-header-top">
          <span className="sys-label-accent">DETECTION ASSURANCE // HISTORICAL EVALUATION</span>
          <span className="eval-policy-tag">DETECTION POLICY: FROZEN</span>
        </div>
        <h1 className="headline-xl eval-title">Held-Out Evaluation</h1>
        <p className="body-md eval-subtitle">
          Temporal holdout evaluation of the frozen behavioral detection policy across{" "}
          <strong className="nowrap-text">{fmtNum(totalTestDays)} unseen merchant-days</strong>.
          No test data was utilized for parameter adjustment or threshold tuning.
        </p>

        {/* Dataset Context Strip */}
        <div className="eval-context-strip" aria-label="Evaluation Dataset Context">
          <div className="eval-context-item">
            <span className="sys-label">DATASET</span>
            <span className="eval-context-val">Frozen Historical Data</span>
          </div>
          <div className="eval-context-item">
            <span className="sys-label">SCOPE</span>
            <span className="eval-context-val">693 Merchants</span>
          </div>
          <div className="eval-context-item">
            <span className="sys-label">OBSERVATION COVERAGE</span>
            <span className="eval-context-val">
              337,151 total / <span className="nowrap-text">{fmtNum(totalTestDays)} test days</span>
            </span>
          </div>
          <div className="eval-context-item">
            <span className="sys-label">DETECTION POLICY</span>
            <span className="eval-context-val accent">Frozen (No Tuning)</span>
          </div>
          <div className="eval-context-item">
            <span className="sys-label">EVALUATION MODE</span>
            <span className="eval-context-val">Temporal Holdout</span>
          </div>
        </div>
      </header>

      {/* ═══════════════════════════════════════════════════════════════
          SECTION 02 — EXECUTIVE PERFORMANCE SNAPSHOT
          ═══════════════════════════════════════════════════════════════ */}
      <section className="eval-section" aria-labelledby="section-snapshot-heading">
        <div className="eval-section-eyebrow">
          <span className="sys-label-accent">ASSURANCE SUMMARY</span>
          <h2 id="section-snapshot-heading" className="sys-label-lg">
            EXECUTIVE PERFORMANCE SNAPSHOT
          </h2>
        </div>

        {/* Primary Verdict Banner */}
        <div className="surface-elevated" style={{ marginBottom: "var(--space-4)", padding: "var(--space-4) var(--space-5)" }}>
          <span className="sys-label" style={{ display: "block", marginBottom: "var(--space-2)" }}>EVALUATION VERDICT</span>
          <div className="headline-md" style={{ marginBottom: "var(--space-2)" }}>Meaningful enrichment</div>
          <p className="body-md" style={{ margin: 0 }}>
            Fraud-containing merchant-days were{" "}
            <strong style={{ color: "var(--accent-primary)" }}>
              {pr?.flagged_vs_normal?.enrichment_vs_normal}× enriched
            </strong>{" "}
            among detected behavioral deviations compared with normal activity.
          </p>
        </div>

        <div className="grid-4 eval-snapshot-grid">
          {/* Card 1: Enrichment vs Normal */}
          <div className="surface eval-snapshot-card">
            <div className="eval-card-provenance">
              <span className="sys-label">ENRICHMENT VS NORMAL</span>
              <span className="eval-prov-badge">RATIO</span>
            </div>
            <div className="eval-metric-stat">
              <span className="metric-xl nowrap-text">{pr?.flagged_vs_normal?.enrichment_vs_normal}×</span>
              <span className="eval-stat-sublabel">higher fraud rate</span>
            </div>
            <p className="body-sm eval-card-expl">
              Flagged activity contains fraud at {pr?.flagged_vs_normal?.enrichment_vs_normal}× the
              rate of behaviorally normal days.
            </p>
            <div className="eval-card-meta">
              <span><strong>Comparison:</strong> Normal activity</span>
              <span><strong>Scope:</strong> Held-out test period</span>
            </div>
          </div>

          {/* Card 2: Enrichment vs Overall */}
          <div className="surface eval-snapshot-card">
            <div className="eval-card-provenance">
              <span className="sys-label">ENRICHMENT VS OVERALL</span>
              <span className="eval-prov-badge">RATIO</span>
            </div>
            <div className="eval-metric-stat">
              <span className="metric-xl nowrap-text">{pr?.flagged_vs_normal?.enrichment_vs_overall}×</span>
              <span className="eval-stat-sublabel">above baseline</span>
            </div>
            <p className="body-sm eval-card-expl">
              Signal concentration remains {pr?.flagged_vs_normal?.enrichment_vs_overall}× above the
              general historical population base rate.
            </p>
            <div className="eval-card-meta">
              <span><strong>Comparison:</strong> General population</span>
              <span><strong>Scope:</strong> Held-out test period</span>
            </div>
          </div>

          {/* Card 3: Proxy-Positive Coverage */}
          <div className="surface eval-snapshot-card">
            <div className="eval-card-provenance">
              <span className="sys-label">PROXY-POSITIVE COVERAGE</span>
              <span className="eval-prov-badge">PERCENTAGE</span>
            </div>
            <div className="eval-metric-stat">
              <span className="metric-xl nowrap-text">{ae?.proxy_capture_rate_pct}%</span>
              <span className="eval-stat-sublabel">proxy fraud surfaced</span>
            </div>
            <p className="body-sm eval-card-expl">
              Surfaced {fmtNum(ae?.proxy_fraud_days_captured || 0)} of{" "}
              {fmtNum(ae?.total_proxy_fraud_days || 0)} merchant-days containing proxy indicators.
            </p>
            <div className="eval-card-meta">
              <span><strong>Unit:</strong> Fraud-tagged merchant-days</span>
              <span><strong>Method:</strong> Proxy ground truth</span>
            </div>
          </div>

          {/* Card 4: Alerts per Proxy-Positive Day */}
          <div className="surface eval-snapshot-card">
            <div className="eval-card-provenance">
              <span className="sys-label">ALERTS PER PROXY-POSITIVE DAY</span>
              <span className="eval-prov-badge">WORKLOAD</span>
            </div>
            <div className="eval-metric-stat">
              <span className="metric-xl nowrap-text">~{ae?.alerts_per_proxy_positive}</span>
              <span className="eval-stat-sublabel">alerts / positive day</span>
            </div>
            <p className="body-sm eval-card-expl">
              Investigation workload proxy: approximately 15 alerts generated per proxy-positive day
              surfaced.
            </p>
            <div className="eval-card-meta">
              <span><strong>Workload:</strong> Screening burden ratio</span>
              <span><strong>Yield:</strong> 1 positive per ~15 alerts</span>
            </div>
          </div>
        </div>
      </section>

      <hr className="section-rule" />

      {/* ═══════════════════════════════════════════════════════════════
          SECTION 03 — DETECTION PERFORMANCE EVIDENCE
          ═══════════════════════════════════════════════════════════════ */}
      <section className="eval-section" aria-labelledby="section-evidence-heading">
        <span className="sys-label-accent">SECTION 01</span>
        <h2 id="section-evidence-heading" className="sys-label-lg">
          01 // DETECTION PERFORMANCE EVIDENCE
        </h2>
        <p className="body-md" style={{ marginBottom: "var(--space-5)" }}>
          Comparative evidence demonstrating fraud proxy concentration across detection groups versus
          unflagged and population baselines.
        </p>

        {/* Group Comparison Overview */}
        <div className="surface eval-evidence-container" style={{ marginBottom: "var(--space-5)" }}>
          <span className="sys-label" style={{ display: "block", marginBottom: "var(--space-4)" }}>
            POPULATION FRAUD PROXY CONCENTRATION (HELD-OUT TEST SET)
          </span>

          <div className="eval-proportional-groups">
            {/* Group A: Flagged (Elevated + High) */}
            <div className="eval-group-row">
              <div className="eval-group-info">
                <div className="eval-group-title">
                  <strong>FLAGGED (ELEVATED + HIGH)</strong>
                  <span className="eval-group-sub">Composite MAD ≥ 4.0</span>
                </div>
                <div className="eval-group-metrics">
                  <span className="eval-rate-val accent nowrap-text">
                    {flaggedFraudRate}% fraud rate
                  </span>
                  <span className="eval-count-val">
                    {fmtNum(flaggedFraudDays)} / {fmtNum(flaggedCount)} days
                  </span>
                </div>
              </div>
              <div className="eval-bar-track" aria-hidden="true">
                <div
                  className="eval-bar-fill flagged"
                  style={{ width: `${Math.min(100, (parseFloat(flaggedFraudRate) / 10) * 100)}%` }}
                />
              </div>
              <div className="eval-group-enrichment">
                <strong className="nowrap-text">{behavioralEnrichment}×</strong> vs normal
              </div>
            </div>

            {/* Group B: Normal Comparison Group */}
            <div className="eval-group-row">
              <div className="eval-group-info">
                <div className="eval-group-title">
                  <strong>NORMAL COMPARISON GROUP</strong>
                  <span className="eval-group-sub">Composite MAD &lt; 4.0</span>
                </div>
                <div className="eval-group-metrics">
                  <span className="eval-rate-val nowrap-text">
                    {normalFraudRate}% fraud rate
                  </span>
                  <span className="eval-count-val">
                    {fmtNum(normalFraudDays)} / {fmtNum(normalCount)} days
                  </span>
                </div>
              </div>
              <div className="eval-bar-track" aria-hidden="true">
                <div
                  className="eval-bar-fill normal"
                  style={{ width: `${Math.min(100, (Number(normalFraudRate) / 10) * 100)}%` }}
                />
              </div>
              <div className="eval-group-enrichment muted">
                1.00× (baseline)
              </div>
            </div>

            {/* Group C: General Population Base Rate */}
            <div className="eval-group-row">
              <div className="eval-group-info">
                <div className="eval-group-title">
                  <strong>GENERAL POPULATION</strong>
                  <span className="eval-group-sub">All test merchant-days</span>
                </div>
                <div className="eval-group-metrics">
                  <span className="eval-rate-val nowrap-text">
                    1.70% base rate
                  </span>
                  <span className="eval-count-val">
                    {fmtNum(ae?.total_proxy_fraud_days || 2146)} / {fmtNum(totalTestDays)} days
                  </span>
                </div>
              </div>
              <div className="eval-bar-track" aria-hidden="true">
                <div
                  className="eval-bar-fill population"
                  style={{ width: `${(1.70 / 10) * 100}%` }}
                />
              </div>
              <div className="eval-group-enrichment muted">
                Base prevalence
              </div>
            </div>
          </div>
        </div>

        {/* Proxy Classification Metrics Strip */}
        <div className="grid-2" style={{ marginBottom: "var(--space-5)" }}>
          <div className="surface">
            <span className="sys-label" style={{ display: "block", marginBottom: "var(--space-3)" }}>
              PROXY DETECTION PERFORMANCE
            </span>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "var(--space-4)" }}>
              <div className="metric-block">
                <span className="metric-md nowrap-text">{pm?.proxy_precision_pct}%</span>
                <span className="sys-label" style={{ fontSize: "0.5rem" }}>PROXY PRECISION</span>
              </div>
              <div className="metric-block">
                <span className="metric-md nowrap-text">{pm?.proxy_recall_pct}%</span>
                <span className="sys-label" style={{ fontSize: "0.5rem" }}>PROXY RECALL</span>
              </div>
              <div className="metric-block">
                <span className="metric-md nowrap-text">{pm?.proxy_f1_pct}%</span>
                <span className="sys-label" style={{ fontSize: "0.5rem" }}>PROXY F1</span>
              </div>
            </div>
            <div className="methodology-notice" style={{ marginTop: "var(--space-4)" }}>
              {pm?.methodology_note}
            </div>
          </div>

          <div className="surface">
            <span className="sys-label" style={{ display: "block", marginBottom: "var(--space-3)" }}>
              ALERT EFFICIENCY
            </span>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "var(--space-4)" }}>
              <div className="metric-block">
                <span className="metric-md nowrap-text">{fmtNum(ae?.total_alerts || 0)}</span>
                <span className="sys-label" style={{ fontSize: "0.5rem" }}>TOTAL ALERTS</span>
              </div>
              <div className="metric-block">
                <span className="metric-md nowrap-text">{ae?.alert_rate_pct}%</span>
                <span className="sys-label" style={{ fontSize: "0.5rem" }}>ALERT RATE</span>
              </div>
              <div className="metric-block">
                <span className="metric-md nowrap-text">{ae?.alerts_per_proxy_positive}</span>
                <span className="sys-label" style={{ fontSize: "0.5rem" }}>ALERTS / POSITIVE</span>
              </div>
            </div>
            <p className="body-sm" style={{ color: "var(--ink-secondary)", marginTop: "var(--space-4)" }}>
              Surfaced <strong>{ae?.proxy_capture_rate_pct}%</strong> of available fraud-containing days
              ({fmtNum(ae?.proxy_fraud_days_captured || 0)} of {fmtNum(ae?.total_proxy_fraud_days || 0)}).
            </p>
          </div>
        </div>

        {/* Risk-Level Performance Table */}
        <div className="eval-subcard">
          <span className="sys-label" style={{ display: "block", marginBottom: "var(--space-3)" }}>
            RISK-LEVEL PERFORMANCE
          </span>
          <div className="surface" style={{ padding: 0, overflow: "hidden" }}>
            <div className="table-scroll">
              <table className="data-table" aria-label="Risk level performance">
                <thead>
                  <tr>
                    <th scope="col">Risk Level</th>
                    <th scope="col" className="align-right">Count</th>
                    <th scope="col" className="align-right">Fraud Days</th>
                    <th scope="col" className="align-right">Fraud Rate</th>
                    <th scope="col" className="align-right">Enrichment</th>
                  </tr>
                </thead>
                <tbody>
                  {["normal", "elevated", "high"].map((level) => {
                    const d = pr?.risk_levels?.[level];
                    if (!d) return null;
                    return (
                      <tr key={level}>
                        <td>
                          <span className={`risk-badge risk-${level}`}>
                            {level.toUpperCase()}
                          </span>
                        </td>
                        <td className="align-right">{fmtNum(d.count || 0)}</td>
                        <td className="align-right">{fmtNum(d.fraud_days || 0)}</td>
                        <td className="align-right strong nowrap-text">{d.fraud_rate}%</td>
                        <td className="align-right accent nowrap-text">{d.enrichment}×</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <hr className="section-rule" />

      {/* ═══════════════════════════════════════════════════════════════
          SECTION 04 — SIGNAL CONCENTRATION ANALYSIS
          ═══════════════════════════════════════════════════════════════ */}
      <section className="eval-section" aria-labelledby="section-signal-heading">
        <span className="sys-label-accent">SECTION 02</span>
        <h2 id="section-signal-heading" className="sys-label-lg">
          02 // SIGNAL CONCENTRATION ANALYSIS
        </h2>
        <p className="body-md" style={{ marginBottom: "var(--space-4)" }}>
          Statistical enrichment achieved by behavioral anomaly modeling versus naive volume-only
          thresholding.
        </p>

        <div className="grid-2 eval-signal-comparison">
          {/* Behavioral Model Card */}
          <div className="surface eval-signal-card active">
            <div className="eval-signal-header">
              <span className="sys-label-accent">BEHAVIORAL MODEL</span>
              <span className="eval-prov-badge">30-DAY MAD</span>
            </div>
            <div className="eval-signal-stat">
              <span className="metric-lg accent nowrap-text">
                {pr?.flagged_vs_normal?.enrichment_vs_normal}×
              </span>
              <span className="eval-signal-unit">higher fraud prevalence</span>
            </div>
            <p className="body-sm" style={{ color: "var(--ink-secondary)", marginTop: "var(--space-3)" }}>
              Dual-signal composite deviation: detects shifts relative to merchant-specific historical
              spending patterns and transaction frequency.
            </p>
          </div>

          {/* Volume-Only Baseline Card */}
          <div className="surface eval-signal-card">
            <div className="eval-signal-header">
              <span className="sys-label" style={{ color: "var(--ink-tertiary)" }}>
                VOLUME-ONLY BASELINE
              </span>
              <span className="eval-prov-badge">NAIVE STRATEGY</span>
            </div>
            <div className="eval-signal-stat">
              <span className="metric-lg nowrap-text" style={{ color: "var(--ink-ghost)" }}>
                {data.baseline_comparison?.volume_only?.enrichment_vs_normal}×
              </span>
              <span className="eval-signal-unit">higher fraud prevalence</span>
            </div>
            <p className="body-sm" style={{ color: "var(--ink-secondary)", marginTop: "var(--space-3)" }}>
              Flagging solely on highest absolute daily transaction volume surfaces disproportionately
              large merchants rather than anomalous shifts.
            </p>
          </div>
        </div>

        {/* Advantage Callout Notice */}
        <div className="eval-advantage-notice">
          <span className="sys-label-accent">ANALYTICAL ADVANTAGE:</span>
          <span className="body-sm" style={{ color: "var(--ink-secondary)" }}>
            Behavioral anomaly modeling delivers a{" "}
            <strong className="nowrap-text" style={{ color: "var(--accent-primary)" }}>
              {advantageRatio}× advantage
            </strong>{" "}
            in fraud proxy enrichment over a simple volume-only heuristic.
          </span>
          <span className="body-sm eval-disclaimer-text">
            Non-causal interpretation: Measures historical statistical concentration, not transaction guilt.
          </span>
        </div>
      </section>

      <hr className="section-rule" />

      {/* ═══════════════════════════════════════════════════════════════
          SECTION 05 — RESPONSIVE METHODOLOGY WORKFLOW
          ═══════════════════════════════════════════════════════════════ */}
      <section className="eval-section" aria-labelledby="section-methodology-heading">
        <span className="sys-label-accent">SECTION 03</span>
        <h2 id="section-methodology-heading" className="sys-label-lg">
          03 // EVALUATION METHODOLOGY
        </h2>
        <p className="body-md" style={{ marginBottom: "var(--space-5)" }}>
          Deterministic analytical pipeline utilized to measure performance across frozen historical data.
        </p>

        <div className="eval-methodology-workflow" aria-label="Evaluation Pipeline Workflow">
          {/* Step 1 */}
          <div className="eval-flow-card">
            <div className="eval-flow-step-num">01</div>
            <div className="eval-flow-title">FROZEN HISTORICAL DATA</div>
            <p className="eval-flow-desc">
              693 merchants, 337,151 total merchant-days. Strict temporal holdout partitioning.
            </p>
          </div>

          <div className="eval-flow-arrow" aria-hidden="true">→</div>

          {/* Step 2 */}
          <div className="eval-flow-card">
            <div className="eval-flow-step-num">02</div>
            <div className="eval-flow-title">BASELINE CONSTRUCTION</div>
            <p className="eval-flow-desc">
              30-day rolling window: median payment value and Median Absolute Deviation (MAD) per merchant.
            </p>
          </div>

          <div className="eval-flow-arrow" aria-hidden="true">→</div>

          {/* Step 3 */}
          <div className="eval-flow-card">
            <div className="eval-flow-step-num">03</div>
            <div className="eval-flow-title">DETERMINISTIC DETECTION</div>
            <p className="eval-flow-desc">
              Composite deviation evaluated: Elevated ≥ 4.0 MADs, High ≥ 5.0 MADs without tuning.
            </p>
          </div>

          <div className="eval-flow-arrow" aria-hidden="true">→</div>

          {/* Step 4 */}
          <div className="eval-flow-card">
            <div className="eval-flow-step-num">04</div>
            <div className="eval-flow-title">HISTORICAL COMPARISON</div>
            <p className="eval-flow-desc">
              Cross-tabulation against historical fraud indicators across 126,574 unseen test days.
            </p>
          </div>

          <div className="eval-flow-arrow" aria-hidden="true">→</div>

          {/* Step 5 */}
          <div className="eval-flow-card">
            <div className="eval-flow-step-num">05</div>
            <div className="eval-flow-title">EVALUATION RESULTS</div>
            <p className="eval-flow-desc">
              Enrichment ratios, proxy-positive coverage, and scenario-based review workload models.
            </p>
          </div>
        </div>
      </section>

      <hr className="section-rule" />

      {/* ═══════════════════════════════════════════════════════════════
          SECTION 06 — POLICY TRANSPARENCY & INVESTIGATION BURDEN
          ═══════════════════════════════════════════════════════════════ */}
      <section className="eval-section" aria-labelledby="section-policy-heading">
        <span className="sys-label-accent">SECTION 04</span>
        <h2 id="section-policy-heading" className="sys-label-lg">
          04 // DETECTION POLICY TRANSPARENCY
        </h2>

        {/* Study Parameters Surface */}
        <div className="surface" style={{ marginBottom: "var(--space-5)" }}>
          <span className="sys-label" style={{ display: "block", marginBottom: "var(--space-4)" }}>
            STUDY PARAMETERS
          </span>
          <div className="eval-params-grid">
            <span className="sys-label">DETECTION UNIT</span>
            <span className="body-sm">Merchant-day</span>

            <span className="sys-label">PROXY TRUTH</span>
            <span className="body-sm">Merchant-day containing ≥1 fraud-tagged transaction</span>

            <span className="sys-label">METHOD</span>
            <span className="body-sm">Frozen behavioral detection policy — no test-data tuning</span>

            <span className="sys-label">BASELINE</span>
            <span className="body-sm">30-day rolling median + MAD per merchant</span>

            <span className="sys-label">SIGNALS</span>
            <span className="body-sm">Amount deviation (primary), velocity deviation (context)</span>

            <span className="sys-label">THRESHOLDS</span>
            <span className="body-sm nowrap-text">
              Elevated ≥ {data.methodology?.thresholds?.elevated} MADs, High ≥ {data.methodology?.thresholds?.high} MADs
            </span>

            <span className="sys-label">OBSERVATIONS</span>
            <span className="body-sm nowrap-text">{fmtNum(totalTestDays)} eligible merchant-days</span>
          </div>
        </div>

        {/* Proxy Outcome Cross-Tabulation (Confusion Matrix) */}
        <div className="eval-subcard" style={{ marginBottom: "var(--space-6)" }}>
          <div className="eval-matrix-header">
            <span className="sys-label">PROXY OUTCOME CROSS-TABULATION (CONFUSION MATRIX)</span>
            <span className="eval-prov-badge">MERCHANT-DAY LEVEL</span>
          </div>

          <div className="surface" style={{ padding: 0, overflow: "hidden" }}>
            <div className="eval-matrix-notice">
              <span className="sys-label-accent">PROXY INTERPRETATION NOTICE:</span>
              <p className="body-sm" style={{ color: "var(--ink-secondary)", margin: 0 }}>
                Unit of analysis: <strong>{cm?.unit}</strong>. Positive definition:{" "}
                <strong>{cm?.positive_definition}</strong>. A proxy-positive merchant-day indicates the
                presence of at least one transaction carrying the available fraud indicator. This is not
                equivalent to independently verified transaction-level ground truth.
              </p>
            </div>

            <div className="table-scroll">
              <table className="data-table" aria-label="Confusion matrix">
                <thead>
                  <tr>
                    <th scope="col">Detection Outcome</th>
                    <th
                      scope="col"
                      className="align-right"
                      style={{ borderBottom: "2px solid var(--accent-primary)" }}
                    >
                      FRAUD-CONTAINING DAY (PROXY +)
                    </th>
                    <th scope="col" className="align-right">
                      NO FRAUD DETECTED (PROXY -)
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>
                      <span className="sys-label" style={{ color: "var(--accent-warm)" }}>
                        FLAGGED (ELEVATED + HIGH)
                      </span>
                    </td>
                    <td className="align-right">
                      <span className="metric-sm nowrap-text" style={{ color: "var(--accent-primary)" }}>
                        TP {fmtNum(cm?.tp || 0)}
                      </span>
                    </td>
                    <td className="align-right">
                      <span className="metric-sm nowrap-text" style={{ color: "var(--risk-elevated)" }}>
                        FP {fmtNum(cm?.fp || 0)}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <span className="sys-label">NOT FLAGGED (NORMAL)</span>
                    </td>
                    <td className="align-right">
                      <span className="metric-sm nowrap-text" style={{ color: "var(--risk-elevated)" }}>
                        FN {fmtNum(cm?.fn || 0)}
                      </span>
                    </td>
                    <td className="align-right">
                      <span className="metric-sm nowrap-text">TN {fmtNum(cm?.tn || 0)}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Investigation Burden Workload Model */}
        <div className="eval-subcard">
          <div className="eval-matrix-header">
            <span className="sys-label">INVESTIGATION BURDEN &amp; WORKLOAD COST MODEL</span>
            <span className="eval-prov-badge">API-BACKED SCENARIOS</span>
          </div>

          <p className="body-sm" style={{ color: "var(--ink-secondary)", marginBottom: "var(--space-4)" }}>
            Scenario names, review durations, and workload estimates are sourced directly from the
            analytical cost-model endpoint.
          </p>

          {/* Scenario Selector */}
          <div
            className="eval-scenario-selector"
            role="group"
            aria-label="Scenario selector"
            style={{ marginBottom: "var(--space-4)" }}
          >
            {(["lean", "standard", "intensive"] as ScenarioPreset[]).map((s) => (
              <button
                key={s}
                type="button"
                className={`filter-chip ${activeScenario === s ? "active" : ""}`}
                onClick={() => setActiveScenario(s)}
                aria-pressed={activeScenario === s}
              >
                {s.toUpperCase()}
              </button>
            ))}
          </div>

          {costLoading && <LoadingState label="Computing investigation burden..." />}

          {costModel && !costLoading && (
            <>
              {/* Active Scenario Assumptions */}
              <div className="surface" style={{ marginBottom: "var(--space-4)" }}>
                <span className="sys-label" style={{ display: "block", marginBottom: "var(--space-3)" }}>
                  SCENARIO ASSUMPTIONS ({activeScenario.toUpperCase()})
                </span>
                <div className="eval-params-grid">
                  <span className="sys-label">REVIEW DURATION</span>
                  <span className="body-sm">{costModel.assumptions.review_minutes} minutes / alert</span>

                  <span className="sys-label">ANALYST COST</span>
                  <span className="body-sm">{fmtINR(costModel.assumptions.analyst_hourly_cost)} / hour</span>

                  <span className="sys-label">DATA SOURCE</span>
                  <span className="body-sm" style={{ color: "var(--ink-ghost)" }}>
                    {costModel.assumptions.source}
                  </span>
                </div>
              </div>

              {/* Workload Metric Cards */}
              <div className="grid-3" style={{ marginBottom: "var(--space-4)" }}>
                <div className="surface">
                  <div className="metric-block">
                    <span className="metric-lg nowrap-text">
                      {fmtNum(costModel.results.estimated_false_positive_alerts)}
                    </span>
                    <span className="sys-label">EST. FALSE POSITIVE ALERTS</span>
                  </div>
                </div>
                <div className="surface">
                  <div className="metric-block">
                    <span className="metric-lg nowrap-text">
                      {fmtNum(costModel.results.estimated_review_hours)}
                    </span>
                    <span className="sys-label">EST. REVIEW HOURS</span>
                  </div>
                </div>
                <div className="surface-elevated">
                  <div className="metric-block">
                    <span className="metric-lg nowrap-text">
                      {fmtINR(costModel.results.scenario_based_review_cost)}
                    </span>
                    <span className="sys-label">SCENARIO-BASED REVIEW COST</span>
                  </div>
                </div>
              </div>

              {/* Scenario Comparison Table */}
              <div className="surface" style={{ padding: 0, overflow: "hidden", marginBottom: "var(--space-4)" }}>
                <div className="table-scroll">
                  <table className="data-table" aria-label="Scenario comparison">
                    <thead>
                      <tr>
                        <th scope="col">Scenario</th>
                        <th scope="col" className="align-right">Minutes/Alert</th>
                        <th scope="col" className="align-right">₹/Hour</th>
                        <th scope="col" className="align-right">Est. FP Alerts</th>
                        <th scope="col" className="align-right">Review Hours</th>
                        <th scope="col" className="align-right">Review Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {costModel.scenarios.map((s) => (
                        <tr
                          key={s.name}
                          style={{
                            background:
                              s.name.toLowerCase() === activeScenario ? "var(--surface-1)" : undefined,
                          }}
                        >
                          <td><strong>{s.name}</strong></td>
                          <td className="align-right">{s.review_minutes}</td>
                          <td className="align-right nowrap-text">{fmtINR(s.analyst_hourly_cost)}</td>
                          <td className="align-right nowrap-text">{fmtNum(s.estimated_false_positive_alerts)}</td>
                          <td className="align-right nowrap-text">{fmtNum(s.estimated_review_hours)}</td>
                          <td className="align-right strong nowrap-text">{fmtINR(s.scenario_based_review_cost)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Policy Threshold Trade-off Table */}
              <div className="surface" style={{ padding: 0, overflow: "hidden", marginBottom: "var(--space-4)" }}>
                <div className="table-scroll">
                  <table className="data-table" aria-label="Policy comparison">
                    <thead>
                      <tr>
                        <th scope="col">Policy</th>
                        <th scope="col" className="align-right">Alerts</th>
                        <th scope="col" className="align-right">Proxy TP</th>
                        <th scope="col" className="align-right">Est. FP</th>
                        <th scope="col" className="align-right">Precision</th>
                        <th scope="col" className="align-right">Recall</th>
                        <th scope="col" className="align-right">Enrichment</th>
                        <th scope="col" className="align-right">Review Hours</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(costModel.policy_comparison).map(([key, p]) => (
                        <tr key={key}>
                          <td><strong className="body-sm">{p.label}</strong></td>
                          <td className="align-right nowrap-text">{fmtNum(p.total_alerts)}</td>
                          <td className="align-right nowrap-text">{fmtNum(p.proxy_true_positives)}</td>
                          <td className="align-right nowrap-text">{fmtNum(p.estimated_false_positive_alerts)}</td>
                          <td className="align-right nowrap-text">{p.proxy_precision_pct}%</td>
                          <td className="align-right accent nowrap-text">{p.proxy_recall_pct}%</td>
                          <td className="align-right strong nowrap-text">{p.enrichment_vs_normal}×</td>
                          <td className="align-right nowrap-text">{fmtNum(p.estimated_review_hours)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="methodology-notice">
                {costModel.assumptions.disclaimer}
              </div>
            </>
          )}
        </div>
      </section>

      <hr className="section-rule" />

      {/* ═══════════════════════════════════════════════════════════════
          SECTION 07 — EVALUATION BOUNDARIES & SCOPE DISCLOSURES
          ═══════════════════════════════════════════════════════════════ */}
      <section className="eval-section" aria-labelledby="section-boundaries-heading">
        <span className="sys-label-accent">SECTION 05</span>
        <h2 id="section-boundaries-heading" className="sys-label-lg">
          05 // EVALUATION BOUNDARIES
        </h2>
        <p className="body-md" style={{ marginBottom: "var(--space-5)" }}>
          Explicit boundaries of what the deterministic detection system establishes versus areas
          outside analytical scope.
        </p>

        <div className="grid-2 eval-boundary-grid" style={{ marginBottom: "var(--space-5)" }}>
          {/* Card 1: Validated */}
          <div className="surface eval-boundary-card">
            <div className="eval-boundary-header">
              <span className="eval-status-badge status-validated">VALIDATED</span>
              <strong>Historical Dataset Analysis</strong>
            </div>
            <p className="body-sm" style={{ color: "var(--ink-secondary)" }}>
              30-day baseline model validated on {fmtNum(totalTestDays)} held-out merchant-days.
              Confirmed 7.13× proxy fraud concentration among behavioral anomalies.
            </p>
          </div>

          {/* Card 2: Not Evaluated */}
          <div className="surface eval-boundary-card">
            <div className="eval-boundary-header">
              <span className="eval-status-badge status-not-evaluated">NOT EVALUATED</span>
              <strong>Live Production Ingestion</strong>
            </div>
            <p className="body-sm" style={{ color: "var(--ink-secondary)" }}>
              Live payment streaming ingestion and sub-daily transaction latencies are outside the
              current evaluation scope. Historical batch replay only.
            </p>
          </div>

          {/* Card 3: Not Available */}
          <div className="surface eval-boundary-card">
            <div className="eval-boundary-header">
              <span className="eval-status-badge status-not-available">NOT AVAILABLE</span>
              <strong>Ground-Truth Transaction Intent</strong>
            </div>
            <p className="body-sm" style={{ color: "var(--ink-secondary)" }}>
              Individual transaction fraud intent is outside deterministic scope. The system utilizes
              historical proxy flags at the merchant-day resolution.
            </p>
          </div>

          {/* Card 4: Disabled */}
          <div className="surface eval-boundary-card">
            <div className="eval-boundary-header">
              <span className="eval-status-badge status-disabled">DISABLED</span>
              <strong>Automated Fraud Enforcement</strong>
            </div>
            <p className="body-sm" style={{ color: "var(--ink-secondary)" }}>
              Automated merchant blocking, chargeback triggering, and account freezes are intentionally
              disabled. Detection provides evidence to support human investigation.
            </p>
          </div>
        </div>

        {/* Limitations List */}
        <div className="surface" style={{ padding: 0 }} role="list" aria-label="Limitations">
          {data.limitations?.map((lim, i) => (
            <div
              key={i}
              role="listitem"
              style={{
                padding: "var(--space-3) var(--space-5)",
                borderBottom: i < data.limitations.length - 1 ? "1px solid var(--surface-2)" : "none",
                display: "flex",
                alignItems: "center",
                gap: "var(--space-3)",
              }}
            >
              <span style={{ color: "var(--ink-ghost)", fontSize: "0.6875rem", flexShrink: 0 }}>—</span>
              <span className="body-sm" style={{ color: "var(--ink-secondary)" }}>{lim}</span>
            </div>
          ))}
        </div>
      </section>

      <hr className="section-rule" />

      {/* ═══════════════════════════════════════════════════════════════
          SECTION 08 — HUMAN INTERPRETATION BOUNDARY & ACTIONS
          ═══════════════════════════════════════════════════════════════ */}
      <section className="eval-section" aria-labelledby="section-governance-heading">
        <div className="eval-governance-card" data-testid="eval-human-boundary">
          <div className="eval-governance-header">
            <span className="sys-label-accent">06 // HUMAN INTERPRETATION BOUNDARY</span>
            <h3 id="section-governance-heading" className="headline-md" style={{ margin: "var(--space-1) 0" }}>
              Human Authority &amp; System Purpose
            </h3>
            <p className="body-md eval-governance-lead">
              The evaluation demonstrates historical statistical behavior under the current deterministic
              methodology. It does not independently establish transaction intent, fraud, or future
              production performance.
            </p>
            <p className="body-sm" style={{ color: "var(--ink-secondary)", maxWidth: 720 }}>
              Payment Burst Sentinel functions as an anomaly intelligence layer that flags mathematically
              unusual merchant behavior. Analytical evidence and advisory summaries assist human risk
              investigators; they do not replace human judgment.
            </p>
          </div>

          {/* Cross-Screen Navigation Action Controls */}
          <div className="eval-nav-actions" aria-label="Evaluation Navigation Actions">
            {onNavigateToInvestigations && (
              <button
                type="button"
                className="filter-chip active eval-btn-primary"
                onClick={onNavigateToInvestigations}
                id="btn-eval-nav-investigations"
              >
                View Investigations →
              </button>
            )}

            {onNavigateToMerchantRhythm && (
              <button
                type="button"
                className="filter-chip eval-btn-secondary"
                onClick={onNavigateToMerchantRhythm}
                id="btn-eval-nav-merchant"
              >
                View Merchant Rhythm →
              </button>
            )}

            {onNavigateToMonitor && (
              <button
                type="button"
                className="filter-chip eval-btn-tertiary"
                onClick={onNavigateToMonitor}
                id="btn-eval-nav-monitor"
              >
                ← Back to Monitor
              </button>
            )}
          </div>
        </div>
      </section>

    </div>
  );
}
