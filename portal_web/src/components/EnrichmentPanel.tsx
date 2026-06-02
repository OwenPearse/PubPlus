import type { EnrichmentResult } from "@/lib/types";

type Props = {
  result: EnrichmentResult | null;
  loading: boolean;
  onDryRun: () => void;
  onRealEnrich: () => void;
};

export function EnrichmentPanel({ result, loading, onDryRun, onRealEnrich }: Props) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h2 className="text-lg font-semibold">Website enrichment</h2>
        <button
          type="button"
          className="rounded bg-slate-800 px-3 py-1.5 text-sm text-white disabled:opacity-50"
          disabled={loading}
          onClick={onDryRun}
        >
          Dry-run
        </button>
        {result?.dry_run ? (
          <button
            type="button"
            className="rounded bg-emerald-700 px-3 py-1.5 text-sm text-white disabled:opacity-50"
            disabled={loading}
            onClick={onRealEnrich}
          >
            Apply enrichment
          </button>
        ) : null}
      </div>

      {loading ? <p className="text-sm text-slate-600">Running enrichment…</p> : null}

      {result ? (
        <div className="space-y-3 text-sm">
          {result.fetched_urls.length > 0 ? (
            <div>
              <p className="font-medium">Fetched URLs</p>
              <ul className="list-inside list-disc text-slate-700">
                {result.fetched_urls.map((url) => (
                  <li key={url} className="truncate">
                    {url}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {result.product_signals.length > 0 ? (
            <div>
              <p className="font-medium">Product signals</p>
              <ul className="list-inside list-disc">
                {result.product_signals.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {result.candidates.length > 0 ? (
            <div>
              <p className="font-medium">Candidates</p>
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-xs">
                  <thead>
                    <tr className="border-b">
                      <th className="py-1 pr-2">Field</th>
                      <th className="py-1 pr-2">Normalized</th>
                      <th className="py-1 pr-2">Confidence</th>
                      <th className="py-1">Safety</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.candidates.map((c, i) => (
                      <tr key={`${c.field_name}-${i}`} className="border-b border-slate-100">
                        <td className="py-1 pr-2">{c.field_name}</td>
                        <td className="py-1 pr-2 max-w-xs truncate">
                          {c.normalized_value ?? c.raw_value}
                        </td>
                        <td className="py-1 pr-2">{c.confidence}</td>
                        <td className="py-1">{c.contact_safety_class ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          {result.dry_run ? (
            <p className="text-slate-600">
              Dry-run only — no fields were written. Review candidates, then apply enrichment.
            </p>
          ) : (
            <>
              {result.fields_promoted.length > 0 ? (
                <p>
                  <span className="font-medium">Fields promoted:</span>{" "}
                  {result.fields_promoted.join(", ")}
                </p>
              ) : null}
              {result.enrichment_status ? (
                <p>
                  <span className="font-medium">Enrichment status:</span>{" "}
                  {result.enrichment_status}
                </p>
              ) : null}
            </>
          )}

          {result.warnings.length > 0 ? (
            <div className="rounded bg-amber-50 p-2 text-amber-900">
              <p className="font-medium">Warnings</p>
              <ul className="list-inside list-disc">
                {result.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {result.errors.length > 0 ? (
            <div className="rounded bg-red-50 p-2 text-red-900">
              <p className="font-medium">Errors</p>
              <ul className="list-inside list-disc">
                {result.errors.map((e) => (
                  <li key={e}>{e}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : (
        <p className="text-sm text-slate-600">
          Run a dry-run on leads with a real venue website to preview candidates before applying.
        </p>
      )}
    </section>
  );
}
