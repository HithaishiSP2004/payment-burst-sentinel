import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { InvestigationsScreen } from "@/components/screens/InvestigationsScreen";
import { mockInvestigations, mockEmptyInvestigations } from "../fixtures/data";

function renderInvestigations(overrides: Record<string, unknown> = {}) {
  const defaults = {
    data: mockInvestigations,
    riskFilter: null as string | null,
    typeFilter: null as string | null,
    setRiskFilter: vi.fn(),
    setTypeFilter: vi.fn(),
    onMerchantClick: vi.fn(),
    currentPage: 0,
    onPageChange: vi.fn(),
  };
  const props = { ...defaults, ...overrides };
  return { ...render(<InvestigationsScreen {...props} />), ...props };
}

/* ═══════════════════════════════════════════════════════════════
   DATA RENDERING
   ═══════════════════════════════════════════════════════════════ */

describe("InvestigationsScreen — Data Rendering", () => {
  it("shows loading state when data is null", () => {
    renderInvestigations({ data: null });
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText("Retrieving investigation records...")).toBeInTheDocument();
  });

  it("renders investigation events", () => {
    renderInvestigations();
    expect(screen.getByText("Kovacek Ltd")).toBeInTheDocument();
    expect(screen.getByText("Test Merchant B")).toBeInTheDocument();
    expect(screen.getByText("Volume Corp")).toBeInTheDocument();
  });

  it("renders event count", () => {
    renderInvestigations();
    expect(screen.getByText("3 EVENTS")).toBeInTheDocument();
  });

  it("renders empty state for zero results", () => {
    renderInvestigations({ data: mockEmptyInvestigations });
    expect(screen.getByText(/No deviations match/)).toBeInTheDocument();
  });
});

/* ═══════════════════════════════════════════════════════════════
   FILTER INTERACTION
   ═══════════════════════════════════════════════════════════════ */

describe("InvestigationsScreen — Filtering", () => {
  it("renders risk filter buttons", () => {
    renderInvestigations();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Elevated")).toBeInTheDocument();
  });

  it("renders signal filter buttons", () => {
    renderInvestigations();
    expect(screen.getByText("Amount")).toBeInTheDocument();
    expect(screen.getByText("Volume")).toBeInTheDocument();
    expect(screen.getByText("Combined")).toBeInTheDocument();
  });

  it("calls setRiskFilter when High clicked", () => {
    const { setRiskFilter } = renderInvestigations();
    fireEvent.click(screen.getByText("High"));
    expect(setRiskFilter).toHaveBeenCalledWith("high");
  });

  it("calls setRiskFilter(null) when High clicked while active", () => {
    const { setRiskFilter } = renderInvestigations({ riskFilter: "high" });
    fireEvent.click(screen.getByText("High"));
    expect(setRiskFilter).toHaveBeenCalledWith(null);
  });

  it("calls setTypeFilter when Amount clicked", () => {
    const { setTypeFilter } = renderInvestigations();
    fireEvent.click(screen.getByText("Amount"));
    expect(setTypeFilter).toHaveBeenCalledWith("amount_anomaly");
  });

  it("calls setTypeFilter(null) when All (signal) clicked", () => {
    const { setTypeFilter } = renderInvestigations({ typeFilter: "amount_anomaly" });
    const allButtons = screen.getAllByText("All");
    fireEvent.click(allButtons[1]); // Second "All" is for signal filter
    expect(setTypeFilter).toHaveBeenCalledWith(null);
  });
});

/* ═══════════════════════════════════════════════════════════════
   ARIA STATE
   ═══════════════════════════════════════════════════════════════ */

describe("InvestigationsScreen — Accessibility", () => {
  it("filter toolbar has role=toolbar", () => {
    renderInvestigations();
    expect(screen.getByRole("toolbar")).toBeInTheDocument();
  });

  it("filter groups have role=group", () => {
    renderInvestigations();
    expect(screen.getAllByRole("group")).toHaveLength(2);
  });

  it("active risk filter has aria-pressed=true", () => {
    renderInvestigations({ riskFilter: "high" });
    expect(screen.getByText("High")).toHaveAttribute("aria-pressed", "true");
  });

  it("inactive risk filter has aria-pressed=false", () => {
    renderInvestigations({ riskFilter: null });
    expect(screen.getByText("High")).toHaveAttribute("aria-pressed", "false");
  });

  it("All risk button has aria-pressed=true when no filter", () => {
    renderInvestigations({ riskFilter: null });
    const allButtons = screen.getAllByText("All");
    expect(allButtons[0]).toHaveAttribute("aria-pressed", "true");
  });

  it("investigation list has role=list", () => {
    renderInvestigations();
    expect(screen.getByRole("list", { name: "Investigation events" })).toBeInTheDocument();
  });
});

/* ═══════════════════════════════════════════════════════════════
   KEYBOARD INTERACTION
   ═══════════════════════════════════════════════════════════════ */

describe("InvestigationsScreen — Keyboard Navigation", () => {
  it("investigation rows are keyboard-reachable", () => {
    renderInvestigations();
    const items = screen.getAllByRole("listitem");
    expect(items[0]).toHaveAttribute("tabIndex", "0");
  });

  it("Enter key activates merchant click", () => {
    const { onMerchantClick } = renderInvestigations();
    const items = screen.getAllByRole("listitem");
    fireEvent.keyDown(items[0], { key: "Enter" });
    expect(onMerchantClick).toHaveBeenCalledWith("Kovacek Ltd");
  });

  it("Space key activates merchant click", () => {
    const { onMerchantClick } = renderInvestigations();
    const items = screen.getAllByRole("listitem");
    fireEvent.keyDown(items[0], { key: " " });
    expect(onMerchantClick).toHaveBeenCalledWith("Kovacek Ltd");
  });

  it("click activates merchant click", () => {
    const { onMerchantClick } = renderInvestigations();
    const items = screen.getAllByRole("listitem");
    fireEvent.click(items[0]);
    expect(onMerchantClick).toHaveBeenCalledWith("Kovacek Ltd");
  });
});
