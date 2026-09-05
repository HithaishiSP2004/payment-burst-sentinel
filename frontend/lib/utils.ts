import type React from "react";

/* ─── Formatting ─────────────────────────────────────────── */

export function formatCurrency(value: number | undefined | null, currency: string = "INR"): string {
  if (value == null) return "—";
  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: currency || "INR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(value);
  } catch {
    return `₹${value.toLocaleString("en-IN")}`;
  }
}

export function formatCurrencyRound(value: number | undefined | null, currency: string = "INR"): string {
  if (value == null) return "—";
  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: currency || "INR",
      maximumFractionDigits: 0,
    }).format(Math.round(value));
  } catch {
    return `₹${Math.round(value).toLocaleString("en-IN")}`;
  }
}

export function formatNumber(value: number | undefined | null): string {
  if (value == null) return "—";
  return value.toLocaleString();
}

export function formatMads(value: number | undefined | null): string {
  if (value == null) return "";
  return `+${value.toFixed(1)} MADs`;
}

export function formatAnomalyType(type: string): string {
  switch (type) {
    case "amount_anomaly": return "AMOUNT";
    case "combined_anomaly": return "COMBINED";
    case "velocity_anomaly": return "VOLUME";
    default: return type?.replace("_", " ").toUpperCase() || "UNKNOWN";
  }
}

export function formatAnomalyShift(type: string): string {
  switch (type) {
    case "amount_anomaly": return "AMOUNT SHIFT";
    case "combined_anomaly": return "COMBINED";
    case "velocity_anomaly": return "VOLUME SHIFT";
    default: return type?.replace("_", " ").toUpperCase() || "UNKNOWN";
  }
}

export function formatSignalDominance(type: string): string {
  switch (type) {
    case "amount_anomaly": return "AMOUNT DOMINANT";
    case "combined_anomaly": return "COMBINED";
    case "velocity_anomaly": return "VOLUME";
    default: return type?.replace("_", " ").toUpperCase() || "UNKNOWN";
  }
}

/* ─── Anomaly Detection ──────────────────────────────────── */

export function isAnomaly(anomalyType: string | undefined | null): boolean {
  return !!anomalyType && anomalyType !== "normal" && anomalyType !== "not_scored";
}

/* ─── Chart Tooltip Positioning ──────────────────────────── */

export function getTooltipStyle(
  barIndex: number,
  barCount: number,
  obsHeight: number
): React.CSSProperties {
  const isLeftEdge = barIndex < barCount * 0.15;
  const isRightEdge = barIndex > barCount * 0.85;

  return {
    position: "absolute",
    bottom: obsHeight + 14,
    ...(isLeftEdge ? { left: 0 } : isRightEdge ? { right: 0 } : { left: "50%", transform: "translateX(-50%)" }),
    background: "var(--ink-primary)",
    color: "var(--surface-canvas)",
    padding: "8px 10px",
    borderRadius: "var(--radius-sm)",
    fontSize: "0.5625rem",
    fontFamily: "var(--font-mono)",
    whiteSpace: "nowrap",
    zIndex: 10,
    lineHeight: 1.5,
    letterSpacing: "0.04em",
    pointerEvents: "none",
    boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
  };
}
