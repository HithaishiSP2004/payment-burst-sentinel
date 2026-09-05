"use client";

import { useState, useEffect } from "react";
import type { IntegrationStatus, DemoIngestionResult, Overview } from "@/types/api";
import { getIntegrationStatus, demoIngest } from "@/lib/api";

/* ═══════════════════════════════════════════════════════════════
   INTEGRATION READINESS & PRODUCT EXPERIENCE — Phase 17
   Demonstrates canonical normalization and architectural boundaries.
   Honest representation: adapter_ready ≠ connected.
   Events terminate at canonical event creation.
   ═══════════════════════════════════════════════════════════════ */

interface IntegrationScreenProps {
  overview: Overview | null;
}

export function IntegrationScreen({ overview }: IntegrationScreenProps) {
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [demoResult, setDemoResult] = useState<DemoIngestionResult | null>(null);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoPayload, setDemoPayload] = useState<Record<string, unknown> | null>(null);
  const [copiedPayload, setCopiedPayload] = useState(false);
  const [copiedCanonical, setCopiedCanonical] = useState(false);

  useEffect(() => {
    let isMounted = true;
    getIntegrationStatus()
      .then((data) => {
        if (isMounted) setStatus(data);
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, []);

  async function handleDemoIngest() {
    setDemoLoading(true);
    setDemoResult(null);
    setDemoPayload(null);
    try {
      const result = await demoIngest();
      setDemoResult(result);
      if (result.canonical_event) {
        setDemoPayload({
          source: "demo",
          source_event_id: result.canonical_event.source_event_id,
          merchant_id: result.canonical_event.merchant_id,
          merchant_name: result.canonical_event.merchant_name,
          timestamp: result.canonical_event.timestamp,
          amount: result.canonical_event.amount,
          currency: result.canonical_event.currency,
          status: result.canonical_event.provider_status || result.canonical_event.normalized_status,
          payment_method: result.canonical_event.payment_method,
          event_type: result.canonical_event.event_type,
        });
      }
    } catch {
      setDemoResult({
        status: "rejected",
        validation_errors: ["Failed to connect to integration service"],
        pipeline_status: {
          payload_validated: false,
          canonical_event_created: false,
          historical_aggregation: "future_phase",
          detection_execution: "not_triggered",
          ai_analysis: "not_triggered",
        },
      });
    }
    setDemoLoading(false);
  }

  async function copyToClipboard(text: string, setCopied: (v: boolean) => void) {
    let success = false;
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        success = true;
      } catch {
        success = false;
      }
    }
    if (!success && typeof document !== "undefined") {
      try {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        success = document.execCommand("copy");
        document.body.removeChild(textarea);
      } catch {
        success = false;
      }
    }
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  const merchantCount = overview?.merchants_monitored ?? "—";
  const merchantDays = overview?.total_merchant_days_analyzed ?? "—";

  return (
    <div className="page-container integration-page">
      {/* ── Page Header ── */}
      <div className="page-header animate-in">
        <span className="sys-label-accent">SYSTEM READINESS // INTEGRATION BOUNDARY</span>
        <h1 className="headline-xl">Provider Normalization &amp; Ingestion Readiness</h1>
        <p className="body-md" style={{ marginTop: "var(--space-2)" }}>
          Establishing a provider-neutral canonical contract for payment activity. Incoming integration events normalize and terminate at the canonical boundary without modifying validated analytical baselines.
        </p>
      </div>

      {/* ── Section 1: Current Operational Mode ── */}
      <section className="integration-mode-card animate-in stagger-1">
        <div className="integration-mode-badge">CURRENT MODE</div>
        <h2 className="integration-mode-title">Historical Analytical Dataset</h2>
        <p className="integration-mode-detail">
          {merchantCount} merchants · {merchantDays.toLocaleString()} merchant-days analyzed
        </p>
        <p className="integration-mode-note">
          The current validated analysis operates on a frozen historical dataset.
          External integration readiness has been established for future payment sources.
        </p>
      </section>

      {/* ── Section 2: Why This Boundary Matters ── */}
      <section className="integration-why-card animate-in stagger-1" style={{ marginBottom: "var(--space-5)" }}>
        <h3 className="integration-section-label">Why This Boundary Matters</h3>
        <p className="integration-why-text">
          Payment providers expose provider-specific event formats. Payment Burst Sentinel
          prepares a provider-neutral canonical contract so future external events can be
          normalized before a future aggregation pipeline — preventing external provider
          logic from contaminating the frozen detection engine.
        </p>
      </section>

      {/* ── Responsive Two-Column Layout ── */}
      <div className="integration-layout animate-in stagger-2">
        {/* ── Left Column: Architecture & Readiness ── */}
        <div className="integration-col">
          {/* Card: Integration Readiness */}
          <section className="integration-card">
            <h3 className="integration-section-label">Integration Readiness</h3>
            {status ? (
              <div className="integration-readiness-grid">
                <div className="readiness-group">
                  <h4 className="readiness-group-title">Architecture</h4>
                  <ReadinessItem done label="Provider abstraction" />
                  <ReadinessItem done label="Canonical event normalization" />
                  <ReadinessItem done label="Payload validation" />
                  <ReadinessItem done label="Idempotency boundary" />
                </div>
                <div className="readiness-group">
                  <h4 className="readiness-group-title">Providers</h4>
                  <ReadinessItem done label="Demo integration available" />
                  <ReadinessItem
                    done={false}
                    label={`Razorpay adapter ready${status.providers.razorpay?.configured ? "" : " — credentials not configured"}`}
                  />
                  <ReadinessItem done={false} label="External ingestion — future phase" />
                  <ReadinessItem done={false} label="Live ingestion — future phase" />
                </div>
              </div>
            ) : (
              <p className="integration-loading">Loading integration status…</p>
            )}
          </section>

          {/* Card: System Architecture Diagram */}
          <section className="integration-card">
            <h3 className="integration-section-label">Architecture</h3>
            <div className="integration-architecture">
              <div className="arch-flow">
                <div className="arch-flow-section">
                  <div className="arch-flow-label">CURRENT IMPLEMENTATION</div>
                  <div className="arch-flow-steps">
                    <ArchStep label="Payment Provider" status="active" />
                    <ArchArrow />
                    <ArchStep label="Validation" status="active" />
                    <ArchArrow />
                    <ArchStep label="Canonical Event" status="active" />
                    <ArchArrow />
                    <ArchStep label="STOP" status="boundary" />
                  </div>
                  <div className="arch-stop-boundary-box" style={{ marginTop: "var(--space-2)" }}>
                    <strong>STOP // CURRENT BOUNDARY:</strong> Ingestion pipeline validates and normalizes external events into a canonical contract. Events terminate here; detection execution and baseline updates are NOT triggered.
                  </div>
                </div>

                <div className="arch-flow-divider" />

                <div className="arch-flow-section">
                  <div className="arch-flow-label future">FUTURE ARCHITECTURE</div>
                  <div className="arch-flow-steps">
                    <ArchStep label="Canonical Event" status="future" />
                    <ArchArrow muted />
                    <ArchStep label="Aggregation Pipeline" status="not-implemented" />
                    <ArchArrow muted />
                    <ArchStep label="Detection" status="future" />
                    <ArchArrow muted />
                    <ArchStep label="AI Explanation" status="future" />
                  </div>
                  <div className="arch-not-implemented">NOT IMPLEMENTED IN PHASE 16</div>
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* ── Right Column: Interactive Demo Pipeline ── */}
        <div className="integration-col">
          <section className="integration-card">
            <h3 className="integration-section-label">Demo Integration</h3>
            <p className="integration-demo-desc">
              Demonstrates the integration pipeline: raw payload → validation → normalization → canonical event.
              All output is explicitly simulated.
            </p>

            <button
              className="integration-demo-btn"
              onClick={handleDemoIngest}
              disabled={demoLoading}
              id="demo-ingest-btn"
              type="button"
            >
              {demoLoading ? "Processing…" : "Generate Demo Event"}
            </button>

            {demoResult && (
              <div className="integration-demo-result">
                {/* Validation Badge & Errors */}
                <div className="demo-stage-header">
                  <span className={`demo-stage-badge ${demoResult.status === "rejected" ? "rejected" : "validated"}`}>
                    {demoResult.status === "rejected" ? "VALIDATION FAILED" : "VALIDATION PASSED"}
                  </span>
                </div>
                {demoResult.validation_errors.length > 0 && (
                  <ul className="demo-errors">
                    {demoResult.validation_errors.map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                )}

                {/* Layer 1: Human-Readable Summary Cards */}
                {demoPayload && demoResult.canonical_event && (
                  <div className="demo-summary-grid">
                    {/* Simulated Provider Payload Card */}
                    <div className="demo-summary-card">
                      <div className="demo-summary-card-header">
                        <span className="demo-stage-badge simulated">SIMULATED PROVIDER PAYLOAD</span>
                      </div>
                      <div className="demo-summary-meta-list">
                        <div className="demo-summary-row">
                          <span className="demo-summary-row-label">Merchant</span>
                          <span className="demo-summary-row-val">{String(demoPayload.merchant_name || demoPayload.merchant_id)}</span>
                        </div>
                        <div className="demo-summary-row">
                          <span className="demo-summary-row-label">Amount</span>
                          <span className="demo-summary-row-val">{String(demoPayload.currency)} {String(demoPayload.amount)}</span>
                        </div>
                        <div className="demo-summary-row">
                          <span className="demo-summary-row-label">Method</span>
                          <span className="demo-summary-row-val">{String(demoPayload.payment_method || "N/A")}</span>
                        </div>
                        <div className="demo-summary-row">
                          <span className="demo-summary-row-label">Status</span>
                          <span className="demo-summary-row-val">{String(demoPayload.status)}</span>
                        </div>
                        <div className="demo-summary-row">
                          <span className="demo-summary-row-label">Source ID</span>
                          <span className="demo-summary-row-val tech-val-id" title={String(demoPayload.source_event_id)}>
                            {String(demoPayload.source_event_id)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Canonical Event Card */}
                    <div className="demo-summary-card canonical">
                      <div className="demo-summary-card-header">
                        <span className="demo-stage-badge canonical">CANONICAL EVENT</span>
                      </div>
                      <div className="demo-summary-meta-list">

                        <div className="demo-summary-row">
                          <span className="demo-summary-row-label">Canonical ID</span>
                          <span className="demo-summary-row-val tech-val-id" title={demoResult.canonical_event.event_id}>
                            {formatShortId(demoResult.canonical_event.event_id)}
                          </span>
                        </div>
                        <div className="demo-summary-row">
                          <span className="demo-summary-row-label">Amount (Decimal)</span>
                          <span className="demo-summary-row-val">
                            {demoResult.canonical_event.currency} {demoResult.canonical_event.amount}
                          </span>
                        </div>
                        <div className="demo-summary-row">
                          <span className="demo-summary-row-label">Normalized Status</span>
                          <span className="demo-summary-row-val">{demoResult.canonical_event.normalized_status}</span>
                        </div>
                        <div className="demo-summary-row">
                          <span className="demo-summary-row-label">Timestamp (UTC)</span>
                          <span className="demo-summary-row-val tech-val-timestamp" title={demoResult.canonical_event.timestamp}>
                            {formatDemoTimestamp(demoResult.canonical_event.timestamp)}
                          </span>
                        </div>
                        <div className="demo-summary-row">
                          <span className="demo-summary-row-label">Schema Version</span>
                          <span className="demo-summary-row-val">{demoResult.canonical_event.schema_version}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Layer 2: Field Normalization Matrix */}
                {demoPayload && demoResult.canonical_event && (
                  <div className="transformation-matrix-card">
                    <div style={{ padding: "var(--space-2) var(--space-3)", background: "var(--surface-1)", borderBottom: "1px solid var(--surface-2)" }}>
                      <span className="readiness-group-title">Field Transformation Matrix</span>
                    </div>
                    <div className="table-scroll">
                      <table className="transformation-table" aria-label="Field transformation matrix">
                        <thead>
                          <tr>
                            <th scope="col">Provider Input</th>
                            <th scope="col">Transformation Rule</th>
                            <th scope="col">Canonical Output</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>amount ({String(demoPayload.amount)})</td>
                            <td className="transformation-rule">Decimal string preservation</td>
                            <td>{demoResult.canonical_event.amount}</td>
                          </tr>
                          <tr>
                            <td>timestamp</td>
                            <td className="transformation-rule">Normalized to UTC (ISO-8601)</td>
                            <td>{demoResult.canonical_event.timestamp}</td>
                          </tr>
                          <tr>
                            <td>status ({String(demoPayload.status)})</td>
                            <td className="transformation-rule">Canonical status mapping</td>
                            <td>{demoResult.canonical_event.normalized_status}</td>
                          </tr>
                          <tr>
                            <td>source_event_id</td>
                            <td className="transformation-rule">Preserved for idempotency key</td>
                            <td>{demoResult.canonical_event.source_event_id}</td>
                          </tr>
                          <tr>
                            <td>generated event</td>
                            <td className="transformation-rule">Canonical UUID assigned</td>
                            <td>{demoResult.canonical_event.event_id.slice(0, 18)}…</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Layer 3: Expandable Raw Technical Disclosures */}
                {demoPayload && (
                  <details className="raw-json-disclosure">
                    <summary className="raw-json-summary">
                      <span>View Raw Simulated Payload (JSON)</span>
                      <div className="raw-json-header-action" onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          className={`copy-payload-btn ${copiedPayload ? "copied" : ""}`}
                          onClick={() => copyToClipboard(JSON.stringify(demoPayload, null, 2), setCopiedPayload)}
                          aria-label="Copy raw payload JSON"
                        >
                          {copiedPayload ? "Copied!" : "Copy"}
                        </button>
                      </div>
                    </summary>
                    <pre className="demo-code-block">{JSON.stringify(demoPayload, null, 2)}</pre>
                  </details>
                )}

                {demoResult.canonical_event && (
                  <details className="raw-json-disclosure">
                    <summary className="raw-json-summary">
                      <span>View Full Canonical Event (JSON)</span>
                      <div className="raw-json-header-action" onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          className={`copy-payload-btn ${copiedCanonical ? "copied" : ""}`}
                          onClick={() => copyToClipboard(JSON.stringify(demoResult.canonical_event, null, 2), setCopiedCanonical)}
                          aria-label="Copy canonical event JSON"
                        >
                          {copiedCanonical ? "Copied!" : "Copy"}
                        </button>
                      </div>
                    </summary>
                    <pre className="demo-code-block">{JSON.stringify(demoResult.canonical_event, null, 2)}</pre>
                  </details>
                )}

                {/* Pipeline status — MANDATORY */}
                <div className="demo-pipeline-status">
                  <div className="demo-stage-header">
                    <span className="demo-stage-badge pipeline">PIPELINE STATUS</span>
                  </div>
                  <div className="pipeline-items">
                    <PipelineItem done={demoResult.pipeline_status.payload_validated} label="Payload validated" />
                    <PipelineItem done={demoResult.pipeline_status.canonical_event_created} label="Canonical event created" />
                    <PipelineItem done={false} label="Historical aggregation — future phase" muted />
                    <PipelineItem
                      done={false}
                      label="Detection execution"
                      statusTag={demoResult.pipeline_status.detection_execution.toUpperCase().replace("_", " ")}
                      notTriggered
                    />
                    <PipelineItem
                      done={false}
                      label="AI analysis"
                      statusTag={demoResult.pipeline_status.ai_analysis.toUpperCase().replace("_", " ")}
                      notTriggered
                    />
                  </div>
                </div>

                {demoResult.status === "duplicate" && (
                  <div className="demo-duplicate-note">
                    Duplicate event detected — previously processed as {demoResult.duplicate_of}
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

/* ─── Sub-components ──────────────────────────────────────── */

function ReadinessItem({ done, label }: { done: boolean; label: string }) {
  return (
    <div className={`readiness-item ${done ? "done" : "pending"}`}>
      <span className="readiness-icon">{done ? "✓" : "○"}</span>
      <span className="readiness-label">{label}</span>
    </div>
  );
}

function PipelineItem({
  done,
  label,
  muted,
  notTriggered,
  statusTag,
}: {
  done: boolean;
  label: string;
  muted?: boolean;
  notTriggered?: boolean;
  statusTag?: string;
}) {
  return (
    <div className={`pipeline-item ${done ? "done" : "pending"} ${muted ? "muted" : ""} ${notTriggered ? "not-triggered" : ""}`}>
      <span className="pipeline-icon">{done ? "✓" : "○"}</span>
      <span className="pipeline-label">
        {label}
        {statusTag ? (
          <>
            {" — "}
            <span className={notTriggered ? "pipeline-tag-not-triggered" : ""}>
              {statusTag}
            </span>
          </>
        ) : null}
      </span>
    </div>
  );
}

function ArchStep({ label, status }: { label: string; status: string }) {
  return <div className={`arch-step arch-step-${status}`}>{label}</div>;
}

function ArchArrow({ muted }: { muted?: boolean }) {
  return (
    <div className={`arch-arrow ${muted ? "muted" : ""}`}>
      <span className="arch-arrow-h" aria-hidden="true">→</span>
      <span className="arch-arrow-v" aria-hidden="true">↓</span>
    </div>
  );
}

function formatShortId(id: string): string {
  if (!id) return "";
  if (id.length <= 16) return id;
  return `${id.slice(0, 8)}…${id.slice(-4)}`;
}

function formatDemoTimestamp(ts: string): string {
  if (!ts) return "";
  try {
    const [datePart, timePart] = ts.split("T");
    if (!timePart) return ts;
    const timeClean = timePart.split(".")[0].split("+")[0].replace("Z", "");
    return `${datePart} ${timeClean}`;
  } catch {
    return ts;
  }
}
