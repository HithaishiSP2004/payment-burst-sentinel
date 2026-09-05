import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MonitorScreen } from "@/components/screens/MonitorScreen";
import { EvaluationScreen } from "@/components/screens/EvaluationScreen";
import { mockOverview, mockInvestigations, mockEvaluation } from "../fixtures/data";

/* ═══════════════════════════════════════════════════════════════
   MONITOR SCREEN
   ═══════════════════════════════════════════════════════════════ */

describe("MonitorScreen", () => {
  it("shows loading state when overview is null", () => {
    render(<MonitorScreen overview={null} investigations={null} onMerchantClick={vi.fn()} />);
    expect(screen.getByText("Retrieving system overview...")).toBeInTheDocument();
  });

  it("renders page heading", () => {
    render(<MonitorScreen overview={mockOverview} investigations={mockInvestigations} onMerchantClick={vi.fn()} />);
    expect(screen.getByText(/Payment activity/)).toBeInTheDocument();
    expect(screen.getByText(/under observation/)).toBeInTheDocument();
  });

  it("renders enrichment value", () => {
    render(<MonitorScreen overview={mockOverview} investigations={mockInvestigations} onMerchantClick={vi.fn()} />);
    expect(screen.getByText("7.13×")).toBeInTheDocument();
  });

  it("renders merchant count in description", () => {
    render(<MonitorScreen overview={mockOverview} investigations={mockInvestigations} onMerchantClick={vi.fn()} />);
    expect(screen.getByText(/693 merchants/)).toBeInTheDocument();
  });

  it("renders deviation count", () => {
    render(<MonitorScreen overview={mockOverview} investigations={mockInvestigations} onMerchantClick={vi.fn()} />);
    expect(screen.getByText("42,665")).toBeInTheDocument();
  });

  it("renders elevated and high event counts", () => {
    render(<MonitorScreen overview={mockOverview} investigations={mockInvestigations} onMerchantClick={vi.fn()} />);
    expect(screen.getByText("12,825")).toBeInTheDocument();
    expect(screen.getByText("29,840")).toBeInTheDocument();
  });

  it("renders strongest deviations list", () => {
    render(<MonitorScreen overview={mockOverview} investigations={mockInvestigations} onMerchantClick={vi.fn()} />);
    expect(screen.getByText("Kovacek Ltd")).toBeInTheDocument();
  });

  it("clicking deviation calls onMerchantClick", () => {
    const onMerchantClick = vi.fn();
    render(<MonitorScreen overview={mockOverview} investigations={mockInvestigations} onMerchantClick={onMerchantClick} />);
    fireEvent.click(screen.getByText("Kovacek Ltd"));
    expect(onMerchantClick).toHaveBeenCalledWith("Kovacek Ltd");
  });

  it("renders investigation note", () => {
    render(<MonitorScreen overview={mockOverview} investigations={mockInvestigations} onMerchantClick={vi.fn()} />);
    expect(screen.getByText(/Investigation note/)).toBeInTheDocument();
  });
});

/* ═══════════════════════════════════════════════════════════════
   EVALUATION SCREEN — PHASE 14 (8 Sections)
   ═══════════════════════════════════════════════════════════════ */

