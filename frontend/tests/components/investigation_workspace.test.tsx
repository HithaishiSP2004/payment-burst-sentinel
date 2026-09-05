import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { InvestigationDetailWorkspace } from "@/components/screens/InvestigationDetailWorkspace";
import { InvestigationsScreen } from "@/components/screens/InvestigationsScreen";
import { mockInvestigationDetail, mockInvestigations } from "../fixtures/data";
import * as api from "@/lib/api";

// Mock the API calls
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getInvestigationDetail: vi.fn(),
    generateAIBrief: vi.fn(),
  };
});

describe("InvestigationDetailWorkspace Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially while fetching evidence", () => {
    (api.getInvestigationDetail as any).mockReturnValue(new Promise(() => {})); // Never resolves

    render(
      <InvestigationDetailWorkspace
        merchant="Kovacek Ltd"
        date="2020-11-27"
        onBack={vi.fn()}
      />
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText(/Retrieving investigation evidence for/i)).toBeInTheDocument();
  });

  it("renders all 8 sections when evidence is successfully loaded", async () => {
    (api.getInvestigationDetail as any).mockResolvedValue(mockInvestigationDetail);

    render(
      <InvestigationDetailWorkspace
        merchant="Kovacek Ltd"
        date="2020-11-27"
        onBack={vi.fn()}
      />
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });

    // 01 Header & Reference
    expect(screen.getByText("INVESTIGATION INTELLIGENCE // EVIDENCE WORKSPACE")).toBeInTheDocument();
    expect(screen.getByText("Kovacek Ltd")).toBeInTheDocument();
    expect(screen.getByText("REFERENCE: Kovacek Ltd · 2020-11-27")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();

    // 02 Executive Evidence Snapshot
    expect(screen.getByText("EXECUTIVE EVIDENCE SNAPSHOT")).toBeInTheDocument();
    expect(screen.getByText("OBSERVED VALUE")).toBeInTheDocument();
    expect(screen.getByText("EXPECTED BASELINE")).toBeInTheDocument();
    expect(screen.getByText("DEVIATION MAGNITUDE")).toBeInTheDocument();
    expect(screen.getByText("BASELINE HISTORY")).toBeInTheDocument();

    // 03 & 04 Primary Evidence & Behavioral Context
    expect(screen.getByText("01 // PRIMARY DETECTION EVIDENCE")).toBeInTheDocument();
    expect(screen.getByText("Payment Value Deviation")).toBeInTheDocument();
    expect(screen.getByText("02 // BEHAVIORAL CONTEXT")).toBeInTheDocument();
    expect(screen.getByText("Transaction Volume Shift")).toBeInTheDocument();

    // 05 System Evidence Statements
    expect(screen.getByText("03 // FACTUAL DETECTION STATEMENTS")).toBeInTheDocument();
    expect(screen.getByText(/Total payment value/i)).toBeInTheDocument();

    // 06 Structured Detection Signal Map (3 groups)
    expect(screen.getByText("04 // DETECTION SIGNAL MAP")).toBeInTheDocument();
    expect(screen.getByText("CONFIRMED EVIDENCE")).toBeInTheDocument();
    expect(screen.getByText("ANALYTICAL CONTEXT")).toBeInTheDocument();
    expect(screen.getByText("SYSTEM BOUNDARIES")).toBeInTheDocument();
    expect(screen.getByText("Payment Value Shift")).toBeInTheDocument();
    expect(screen.getByText("Velocity Shift")).toBeInTheDocument();
    expect(screen.getByText("External Payment Ingestion")).toBeInTheDocument();
    expect(screen.getByText("Automated Fraud Enforcement")).toBeInTheDocument();

    // 07 Gemini Explanation Layer & Advisory Provenance
    expect(screen.getByText("05 // AI INVESTIGATION INTELLIGENCE")).toBeInTheDocument();
    expect(screen.getByText("PROVENANCE & BOUNDARIES")).toBeInTheDocument();
    expect(screen.getByText(/Gemini Advisory Layer/i)).toBeInTheDocument();
    expect(screen.getByText(/Advisory Only \(Non-binding\)/i)).toBeInTheDocument();

    // 08 Human Review Boundary
    expect(screen.getByText("06 // SYSTEM BOUNDARY")).toBeInTheDocument();
    expect(screen.getByText("Human Decision Boundary")).toBeInTheDocument();
    expect(screen.getByText(/Final assessment remains a human decision/i)).toBeInTheDocument();
  });

  it("renders 404 state with back button when record is not found", async () => {
    (api.getInvestigationDetail as any).mockRejectedValue(new Error("Investigation record not found (404)"));

    render(
      <InvestigationDetailWorkspace
        merchant="Unknown Merchant"
        date="2020-01-01"
        onBack={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Event Not Found")).toBeInTheDocument();
    });

    expect(screen.getByText(/The requested historical detection event for/i)).toBeInTheDocument();
    expect(screen.getByText("Return to Investigations Index")).toBeInTheDocument();
  });

  it("renders error state with retry button on network failure", async () => {
    (api.getInvestigationDetail as any).mockRejectedValue(new Error("Connection refused"));

    render(
      <InvestigationDetailWorkspace
        merchant="Kovacek Ltd"
        date="2020-11-27"
        onBack={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Unable to Retrieve Evidence")).toBeInTheDocument();
    });

    expect(screen.getByText("Connection refused")).toBeInTheDocument();
    expect(screen.getByText("Retry Evidence Retrieval")).toBeInTheDocument();
  });

  it("navigates back when Back button is clicked", async () => {
    (api.getInvestigationDetail as any).mockResolvedValue(mockInvestigationDetail);
    const handleBack = vi.fn();

    render(
      <InvestigationDetailWorkspace
        merchant="Kovacek Ltd"
        date="2020-11-27"
        onBack={handleBack}
      />
    );

    await waitFor(() => {
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });

    const backButton = screen.getByRole("button", { name: "Back to investigations index" });
    fireEvent.click(backButton);

    expect(handleBack).toHaveBeenCalledTimes(1);
  });

  it("navigates to merchant profile and evaluation when action buttons are clicked", async () => {
    (api.getInvestigationDetail as any).mockResolvedValue(mockInvestigationDetail);
    const handleMerchant = vi.fn();
    const handleEval = vi.fn();

    render(
      <InvestigationDetailWorkspace
        merchant="Kovacek Ltd"
        date="2020-11-27"
        onBack={vi.fn()}
        onNavigateToMerchant={handleMerchant}
        onNavigateToEvaluation={handleEval}
      />
    );

    await waitFor(() => {
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });

    const viewMerchantBtn = screen.getByText("View Merchant Rhythm →");
    fireEvent.click(viewMerchantBtn);
    expect(handleMerchant).toHaveBeenCalledWith("Kovacek Ltd");

    const viewEvalBtn = screen.getByText("View Detection Evaluation →");
    fireEvent.click(viewEvalBtn);
    expect(handleEval).toHaveBeenCalledTimes(1);
  });
});

