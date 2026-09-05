import { describe, it, expect, vi, beforeEach } from "vitest";
import { getOverview, getInvestigations, getEvaluation, getMerchantRhythm } from "@/lib/api";
import { mockOverview, mockInvestigations, mockEvaluation, mockMerchantRhythm } from "../fixtures/data";

/* ─── Mock fetch globally ────────────────────────────────── */

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function mockJsonResponse(data: unknown, status = 200) {
  return { ok: status >= 200 && status < 300, status, statusText: status === 200 ? "OK" : "Error", json: () => Promise.resolve(data) };
}

beforeEach(() => {
  mockFetch.mockReset();
});

/* ═══════════════════════════════════════════════════════════════
   getOverview
   ═══════════════════════════════════════════════════════════════ */

describe("getOverview", () => {
  it("calls correct endpoint and returns data", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockOverview));
    const result = await getOverview();
    expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/overview", expect.objectContaining({ signal: expect.any(AbortSignal) }));
    expect(result.merchants_monitored).toBe(693);
    expect(result.enrichment.vs_normal).toBe(7.13);
  });

  it("throws on HTTP error", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(null, 500));
    await expect(getOverview()).rejects.toThrow("API error 500");
  });

  it("throws on network failure", async () => {
    mockFetch.mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(getOverview()).rejects.toThrow("Failed to fetch");
  });

  it("passes AbortSignal for timeout support", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockOverview));
    await getOverview();
    const options = mockFetch.mock.calls[0][1];
    expect(options.signal).toBeInstanceOf(AbortSignal);
  });
});

/* ═══════════════════════════════════════════════════════════════
   getInvestigations
   ═══════════════════════════════════════════════════════════════ */

describe("getInvestigations", () => {
  it("calls correct endpoint without filters", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockInvestigations));
    await getInvestigations(null, null);
    expect(mockFetch.mock.calls[0][0]).toBe("http://localhost:8000/api/investigations?limit=20&offset=0&sort_by=composite_deviation");
  });

  it("appends risk_level filter", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockInvestigations));
    await getInvestigations("high", null);
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("risk_level=high");
  });

  it("appends anomaly_type filter", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockInvestigations));
    await getInvestigations(null, "amount_anomaly");
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("anomaly_type=amount_anomaly");
  });

  it("appends both filters", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockInvestigations));
    await getInvestigations("elevated", "combined_anomaly");
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("risk_level=elevated");
    expect(url).toContain("anomaly_type=combined_anomaly");
  });

  it("returns parsed response", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockInvestigations));
    const result = await getInvestigations(null, null);
    expect(result.total).toBe(3);
    expect(result.events).toHaveLength(3);
  });
});

/* ═══════════════════════════════════════════════════════════════
   getEvaluation
   ═══════════════════════════════════════════════════════════════ */

describe("getEvaluation", () => {
  it("calls correct endpoint", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockEvaluation));
    await getEvaluation();
    expect(mockFetch.mock.calls[0][0]).toBe("http://localhost:8000/api/evaluation");
  });

  it("returns evaluation data", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockEvaluation));
    const result = await getEvaluation();
    expect(result.primary_results.flagged_vs_normal?.enrichment_vs_normal).toBe(7.13);
    expect(result.limitations).toHaveLength(3);
  });

  it("throws on server error", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(null, 503));
    await expect(getEvaluation()).rejects.toThrow("API error 503");
  });
});

/* ═══════════════════════════════════════════════════════════════
   getMerchantRhythm
   ═══════════════════════════════════════════════════════════════ */

describe("getMerchantRhythm", () => {
  it("calls correct endpoint with encoded name", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockMerchantRhythm));
    await getMerchantRhythm("Kovacek Ltd");
    expect(mockFetch.mock.calls[0][0]).toBe("http://localhost:8000/api/merchant/Kovacek%20Ltd/rhythm?days=90");
  });

  it("handles special characters in merchant name", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockMerchantRhythm));
    await getMerchantRhythm("O'Brien & Sons");
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("O'Brien%20%26%20Sons");
  });

  it("uses custom days parameter", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockMerchantRhythm));
    await getMerchantRhythm("Test", 30);
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("days=30");
  });

  it("returns merchant data", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(mockMerchantRhythm));
    const result = await getMerchantRhythm("Kovacek Ltd");
    expect(result.merchant).toBe("Kovacek Ltd");
    expect(result.timeline).toHaveLength(5);
  });

  it("throws on 404 (merchant not found)", async () => {
    mockFetch.mockResolvedValue(mockJsonResponse(null, 404));
    await expect(getMerchantRhythm("Unknown")).rejects.toThrow("API error 404");
  });
});
