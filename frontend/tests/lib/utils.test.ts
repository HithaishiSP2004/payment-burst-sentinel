import { describe, it, expect } from "vitest";
import {
  formatCurrency,
  formatCurrencyRound,
  formatNumber,
  formatMads,
  formatAnomalyType,
  formatAnomalyShift,
  formatSignalDominance,
  isAnomaly,
  getTooltipStyle,
} from "@/lib/utils";

/* ═══════════════════════════════════════════════════════════════
   FORMATTING
   ═══════════════════════════════════════════════════════════════ */

describe("formatCurrency", () => {
  it("formats positive values with ₹ and en-IN grouping", () => {
    expect(formatCurrency(19364.91)).toBe("₹19,364.91");
  });
  it("formats zero", () => {
    expect(formatCurrency(0)).toBe("₹0");
  });
  it("returns em-dash for null", () => {
    expect(formatCurrency(null)).toBe("—");
  });
  it("returns em-dash for undefined", () => {
    expect(formatCurrency(undefined)).toBe("—");
  });
});

describe("formatCurrencyRound", () => {
  it("rounds and formats", () => {
    expect(formatCurrencyRound(19364.91)).toBe("₹19,365");
  });
  it("handles null", () => {
    expect(formatCurrencyRound(null)).toBe("—");
  });
});

describe("formatNumber", () => {
  it("formats with commas", () => {
    expect(formatNumber(42665)).toBe("42,665");
  });
  it("handles null", () => {
    expect(formatNumber(null)).toBe("—");
  });
});

describe("formatMads", () => {
  it("formats positive deviation", () => {
    expect(formatMads(1935.4)).toBe("+1935.4 MADs");
  });
  it("formats decimal deviation", () => {
    expect(formatMads(4.23)).toBe("+4.2 MADs");
  });
  it("returns empty for null", () => {
    expect(formatMads(null)).toBe("");
  });
});

/* ═══════════════════════════════════════════════════════════════
   ANOMALY TYPE FORMATTING
   ═══════════════════════════════════════════════════════════════ */

describe("formatAnomalyType", () => {
  it("maps amount_anomaly", () => expect(formatAnomalyType("amount_anomaly")).toBe("AMOUNT"));
  it("maps combined_anomaly", () => expect(formatAnomalyType("combined_anomaly")).toBe("COMBINED"));
  it("maps velocity_anomaly", () => expect(formatAnomalyType("velocity_anomaly")).toBe("VOLUME"));
  it("handles unknown types", () => expect(formatAnomalyType("new_type")).toBe("NEW TYPE"));
});

describe("formatAnomalyShift", () => {
  it("maps amount_anomaly", () => expect(formatAnomalyShift("amount_anomaly")).toBe("AMOUNT SHIFT"));
  it("maps combined_anomaly", () => expect(formatAnomalyShift("combined_anomaly")).toBe("COMBINED"));
  it("maps velocity_anomaly", () => expect(formatAnomalyShift("velocity_anomaly")).toBe("VOLUME SHIFT"));
});

describe("formatSignalDominance", () => {
  it("maps amount_anomaly", () => expect(formatSignalDominance("amount_anomaly")).toBe("AMOUNT DOMINANT"));
  it("maps combined_anomaly", () => expect(formatSignalDominance("combined_anomaly")).toBe("COMBINED"));
  it("maps velocity_anomaly", () => expect(formatSignalDominance("velocity_anomaly")).toBe("VOLUME"));
});

/* ═══════════════════════════════════════════════════════════════
   ANOMALY DETECTION HELPER
   ═══════════════════════════════════════════════════════════════ */

describe("isAnomaly", () => {
  it("returns true for amount_anomaly", () => expect(isAnomaly("amount_anomaly")).toBe(true));
  it("returns true for combined_anomaly", () => expect(isAnomaly("combined_anomaly")).toBe(true));
  it("returns true for velocity_anomaly", () => expect(isAnomaly("velocity_anomaly")).toBe(true));
  it("returns false for normal", () => expect(isAnomaly("normal")).toBe(false));
  it("returns false for not_scored", () => expect(isAnomaly("not_scored")).toBe(false));
  it("returns false for null", () => expect(isAnomaly(null)).toBe(false));
  it("returns false for undefined", () => expect(isAnomaly(undefined)).toBe(false));
  it("returns false for empty string", () => expect(isAnomaly("")).toBe(false));
});

/* ═══════════════════════════════════════════════════════════════
   TOOLTIP POSITIONING
   ═══════════════════════════════════════════════════════════════ */

describe("getTooltipStyle", () => {
  const barCount = 60;

  it("positions left-edge tooltip with left:0 (no overflow)", () => {
    const style = getTooltipStyle(2, barCount, 100);
    expect(style.left).toBe(0);
    expect(style.right).toBeUndefined();
    expect(style.transform).toBeUndefined();
  });

  it("positions right-edge tooltip with right:0 (no overflow)", () => {
    const style = getTooltipStyle(55, barCount, 100);
    expect(style.right).toBe(0);
    expect(style.left).toBeUndefined();
    expect(style.transform).toBeUndefined();
  });

  it("positions center tooltip with translateX(-50%)", () => {
    const style = getTooltipStyle(30, barCount, 100);
    expect(style.left).toBe("50%");
    expect(style.transform).toBe("translateX(-50%)");
    expect(style.right).toBeUndefined();
  });

  it("positions bottom relative to bar height", () => {
    const style = getTooltipStyle(30, 60, 150);
    expect(style.bottom).toBe(164); // 150 + 14
  });

  it("always sets pointer-events: none", () => {
    const style = getTooltipStyle(0, 10, 50);
    expect(style.pointerEvents).toBe("none");
  });
});
