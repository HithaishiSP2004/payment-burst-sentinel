"use client";

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="error-banner" role="alert">
      <span className="error-banner-text">{message}</span>
      {onRetry && <button className="retry-btn" onClick={onRetry}>Retry</button>}
    </div>
  );
}
