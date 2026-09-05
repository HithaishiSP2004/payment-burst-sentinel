"use client";

import React, { useState, useEffect, useRef } from "react";
import type { Page } from "@/types/api";

export interface PitchTourProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
  onSelectInvestigation: (inv: { merchant: string; date: string } | null) => void;
  onSetRiskFilter: (risk: string | null) => void;
  onSelectMerchant: (merchant: string) => void;
}

interface TourStep {
  id: string;
  time: string;
  title: string;
  subtitle: string;
  durationSec: number;
  action: (handlers: {
    onNavigate: (page: Page) => void;
    onSelectInvestigation: (inv: { merchant: string; date: string } | null) => void;
    onSetRiskFilter: (risk: string | null) => void;
    onSelectMerchant: (merchant: string) => void;
  }) => void;
}

const TOUR_STEPS: TourStep[] = [
  {
    id: "problem",
    time: "0:00 – 0:30",
    title: "The Problem & The Hook",
    subtitle:
      "In payments, fraud risk isn't always visible in a single transaction. A merchant can look completely normal transaction by transaction, but its overall payment behavior can suddenly shift. A static global volume threshold can miss that context, because what is 'normal' varies wildly per merchant. Fifty thousand rupees daily might be standard for a supermarket, but extraordinary for a local bakery. When we analyzed historical merchant transaction data, aggregate transaction volume alone was poorly correlated with fraud. Payment Burst Sentinel was built to solve this: a defensive risk intelligence system that establishes individual behavioral rhythms for every merchant, detects statistical bursts, and arms human risk analysts with evidence-grounded AI explanations.",
    durationSec: 30,
    action: ({ onNavigate, onSelectInvestigation }) => {
      onSelectInvestigation(null);
      onNavigate("monitor");
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
  },
  {
    id: "methodology",
    time: "0:30 – 1:10",
    title: "Detection Methodology (Merchant Rhythm)",
    subtitle:
      "Rather than imposing platform-wide static rules, we construct a rolling thirty-day behavioral baseline for each merchant. To handle skewed financial data robustly, we use the median rather than the mean, and the Median Absolute Deviation—or MAD—rather than standard deviation. This prevents past spikes from distorting what the system expects as normal. Every day, we evaluate two distinct upward signals: transaction velocity deviation and payment value deviation. If a merchant's burst exceeds four MADs above baseline, we classify it as Elevated Risk. At five MADs or greater, it triggers a High Risk deviation. The mathematics are frozen, deterministic, and fully auditable.",
    durationSec: 40,
    action: ({ onNavigate, onSelectMerchant, onSelectInvestigation }) => {
      onSelectInvestigation(null);
      onSelectMerchant("Kovacek Ltd");
      onNavigate("merchant");
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
  },
  {
    id: "investigations-index",
    time: "1:10 – 1:35",
    title: "Investigations Index (High Risk Filter)",
    subtitle:
      "Here in the Investigations Index, an analyst can immediately prioritize severe anomalies. Notice every item exposes its primary signal—such as payment value or transaction volume—alongside the exact statistical deviation in MADs. Let's open a real deviation from our held-out test set: Kovacek Ltd on November 27th, 2020.",
    durationSec: 25,
    action: ({ onNavigate, onSetRiskFilter, onSelectInvestigation }) => {
      onSelectInvestigation(null);
      onSetRiskFilter("high");
      onNavigate("investigations");
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
  },
  {
    id: "evidence-workspace",
    time: "1:35 – 1:55",
    title: "Evidence Workspace (Kovacek Ltd)",
    subtitle:
      "Notice what happens before any AI is touched. The Evidence Workspace lays out deterministic facts: Kovacek Ltd typically processes about ten rupees and seventy-five paise per day. On this day, payment volume surged to nineteen thousand, three hundred and sixty-four rupees. That's a deviation of more than nineteen hundred MADs from its baseline. Yet its transaction count remained at just one transaction. The system immediately isolates that this was a high-value amount burst, not a volume surge. Every statement is grounded in frozen, verifiable baseline data.",
    durationSec: 20,
    action: ({ onNavigate, onSelectInvestigation }) => {
      onSelectInvestigation({ merchant: "Kovacek Ltd", date: "2020-11-27" });
      onNavigate("investigations");
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
  },
  {
    id: "gemini-advisory",
    time: "1:55 – 2:40",
    title: "Gemini AI Advisory Layer",
    subtitle:
      "This is where Google Gemini enters the workflow—but crucially, Gemini is not the detector. The deterministic mathematical core has already identified the anomaly. Gemini receives only structured evidence items, labeled E1 through E6, through an injection-shielded prompt. Behind seven post-generation safety guardrails, Gemini synthesizes what changed, quotes exact evidence IDs, highlights critical unknowns, and suggests defensive investigative questions for the analyst. The guardrails explicitly forbid Gemini from declaring confirmed fraud or autonomously blocking payments. And if the AI service is offline or unconfigured, the system degrades gracefully—one hundred percent of deterministic evidence remains accessible.",
    durationSec: 45,
    action: ({ onNavigate, onSelectInvestigation }) => {
      onSelectInvestigation({ merchant: "Kovacek Ltd", date: "2020-11-27" });
      onNavigate("investigations");
      setTimeout(() => {
        const aiSection = document.getElementById("ai-brief-section") || document.querySelector(".evidence-ai-brief");
        if (aiSection) {
          aiSection.scrollIntoView({ behavior: "smooth", block: "center" });
        } else {
          window.scrollTo({ top: 600, behavior: "smooth" });
        }
      }, 500);
    },
  },
  {
    id: "evaluation-workspace",
    time: "2:40 – 3:35",
    title: "Held-Out Evaluation & False-Positive Cost",
    subtitle:
      "We evaluated Payment Burst Sentinel on a temporal held-out test split of over one hundred and twenty-six thousand merchant-days. Because our detector operates at the merchant-day level while fraud labels exist per transaction, we report our results transparently as proxy classification metrics. Flagged days capture fifty point nine three percent of fraud-containing merchant-days, delivering a seven point one three times fraud enrichment compared to normal days. Because anomaly detection naturally surfaces false positives, we also model the operational workload. In our held-out test set, sixteen thousand and ninety alerts captured one thousand sixty-nine fraud-containing days, leaving fifteen thousand false-positive alerts. Using explicit scenario assumptions—for example, fifteen minutes per review at five hundred rupees an hour—our interactive model quantifies the exact analyst capacity required to triage these signals.",
    durationSec: 55,
    action: ({ onNavigate, onSelectInvestigation }) => {
      onSelectInvestigation(null);
      onNavigate("evaluation");
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
  },
  {
    id: "why-this-matters",
    time: "3:35 – 4:10",
    title: "Why This Matters (Ecosystem Positioning)",
    subtitle:
      "We are not claiming to replace Razorpay's production fraud engines or real-time transaction firewalls. Instead, Payment Burst Sentinel adds a merchant-level behavioral lens alongside transaction-level risk controls, helping analysts investigate sudden payment-value bursts and unusual merchant behavior.",
    durationSec: 35,
    action: ({ onNavigate, onSelectInvestigation }) => {
      onSelectInvestigation(null);
      onNavigate("monitor");
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
  },
  {
    id: "integration-readiness",
    time: "4:10 – 4:35",
    title: "Integration Readiness Boundary",
    subtitle:
      "Finally, we designed an integration readiness boundary. We implemented a provider-neutral canonical event schema enforcing UTC timestamps and exact Decimal amounts, paired with bounded idempotency and HMAC signature verification for Razorpay webhooks. This demonstrates architectural readiness, while maintaining strict isolation: simulated demo events never modify historical data, never alter baselines, and never trigger detection.",
    durationSec: 25,
    action: ({ onNavigate, onSelectInvestigation }) => {
      onSelectInvestigation(null);
      onNavigate("integration");
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
  },
  {
    id: "conclusion",
    time: "4:35 – 5:00",
    title: "Human Decision Boundary & Conclusion",
    subtitle:
      "The core design decision of Payment Burst Sentinel is its strict separation of responsibilities: Deterministic systems detect. Gemini explains. Humans decide. Thank you.",
    durationSec: 25,
    action: ({ onNavigate, onSelectInvestigation }) => {
      onSelectInvestigation({ merchant: "Kovacek Ltd", date: "2020-11-27" });
      onNavigate("investigations");
      setTimeout(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
      }, 500);
    },
  },
];

export function PitchTourBar({
  onNavigate,
  onSelectInvestigation,
  onSetRiskFilter,
  onSelectMerchant,
}: PitchTourProps) {
  const [active, setActive] = useState(true);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const step = TOUR_STEPS[currentStepIdx];

  const goToStep = (idx: number) => {
    if (idx < 0 || idx >= TOUR_STEPS.length) return;
    setCurrentStepIdx(idx);
    TOUR_STEPS[idx].action({
      onNavigate,
      onSelectInvestigation,
      onSetRiskFilter,
      onSelectMerchant,
    });
  };

  useEffect(() => {
    if (!isAutoPlaying) {
      if (timerRef.current) clearTimeout(timerRef.current);
      return;
    }

    timerRef.current = setTimeout(() => {
      if (currentStepIdx < TOUR_STEPS.length - 1) {
        goToStep(currentStepIdx + 1);
      } else {
        setIsAutoPlaying(false);
      }
    }, step.durationSec * 1000);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isAutoPlaying, currentStepIdx]);

  if (!active) {
    return (
      <button
        id="show-pitch-tour-btn"
        onClick={() => {
          setActive(true);
          goToStep(currentStepIdx);
        }}
        style={{
          position: "fixed",
          bottom: 20,
          right: 24,
          zIndex: 9999,
          background: "linear-gradient(135deg, #B87420, #D48A2C)",
          color: "#FFFFFF",
          border: "none",
          borderRadius: 24,
          padding: "10px 18px",
          fontFamily: "var(--font-sans)",
          fontSize: 13,
          fontWeight: 600,
          cursor: "pointer",
          boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <span>🎬</span>
        <span>Show Pitch Tour & Subtitles</span>
      </button>
    );
  }

  return (
    <aside
      aria-label="5-Minute Pitch Tour and Subtitles"
      id="pitch-tour-overlay"
      style={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
        background: "rgba(23, 20, 15, 0.96)",
        backdropFilter: "blur(16px)",
        borderTop: "2px solid #B87420",
        color: "#F9F6F2",
        padding: "12px 28px 14px 28px",
        boxShadow: "0 -8px 32px rgba(0,0,0,0.45)",
        fontFamily: "var(--font-sans)",
      }}
    >
      {/* Top Header Controls */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 8,
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span
            style={{
              background: "#B87420",
              color: "#FFF",
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              padding: "3px 8px",
              borderRadius: 4,
            }}
          >
            5-Min Pitch
          </span>
          <span
            style={{
              fontSize: 12,
              color: "#D48A2C",
              fontWeight: 600,
              fontFamily: "var(--font-mono)",
            }}
          >
            [{step.time}]
          </span>
          <span
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: "#F4F1EC",
            }}
          >
            Step {currentStepIdx + 1}/{TOUR_STEPS.length}: {step.title}
          </span>
        </div>

        {/* Buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button
            id="pitch-tour-prev-btn"
            onClick={() => goToStep(currentStepIdx - 1)}
            disabled={currentStepIdx === 0}
            style={{
              background: "rgba(255,255,255,0.08)",
              color: currentStepIdx === 0 ? "#666" : "#FFF",
              border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: 6,
              padding: "5px 12px",
              fontSize: 12,
              fontWeight: 500,
              cursor: currentStepIdx === 0 ? "not-allowed" : "pointer",
            }}
          >
            ◀ Prev
          </button>

          <button
            id="pitch-tour-autoplay-btn"
            onClick={() => setIsAutoPlaying(!isAutoPlaying)}
            style={{
              background: isAutoPlaying ? "#A64232" : "#B87420",
              color: "#FFF",
              border: "none",
              borderRadius: 6,
              padding: "5px 14px",
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {isAutoPlaying ? "⏸ Pause Auto-Play" : "▶ Auto-Play Tour"}
          </button>

          <button
            id="pitch-tour-next-btn"
            onClick={() => goToStep(currentStepIdx + 1)}
            disabled={currentStepIdx === TOUR_STEPS.length - 1}
            style={{
              background: "rgba(255,255,255,0.08)",
              color: currentStepIdx === TOUR_STEPS.length - 1 ? "#666" : "#FFF",
              border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: 6,
              padding: "5px 12px",
              fontSize: 12,
              fontWeight: 500,
              cursor: currentStepIdx === TOUR_STEPS.length - 1 ? "not-allowed" : "pointer",
            }}
          >
            Next ▶
          </button>

          <button
            id="pitch-tour-close-btn"
            onClick={() => setActive(false)}
            title="Minimize Tour Bar"
            style={{
              background: "transparent",
              color: "#A49C90",
              border: "none",
              fontSize: 16,
              cursor: "pointer",
              marginLeft: 8,
              padding: "2px 6px",
            }}
          >
            ✕
          </button>
        </div>
      </div>

      {/* Synchronized Subtitles Area */}
      <div
        id="pitch-tour-subtitle-text"
        style={{
          background: "rgba(0, 0, 0, 0.4)",
          borderLeft: "3px solid #D48A2C",
          borderRadius: 4,
          padding: "8px 14px",
          fontSize: 13,
          lineHeight: 1.5,
          color: "#EDEAE4",
          maxHeight: 68,
          overflowY: "auto",
        }}
      >
        <span style={{ color: "#D48A2C", fontWeight: 600, marginRight: 6 }}>Voiceover / Subtitle:</span>
        <span>"{step.subtitle}"</span>
      </div>
    </aside>
  );
}
