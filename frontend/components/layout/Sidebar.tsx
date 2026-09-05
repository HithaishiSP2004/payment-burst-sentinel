"use client";

import type React from "react";
import type { Page } from "@/types/api";

interface NavItem {
  page: Page;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  {
    page: "monitor", label: "Monitor",
    icon: <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>,
  },
  {
    page: "investigations", label: "Investigations",
    icon: <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>,
  },
  {
    page: "merchant", label: "Merchant Rhythm",
    icon: <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>,
  },
  {
    page: "evaluation", label: "Evaluation",
    icon: <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>,
  },
];

interface SidebarProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
  sidebarOpen: boolean;
  onOpenSidebar: () => void;
  onCloseSidebar: () => void;
  merchantCount: number | null;
}

export function Sidebar({ currentPage, onNavigate, sidebarOpen, onCloseSidebar, merchantCount }: SidebarProps) {
  return (
    <>
      {sidebarOpen && <div className="sidebar-overlay visible" onClick={onCloseSidebar} />}

      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`} role="navigation" aria-label="Main navigation">
        <button className="sidebar-close" onClick={onCloseSidebar} aria-label="Close navigation">×</button>

        <div className="sidebar-brand">
          <div className="sidebar-brand-name">Sentinel</div>
          <div className="sidebar-brand-title">Payment Burst<br />Sentinel</div>
        </div>

        <div className="sidebar-divider" />
        <div className="sidebar-section-label">Observation</div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.page}
              className={`nav-item ${currentPage === item.page ? "active" : ""}`}
              onClick={() => onNavigate(item.page)}
              aria-current={currentPage === item.page ? "page" : undefined}
              aria-label={item.label}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-divider" />

        <div className="sidebar-status">
          <div className="sidebar-status-item">
            <span className="status-dot" />
            DETECTION POLICY: FROZEN
          </div>
          <div className="sidebar-status-item">
            <span className="status-dot" />
            {merchantCount != null ? `${merchantCount} MERCHANTS` : "LOADING..."}
          </div>
        </div>

        <div className="sidebar-divider" />
        <div className="sidebar-section-label">System</div>
        <nav className="sidebar-nav sidebar-nav-secondary">
          <button
            className={`nav-item nav-item-secondary ${currentPage === "integration" ? "active" : ""}`}
            onClick={() => onNavigate("integration")}
            aria-current={currentPage === "integration" ? "page" : undefined}
            aria-label="Integration"
          >
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
            Integration
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-guardrail">
            <strong>METHOD NOTE</strong><br />
            Behavioral deviation<br />≠ confirmed fraud
          </div>
        </div>
      </aside>
    </>
  );
}

export function MobileHeader({ onOpenSidebar }: { onOpenSidebar: () => void }) {
  return (
    <div className="mobile-header">
      <div className="mobile-brand">
        <span className="mobile-brand-name">Sentinel</span>
        <span className="mobile-brand-title">Payment Burst Sentinel</span>
      </div>
      <button className="hamburger-btn" onClick={onOpenSidebar} aria-label="Open navigation">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
      </button>
    </div>
  );
}