describe("InvestigationsScreen Workspace Integration", () => {
  it("renders InvestigationDetailWorkspace when selectedInvestigation is present", async () => {
    (api.getInvestigationDetail as any).mockResolvedValue(mockInvestigationDetail);
    const handleSelect = vi.fn();

    render(
      <InvestigationsScreen
        data={mockInvestigations}
        riskFilter={null}
        typeFilter={null}
        setRiskFilter={vi.fn()}
        setTypeFilter={vi.fn()}
        onMerchantClick={vi.fn()}
        currentPage={1}
        onPageChange={vi.fn()}
        selectedInvestigation={{ merchant: "Kovacek Ltd", date: "2020-11-27" }}
        onSelectInvestigation={handleSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("INVESTIGATION INTELLIGENCE // EVIDENCE WORKSPACE")).toBeInTheDocument();
    });

    // Clicking back in workspace calls onSelectInvestigation(null)
    const backBtn = screen.getByRole("button", { name: "Back to investigations index" });
    fireEvent.click(backBtn);
    expect(handleSelect).toHaveBeenCalledWith(null);
  });

  it("calls onSelectInvestigation with event details when item is clicked", () => {
    const handleSelect = vi.fn();

    render(
      <InvestigationsScreen
        data={mockInvestigations}
        riskFilter={null}
        typeFilter={null}
        setRiskFilter={vi.fn()}
        setTypeFilter={vi.fn()}
        onMerchantClick={vi.fn()}
        currentPage={1}
        onPageChange={vi.fn()}
        onSelectInvestigation={handleSelect}
      />
    );

    const items = screen.getAllByRole("listitem");
    fireEvent.click(items[0]);

    expect(handleSelect).toHaveBeenCalledWith({
      merchant: "Kovacek Ltd",
      date: "2020-12-27",
    });
  });
});