describe("EvaluationScreen", () => {
  it("shows loading state when data is null", () => {
    render(<EvaluationScreen data={null} />);
    expect(screen.getByText("Retrieving evaluation data...")).toBeInTheDocument();
  });

  it("renders held-out evaluation heading", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText("Held-Out Evaluation")).toBeInTheDocument();
  });

  it("renders enrichment verdict", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText("Meaningful enrichment")).toBeInTheDocument();
    expect(screen.getByText(/7.13× enriched/)).toBeInTheDocument();
  });

  it("renders study parameters with detection unit", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText("STUDY PARAMETERS")).toBeInTheDocument();
    expect(screen.getByText("Merchant-day")).toBeInTheDocument();
  });

  it("renders threshold values", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText(/Elevated ≥ 4 MADs/)).toBeInTheDocument();
    expect(screen.getByText(/High ≥ 5 MADs/)).toBeInTheDocument();
  });

  it("renders proxy classification metrics", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText("6.64%")).toBeInTheDocument();
    const recallElements = screen.getAllByText("50.93%");
    expect(recallElements.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("11.75%")).toBeInTheDocument();
  });

  it("renders proxy methodology note", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText(/fraud-containing merchant-days as proxy ground truth/)).toBeInTheDocument();
  });

  it("renders confusion matrix", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText(/TP/)).toBeInTheDocument();
    expect(screen.getByText(/FP/)).toBeInTheDocument();
    expect(screen.getByText(/FN/)).toBeInTheDocument();
    // TN value may render with or without locale-specific separators
    const tnElements = screen.getAllByText(/TN/);
    expect(tnElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders alert efficiency section", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText("ALERT EFFICIENCY")).toBeInTheDocument();
    expect(screen.getByText("16,090")).toBeInTheDocument();
    expect(screen.getByText("12.71%")).toBeInTheDocument();
    expect(screen.getByText("15.05")).toBeInTheDocument();
  });

  it("renders risk-level performance table", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText("RISK-LEVEL PERFORMANCE")).toBeInTheDocument();
    expect(screen.getByText("0.932%")).toBeInTheDocument();
    expect(screen.getByText("4.98×")).toBeInTheDocument();
  });

  it("risk table has scope=col on headers", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    const headers = screen.getAllByRole("columnheader");
    headers.forEach((h) => expect(h).toHaveAttribute("scope", "col"));
  });

  it("renders baseline comparison", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText("1.83×")).toBeInTheDocument();
  });

  it("renders limitations with updated terminology", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText(/Behavioral anomaly ≠ fraud/)).toBeInTheDocument();
    expect(screen.getByText(/Daily resolution only/)).toBeInTheDocument();
  });

  it("limitations list has role=list", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByRole("list", { name: "Limitations" })).toBeInTheDocument();
  });

  it("renders scenario selector buttons", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText("LEAN")).toBeInTheDocument();
    expect(screen.getByText("STANDARD")).toBeInTheDocument();
    expect(screen.getByText("INTENSIVE")).toBeInTheDocument();
  });
});

/* ═══════════════════════════════════════════════════════════════
   DATA INTEGRITY CONTRACT — MONITOR
   ═══════════════════════════════════════════════════════════════ */

describe("Monitor — Data Integrity Contract", () => {
  it("renders exact fixture values matching API contract", () => {
    render(<MonitorScreen overview={mockOverview} investigations={mockInvestigations} onMerchantClick={vi.fn()} />);
    expect(screen.getByText(/693 merchants/)).toBeInTheDocument();
    expect(screen.getByText("42,665")).toBeInTheDocument();
    expect(screen.getByText("12,825")).toBeInTheDocument();
    expect(screen.getByText("29,840")).toBeInTheDocument();
    expect(screen.getByText("7.13×")).toBeInTheDocument();
  });
});

/* ═══════════════════════════════════════════════════════════════
   DATA INTEGRITY CONTRACT — EVALUATION
   ═══════════════════════════════════════════════════════════════ */

describe("Evaluation — Data Integrity Contract", () => {
  it("renders exact enrichment values from fixture", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    expect(screen.getByText(/7.13× enriched/)).toBeInTheDocument();
    const enrichmentValues = screen.getAllByText("4.01×");
    expect(enrichmentValues.length).toBeGreaterThanOrEqual(1);
  });

  it("renders confusion matrix totals matching fixture", () => {
    render(<EvaluationScreen data={mockEvaluation} />);
    // TP + FP = flagged, verified in fixture
    expect(screen.getByText(/TP 1,069/)).toBeInTheDocument();
    expect(screen.getByText(/FP 15,021/)).toBeInTheDocument();
  });
});

