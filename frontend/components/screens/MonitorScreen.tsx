"use client";

import type { Overview, InvestigationsResponse } from "@/types/api";
import { LoadingState } from "@/components/shared/LoadingState";
import { EmptyState } from "@/components/shared/EmptyState";
import { formatMads, formatCurrencyRound } from "@/lib/utils";

interface MonitorScreenProps {
  overview: Overview | null;
  investigations: InvestigationsResponse | null;
  onMerchantClick: (name: string) => void;
  onInvestigationClick?: (merchant: string, date: string) => void;
}

export function MonitorScreen({ overview, investigations, onMerchantClick, onInvestigationClick }: MonitorScreenProps) {
  if (!overview) return <div className="page-container"><LoadingState label="Retrieving system overview..." /></div>;

  const topEvents = investigations?.events?.slice(0, 5) || [];
  const amountPct = Math.round((overview.anomaly_types.amount / overview.total_flagged_events) * 100);

  return (
    <div className="page-container">
      <div className="page-header animate-in">
        <span className="sys-label-accent">BEHAVIORAL INTELLIGENCE // SYSTEM OVERVIEW</span>
        <h1 className="headline-xl">Payment activity<br />under observation.</h1>
        <p className="body-md" style={{ marginTop: "var(--space-2)" }}>
          Monitoring {overview.merchants_monitored} merchants against their own behavioral baselines.
          {" "}{overview.total_flagged_events.toLocaleString()} behavioral deviations identified across {overview.total_merchant_days_analyzed.toLocaleString()} merchant-days.
        </p>
      </div>

      {/* Enrichment finding */}
      <div className="grid-asymmetric animate-in stagger-1">
        <div className="surface-elevated">
          <span className="sys-label" style={{ display: "block", marginBottom: "var(--space-3)" }}>EVALUATION FINDING</span>
          <div style={{ display: "flex", alignItems: "baseline", gap: "var(--space-2)", marginBottom: "var(--space-3)", flexWrap: "wrap" }}>
            <span className="metric-hero" style={{ color: "var(--accent-primary)" }}>{overview.enrichment.vs_normal}×</span>
            <span className="body-md" style={{ color: "var(--ink-secondary)" }}>fraud-containing rate among flagged activity</span>
          </div>
          <p className="body-sm" style={{ maxWidth: 520 }}>
            Flagged merchant-days contain fraud at {overview.enrichment.vs_normal}× the rate of behaviorally normal days.
            Merchant-specific behavioral context outperforms simple volume flagging by {(overview.enrichment.vs_normal / 1.83).toFixed(1)}×.
          </p>
          <div className="methodology-notice" style={{ marginTop: "var(--space-4)" }}>
            <strong>Correlation, not causation.</strong> Enrichment measures statistical association between behavioral deviations and fraud-containing periods. Anomaly ≠ confirmed fraud.
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <div className="surface">
            <div className="metric-block">
              <span className="sys-label">BEHAVIORAL DEVIATIONS</span>
              <span className="metric-lg">{overview.total_flagged_events.toLocaleString()}</span>
              <span className="body-sm">across {overview.total_merchant_days_analyzed.toLocaleString()} merchant-days</span>
            </div>
          </div>

          <div className="surface">
            <div className="metric-block">
              <span className="sys-label">RISK DISTRIBUTION</span>
              <div style={{ display: "flex", gap: "var(--space-5)", marginTop: "var(--space-2)" }}>
                <div>
                  <span className="metric-md" style={{ color: "var(--risk-elevated)" }}>{overview.elevated_events.toLocaleString()}</span>
                  <div className="sys-label" style={{ fontSize: "0.5rem", marginTop: 2 }}>ELEVATED</div>
                </div>
                <div>
                  <span className="metric-md" style={{ color: "var(--risk-high)" }}>{overview.high_events.toLocaleString()}</span>
                  <div className="sys-label" style={{ fontSize: "0.5rem", marginTop: 2 }}>HIGH</div>
                </div>
              </div>
            </div>
          </div>

          <div className="surface">
            <div className="metric-block">
              <span className="sys-label">PRIMARY SIGNAL DOMINANCE</span>
              <span className="metric-md">{amountPct}%</span>
              <span className="body-sm">of flags driven by amount deviation</span>
            </div>
          </div>
        </div>
      </div>

      {/* Strongest deviations */}
      <hr className="section-rule" />

      <div className="animate-in stagger-2">
        <span className="sys-label-accent" style={{ display: "block", marginBottom: "var(--space-4)" }}>STRONGEST BEHAVIORAL DEVIATIONS</span>

        {topEvents.length === 0 ? (
          <EmptyState message="No behavioral deviations detected in the current dataset." />
        ) : (
          <div className="investigation-list" role="list" aria-label="Top behavioral deviations">
            {topEvents.map((event) => (
              <div key={`${event.merchant}-${event.date}`} className="investigation-item" role="listitem"
                onClick={() => {
                  if (onInvestigationClick) {
                    onInvestigationClick(event.merchant, event.date);
                  } else {
                    onMerchantClick(event.merchant);
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    if (onInvestigationClick) {
                      onInvestigationClick(event.merchant, event.date);
                    } else {
                      onMerchantClick(event.merchant);
                    }
                  }
                }}
                tabIndex={0} aria-label={`${event.merchant}, ${event.risk_level} risk, ${event.composite_deviation.toFixed(1)} MADs`}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)", flexWrap: "wrap" }}>
                    <span className="investigation-merchant">{event.merchant}</span>
                    <span className={`risk-badge risk-${event.risk_level}`}>{event.risk_level.toUpperCase()}</span>
                    <span className="anomaly-tag">{event.anomaly_type === "amount_anomaly" ? "AMOUNT SHIFT" : event.anomaly_type === "combined_anomaly" ? "COMBINED" : "VOLUME SHIFT"}</span>
                  </div>

                  {event.amount_deviation >= 1 && (
                    <div className="evidence-block primary">
                      <div className="evidence-label primary">PRIMARY SIGNAL</div>
                      <div className="evidence-value">
                        Payment value <strong>{formatCurrencyRound(event.total_amount, (event as any).currency)}</strong> vs expected <strong>~{formatCurrencyRound(event.expected_total_amount, (event as any).currency)}</strong>
                        <span className="evidence-deviation high"> {formatMads(event.amount_deviation)}</span>
                      </div>
                    </div>
                  )}

                  {event.velocity_deviation >= 1 && (
                    <div className="evidence-block">
                      <div className="evidence-label context">BEHAVIORAL CONTEXT</div>
                      <div className="evidence-value">
                        {event.transaction_count} transactions vs expected ~{event.expected_tx_count}
                        <span className="evidence-deviation context"> {formatMads(event.velocity_deviation)}</span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="investigation-meta">
                  <div className="investigation-date">{event.date}</div>
                  <div className="investigation-deviation">{event.composite_deviation.toFixed(1)}</div>
                  <div className="investigation-deviation-label">MADs ABOVE BASELINE</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="methodology-notice animate-in stagger-3" style={{ marginTop: "var(--space-6)" }}>
        <strong>Investigation note:</strong> This system identifies unusual payment behavior relative to each merchant&apos;s own historical pattern. Flagged events require human investigation to determine their cause.
      </div>
    </div>
  );
}
