import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { EvaluationScreen } from "@/components/screens/EvaluationScreen";
import { mockEvaluation } from "../fixtures/data";

// Mock API call to getCostModel
vi.mock("@/lib/api", () => ({
  getCostModel: vi.fn().mockResolvedValue({
    assumptions: {
      review_minutes: 15,
      analyst_hourly_cost: 500,
      source: "Industry baseline",
      disclaimer: "Workload model disclaimer text",
    },
    results: {
      estimated_false_positive_alerts: 14997,
      estimated_review_hours: 3749,
      scenario_based_review_cost: 1874500,
    },
    scenarios: [
      {
        name: "Lean",
        review_minutes: 5,
        analyst_hourly_cost: 300,
        estimated_false_positive_alerts: 14997,
        estimated_review_hours: 1250,
        scenario_based_review_cost: 375000,
      },
      {
        name: "Standard",
        review_minutes: 15,
        analyst_hourly_cost: 500,
        estimated_false_positive_alerts: 14997,
        estimated_review_hours: 3749,
        scenario_based_review_cost: 1874500,
      },
      {
        name: "Intensive",
        review_minutes: 30,
        analyst_hourly_cost: 800,
        estimated_false_positive_alerts: 14997,
        estimated_review_hours: 7498,
        scenario_based_review_cost: 5998400,
      },
    ],
    policy_comparison: {
      all_flagged: {
        label: "All Flagged (Elevated + High)",
        total_alerts: 16090,
        proxy_true_positives: 1093,
        estimated_false_positive_alerts: 14997,
        proxy_precision_pct: 6.64,
        proxy_recall_pct: 50.93,
        enrichment_vs_normal: 7.13,
        estimated_review_hours: 3749,
      },
      high_only: {
        label: "High Risk Only",
        total_alerts: 5430,
        proxy_true_positives: 520,
        estimated_false_positive_alerts: 4910,
        proxy_precision_pct: 9.58,
        proxy_recall_pct: 24.23,
        enrichment_vs_normal: 8.85,
        estimated_review_hours: 1268,
      },
    },
  }),
}));

