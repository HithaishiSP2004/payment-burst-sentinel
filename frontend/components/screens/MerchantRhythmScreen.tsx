"use client";

import { useState, useEffect, useRef } from "react";
import type { MerchantRhythm } from "@/types/api";
import { LoadingState } from "@/components/shared/LoadingState";
import { EmptyState } from "@/components/shared/EmptyState";
import { isAnomaly, formatAnomalyType, getTooltipStyle } from "@/lib/utils";
import { searchMerchants } from "@/lib/api";
import { AIInvestigationBrief } from "@/components/ai/AIInvestigationBrief";

interface MerchantRhythmScreenProps {
  rhythm: MerchantRhythm | null;
  merchantName: string | null;
  onSelectMerchant: (name: string) => void;
  loading: boolean;
  error: string | null;
  quickMerchants?: string[];
  onOpenInvestigation?: (merchant: string, date: string) => void;
}

export function MerchantRhythmScreen({ rhythm, merchantName, onSelectMerchant, loading, error, quickMerchants, onOpenInvestigation }: MerchantRhythmScreenProps) {
  const [searchInput, setSearchInput] = useState("");
  const [hoveredBar, setHoveredBar] = useState<number | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<{ date: string; risk_level: string } | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const anomalyDays = rhythm?.timeline?.filter((d) => isAnomaly(d.anomaly_type)) || [];
  const chartData = rhythm?.timeline?.slice(-60) || [];
  const maxAmt = Math.max(...chartData.map((d) => d.total_amount || 0), 1);
  const barCount = chartData.length;

  // Fetch suggestions as user types
  useEffect(() => {
    const q = searchInput.trim();
    if (q.length < 1) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const results = await searchMerchants(q);
        setSuggestions(results);
        setShowSuggestions(results.length > 0);
        setActiveSuggestion(-1);
      } catch {
        setSuggestions([]);
      }
    }, 200); // 200ms debounce

    return () => clearTimeout(timer);
  }, [searchInput]);

  // Close suggestions on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target as Node) &&
          inputRef.current && !inputRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function selectMerchant(name: string) {
    onSelectMerchant(name);
    setSearchInput("");
    setShowSuggestions(false);
    setSuggestions([]);
    setSelectedEvent(null); // Clear AI panel when switching merchants
  }

  function handleSearch() {
    const q = searchInput.trim();
    if (q) {
      selectMerchant(q);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveSuggestion((prev) => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveSuggestion((prev) => Math.max(prev - 1, -1));
    } else if (e.key === "Enter") {
      if (activeSuggestion >= 0 && activeSuggestion < suggestions.length) {
        selectMerchant(suggestions[activeSuggestion]);
      } else {
        handleSearch();
      }
    } else if (e.key === "Escape") {
      setShowSuggestions(false);
    }
  }

  // Highlight matching text in suggestion
  function highlightMatch(text: string, query: string) {
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx === -1) return <>{text}</>;
    return (
      <>
        {text.slice(0, idx)}
        <strong style={{ color: "var(--accent-warm)" }}>{text.slice(idx, idx + query.length)}</strong>
        {text.slice(idx + query.length)}
      </>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <span className="sys-label-accent">MERCHANT PROFILE</span>
        <h1 className="headline-lg" style={{ wordBreak: "break-word" }}>{merchantName || "Merchant Rhythm"}</h1>
        {rhythm && (
          <div className="merchant-header-meta" style={{ display: "flex", gap: "var(--space-5)", marginTop: "var(--space-3)", flexWrap: "wrap" }}>
            <span className="sys-label">{rhythm.total_days}-DAY OBSERVATION</span>
            <span className="sys-label">{rhythm.anomaly_days} DETECTED DEVIATIONS</span>
            <span className="sys-label">AVG {rhythm.avg_daily_tx} TX/DAY</span>
          </div>
        )}
        {!rhythm && !merchantName && !loading && (
          <p className="body-md">
            Normal is different for every merchant. Search a merchant name to explore their behavioral profile.
          </p>
        )}
      </div>

      {/* Search with autocomplete */}
      <label htmlFor="merchant-search" className="sys-label" style={{ display: "block", marginBottom: "var(--space-2)" }}>SEARCH MERCHANT</label>
      <div style={{ position: "relative" }}>
        <input
          ref={inputRef}
          id="merchant-search"
          type="text"
          className="search-input"
          placeholder="Enter merchant name..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => { if (suggestions.length > 0) setShowSuggestions(true); }}
          aria-label="Search merchant by name"
          autoComplete="off"
          role="combobox"
          aria-expanded={showSuggestions}
          aria-controls="merchant-suggestions"
          aria-activedescendant={activeSuggestion >= 0 ? `suggestion-${activeSuggestion}` : undefined}
        />

        {/* Suggestions dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div
            ref={suggestionsRef}
            id="merchant-suggestions"
            role="listbox"
            style={{
              position: "absolute",
              top: "100%",
              left: 0,
              right: 0,
              background: "var(--surface-canvas)",
              border: "1px solid var(--surface-2)",
              borderTop: "none",
              borderRadius: "0 0 var(--radius-sm) var(--radius-sm)",
              maxHeight: 280,
              overflowY: "auto",
              zIndex: 20,
              boxShadow: "0 8px 24px rgba(0,0,0,0.08)",
            }}
          >
            {suggestions.map((name, i) => (
              <div
                key={name}
                id={`suggestion-${i}`}
                role="option"
                aria-selected={i === activeSuggestion}
                onClick={() => selectMerchant(name)}
                style={{
                  padding: "10px 16px",
                  cursor: "pointer",
                  fontSize: "0.875rem",
                  fontFamily: "var(--font-mono)",
                  letterSpacing: "0.02em",
                  background: i === activeSuggestion ? "var(--surface-1)" : "transparent",
                  borderBottom: i < suggestions.length - 1 ? "1px solid var(--surface-1)" : "none",
                  transition: "background 100ms ease",
                }}
                onMouseEnter={() => setActiveSuggestion(i)}
              >
                {highlightMatch(name, searchInput.trim())}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Loading */}
      {loading && <LoadingState label={`Retrieving behavioral data for ${merchantName}...`} />}

      {/* Error */}
      {error && !loading && (
        <div style={{ marginTop: "var(--space-6)" }}>
          <EmptyState message={error} />
        </div>
      )}

      {/* Data */}
      {rhythm && !loading && (
        <>
          <div className="grid-3" style={{ margin: "var(--space-6) 0" }}>
            <div className="surface">
              <div className="metric-block">
                <span className="sys-label">OBSERVATION PERIOD</span>
                <span className="metric-lg">{rhythm.total_days}</span>
                <span className="body-sm">days analyzed</span>
              </div>
            </div>
            <div className="surface">
              <div className="metric-block">
                <span className="sys-label">AVERAGE DAILY VALUE</span>
                <span className="metric-lg">₹{rhythm.avg_daily_amount.toFixed(0)}</span>
                <span className="body-sm">{rhythm.avg_daily_tx} transactions / day</span>
              </div>
            </div>
            <div className="surface-elevated">
              <div className="metric-block">
                <span className="sys-label">ANOMALY DAYS</span>
                <span className="metric-lg" style={{ color: rhythm.anomaly_days > 0 ? "var(--risk-elevated)" : "var(--risk-normal)" }}>
                  {rhythm.anomaly_days}
                </span>
                <span className="body-sm">behavioral deviations</span>
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="chart-wrapper" role="figure" aria-label="Daily payment value chart">
            <div className="chart-header">
              <span className="sys-label-lg">DAILY PAYMENT VALUE — OBSERVED vs EXPECTED</span>
              <div className="chart-legend">
                <div className="chart-legend-item"><div className="chart-legend-dot" style={{ background: "var(--ink-primary)", opacity: 0.2 }} /> OBSERVED</div>
                <div className="chart-legend-item"><div className="chart-legend-dot" style={{ background: "var(--accent-primary)" }} /> EXPECTED</div>
                <div className="chart-legend-item"><div className="chart-legend-dot" style={{ background: "var(--risk-high)" }} /> ANOMALY</div>
              </div>
            </div>

            <div style={{ position: "relative" }}>
              <div style={{ display: "flex", gap: 1, alignItems: "end", height: 200 }}>
                {chartData.map((day, i) => {
                  const obsHeight = Math.max((day.total_amount / maxAmt) * 180, 1);
                  const expHeight = day.expected_total_amount ? (day.expected_total_amount / maxAmt) * 180 : 0;
                  const dayIsAnomaly = isAnomaly(day.anomaly_type);
                  const isHovered = hoveredBar === i;

                  return (
                    <div key={i}
                      style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", position: "relative", cursor: "crosshair" }}
                      onMouseEnter={() => setHoveredBar(i)}
                      onMouseLeave={() => setHoveredBar(null)}
                      role="img" aria-label={`${day.date}: ₹${day.total_amount?.toFixed(0) ?? 0}`}
                    >
                      {dayIsAnomaly && (
                        <div style={{ width: 4, height: 4, borderRadius: "50%", background: "var(--risk-high)", marginBottom: 3, flexShrink: 0 }} />
                      )}

                      <div style={{
                        width: "100%", height: obsHeight,
                        background: dayIsAnomaly ? "var(--risk-high)" : "var(--ink-primary)",
                        opacity: dayIsAnomaly ? 0.7 : (isHovered ? 0.3 : 0.12),
                        borderRadius: "1px 1px 0 0",
                        transition: "opacity 150ms ease",
                      }} />

                      {expHeight > 0 && (
                        <div style={{
                          position: "absolute", bottom: 0, left: 0, right: 0, height: 2,
                          background: "var(--accent-primary)", opacity: 0.4,
                          transform: `translateY(-${expHeight}px)`,
                        }} />
                      )}

                      {isHovered && (
                        <div style={getTooltipStyle(i, barCount, obsHeight)}>
                          <div style={{ marginBottom: 4, fontWeight: 600 }}>{day.date}</div>
                          <div>OBSERVED: ₹{day.total_amount?.toFixed(0) ?? "N/A"}</div>
                          {day.expected_total_amount != null && <div>EXPECTED: ~₹{day.expected_total_amount?.toFixed(0)}</div>}
                          {day.amount_deviation > 0 && <div style={{ color: "var(--accent-warm)" }}>AMOUNT DEV: +{day.amount_deviation?.toFixed(1)} MADs</div>}
                          {dayIsAnomaly && <div style={{ color: "#ff8a80", marginTop: 2 }}>● {day.anomaly_type?.replace("_", " ").toUpperCase()}</div>}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: "var(--space-2)" }}>
                <span className="body-sm">{chartData[0]?.date}</span>
                <span className="body-sm">{chartData[chartData.length - 1]?.date}</span>
              </div>
            </div>
          </div>

          {/* Recent deviations — clickable for AI investigation */}
          {anomalyDays.length > 0 && (
            <div style={{ marginTop: "var(--space-6)" }}>
              <span className="sys-label-accent" style={{ display: "block", marginBottom: "var(--space-3)" }}>RECENT DEVIATIONS</span>
              <span className="body-sm" style={{ display: "block", marginBottom: "var(--space-3)", color: "var(--ink-ghost)" }}>
                Click a deviation to generate an AI investigation brief.
              </span>
              <div className="investigation-list" role="list" aria-label="Recent deviations">
                {anomalyDays.slice(-10).reverse().map((day, i) => {
                  const isSelected = selectedEvent?.date === day.date;
                  // Determine risk level from deviation
                  const riskLevel = (day.amount_deviation >= 5 || day.velocity_deviation >= 5) ? "high" : "elevated";
                  return (
                    <div
                      key={i}
                      role="listitem"
                      tabIndex={0}
                      onClick={() => setSelectedEvent(isSelected ? null : { date: day.date, risk_level: riskLevel })}
                      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setSelectedEvent(isSelected ? null : { date: day.date, risk_level: riskLevel }); } }}
                      style={{
                        padding: "var(--space-3) var(--space-5)",
                        borderBottom: i < Math.min(anomalyDays.length, 10) - 1 ? "1px solid var(--surface-2)" : "none",
                        display: "grid", gridTemplateColumns: "auto 1fr auto", gap: "var(--space-3)", alignItems: "center",
                        cursor: "pointer",
                        background: isSelected ? "var(--accent-subtle)" : "transparent",
                        borderLeft: isSelected ? "3px solid var(--accent-primary)" : "3px solid transparent",
                        transition: "background 150ms ease, border-left 150ms ease",
                      }}
                      aria-label={`${day.date}: ${day.anomaly_type?.replace("_", " ")}${isSelected ? " (selected)" : ""}`}
                    >
                      <span className="metric-sm" style={{ minWidth: 80 }}>{day.date}</span>
                      <span className="anomaly-tag">{formatAnomalyType(day.anomaly_type)}</span>
                      <span className="body-sm" style={{ textAlign: "right" }}>
                        <strong>₹{day.total_amount?.toFixed(0) ?? "—"}</strong> observed vs <strong>₹{day.expected_total_amount?.toFixed(0) ?? "—"}</strong> expected
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {anomalyDays.length === 0 && (
            <div style={{ marginTop: "var(--space-6)" }}>
              <EmptyState message="No recent deviations recorded for this observation period." />
            </div>
          )}

          {/* AI Investigation Brief — shown when an event is selected */}
          {selectedEvent && merchantName && (
            <div style={{ marginTop: "var(--space-5)" }}>
              {onOpenInvestigation && (
                <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "var(--space-2)" }}>
                  <button
                    type="button"
                    className="workspace-back-btn"
                    onClick={() => onOpenInvestigation(merchantName, selectedEvent.date)}
                    style={{ fontSize: "0.75rem" }}
                  >
                    Open Investigation Workspace for {selectedEvent.date} →
                  </button>
                </div>
              )}
              <AIInvestigationBrief
                merchant={merchantName}
                date={selectedEvent.date}
                riskLevel={selectedEvent.risk_level}
              />
            </div>
          )}
        </>
      )}

      {!rhythm && !merchantName && !loading && !error && (
        <div style={{ textAlign: "center", padding: "var(--space-9) 0" }}>
          <div className="headline-md" style={{ color: "var(--ink-ghost)", marginBottom: "var(--space-3)" }}>Select a merchant</div>
          <p className="body-md">Search above or click a merchant name from the Monitor or Investigations pages.</p>
          {quickMerchants && quickMerchants.length > 0 && (
            <div className="quick-explore-bar" style={{ justifyContent: "center", marginTop: "var(--space-5)" }}>
              <span className="quick-explore-label">Quick Explore:</span>
              {quickMerchants.map((name) => (
                <button
                  key={name}
                  type="button"
                  className="quick-explore-pill"
                  onClick={() => selectMerchant(name)}
                  aria-label={`Select merchant ${name}`}
                >
                  {name}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
