"use client";

interface ErrorBannerProps {
  error: string | null;
  onDismiss: () => void;
}

export function ErrorBanner({ error, onDismiss }: ErrorBannerProps) {
  if (!error) return null;
  return (
    <div className="mb-4 rounded border border-red-400 bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950">
      {error}
      <button className="ml-2 underline" onClick={onDismiss}>
        dismiss
      </button>
    </div>
  );
}
