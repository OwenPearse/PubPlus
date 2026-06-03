type Props = {
  message: string;
  onDismiss?: () => void;
};

export function ErrorBanner({ message, onDismiss }: Props) {
  if (!message) return null;
  return (
    <div
      className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
      role="alert"
    >
      <div className="flex items-start justify-between gap-3">
        <span>{message}</span>
        {onDismiss ? (
          <button
            type="button"
            className="shrink-0 text-red-600 underline"
            onClick={onDismiss}
          >
            Dismiss
          </button>
        ) : null}
      </div>
    </div>
  );
}
