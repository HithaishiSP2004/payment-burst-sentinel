"use client";

export function LoadingState({ label }: { label: string }) {
  return (
    <div className="loading-state" role="status" aria-label={label}>
      <div className="loading-bar" />
      <span className="loading-indicator">{label}</span>
    </div>
  );
}
