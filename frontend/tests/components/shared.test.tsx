import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { LoadingState } from "@/components/shared/LoadingState";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorBanner } from "@/components/shared/ErrorBanner";

/* ═══════════════════════════════════════════════════════════════
   LoadingState
   ═══════════════════════════════════════════════════════════════ */

describe("LoadingState", () => {
  it("renders the label text", () => {
    render(<LoadingState label="Retrieving system overview..." />);
    expect(screen.getByText("Retrieving system overview...")).toBeInTheDocument();
  });

  it("has status role for assistive technology", () => {
    render(<LoadingState label="Loading..." />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("has accessible aria-label", () => {
    render(<LoadingState label="Loading data..." />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-label", "Loading data...");
  });
});

/* ═══════════════════════════════════════════════════════════════
   EmptyState
   ═══════════════════════════════════════════════════════════════ */

describe("EmptyState", () => {
  it("renders the message", () => {
    render(<EmptyState message="No deviations match the current filters." />);
    expect(screen.getByText("No deviations match the current filters.")).toBeInTheDocument();
  });

  it("renders the em-dash icon", () => {
    render(<EmptyState message="No data" />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("has status role", () => {
    render(<EmptyState message="Empty" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});

/* ═══════════════════════════════════════════════════════════════
   ErrorBanner
   ═══════════════════════════════════════════════════════════════ */

describe("ErrorBanner", () => {
  it("renders error message", () => {
    render(<ErrorBanner message="Cannot connect to API." />);
    expect(screen.getByText("Cannot connect to API.")).toBeInTheDocument();
  });

  it("has alert role", () => {
    render(<ErrorBanner message="Error" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("renders retry button when onRetry provided", () => {
    const onRetry = vi.fn();
    render(<ErrorBanner message="Error" onRetry={onRetry} />);
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("calls onRetry when retry button clicked", () => {
    const onRetry = vi.fn();
    render(<ErrorBanner message="Error" onRetry={onRetry} />);
    fireEvent.click(screen.getByText("Retry"));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("does not render retry button when onRetry not provided", () => {
    render(<ErrorBanner message="Error" />);
    expect(screen.queryByText("Retry")).not.toBeInTheDocument();
  });
});
