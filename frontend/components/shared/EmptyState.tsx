"use client";

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="empty-state" role="status">
      <div className="empty-state-icon">—</div>
      <p className="empty-state-text">{message}</p>
    </div>
  );
}
