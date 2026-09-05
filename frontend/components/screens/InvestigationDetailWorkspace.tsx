"use client";

import { useState, useEffect, useRef } from "react";
import type { InvestigationDetail } from "@/types/api";
import { getInvestigationDetail } from "@/lib/api";
import { LoadingState } from "@/components/shared/LoadingState";
import { formatMads, formatSignalDominance } from "@/lib/utils";
import { AIInvestigationBrief } from "@/components/ai/AIInvestigationBrief";

interface InvestigationDetailWorkspaceProps {
  merchant: string;
  date: string;
  onBack: () => void;
  onNavigateToMerchant?: (merchant: string) => void;
  onNavigateToEvaluation?: () => void;
}

export function InvestigationDetailWorkspace({
  merchant,
  date,
  onBack,
  onNavigateToMerchant,
  onNavigateToEvaluation,
}: InvestigationDetailWorkspaceProps) {
  const [detail, setDetail] = useState<InvestigationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [is404, setIs404] = useState(false);

  // Request de-duplication and cancellation ref
  const abortControllerRef = useRef<AbortController | null>(null);

  async function loadDetail() {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);
    setError(null);
    setIs404(false);

    try {
      const data = await getInvestigationDetail(merchant, date, controller.signal);
      if (!controller.signal.aborted) {
        setDetail(data);
        setLoading(false);
      }
    } catch (err: unknown) {
      if (controller.signal.aborted) {
        return; // Stale request cancelled, ignore
      }
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("404")) {
        setIs404(true);
      } else {
        setError(msg || "Failed to load investigation evidence. Ensure backend is running.");
      }
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDetail();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [merchant, date]);

  /* ─── State 1: Loading ─────────────────────────────────── */
  if (loading) {
    return (
      <div className="page-container" data-testid="workspace-loading">
        <div className="workspace-nav-bar">
          <button type="button" className="workspace-back-btn" onClick={onBack} aria-label="Back to investigations index">
            ← Back to Investigations
          </button>
        </div>
        <LoadingState label={`Retrieving investigation evidence for ${merchant} (${date})…`} />
      </div>
    );
  }

  /* ─── State 2: 404 Not Found ───────────────────────────── */
  if (is404) {
    return (
      <div className="page-container" data-testid="workspace-404">
        <div className="workspace-nav-bar">
          <button type="button" className="workspace-back-btn" onClick={onBack} aria-label="Back to investigations index">
            ← Back to Investigations
          </button>
        </div>
        <div className="workspace-error-card">
          <span className="sys-label-accent">INVESTIGATION NOT AVAILABLE</span>
          <h2 className="headline-md" style={{ margin: "var(--space-2) 0" }}>Event Not Found</h2>
          <p className="body-md" style={{ color: "var(--ink-secondary)", maxWidth: 540 }}>
            The requested historical detection event for <strong>{merchant}</strong> on <strong>{date}</strong> could not be resolved from the dataset.
          </p>
          <div style={{ marginTop: "var(--space-4)" }}>
            <button type="button" className="filter-chip active" onClick={onBack}>
              Return to Investigations Index
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* ─── State 3: API Error ───────────────────────────────── */
  if (error || !detail) {
    return (
      <div className="page-container" data-testid="workspace-error">
        <div className="workspace-nav-bar">
          <button type="button" className="workspace-back-btn" onClick={onBack} aria-label="Back to investigations index">
            ← Back to Investigations
          </button>
        </div>
        <div className="workspace-error-card">
          <span className="sys-label-accent" style={{ color: "var(--risk-high)" }}>EVIDENCE LOAD FAILED</span>
          <h2 className="headline-md" style={{ margin: "var(--space-2) 0" }}>Unable to Retrieve Evidence</h2>
          <p className="body-sm" style={{ color: "var(--ink-secondary)", marginBottom: "var(--space-4)" }}>
            {error || "An unexpected error occurred while loading this investigation."}
          </p>
          <div style={{ display: "flex", gap: "var(--space-3)" }}>
            <button type="button" className="filter-chip active" onClick={loadDetail}>
              Retry Evidence Retrieval
            </button>
            <button type="button" className="filter-chip" onClick={onBack}>
              Return to Index
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* ─── State 4: Investigation Detail Workspace ───────────── */
  const primary = detail.primary_evidence;
  const context = detail.behavioral_context;
  const baselineRatio = (primary.observed / Math.max(primary.expected, 0.01)).toFixed(1);

  return (
    <div className="page-container investigation-workspace" data-testid="investigation-workspace">
      {/* 01 — Investigation Header */}
      <header className="workspace-header">
        <div className="workspace-nav-bar">
          <button
            type="button"
            className="workspace-back-btn"
            onClick={onBack}
            aria-label="Back to investigations index"
            id="workspace-back-btn"
          >
            ← Back to Investigations
          </button>
          <span className="workspace-reference-tag" aria-label="Display reference">
            REFERENCE: {detail.merchant} · {detail.date}
          </span>
        </div>

        <div className="workspace-title-row">
          <div>
            <span className="sys-label-accent">INVESTIGATION INTELLIGENCE // EVIDENCE WORKSPACE</span>
            <h1 className="headline-xl workspace-merchant-title" style={{ marginTop: "var(--space-1)" }}>
              {detail.merchant}
            </h1>
          </div>
          <div className="workspace-header-badges">
            <span className={`risk-badge risk-${detail.risk_level}`} aria-label={`Risk level: ${detail.risk_level}`}>
              {detail.risk_level.toUpperCase()}
            </span>
            <span className="anomaly-tag">
              {formatSignalDominance(detail.anomaly_type)}
            </span>
          </div>
        </div>

        <div className="workspace-meta-strip">
          <div className="workspace-meta-item">
            <span className="sys-label">DETECTION DATE</span>
            <span className="workspace-meta-val">{detail.date}</span>
          </div>
          <div className="workspace-meta-item">
            <span className="sys-label">COMPOSITE SIGNAL</span>
            <span className="workspace-meta-val accent">+{detail.composite_deviation.toFixed(1)} MADs</span>
          </div>
          <div className="workspace-meta-item">
            <span className="sys-label">HISTORICAL STATUS</span>
            <span className="workspace-meta-val">{(detail.baseline_info?.baseline_status || "sufficient_history").replace(/_/g, " ")}</span>
          </div>
          <div className="workspace-meta-item">
            <span className="sys-label">DATASET PROVENANCE</span>
            <span className="workspace-meta-val">Frozen Historical Data</span>
          </div>
        </div>
      </header>

      {/* 02 — Executive Evidence Snapshot */}
      <section className="workspace-section" aria-labelledby="section-snapshot-heading">
        <h2 id="section-snapshot-heading" className="workspace-section-label">
          EXECUTIVE EVIDENCE SNAPSHOT
        </h2>
        <div className="grid-4 workspace-snapshot-grid">
          <div className="surface workspace-snapshot-card">
            <span className="sys-label">OBSERVED VALUE</span>
            <span className="metric-lg workspace-stat-observed">₹{primary.observed.toLocaleString("en-IN")}</span>
            <span className="body-sm workspace-stat-sub">
              <strong>{baselineRatio}×</strong> baseline
            </span>
          </div>

          <div className="surface workspace-snapshot-card">
            <span className="sys-label">EXPECTED BASELINE</span>
            <span className="metric-lg">~₹{primary.expected.toLocaleString("en-IN")}</span>
            <span className="body-sm workspace-stat-sub">
              variability ±₹{primary.variability.toLocaleString("en-IN")}
            </span>
          </div>

          <div className="surface workspace-snapshot-card">
            <span className="sys-label">DEVIATION MAGNITUDE</span>
            <span className="metric-lg" style={{ color: "var(--accent-warm)" }}>
              {formatMads(primary.deviation_mads)}
            </span>
            <span className="body-sm workspace-stat-sub">
              Composite: {formatMads(detail.composite_deviation)}
            </span>
          </div>

          <div className="surface workspace-snapshot-card">
            <span className="sys-label">BASELINE HISTORY</span>
            <span className="metric-lg">
              {detail.baseline_info.historical_days_used}
              <span style={{ fontSize: "1rem", color: "var(--ink-ghost)" }}> / {detail.baseline_info.baseline_window_days}</span>
            </span>
            <span className="body-sm workspace-stat-sub">
              days in window used
            </span>
          </div>
        </div>
      </section>

      {/* 03 & 04 — Deterministic Evidence: Primary vs Context */}
      <div className="workspace-evidence-split">
        {/* 03 — Primary Detection Evidence */}
        <section className="surface workspace-evidence-card primary" aria-labelledby="section-primary-evidence-heading">
          <div className="evidence-card-header">
            <div>
              <span className="sys-label-accent">01 // PRIMARY DETECTION EVIDENCE</span>
              <h3 id="section-primary-evidence-heading" className="headline-md" style={{ marginTop: "var(--space-1)" }}>
                {primary.signal}
              </h3>
            </div>
            <span className="evidence-role-badge primary">{primary.role}</span>
          </div>

          <div className="evidence-kv-grid">
            <div className="evidence-kv-item">
              <span className="sys-label">OBSERVED PAYMENT VALUE</span>
              <span className="evidence-kv-num">₹{primary.observed.toLocaleString("en-IN")}</span>
            </div>
            <div className="evidence-kv-item">
              <span className="sys-label">EXPECTED HISTORICAL VALUE</span>
              <span className="evidence-kv-num">~₹{primary.expected.toLocaleString("en-IN")}</span>
            </div>
            <div className="evidence-kv-item">
              <span className="sys-label">EXPECTED VARIABILITY</span>
              <span className="evidence-kv-num">±₹{primary.variability.toLocaleString("en-IN")}</span>
            </div>
            <div className="evidence-kv-item">
              <span className="sys-label">STATISTICAL DEVIATION</span>
              <span className="evidence-kv-num accent">{formatMads(primary.deviation_mads)}</span>
            </div>
          </div>

          {/* CSS-Native Relative Magnitude Comparison Meter */}
          <div className="evidence-meter-container" aria-label="Observed vs expected baseline comparison meter">
            <div className="evidence-meter-header">
              <span className="sys-label">RELATIVE MAGNITUDE COMPARISON</span>
              <span className="body-sm" style={{ color: "var(--accent-warm)" }}>
                {baselineRatio}× expected
              </span>
            </div>
            <div className="evidence-meter-bar-wrapper">
              <div
                className="evidence-meter-fill"
                style={{
                  width: `${Math.min(100, Math.max(12, (primary.observed / Math.max(primary.expected * 2, 1)) * 50))}%`,
                }}
              />
              <div
                className="evidence-meter-baseline-line"
                title={`Expected baseline: ₹${primary.expected.toFixed(0)}`}
              />
            </div>
            <div className="evidence-meter-legend">
              <span className="body-sm">
                <span className="legend-indicator baseline" /> Baseline: ~₹{primary.expected.toLocaleString("en-IN")}
              </span>
              <span className="body-sm">
                <span className="legend-indicator burst" /> Observed Burst: ₹{primary.observed.toLocaleString("en-IN")}
              </span>
            </div>
          </div>
        </section>

        {/* 04 — Behavioral Context */}
        <section className="surface workspace-evidence-card context" aria-labelledby="section-context-evidence-heading">
          <div className="evidence-card-header">
            <div>
              <span className="sys-label" style={{ color: "var(--ink-secondary)" }}>02 // BEHAVIORAL CONTEXT</span>
              <h3 id="section-context-evidence-heading" className="headline-md" style={{ marginTop: "var(--space-1)" }}>
                {context.signal}
              </h3>
            </div>
            <span className="evidence-role-badge context">{context.role}</span>
          </div>

          <div className="evidence-kv-grid">
            <div className="evidence-kv-item">
              <span className="sys-label">OBSERVED TRANSACTION COUNT</span>
              <span className="evidence-kv-num">{context.observed} tx</span>
            </div>
            <div className="evidence-kv-item">
              <span className="sys-label">EXPECTED TRANSACTION COUNT</span>
              <span className="evidence-kv-num">~{context.expected} tx</span>
            </div>
            <div className="evidence-kv-item">
              <span className="sys-label">COUNT VARIABILITY</span>
              <span className="evidence-kv-num">±{context.variability} tx</span>
            </div>
            <div className="evidence-kv-item">
              <span className="sys-label">VELOCITY DEVIATION</span>
              <span className="evidence-kv-num">{formatMads(context.deviation_mads)}</span>
            </div>
          </div>

          <div className="context-interpretation-box">
            <span className="sys-label">BEHAVIORAL STATUS</span>
            <p className="body-sm" style={{ margin: "var(--space-1) 0 0" }}>
              {context.deviation_mads >= 3.0
                ? "Transaction frequency exhibited significant simultaneous shift alongside payment value."
                : "Transaction volume remained within normal variability bounds; deviation driven primarily by payment amount."}
            </p>
          </div>
        </section>
      </div>

      {/* 05 — System Evidence Statements */}
      {detail.evidence_statements && detail.evidence_statements.length > 0 && (
        <section className="workspace-section" aria-labelledby="section-statements-heading">
          <h2 id="section-statements-heading" className="workspace-section-label">
            03 // FACTUAL DETECTION STATEMENTS
          </h2>
          <div className="surface workspace-statements-card">
            <ul className="workspace-statements-list">
              {detail.evidence_statements.map((stmt, idx) => {
                // Normalize currency in factual statements from $ to formatted ₹
                const formattedStmt = stmt.replace(/\$(\d+(?:\.\d+)?)/g, (_, numStr) => {
                  const num = parseFloat(numStr);
                  return isNaN(num)
                    ? `₹${numStr}`
                    : `₹${num.toLocaleString("en-IN", {
                        minimumFractionDigits: numStr.includes(".") ? 2 : 0,
                        maximumFractionDigits: 2,
                      })}`;
                });
                return (
                  <li key={idx} className="workspace-statement-item">
                    <span className="workspace-statement-bullet">◆</span>
                    <span>{formattedStmt}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        </section>
      )}

      {/* 06 — Structured Detection Signal Map (3 Groups) */}
      <section className="workspace-section" aria-labelledby="section-signals-heading">
        <h2 id="section-signals-heading" className="workspace-section-label">
          04 // DETECTION SIGNAL MAP
        </h2>
        <div className="grid-3 workspace-signal-grid">
          {/* Group A: Confirmed Evidence */}
          <div className="surface signal-group-card">
            <div className="signal-group-header">
              <span className="sys-label-accent">CONFIRMED EVIDENCE</span>
            </div>
            <div className="signal-group-items">
              <div className="signal-item confirmed">
                <span className="signal-icon">✓</span>
                <div>
                  <strong>Payment Value Shift</strong>
                  <div className="signal-subtext">+{primary.deviation_mads.toFixed(1)} MADs above median</div>
                </div>
              </div>

              {context.deviation_mads >= 1.0 ? (
                <div className="signal-item confirmed">
                  <span className="signal-icon">✓</span>
                  <div>
                    <strong>Velocity Shift</strong>
                    <div className="signal-subtext">+{context.deviation_mads.toFixed(1)} MADs above expected</div>
                  </div>
                </div>
              ) : (
                <div className="signal-item context-neutral">
                  <span className="signal-icon">○</span>
                  <div>
                    <strong>Velocity Normal</strong>
                    <div className="signal-subtext">Volume within ±{context.variability} range</div>
                  </div>
                </div>
              )}

              <div className="signal-item confirmed">
                <span className="signal-icon">✓</span>
                <div>
                  <strong>Threshold Exceeded</strong>
                  <div className="signal-subtext">Composite deviation: +{detail.composite_deviation.toFixed(1)} MADs</div>
                </div>
              </div>
            </div>
          </div>

          {/* Group B: Analytical Context */}
          <div className="surface signal-group-card">
            <div className="signal-group-header">
              <span className="sys-label" style={{ color: "var(--ink-secondary)" }}>ANALYTICAL CONTEXT</span>
            </div>
            <div className="signal-group-items">
              <div className="signal-item context-neutral">
                <span className="signal-icon">ℹ</span>
                <div>
                  <strong>Baseline Window</strong>
                  <div className="signal-subtext">{detail.baseline_info.historical_days_used} of {detail.baseline_info.baseline_window_days} days utilized</div>
                </div>
              </div>

              <div className="signal-item context-neutral">
                <span className="signal-icon">ℹ</span>
                <div>
                  <strong>Temporal Anchor</strong>
                  <div className="signal-subtext">Day {detail.baseline_info.day_of_week} of week · {detail.date}</div>
                </div>
              </div>

              <div className="signal-item context-neutral">
                <span className="signal-icon">ℹ</span>
                <div>
                  <strong>Historical Proxy Labels</strong>
                  <div className="signal-subtext">{detail.metadata.fraud_count} known label period in window</div>
                </div>
              </div>
            </div>
          </div>

          {/* Group C: System Boundaries */}
          <div className="surface signal-group-card boundary">
            <div className="signal-group-header">
              <span className="sys-label" style={{ color: "var(--accent-primary)" }}>SYSTEM BOUNDARIES</span>
            </div>
            <div className="signal-group-items">
              <div className="signal-item boundary">
                <span className="signal-icon">⊘</span>
                <div>
                  <strong>External Payment Ingestion</strong>
                  <div className="signal-subtext" style={{ color: "var(--ink-tertiary)" }}>NOT INVOLVED — Historical dataset analysis</div>
                </div>
              </div>

              <div className="signal-item boundary">
                <span className="signal-icon">⊘</span>
                <div>
                  <strong>Automated Fraud Enforcement</strong>
                  <div className="signal-subtext" style={{ color: "var(--ink-tertiary)" }}>NOT TRIGGERED — Human decision required</div>
                </div>
              </div>

              <div className="signal-item boundary">
                <span className="signal-icon">⊘</span>
                <div>
                  <strong>AI Detection Override</strong>
                  <div className="signal-subtext" style={{ color: "var(--ink-tertiary)" }}>DISABLED — Gemini remains advisory</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 07 — Gemini Explanation Layer */}
      <section className="workspace-section" aria-labelledby="section-gemini-heading">
        <h2 id="section-gemini-heading" className="workspace-section-label">
          05 // AI INVESTIGATION INTELLIGENCE
        </h2>
        <div className="workspace-ai-provenance-box">
          <span className="sys-label">PROVENANCE & BOUNDARIES</span>
          <div className="workspace-ai-provenance-grid">
            <div><strong>SOURCE:</strong> Gemini Advisory Layer</div>
            <div><strong>INPUT:</strong> Deterministic Investigation Evidence</div>
            <div><strong>AUTHORITY:</strong> Advisory Only (Non-binding)</div>
            <div><strong>DECISION:</strong> Human Analyst Decision Required</div>
          </div>
        </div>

        {/* Embedded AIInvestigationBrief */}
        <AIInvestigationBrief
          merchant={detail.merchant}
          date={detail.date}
          riskLevel={detail.risk_level}
        />
      </section>

      {/* 08 — Human Review Boundary & Action Controls */}
      <section className="workspace-section" aria-labelledby="section-human-heading">
        <div className="human-boundary-card" data-testid="human-decision-boundary">
          <div className="human-boundary-header">
            <span className="sys-label-accent">06 // SYSTEM BOUNDARY</span>
            <h3 id="section-human-heading" className="headline-md" style={{ margin: "var(--space-1) 0" }}>
              Human Decision Boundary
            </h3>
            <p className="body-sm" style={{ color: "var(--ink-secondary)", maxWidth: 640 }}>
              The system detected and explained this behavioral deviation using deterministic policies and advisory AI.
              Automated fraud classification, merchant blocking, and transaction enforcement are disabled. Final assessment remains a human decision.
            </p>
          </div>

          <div className="human-boundary-actions">
            {onNavigateToMerchant && (
              <button
                type="button"
                className="filter-chip active"
                onClick={() => onNavigateToMerchant(detail.merchant)}
                id="btn-nav-merchant-rhythm"
              >
                View Merchant Rhythm →
              </button>
            )}

            {onNavigateToEvaluation && (
              <button
                type="button"
                className="filter-chip"
                onClick={onNavigateToEvaluation}
                id="btn-nav-evaluation"
              >
                View Detection Evaluation →
              </button>
            )}

            <button
              type="button"
              className="filter-chip"
              onClick={onBack}
              id="btn-back-to-index"
            >
              ← Back to Investigations Index
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