describe("Phase 19 — Detection Evaluation & Analytical Performance Workspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  async function renderWorkspace(extraProps = {}) {
    await act(async () => {
      render(<EvaluationScreen data={mockEvaluation} {...extraProps} />);
    });
  }

  /* ─── SECTION 01 — HEADER & CONTEXT STRIP ─── */
  it("renders workspace header with frozen policy badge and context strip", async () => {
    await renderWorkspace();
    expect(screen.getByText("DETECTION ASSURANCE // HISTORICAL EVALUATION")).toBeInTheDocument();
    expect(screen.getByText("DETECTION POLICY: FROZEN")).toBeInTheDocument();
    expect(screen.getByText("Held-Out Evaluation")).toBeInTheDocument();
    expect(screen.getByText("Frozen Historical Data")).toBeInTheDocument();
    expect(screen.getByText("693 Merchants")).toBeInTheDocument();
    expect(screen.getByText("Temporal Holdout")).toBeInTheDocument();
  });

  /* ─── SECTION 02 — EXECUTIVE PERFORMANCE SNAPSHOT ─── */
  it("renders 4 executive snapshot cards with precision labels and metadata", async () => {
    await renderWorkspace();
    expect(screen.getByText("EXECUTIVE PERFORMANCE SNAPSHOT")).toBeInTheDocument();
    expect(screen.getByText("ENRICHMENT VS NORMAL")).toBeInTheDocument();
    expect(screen.getByText("ENRICHMENT VS OVERALL")).toBeInTheDocument();
    expect(screen.getByText("PROXY-POSITIVE COVERAGE")).toBeInTheDocument();
    expect(screen.getByText("ALERTS PER PROXY-POSITIVE DAY")).toBeInTheDocument();
    expect(screen.getByText("Meaningful enrichment")).toBeInTheDocument();
  });

  /* ─── SECTION 03 — DETECTION PERFORMANCE EVIDENCE ─── */
  it("renders evidence comparison with distinct group definitions and risk table", async () => {
    await renderWorkspace();
    expect(screen.getByText("01 // DETECTION PERFORMANCE EVIDENCE")).toBeInTheDocument();
    expect(screen.getAllByText("FLAGGED (ELEVATED + HIGH)").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("NORMAL COMPARISON GROUP")).toBeInTheDocument();
    expect(screen.getByText("GENERAL POPULATION")).toBeInTheDocument();
    expect(screen.getByText("RISK-LEVEL PERFORMANCE")).toBeInTheDocument();

    const columnHeaders = screen.getAllByRole("columnheader");
    expect(columnHeaders.length).toBeGreaterThanOrEqual(4);
    columnHeaders.forEach((h) => expect(h).toHaveAttribute("scope", "col"));
  });

  /* ─── SECTION 04 — SIGNAL CONCENTRATION ANALYSIS ─── */
  it("renders signal concentration comparison with non-causal disclaimer", async () => {
    await renderWorkspace();
    expect(screen.getByText("02 // SIGNAL CONCENTRATION ANALYSIS")).toBeInTheDocument();
    expect(screen.getByText("BEHAVIORAL MODEL")).toBeInTheDocument();
    expect(screen.getByText("VOLUME-ONLY BASELINE")).toBeInTheDocument();
    expect(screen.getByText(/3.9× advantage/)).toBeInTheDocument();
    expect(screen.getByText(/Non-causal interpretation/)).toBeInTheDocument();
  });

  /* ─── SECTION 05 — RESPONSIVE METHODOLOGY WORKFLOW ─── */
  it("renders 5-step methodology pipeline workflow", async () => {
    await renderWorkspace();
    expect(screen.getByText("03 // EVALUATION METHODOLOGY")).toBeInTheDocument();
    expect(screen.getByText("FROZEN HISTORICAL DATA")).toBeInTheDocument();
    expect(screen.getByText("BASELINE CONSTRUCTION")).toBeInTheDocument();
    expect(screen.getByText("DETERMINISTIC DETECTION")).toBeInTheDocument();
    expect(screen.getByText("HISTORICAL COMPARISON")).toBeInTheDocument();
    expect(screen.getByText("EVALUATION RESULTS")).toBeInTheDocument();
  });

  /* ─── SECTION 06 — POLICY TRANSPARENCY & CROSS-TABULATION ─── */
  it("renders policy transparency, cross-tabulation matrix, and scenario toggles", async () => {
    await renderWorkspace();
    expect(screen.getByText("04 // DETECTION POLICY TRANSPARENCY")).toBeInTheDocument();
    expect(screen.getByText("STUDY PARAMETERS")).toBeInTheDocument();
    expect(screen.getByText("PROXY OUTCOME CROSS-TABULATION (CONFUSION MATRIX)")).toBeInTheDocument();
    expect(screen.getByText(/PROXY INTERPRETATION NOTICE:/)).toBeInTheDocument();

    // Confusion matrix cells
    expect(screen.getAllByText(/TP/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/FP/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/FN/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/TN/).length).toBeGreaterThanOrEqual(1);

    // Scenario buttons
    const leanBtn = screen.getByText("LEAN");
    const standardBtn = screen.getByText("STANDARD");
    const intensiveBtn = screen.getByText("INTENSIVE");
    expect(leanBtn).toBeInTheDocument();
    expect(standardBtn).toBeInTheDocument();
    expect(intensiveBtn).toBeInTheDocument();

    // Click scenario button
    await act(async () => {
      fireEvent.click(intensiveBtn);
    });
    await waitFor(() => {
      expect(intensiveBtn).toHaveClass("active");
    });
  });

  /* ─── SECTION 07 — EVALUATION BOUNDARIES ─── */
  it("renders 4 semantic boundary badges and limitations list", async () => {
    await renderWorkspace();
    expect(screen.getByText("05 // EVALUATION BOUNDARIES")).toBeInTheDocument();
    expect(screen.getByText("VALIDATED")).toBeInTheDocument();
    expect(screen.getByText("NOT EVALUATED")).toBeInTheDocument();
    expect(screen.getByText("NOT AVAILABLE")).toBeInTheDocument();
    expect(screen.getByText("DISABLED")).toBeInTheDocument();

    const limitationsList = screen.getByRole("list", { name: "Limitations" });
    expect(limitationsList).toBeInTheDocument();
    expect(screen.getByText(/Behavioral anomaly ≠ fraud/)).toBeInTheDocument();
  });

  /* ─── SECTION 08 — HUMAN INTERPRETATION BOUNDARY & ACTIONS ─── */
  it("renders human governance card and fires navigation callbacks with correct hierarchy", async () => {
    const onNavigateToInvestigations = vi.fn();
    const onNavigateToMerchantRhythm = vi.fn();
    const onNavigateToMonitor = vi.fn();

    await renderWorkspace({
      onNavigateToInvestigations,
      onNavigateToMerchantRhythm,
      onNavigateToMonitor,
    });

    expect(screen.getByText("06 // HUMAN INTERPRETATION BOUNDARY")).toBeInTheDocument();
    expect(screen.getByText("Human Authority & System Purpose")).toBeInTheDocument();

    // Primary button: View Investigations
    const invBtn = screen.getByText("View Investigations →");
    expect(invBtn).toBeInTheDocument();
    expect(invBtn).toHaveClass("eval-btn-primary");
    fireEvent.click(invBtn);
    expect(onNavigateToInvestigations).toHaveBeenCalledTimes(1);

    // Secondary button: View Merchant Rhythm
    const rhythmBtn = screen.getByText("View Merchant Rhythm →");
    expect(rhythmBtn).toBeInTheDocument();
    expect(rhythmBtn).toHaveClass("eval-btn-secondary");
    fireEvent.click(rhythmBtn);
    expect(onNavigateToMerchantRhythm).toHaveBeenCalledTimes(1);

    // Tertiary button: Back to Monitor
    const monBtn = screen.getByText("← Back to Monitor");
    expect(monBtn).toBeInTheDocument();
    expect(monBtn).toHaveClass("eval-btn-tertiary");
    fireEvent.click(monBtn);
    expect(onNavigateToMonitor).toHaveBeenCalledTimes(1);
  });
});
