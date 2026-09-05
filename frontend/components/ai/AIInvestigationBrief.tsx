"use client";

import { useState } from "react";
import type { AIBriefResponse } from "@/types/api";
import { generateAIBrief } from "@/lib/api";

interface AIInvestigationBriefProps {
  merchant: string;
  date: string;
  riskLevel: string;
}

export function AIInvestigationBrief({ merchant, date, riskLevel }: AIInvestigationBriefProps) {
  const [briefResponse, setBriefResponse] = useState<AIBriefResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleGenerate() {
    setLoading(true);
    setBriefResponse(null);
    try {
      const response = await generateAIBrief(merchant, date);
      setBriefResponse(response);
    } catch {
      setBriefResponse({
        status: "unavailable",
        cached: false,
        reason: "Failed to generate AI brief. Please try again.",
      });
    }
    setLoading(false);
  }

  // ─── STATE 2: Ready (button to generate) ──────────────────
  if (!briefResponse && !loading) {
    return (
      <div className="ai-brief-panel" data-testid="ai-brief-ready">
        <div className="ai-brief-header">
          <div className="ai-brief-badge">AI INTELLIGENCE</div>
          <h3 className="ai-brief-title">Investigation Brief</h3>
          <p className="ai-brief-subtitle">
            Generate an evidence-grounded Gemini summary of this behavioral anomaly.
          </p>
        </div>
        <button
          className="ai-generate-btn"
          onClick={handleGenerate}
          data-testid="ai-generate-btn"
        >
          <span className="ai-generate-icon">◇</span>
          Generate AI Brief
        </button>
      </div>
    );
  }

  // ─── STATE 3: Generating ──────────────────────────────────
  if (loading) {
    return (
      <div className="ai-brief-panel ai-brief-loading" data-testid="ai-brief-loading">
        <div className="ai-brief-header">
          <div className="ai-brief-badge">AI INTELLIGENCE</div>
          <h3 className="ai-brief-title">Investigation Brief</h3>
        </div>
        <div className="ai-loading-indicator">
          <div className="ai-loading-pulse" />
          <span>Analyzing deterministic evidence…</span>
        </div>
      </div>
    );
  }

  // ─── STATE 5: Unavailable / Not Configured ────────────────
  if (briefResponse?.status !== "available" || !briefResponse.brief) {
    const isUnconfigured =
      briefResponse?.reason?.toLowerCase().includes("not configured") ||
      briefResponse?.reason?.toLowerCase().includes("gemini_api_key");

    return (
      <div
        className={`ai-brief-panel ai-brief-unavailable ${isUnconfigured ? "ai-brief-unconfigured" : ""}`}
        data-testid="ai-brief-unavailable"
      >
        <div className="ai-brief-header">
          <div
            className="ai-brief-badge"
            style={
              isUnconfigured
                ? {
                    background: "var(--surface-2)",
                    color: "var(--ink-secondary)",
                    borderColor: "var(--surface-3)",
                    letterSpacing: "0.08em",
                  }
                : undefined
            }
          >
            {isUnconfigured ? "AI NOT CONFIGURED" : "AI INTELLIGENCE"}
          </div>
          <h3 className="ai-brief-title">Investigation Brief</h3>
        </div>
        <div className="ai-unavailable-message">
          <p>
            {isUnconfigured
              ? "AI investigation intelligence is currently inactive. Deterministic evidence and factual statements remain complete and operational."
              : briefResponse?.reason || "AI Investigation Intelligence is currently unavailable."}
          </p>
          <p className="ai-unavailable-note">
            The deterministic investigation evidence remains available and unchanged.
          </p>
          {isUnconfigured && (
            <p className="body-xs" style={{ color: "var(--ink-secondary)", marginTop: "var(--space-2)" }}>
              To activate Gemini explanations, add <code>GEMINI_API_KEY=your_key</code> to your <code>.env</code> file.
            </p>
          )}
        </div>
        <button
          className="ai-retry-btn"
          onClick={handleGenerate}
          data-testid="ai-retry-btn"
        >
          {isUnconfigured ? "Check Key & Retry" : "Retry"}
        </button>
      </div>
    );
  }

  // ─── STATE 4: Available ───────────────────────────────────
  const brief = briefResponse.brief;

  return (
    <div className="ai-brief-panel ai-brief-available" data-testid="ai-brief-available">
      <div className="ai-brief-header">
        <div className="ai-brief-badge">AI INTELLIGENCE</div>
        <h3 className="ai-brief-title">Investigation Brief</h3>
        <div className="ai-brief-meta">
          {briefResponse.cached && <span className="ai-cached-badge">CACHED</span>}
          {briefResponse.provider && (
            <span className="ai-provider-badge">{briefResponse.provider} · {briefResponse.model}</span>
          )}
        </div>
      </div>

      {/* Headline */}
      <div className="ai-section ai-headline">
        <h4>{brief.headline}</h4>
      </div>

      {/* Summary */}
      <div className="ai-section">
        <div className="ai-section-label">SUMMARY</div>
        <p className="ai-section-text">{brief.summary}</p>
      </div>

      {/* What Changed */}
      {brief.what_changed.length > 0 && (
        <div className="ai-section">
          <div className="ai-section-label">WHAT CHANGED</div>
          <ul className="ai-evidence-list">
            {brief.what_changed.map((claim, i) => (
              <li key={i}>
                <span className="ai-evidence-ids">
                  {claim.evidence_ids.map(id => (
                    <span key={id} className="ai-eid">[{id}]</span>
                  ))}
                </span>
                {claim.statement}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Key Evidence */}
      {brief.key_evidence.length > 0 && (
        <div className="ai-section">
          <div className="ai-section-label">KEY EVIDENCE</div>
          <div className="ai-key-evidence-grid">
            {brief.key_evidence.map((ke, i) => (
              <div key={i} className="ai-key-evidence-item">
                <div className="ai-ke-header">
                  <span className="ai-eid">[{ke.evidence_id}]</span>
                  <span className="ai-ke-observation">{ke.observation}</span>
                </div>
                <p className="ai-ke-significance">{ke.why_it_matters}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Investigate Next */}
      {brief.investigate_next.length > 0 && (
        <div className="ai-section">
          <div className="ai-section-label">INVESTIGATE NEXT</div>
          <div className="ai-section-sublabel">Defensive investigation questions</div>
          <ul className="ai-questions-list">
            {brief.investigate_next.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </div>
      )}

      {/* What Remains Unknown — mandatory, visually prominent */}
      <div className="ai-section ai-unknown-section">
        <div className="ai-section-label ai-unknown-label">WHAT REMAINS UNKNOWN</div>
        <ul className="ai-unknown-list">
          {brief.what_remains_unknown.map((u, i) => (
            <li key={i}>{u}</li>
          ))}
        </ul>
      </div>

      {/* Safety Note — always visible */}
      <div className="ai-safety-note" data-testid="ai-safety-note">
        <span className="ai-safety-icon">⊘</span>
        {brief.safety_note}
      </div>

      {/* Regenerate button */}
      <div className="ai-brief-footer">
        <button className="ai-retry-btn" onClick={handleGenerate}>
          Regenerate Brief
        </button>
      </div>
    </div>
  );
}
