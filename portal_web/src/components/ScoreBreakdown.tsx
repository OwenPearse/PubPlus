import type { FounderFitBreakdown } from "@/lib/types";

type Props = {
  breakdown: FounderFitBreakdown;
  founderFitScore: number;
  confidenceScore: number;
};

export function ScoreBreakdown({ breakdown, founderFitScore, confidenceScore }: Props) {
  const components = breakdown.components ?? {};

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="mb-3 text-lg font-semibold">Score breakdown</h2>
      <p className="mb-2 text-sm text-slate-600">
        Founder fit: <strong>{founderFitScore}</strong> · Confidence:{" "}
        <strong>{confidenceScore}</strong>
      </p>

      {Object.keys(components).length > 0 ? (
        <div className="mb-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
          {Object.entries(components).map(([key, value]) => (
            <div key={key} className="rounded bg-slate-50 px-2 py-1">
              <span className="text-slate-500">{key.replace(/_/g, " ")}</span>
              <span className="ml-2 font-medium">{value}</span>
            </div>
          ))}
        </div>
      ) : null}

      <SignalList title="Positive signals" items={breakdown.positive_signals ?? []} />
      <SignalList title="Negative signals" items={breakdown.negative_signals ?? []} />
      <SignalList title="Warnings" items={breakdown.warnings ?? []} />
    </section>
  );
}

function SignalList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="mt-3">
      <p className="text-sm font-medium text-slate-700">{title}</p>
      <ul className="mt-1 list-inside list-disc text-sm text-slate-600">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
