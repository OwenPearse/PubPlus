import type { FounderVenueWorkspaceSummary } from "@/shared/lib/types";

type Props = {
  summary: FounderVenueWorkspaceSummary | null;
};

export function OutreachStatusCounts({ summary }: Props) {
  if (!summary) return null;

  const parts = [
    { label: "Not contacted", value: summary.not_contacted },
    { label: "Called", value: summary.called },
    { label: "Emailed", value: summary.emailed },
    { label: "Replied", value: summary.replied },
    { label: "Signed up", value: summary.signed_up },
  ];

  return (
    <p className="mb-3 text-xs text-slate-600">
      {parts.map((p, i) => (
        <span key={p.label}>
          {i > 0 ? " | " : null}
          <span className="font-medium text-slate-700">{p.label}:</span> {p.value}
        </span>
      ))}
    </p>
  );
}
