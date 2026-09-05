import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { IntegrationScreen } from "@/components/screens/IntegrationScreen";
import { mockOverview } from "../fixtures/data";

/* ═══════════════════════════════════════════════════════════════
   INTEGRATION SCREEN TESTS — Phase 17
   Verifies 3-layer demo experience, architecture boundaries,
   and async state handling without act() warnings.
   ═══════════════════════════════════════════════════════════════ */

vi.mock("@/lib/api", () => ({
  getIntegrationStatus: vi.fn().mockResolvedValue({
    current_data_mode: "dataset",
    integration_readiness: {
      provider_abstraction: true,
      canonical_normalization: true,
      payload_validation: true,
      idempotency_boundary: true,
    },
    providers: {
      demo: { available: true },
      razorpay: { adapter_ready: true, configured: false, connected: false },
    },
  }),
  demoIngest: vi.fn().mockResolvedValue({
    event_id: "test-uuid-001",
    status: "accepted",
    canonical_event: {
      event_id: "test-uuid-001",
      source: "demo",
      source_event_id: "demo_evt_abc123",
      merchant_id: "demo_merchant_001",
      merchant_name: "Acme Electronics (Demo)",
      timestamp: "2024-06-15T05:00:00+00:00",
      amount: "2499.00",
      currency: "INR",
      normalized_status: "captured",
      provider_status: "captured",
      payment_method: "card",
      event_type: "payment",
      source_metadata: { provider: "demo", mode: "simulated", label: "SIMULATED PROVIDER PAYLOAD" },
      received_at: "2024-06-15T05:00:00+00:00",
      schema_version: "1.0",
    },
    validation_errors: [],
    pipeline_status: {
      payload_validated: true,
      canonical_event_created: true,
      historical_aggregation: "future_phase",
      detection_execution: "not_triggered",
      ai_analysis: "not_triggered",
    },
  }),
  getOverview: vi.fn(),
  getInvestigations: vi.fn(),
  getEvaluation: vi.fn(),
  getMerchantRhythm: vi.fn(),
  generateAIBrief: vi.fn(),
}));

describe("IntegrationScreen", () => {
  it("renders current data mode", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("CURRENT MODE")).toBeInTheDocument();
      expect(screen.getByText("Historical Analytical Dataset")).toBeInTheDocument();
    });
  });

  it("renders merchant count from overview", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText(/693 merchants/)).toBeInTheDocument();
    });
  });

  it("renders why this matters section", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Why This Boundary Matters")).toBeInTheDocument();
      expect(screen.getAllByText(/provider-neutral canonical contract/).length).toBeGreaterThan(0);
    });
  });

  it("renders integration readiness", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Provider abstraction")).toBeInTheDocument();
      expect(screen.getByText("Canonical event normalization")).toBeInTheDocument();
      expect(screen.getByText("Payload validation")).toBeInTheDocument();
      expect(screen.getByText("Idempotency boundary")).toBeInTheDocument();
    });
  });

  it("shows Razorpay as not configured", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText(/Razorpay adapter ready.*credentials not configured/)).toBeInTheDocument();
    });
  });

  it("renders demo integration button", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Generate Demo Event")).toBeInTheDocument();
    });
  });

  it("shows demo result after clicking generate", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Generate Demo Event")).toBeInTheDocument();
    });
    const btn = screen.getByText("Generate Demo Event");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByText("SIMULATED PROVIDER PAYLOAD")).toBeInTheDocument();
    });
  });

  it("shows pipeline status with NOT TRIGGERED", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Generate Demo Event")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Generate Demo Event"));

    await waitFor(() => {
      expect(screen.getByText("PIPELINE STATUS")).toBeInTheDocument();
      expect(screen.getByText("Payload validated")).toBeInTheDocument();
      expect(screen.getByText("Canonical event created")).toBeInTheDocument();
      expect(screen.getByText(/Detection execution/)).toBeInTheDocument();
      expect(screen.getByText(/AI analysis/)).toBeInTheDocument();
      expect(screen.getAllByText("NOT TRIGGERED").length).toBe(2);
    });
  });

  it("shows canonical event details", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Generate Demo Event")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Generate Demo Event"));

    await waitFor(() => {
      expect(screen.getByText("CANONICAL EVENT")).toBeInTheDocument();
    });
  });

  it("renders architecture flow sections", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("CURRENT IMPLEMENTATION")).toBeInTheDocument();
      expect(screen.getByText("FUTURE ARCHITECTURE")).toBeInTheDocument();
      expect(screen.getByText("NOT IMPLEMENTED IN PHASE 16")).toBeInTheDocument();
    });
  });

  it("shows STOP boundary in current flow", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("STOP")).toBeInTheDocument();
      expect(screen.getByText(/STOP \/\/ CURRENT BOUNDARY:/)).toBeInTheDocument();
    });
  });

  it("renders architecture section with boundary", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Architecture")).toBeInTheDocument();
      expect(screen.getByText("Validation")).toBeInTheDocument();
    });
  });

  it("renders Layer 1 human-readable summary cards with merchant and amount", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Generate Demo Event")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Generate Demo Event"));

    await waitFor(() => {
      expect(screen.getAllByText("Acme Electronics (Demo)").length).toBeGreaterThan(0);
      expect(screen.getAllByText("INR 2499.00").length).toBeGreaterThan(0);
    });
  });

  it("renders Layer 2 field transformation matrix table", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Generate Demo Event")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Generate Demo Event"));

    await waitFor(() => {
      expect(screen.getByText("Field Transformation Matrix")).toBeInTheDocument();
      expect(screen.getByText("Decimal string preservation")).toBeInTheDocument();
      expect(screen.getByText("Normalized to UTC (ISO-8601)")).toBeInTheDocument();
      expect(screen.getByText("Canonical status mapping")).toBeInTheDocument();
    });
  });

  it("renders Layer 3 expandable raw JSON technical disclosures with copy buttons", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Generate Demo Event")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Generate Demo Event"));

    await waitFor(() => {
      expect(screen.getByText("View Raw Simulated Payload (JSON)")).toBeInTheDocument();
      expect(screen.getByText("View Full Canonical Event (JSON)")).toBeInTheDocument();
      expect(screen.getByLabelText("Copy raw payload JSON")).toBeInTheDocument();
      expect(screen.getByLabelText("Copy canonical event JSON")).toBeInTheDocument();
    });
  });

  it("provides full technical values via title attribute without fragmentation", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Generate Demo Event")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Generate Demo Event"));

    await waitFor(() => {
      const canonicalIdEl = screen.getByTitle("test-uuid-001");
      expect(canonicalIdEl).toBeInTheDocument();
      expect(canonicalIdEl).toHaveClass("tech-val-id");

      const timestampEl = screen.getByTitle("2024-06-15T05:00:00+00:00");
      expect(timestampEl).toBeInTheDocument();
      expect(timestampEl).toHaveClass("tech-val-timestamp");
    });
  });

  it("renders NOT TRIGGERED status tags distinctly in pipeline status", async () => {
    render(<IntegrationScreen overview={mockOverview} />);
    await waitFor(() => {
      expect(screen.getByText("Generate Demo Event")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Generate Demo Event"));

    await waitFor(() => {
      const notTriggeredTags = screen.getAllByText("NOT TRIGGERED");
      expect(notTriggeredTags.length).toBe(2);
      notTriggeredTags.forEach((tag) => {
        expect(tag).toHaveClass("pipeline-tag-not-triggered");
      });
    });
  });
});
