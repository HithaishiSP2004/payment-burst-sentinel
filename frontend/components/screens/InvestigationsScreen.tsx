"use client";

import type { InvestigationsResponse } from "@/types/api";
import { LoadingState } from "@/components/shared/LoadingState";
import { EmptyState } from "@/components/shared/EmptyState";
import { formatMads, formatSignalDominance } from "@/lib/utils";
import { InvestigationDetailWorkspace } from "./InvestigationDetailWorkspace";

interface InvestigationsScreenProps {
  data: InvestigationsResponse | null;
  riskFilter: string | null;
  typeFilter: string | null;
  setRiskFilter: (v: string | null) => void;
  setTypeFilter: (v: string | null) => void;
  onMerchantClick: (name: string) => void;
  currentPage: number;
  onPageChange: (page: number) => void;
  selectedInvestigation?: { merchant: string; date: string } | null;
  onSelectInvestigation?: (event: { merchant: string; date: string } | null) => void;
  onNavigateToMerchant?: (merchant: string) => void;
  onNavigateToEvaluation?: () => void;
}

const PAGE_SIZE = 20;

export function InvestigationsScreen({
  data,
  riskFilter,
  typeFilter,
  setRiskFilter,
  setTypeFilter,
  onMerchantClick,
  currentPage,
  onPageChange,
  selectedInvestigation,
  onSelectInvestigation,
  onNavigateToMerchant,
  onNavigateToEvaluation,
}: InvestigationsScreenProps) {
  if (selectedInvestigation) {
    return (
      <InvestigationDetailWorkspace
        merchant={selectedInvestigation.merchant}
        date={selectedInvestigation.date}
        onBack={() => onSelectInvestigation ? onSelectInvestigation(null) : undefined}
        onNavigateToMerchant={onNavigateToMerchant || onMerchantClick}
        onNavigateToEvaluation={onNavigateToEvaluation}
      />
    );
  }

  if (!data) return <div className="page-container"><LoadingState label="Retrieving investigation records..." /></div>;

  const totalPages = Math.ceil(data.total / PAGE_SIZE);

  // Generate page numbers to display
  function getPageNumbers(): (number | "...")[] {
    const pages: (number | "...")[] = [];
    const maxVisible = 7;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push("...");

      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      for (let i = start; i <= end; i++) pages.push(i);

      if (currentPage < totalPages - 2) pages.push("...");
      pages.push(totalPages);
    }

    return pages;
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <span className="sys-label-accent">INVESTIGATION INDEX</span>
        <h1 className="headline-lg">Behavioral Anomalies</h1>
        <p className="body-md">
          A chronological record of behavioral deviations identified by the frozen detection policy.
        </p>
      </div>

      {/* Filters */}
      <div className="filter-bar" role="toolbar" aria-label="Filter controls">
        <div className="filter-group" role="group" aria-label="Risk level filter">
          <span className="filter-group-label">RISK</span>
          <button className={`filter-chip ${!riskFilter ? "active" : ""}`} onClick={() => setRiskFilter(null)} aria-pressed={!riskFilter}>All</button>
          <button className={`filter-chip ${riskFilter === "high" ? "active" : ""}`} onClick={() => setRiskFilter(riskFilter === "high" ? null : "high")} aria-pressed={riskFilter === "high"}>High</button>
          <button className={`filter-chip ${riskFilter === "elevated" ? "active" : ""}`} onClick={() => setRiskFilter(riskFilter === "elevated" ? null : "elevated")} aria-pressed={riskFilter === "elevated"}>Elevated</button>
        </div>

        <div className="filter-separator" />

        <div className="filter-group" role="group" aria-label="Signal type filter">
          <span className="filter-group-label">SIGNAL</span>
          <button className={`filter-chip ${!typeFilter ? "active" : ""}`} onClick={() => setTypeFilter(null)} aria-pressed={!typeFilter}>All</button>
          <button className={`filter-chip ${typeFilter === "amount_anomaly" ? "active" : ""}`} onClick={() => setTypeFilter(typeFilter === "amount_anomaly" ? null : "amount_anomaly")} aria-pressed={typeFilter === "amount_anomaly"}>Amount</button>
          <button className={`filter-chip ${typeFilter === "velocity_anomaly" ? "active" : ""}`} onClick={() => setTypeFilter(typeFilter === "velocity_anomaly" ? null : "velocity_anomaly")} aria-pressed={typeFilter === "velocity_anomaly"}>Volume</button>
          <button className={`filter-chip ${typeFilter === "combined_anomaly" ? "active" : ""}`} onClick={() => setTypeFilter(typeFilter === "combined_anomaly" ? null : "combined_anomaly")} aria-pressed={typeFilter === "combined_anomaly"}>Combined</button>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
        <span className="sys-label">
          {data.total.toLocaleString()} EVENTS
        </span>
        <span className="body-sm" style={{ color: "var(--ink-ghost)" }}>
          Page {currentPage} of {totalPages}
        </span>
      </div>

      {data.events.length === 0 ? (
        <EmptyState message="No deviations match the current filters. Try adjusting risk level or signal type." />
      ) : (
        <div className="investigation-list" role="list" aria-label="Investigation events">
          {data.events.map((event) => (
            <div key={`${event.merchant}-${event.date}`} className="investigation-item" role="listitem"
              onClick={() => {
                if (onSelectInvestigation) {
                  onSelectInvestigation({ merchant: event.merchant, date: event.date });
                } else {
                  onMerchantClick(event.merchant);
                }
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  if (onSelectInvestigation) {
                    onSelectInvestigation({ merchant: event.merchant, date: event.date });
                  } else {
                    onMerchantClick(event.merchant);
                  }
                }
              }}
              tabIndex={0} aria-label={`${event.merchant}, ${event.date}, ${event.composite_deviation.toFixed(1)} MADs`}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)", flexWrap: "wrap" }}>
                  <span className="investigation-merchant">{event.merchant}</span>
                  <span className={`risk-badge risk-${event.risk_level}`}>{event.risk_level.toUpperCase()}</span>
                </div>

                {event.amount_deviation > 0 && (
                  <div className="evidence-block primary">
                    <div className="evidence-label primary">PRIMARY SIGNAL</div>
                    <div className="evidence-value">
                      Payment value <strong>₹{event.total_amount.toLocaleString("en-IN")}</strong> vs expected <strong>~₹{event.expected_total_amount.toLocaleString("en-IN")}</strong>
                      <span className="evidence-deviation high"> {formatMads(event.amount_deviation)}</span>
                    </div>
                  </div>
                )}

                {event.velocity_deviation > 0 && (
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
                <div className="investigation-deviation-label">COMPOSITE SIGNAL</div>
                <span className="anomaly-tag" style={{ marginTop: 2 }}>
                  {formatSignalDominance(event.anomaly_type)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <nav aria-label="Pagination" style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 4,
          marginTop: "var(--space-6)",
          paddingBottom: "var(--space-4)",
        }}>
          <button
            className="filter-chip"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            aria-label="Previous page"
            style={{ opacity: currentPage <= 1 ? 0.3 : 1 }}
          >
            ← Prev
          </button>

          {getPageNumbers().map((page, i) =>
            page === "..." ? (
              <span key={`ellipsis-${i}`} style={{ padding: "4px 8px", color: "var(--ink-ghost)", fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>…</span>
            ) : (
              <button
                key={page}
                className={`filter-chip ${page === currentPage ? "active" : ""}`}
                onClick={() => onPageChange(page)}
                aria-label={`Page ${page}`}
                aria-current={page === currentPage ? "page" : undefined}
                style={{
                  minWidth: 36,
                  textAlign: "center",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.75rem",
                }}
              >
                {page}
              </button>
            )
          )}

          <button
            className="filter-chip"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            aria-label="Next page"
            style={{ opacity: currentPage >= totalPages ? 0.3 : 1 }}
          >
            Next →
          </button>
        </nav>
      )}
    </div>
  );
}
