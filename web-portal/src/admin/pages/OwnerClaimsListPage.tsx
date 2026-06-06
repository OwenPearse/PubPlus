import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { StatusBadge } from "@/admin/components/StatusBadge";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import { formatApiError, listOwnerClaims, type OwnerClaimListItem } from "@/shared/lib/api";

const STATUS_FILTERS = [
  { value: "submitted,under_review", label: "Open" },
  { value: "submitted", label: "Submitted" },
  { value: "under_review", label: "Needs more info" },
  { value: "closed,denied", label: "Closed" },
] as const;

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function formatLocation(item: OwnerClaimListItem) {
  const parts = [item.locality_name, item.state_code].filter(Boolean);
  return parts.length > 0 ? parts.join(", ") : "—";
}

export function OwnerClaimsListPage() {
  const [statusFilter, setStatusFilter] = useState<string>(STATUS_FILTERS[0].value);
  const [items, setItems] = useState<OwnerClaimListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadClaims = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await listOwnerClaims({ status: statusFilter });
      setItems(data.items);
    } catch (err) {
      setError(formatApiError(err));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void loadClaims();
  }, [loadClaims]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Owner venue claims</h1>
          <p className="mt-1 text-sm text-slate-600">
            Review pub signup requests from owners waiting for venue access.
          </p>
        </div>
        <Link
          to="/internal/founder-venues"
          className="text-sm font-medium text-slate-700 underline"
        >
          Founder venues
        </Link>
      </div>

      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />

      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map((filter) => (
          <button
            key={filter.value}
            type="button"
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              statusFilter === filter.value
                ? "bg-slate-900 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
            onClick={() => setStatusFilter(filter.value)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-sm text-slate-600">Loading claims…</p>
      ) : items.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600">
          No claim requests match this filter.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-600">
              <tr>
                <th className="px-4 py-3">Submitted</th>
                <th className="px-4 py-3">Pub</th>
                <th className="px-4 py-3">Claimant</th>
                <th className="px-4 py-3">Duplicates</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.claim_request_id} className="border-b border-slate-100">
                  <td className="px-4 py-3 text-slate-700">{formatDate(item.submitted_at)}</td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-slate-900">{item.venue_name ?? "—"}</p>
                    <p className="text-xs text-slate-600">
                      {item.address_line_1 ?? "—"} · {formatLocation(item)}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {item.claimant_email ?? item.owner_account_id}
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {item.duplicate_candidate_count}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={item.status} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/internal/owner-claims/${item.claim_request_id}`}
                      className="font-medium text-slate-900 underline"
                    >
                      Review
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
