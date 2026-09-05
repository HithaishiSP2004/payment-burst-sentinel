"use client";

import { useState, useEffect } from "react";

import type { Page, Overview, InvestigationsResponse, EvaluationData, MerchantRhythm } from "@/types/api";
import { getOverview, getInvestigations, getEvaluation, getMerchantRhythm } from "@/lib/api";

import { Sidebar, MobileHeader } from "@/components/layout/Sidebar";
import { ErrorBanner } from "@/components/shared/ErrorBanner";
import { MonitorScreen } from "@/components/screens/MonitorScreen";
import { InvestigationsScreen } from "@/components/screens/InvestigationsScreen";
import { MerchantRhythmScreen } from "@/components/screens/MerchantRhythmScreen";
import { EvaluationScreen } from "@/components/screens/EvaluationScreen";
import { IntegrationScreen } from "@/components/screens/IntegrationScreen";

/* ═══════════════════════════════════════════════════════════════
   APPLICATION ROOT — Navigation, global state, screen routing
   ═══════════════════════════════════════════════════════════════ */

const PAGE_SIZE = 20;

export default function Home() {
  /* ─── Navigation ───────────────────────────────────────── */
  const [currentPage, setCurrentPage] = useState<Page>("monitor");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  /* ─── Data ─────────────────────────────────────────────── */
  const [overview, setOverview] = useState<Overview | null>(null);
  const [investigations, setInvestigations] = useState<InvestigationsResponse | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationData | null>(null);
  const [merchantRhythm, setMerchantRhythm] = useState<MerchantRhythm | null>(null);

  /* ─── Filters ──────────────────────────────────────────── */
  const [riskFilter, setRiskFilter] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);

  /* ─── Pagination ────────────────────────────────────────── */
  const [investigationPage, setInvestigationPage] = useState(1);

  /* ─── Merchant ─────────────────────────────────────────── */
  const [selectedMerchant, setSelectedMerchant] = useState<string | null>(null);
  const [merchantLoading, setMerchantLoading] = useState(false);
  const [merchantError, setMerchantError] = useState<string | null>(null);

  /* ─── Global Error ─────────────────────────────────────── */
  const [apiError, setApiError] = useState<string | null>(null);

  /* ─── Investigation Detail Workspace ───────────────────── */
  const [selectedInvestigation, setSelectedInvestigation] = useState<{ merchant: string; date: string } | null>(null);

  /* ─── Data Fetching ────────────────────────────────────── */

  async function loadOverview() {
    try {
      setOverview(await getOverview());
      setApiError(null);
    } catch {
      setApiError("Cannot connect to API. Ensure the backend is running on port 8000.");
    }
  }

  async function loadInvestigations(page = 1) {
    try {
      const offset = (page - 1) * PAGE_SIZE;
      setInvestigations(await getInvestigations(riskFilter, typeFilter, PAGE_SIZE, offset));
    } catch { /* silently handled — screen shows loading state */ }
  }

  async function loadEvaluation() {
    try {
      setEvaluation(await getEvaluation());
    } catch { /* silently handled */ }
  }

  async function loadMerchantRhythm(name: string) {
    setMerchantLoading(true);
    setMerchantError(null);
    setMerchantRhythm(null);
    try {
      const data = await getMerchantRhythm(name);
      if (!data?.timeline?.length) {
        setMerchantError(`No behavioral data available for "${name}".`);
      } else {
        setMerchantRhythm(data);
        // Update the selected merchant name to the canonical name from API
        if (data.merchant && data.merchant !== name) {
          setSelectedMerchant(data.merchant);
        }
        setMerchantError(null);
      }
    } catch {
      setMerchantError(`No record found for "${name}". Check the merchant name and try again.`);
    }
    setMerchantLoading(false);
  }

  /* ─── Effects ──────────────────────────────────────────── */

  useEffect(() => { loadOverview(); loadInvestigations(1); loadEvaluation(); }, []);
  useEffect(() => { setInvestigationPage(1); loadInvestigations(1); }, [riskFilter, typeFilter]);
  useEffect(() => { loadInvestigations(investigationPage); }, [investigationPage]);
  useEffect(() => { if (selectedMerchant) loadMerchantRhythm(selectedMerchant); }, [selectedMerchant]);
  useEffect(() => { setSidebarOpen(false); }, [currentPage]);

  /* ─── Handlers ─────────────────────────────────────────── */

  function openMerchant(name: string) {
    setSelectedMerchant(name);
    setCurrentPage("merchant");
  }

  function openInvestigation(merchant: string, date: string) {
    setSelectedInvestigation({ merchant, date });
    setCurrentPage("investigations");
  }

  function navigateTo(page: Page) {
    if (page === "investigations" && currentPage === "investigations") {
      setSelectedInvestigation(null);
    }
    setCurrentPage(page);
  }

  function handlePageChange(page: number) {
    setInvestigationPage(page);
    // Scroll to top of content when paginating
    document.getElementById("main-content")?.scrollTo(0, 0);
  }

  function retryAll() {
    loadOverview();
    loadInvestigations(investigationPage);
    loadEvaluation();
  }

  /* ─── Render ───────────────────────────────────────────── */

  const quickMerchants = Array.from(
    new Set(investigations?.events.map((e) => e.merchant) ?? [])
  ).slice(0, 4);

  return (
    <div className="app-layout">
      <a href="#main-content" className="skip-link">Skip to content</a>

      <MobileHeader onOpenSidebar={() => setSidebarOpen(true)} />

      <Sidebar
        currentPage={currentPage}
        onNavigate={navigateTo}
        sidebarOpen={sidebarOpen}
        onOpenSidebar={() => setSidebarOpen(true)}
        onCloseSidebar={() => setSidebarOpen(false)}
        merchantCount={overview?.merchants_monitored ?? null}
      />

      <main className="main-content" id="main-content">
        {apiError && <ErrorBanner message={apiError} onRetry={retryAll} />}

        {currentPage === "monitor" && (
          <MonitorScreen
            overview={overview}
            investigations={investigations}
            onMerchantClick={openMerchant}
            onInvestigationClick={openInvestigation}
          />
        )}
        {currentPage === "investigations" && (
          <InvestigationsScreen
            data={investigations}
            riskFilter={riskFilter}
            typeFilter={typeFilter}
            setRiskFilter={setRiskFilter}
            setTypeFilter={setTypeFilter}
            onMerchantClick={openMerchant}
            currentPage={investigationPage}
            onPageChange={handlePageChange}
            selectedInvestigation={selectedInvestigation}
            onSelectInvestigation={setSelectedInvestigation}
            onNavigateToMerchant={openMerchant}
            onNavigateToEvaluation={() => navigateTo("evaluation")}
          />
        )}
        {currentPage === "merchant" && (
          <MerchantRhythmScreen
            rhythm={merchantRhythm}
            merchantName={selectedMerchant}
            onSelectMerchant={setSelectedMerchant}
            loading={merchantLoading}
            error={merchantError}
            quickMerchants={quickMerchants}
            onOpenInvestigation={openInvestigation}
          />
        )}
        {currentPage === "evaluation" && (
          <EvaluationScreen
            data={evaluation}
            onNavigateToInvestigations={() => navigateTo("investigations")}
            onNavigateToMerchantRhythm={() => navigateTo("merchant")}
            onNavigateToMonitor={() => navigateTo("monitor")}
          />
        )}
        {currentPage === "integration" && (
          <IntegrationScreen overview={overview} />
        )}
      </main>
    </div>
  );
}
