import type { FounderVenueWorkspaceSummary } from "@/shared/lib/types";

const CARDS: { key: keyof FounderVenueWorkspaceSummary; label: string }[] = [
  { key: "vic_leads", label: "VIC leads" },
  { key: "vic_score_80_plus", label: "VIC 80+" },
  { key: "not_contacted", label: "Not contacted" },
  { key: "called", label: "Called" },
  { key: "replied", label: "Replied" },
  { key: "signed_up", label: "Signed up" },
  { key: "needs_review", label: "Needs review" },
  { key: "missing_email", label: "Missing email" },
];

type Props = {
  summary: FounderVenueWorkspaceSummary | null;
  loading?: boolean;
};

export function DashboardCards({ summary, loading }: Props) {
  return (
    <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-8">
      {CARDS.map(({ key, label }) => (
        <div
          key={key}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm"
        >
          <p className="text-xs text-slate-500">{label}</p>
          <p className="text-lg font-semibold tabular-nums text-slate-900">
            {loading ? "…" : (summary?.[key] ?? "—")}
          </p>
        </div>
      ))}
    </div>
  );
}
