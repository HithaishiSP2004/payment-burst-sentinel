import type {
  Overview,
  InvestigationsResponse,
  InvestigationDetail,
  EvaluationData,
  MerchantRhythm,
  CostModelResponse,
  AIBriefResponse,
  IntegrationStatus,
  DemoIngestionResult,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const REQUEST_TIMEOUT_MS = 15000;
const AI_REQUEST_TIMEOUT_MS = 45000; // Longer timeout for Gemini API calls

/* ─── Generic request helper ─────────────────────────────── */

async function apiGet<T>(path: string, externalSignal?: AbortSignal): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  if (externalSignal) {
    if (externalSignal.aborted) {
      controller.abort();
    } else {
      externalSignal.addEventListener("abort", () => controller.abort(), { once: true });
    }
  }

  try {
    const res = await fetch(`${API_BASE}${path}`, { signal: controller.signal });
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText}`);
    }
    return res.json();
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(`Request timed out or cancelled: ${path}`);
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

/* ─── Domain-specific API functions ──────────────────────── */

export async function getOverview(): Promise<Overview> {
  return apiGet<Overview>("/api/overview");
}

export async function getInvestigations(
  riskFilter: string | null,
  typeFilter: string | null,
  limit = 20,
  offset = 0,
  sortBy = "composite_deviation"
): Promise<InvestigationsResponse> {
  let url = `/api/investigations?limit=${limit}&offset=${offset}&sort_by=${sortBy}`;
  if (riskFilter) url += `&risk_level=${riskFilter}`;
  if (typeFilter) url += `&anomaly_type=${typeFilter}`;
  return apiGet<InvestigationsResponse>(url);
}

export async function getInvestigationDetail(
  merchant: string,
  date: string,
  signal?: AbortSignal
): Promise<InvestigationDetail> {
  return apiGet<InvestigationDetail>(
    `/api/investigation/${encodeURIComponent(merchant)}/${encodeURIComponent(date)}`,
    signal
  );
}

export async function getEvaluation(): Promise<EvaluationData> {
  return apiGet<EvaluationData>("/api/evaluation");
}

export async function getMerchantRhythm(name: string, days = 90): Promise<MerchantRhythm> {
  return apiGet<MerchantRhythm>(`/api/merchant/${encodeURIComponent(name)}/rhythm?days=${days}`);
}

export async function searchMerchants(query: string): Promise<string[]> {
  const data = await apiGet<{ suggestions: string[] }>(`/api/merchants/suggest?q=${encodeURIComponent(query)}&limit=8`);
  return data.suggestions;
}

export async function getCostModel(
  reviewMinutes = 15,
  analystHourlyCost = 500,
  policy = "all_flagged"
): Promise<CostModelResponse> {
  return apiGet<CostModelResponse>(
    `/api/evaluation/cost-model?review_minutes=${reviewMinutes}&analyst_hourly_cost=${analystHourlyCost}&policy=${policy}`
  );
}

/* ─── AI Investigation Intelligence (Phase 15) ──────────── */

export async function generateAIBrief(
  merchant: string,
  date: string
): Promise<AIBriefResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), AI_REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(
      `${API_BASE}/api/investigation/${encodeURIComponent(merchant)}/${encodeURIComponent(date)}/ai-brief`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
      }
    );

    if (!res.ok) {
      // Return unavailable instead of throwing — AI failure is graceful
      return {
        status: "unavailable",
        cached: false,
        reason: `AI service returned status ${res.status}`,
      };
    }

    return res.json();
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return {
        status: "unavailable",
        cached: false,
        reason: "AI request timed out. Please try again.",
      };
    }
    return {
      status: "unavailable",
      cached: false,
      reason: "Failed to connect to AI service.",
    };
  } finally {
    clearTimeout(timeout);
  }
}


/* ─── Integration Readiness (Phase 16) ───────────────────── */

export async function getIntegrationStatus(): Promise<IntegrationStatus> {
  return apiGet<IntegrationStatus>("/api/integration/status");
}

export async function demoIngest(payload?: Record<string, unknown>): Promise<DemoIngestionResult> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE}/api/integration/demo/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload ? JSON.stringify(payload) : undefined,
      signal: controller.signal,
    });

    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}
