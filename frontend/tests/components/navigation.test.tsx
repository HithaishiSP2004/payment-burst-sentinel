import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Sidebar, MobileHeader } from "@/components/layout/Sidebar";

function renderSidebar(overrides: Record<string, unknown> = {}) {
  const defaults = {
    currentPage: "monitor" as const,
    onNavigate: vi.fn(),
    sidebarOpen: false,
    onOpenSidebar: vi.fn(),
    onCloseSidebar: vi.fn(),
    merchantCount: 693,
  };
  const props = { ...defaults, ...overrides };
  return { ...render(<Sidebar {...props} />), ...props };
}

/* ═══════════════════════════════════════════════════════════════
   DESKTOP NAVIGATION
   ═══════════════════════════════════════════════════════════════ */

describe("Sidebar — Desktop Navigation", () => {
  it("renders all navigation items", () => {
    renderSidebar();
    expect(screen.getByText("Monitor")).toBeInTheDocument();
    expect(screen.getByText("Investigations")).toBeInTheDocument();
    expect(screen.getByText("Merchant Rhythm")).toBeInTheDocument();
    expect(screen.getByText("Evaluation")).toBeInTheDocument();
  });

  it("calls onNavigate when nav item clicked", () => {
    const { onNavigate } = renderSidebar();
    fireEvent.click(screen.getByText("Investigations"));
    expect(onNavigate).toHaveBeenCalledWith("investigations");
  });

  it("navigates to merchant page", () => {
    const { onNavigate } = renderSidebar();
    fireEvent.click(screen.getByText("Merchant Rhythm"));
    expect(onNavigate).toHaveBeenCalledWith("merchant");
  });

  it("navigates to evaluation page", () => {
    const { onNavigate } = renderSidebar();
    fireEvent.click(screen.getByText("Evaluation"));
    expect(onNavigate).toHaveBeenCalledWith("evaluation");
  });
});

/* ═══════════════════════════════════════════════════════════════
   ACTIVE NAVIGATION SEMANTICS
   ═══════════════════════════════════════════════════════════════ */

describe("Sidebar — Active Navigation Semantics", () => {
  it("active page has aria-current=page", () => {
    renderSidebar({ currentPage: "monitor" });
    expect(screen.getByLabelText("Monitor")).toHaveAttribute("aria-current", "page");
  });

  it("inactive pages do not have aria-current", () => {
    renderSidebar({ currentPage: "monitor" });
    expect(screen.getByLabelText("Investigations")).not.toHaveAttribute("aria-current");
  });

  it("switching active page updates aria-current", () => {
    renderSidebar({ currentPage: "investigations" });
    expect(screen.getByLabelText("Investigations")).toHaveAttribute("aria-current", "page");
    expect(screen.getByLabelText("Monitor")).not.toHaveAttribute("aria-current");
  });
});

/* ═══════════════════════════════════════════════════════════════
   SIDEBAR STATUS
   ═══════════════════════════════════════════════════════════════ */

describe("Sidebar — Status", () => {
  it("shows merchant count", () => {
    renderSidebar({ merchantCount: 693 });
    expect(screen.getByText("693 MERCHANTS")).toBeInTheDocument();
  });

  it("shows LOADING when merchant count is null", () => {
    renderSidebar({ merchantCount: null });
    expect(screen.getByText("LOADING...")).toBeInTheDocument();
  });

  it("shows frozen policy status", () => {
    renderSidebar();
    expect(screen.getByText("DETECTION POLICY: FROZEN")).toBeInTheDocument();
  });

  it("shows method guardrail", () => {
    renderSidebar();
    expect(screen.getByText("METHOD NOTE")).toBeInTheDocument();
  });
});

/* ═══════════════════════════════════════════════════════════════
   SIDEBAR NAVIGATION ROLE
   ═══════════════════════════════════════════════════════════════ */

describe("Sidebar — Accessibility", () => {
  it("has navigation role", () => {
    renderSidebar();
    expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
  });

  it("has accessible close button", () => {
    renderSidebar({ sidebarOpen: true });
    expect(screen.getByLabelText("Close navigation")).toBeInTheDocument();
  });

  it("close button calls onCloseSidebar", () => {
    const { onCloseSidebar } = renderSidebar({ sidebarOpen: true });
    fireEvent.click(screen.getByLabelText("Close navigation"));
    expect(onCloseSidebar).toHaveBeenCalledOnce();
  });
});

/* ═══════════════════════════════════════════════════════════════
   MOBILE HEADER
   ═══════════════════════════════════════════════════════════════ */

describe("MobileHeader", () => {
  it("renders brand name", () => {
    render(<MobileHeader onOpenSidebar={vi.fn()} />);
    expect(screen.getByText("Sentinel")).toBeInTheDocument();
  });

  it("renders hamburger button with accessible label", () => {
    render(<MobileHeader onOpenSidebar={vi.fn()} />);
    expect(screen.getByLabelText("Open navigation")).toBeInTheDocument();
  });

  it("calls onOpenSidebar when hamburger clicked", () => {
    const onOpen = vi.fn();
    render(<MobileHeader onOpenSidebar={onOpen} />);
    fireEvent.click(screen.getByLabelText("Open navigation"));
    expect(onOpen).toHaveBeenCalledOnce();
  });
});

/* ═══════════════════════════════════════════════════════════════
   MOBILE DRAWER BEHAVIOR
   ═══════════════════════════════════════════════════════════════ */

describe("Sidebar — Mobile Drawer", () => {
  it("sidebar has open class when sidebarOpen is true", () => {
    renderSidebar({ sidebarOpen: true });
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    expect(nav.className).toContain("open");
  });

  it("sidebar does not have open class when closed", () => {
    renderSidebar({ sidebarOpen: false });
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    expect(nav.className).not.toContain("open");
  });

  it("overlay is visible when sidebar open", () => {
    const { container } = renderSidebar({ sidebarOpen: true });
    const overlay = container.querySelector(".sidebar-overlay");
    expect(overlay?.className).toContain("visible");
  });

  it("clicking overlay closes sidebar", () => {
    const { onCloseSidebar, container } = renderSidebar({ sidebarOpen: true });
    const overlay = container.querySelector(".sidebar-overlay.visible");
    if (overlay) fireEvent.click(overlay);
    expect(onCloseSidebar).toHaveBeenCalledOnce();
  });
});
