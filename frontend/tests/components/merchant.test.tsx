import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MerchantRhythmScreen } from "@/components/screens/MerchantRhythmScreen";
import { mockMerchantRhythm, mockMerchantNoDeviations } from "../fixtures/data";

function renderMerchant(overrides: Record<string, unknown> = {}) {
  const defaults = {
    rhythm: null as typeof mockMerchantRhythm | null,
    merchantName: null as string | null,
    onSelectMerchant: vi.fn(),
    loading: false,
    error: null as string | null,
  };
  const props = { ...defaults, ...overrides };
  return { ...render(<MerchantRhythmScreen {...props} />), ...props };
}

/* ═══════════════════════════════════════════════════════════════
   INITIAL STATE
   ═══════════════════════════════════════════════════════════════ */

describe("MerchantRhythmScreen — Initial State", () => {
  it("shows merchant selection prompt when no merchant selected", () => {
    renderMerchant();
    expect(screen.getByText("Select a merchant")).toBeInTheDocument();
  });

  it("renders search input", () => {
    renderMerchant();
    expect(screen.getByLabelText("Search merchant by name")).toBeInTheDocument();
  });

  it("search input has accessible label element", () => {
    renderMerchant();
    expect(screen.getByText("SEARCH MERCHANT")).toBeInTheDocument();
  });
});

/* ═══════════════════════════════════════════════════════════════
   SEARCH FLOW
   ═══════════════════════════════════════════════════════════════ */

describe("MerchantRhythmScreen — Search", () => {
  it("calls onSelectMerchant on Enter key", () => {
    const { onSelectMerchant } = renderMerchant();
    const input = screen.getByLabelText("Search merchant by name");
    fireEvent.change(input, { target: { value: "Kovacek Ltd" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onSelectMerchant).toHaveBeenCalledWith("Kovacek Ltd");
  });

  it("does not call onSelectMerchant for empty input", () => {
    const { onSelectMerchant } = renderMerchant();
    const input = screen.getByLabelText("Search merchant by name");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onSelectMerchant).not.toHaveBeenCalled();
  });

  it("clears search input after search", () => {
    renderMerchant();
    const input = screen.getByLabelText("Search merchant by name") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Test" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(input.value).toBe("");
  });
});

/* ═══════════════════════════════════════════════════════════════
   LOADING STATE
   ═══════════════════════════════════════════════════════════════ */

describe("MerchantRhythmScreen — Loading", () => {
  it("shows loading state with merchant name", () => {
    renderMerchant({ loading: true, merchantName: "Kovacek Ltd" });
    expect(screen.getByText("Retrieving behavioral data for Kovacek Ltd...")).toBeInTheDocument();
  });

  it("does not show stale data while loading", () => {
    // CRITICAL REGRESSION TEST: No stale merchant data during search
    renderMerchant({ loading: true, merchantName: "Kovacek Ltd", rhythm: null });
    expect(screen.queryByText("90-DAY OBSERVATION")).not.toBeInTheDocument();
    expect(screen.queryByText("OBSERVATION PERIOD")).not.toBeInTheDocument();
  });
});

/* ═══════════════════════════════════════════════════════════════
   SUCCESS STATE
   ═══════════════════════════════════════════════════════════════ */

describe("MerchantRhythmScreen — Success", () => {
  it("renders merchant name as heading", () => {
    renderMerchant({ rhythm: mockMerchantRhythm, merchantName: "Kovacek Ltd" });
    expect(screen.getByText("Kovacek Ltd")).toBeInTheDocument();
  });

  it("renders observation period metric", () => {
    renderMerchant({ rhythm: mockMerchantRhythm, merchantName: "Kovacek Ltd" });
    expect(screen.getByText("90")).toBeInTheDocument();
    expect(screen.getByText("days analyzed")).toBeInTheDocument();
  });

  it("renders anomaly days metric", () => {
    renderMerchant({ rhythm: mockMerchantRhythm, merchantName: "Kovacek Ltd" });
    expect(screen.getByText("18")).toBeInTheDocument();
  });

  it("renders chart with figure role", () => {
    renderMerchant({ rhythm: mockMerchantRhythm, merchantName: "Kovacek Ltd" });
    expect(screen.getByRole("figure", { name: "Daily payment value chart" })).toBeInTheDocument();
  });

  it("renders recent deviations when present", () => {
    renderMerchant({ rhythm: mockMerchantRhythm, merchantName: "Kovacek Ltd" });
    expect(screen.getByText("RECENT DEVIATIONS")).toBeInTheDocument();
  });

  it("renders no-deviation message for clean merchant", () => {
    renderMerchant({ rhythm: mockMerchantNoDeviations, merchantName: "Clean Corp" });
    expect(screen.getByText(/No recent deviations/)).toBeInTheDocument();
  });
});

/* ═══════════════════════════════════════════════════════════════
   ERROR / NOT FOUND
   ═══════════════════════════════════════════════════════════════ */

describe("MerchantRhythmScreen — Error States", () => {
  it("shows error message for not-found merchant", () => {
    renderMerchant({ error: 'No record found for "Unknown". Check the merchant name and try again.', merchantName: "Unknown" });
    expect(screen.getByText(/No record found/)).toBeInTheDocument();
  });

  it("does not show chart or metrics during error", () => {
    renderMerchant({ error: "Error occurred", merchantName: "Unknown" });
    expect(screen.queryByRole("figure")).not.toBeInTheDocument();
    expect(screen.queryByText("OBSERVATION PERIOD")).not.toBeInTheDocument();
  });

  it("does not show error while loading", () => {
    renderMerchant({ loading: true, error: "Stale error", merchantName: "Test" });
    expect(screen.queryByText("Stale error")).not.toBeInTheDocument();
  });
});

/* ═══════════════════════════════════════════════════════════════
   NO-STALE-DATA REGRESSION
   ═══════════════════════════════════════════════════════════════ */

describe("MerchantRhythmScreen — No Stale Data Regression", () => {
  it("clears previous merchant data when loading new merchant", () => {
    // Simulate: previous merchant was "Clean Corp", now loading "Kovacek Ltd"
    // rhythm should be null during loading to prevent stale data display
    const { rerender } = render(
      <MerchantRhythmScreen rhythm={mockMerchantNoDeviations} merchantName="Clean Corp" onSelectMerchant={vi.fn()} loading={false} error={null} />
    );

    // User initiates new search — rhythm cleared, loading set
    rerender(
      <MerchantRhythmScreen rhythm={null} merchantName="Kovacek Ltd" onSelectMerchant={vi.fn()} loading={true} error={null} />
    );

    // Old merchant data should NOT be visible
    expect(screen.queryByText("Clean Corp")).not.toBeInTheDocument();
    expect(screen.queryByText("60")).not.toBeInTheDocument(); // old total_days
    // Loading state for new merchant should be visible
    expect(screen.getByText(/Retrieving behavioral data for Kovacek Ltd/)).toBeInTheDocument();
  });
});
