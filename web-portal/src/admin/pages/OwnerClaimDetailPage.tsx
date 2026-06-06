import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { StatusBadge } from "@/admin/components/StatusBadge";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  approveOwnerClaimExisting,
  approveOwnerClaimNew,
  formatApiError,
  getOwnerClaim,
  markOwnerClaimNeedsMoreInfo,
  rejectOwnerClaim,
  type OwnerClaimDetail,
} from "@/shared/lib/api";

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function formatCandidateLocation(
  localityName: string | null | undefined,
  stateCode: string | null | undefined,
) {
  const parts = [localityName, stateCode].filter(Boolean);
  return parts.length > 0 ? parts.join(", ") : "Location unknown";
}

export function OwnerClaimDetailPage() {
  const { claimRequestId = "" } = useParams();
  const [claim, setClaim] = useState<OwnerClaimDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [adminNote, setAdminNote] = useState("");
  const [busyAction, setBusyAction] = useState<string | null>(null);

  const loadClaim = useCallback(async () => {
    if (!claimRequestId) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await getOwnerClaim(claimRequestId);
      setClaim(data);
    } catch (err) {
      setClaim(null);
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [claimRequestId]);

  useEffect(() => {
    void loadClaim();
  }, [loadClaim]);

  async function runAction(
    action: string,
    runner: () => Promise<{ data: { message: string; status: string } }>,
    confirmMessage: string,
  ) {
    if (!window.confirm(confirmMessage)) return;
    setBusyAction(action);
    setError("");
    setSuccess("");
    try {
      const { data } = await runner();
      setSuccess(data.message);
      await loadClaim();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setBusyAction(null);
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-600">Loading claim request…</p>;
  }

  if (!claim) {
    return (
      <div className="space-y-4">
        <ErrorBanner message={error || "Claim request not found."} />
        <Link to="/internal/owner-claims" className="text-sm font-medium text-slate-900 underline">
          Back to claims queue
        </Link>
      </div>
    );
  }

  const isOpen = claim.status === "submitted" || claim.status === "under_review";

  return (
    <div className="space-y-6">
      <div>
        <Link to="/internal/owner-claims" className="text-sm font-medium text-slate-700 underline">
          ← Back to claims queue
        </Link>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-bold text-slate-900">Review venue claim</h1>
          <StatusBadge status={claim.status} />
        </div>
        <p className="mt-1 text-sm text-slate-600">Claim ID: {claim.claim_request_id}</p>
      </div>

      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
      {success ? (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-slate-800">
          {success}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-900">Submitted pub details</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div>
              <dt className="text-slate-500">Submitted</dt>
              <dd className="text-slate-900">{formatDate(claim.submitted_at)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Pub name</dt>
              <dd className="text-slate-900">{claim.submitted.venue_name ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Address</dt>
              <dd className="text-slate-900">{claim.submitted.address_line_1 ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Locality</dt>
              <dd className="text-slate-900">
                {formatCandidateLocation(
                  claim.submitted.locality_name,
                  claim.submitted.state_code,
                )}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Claimant</dt>
              <dd className="text-slate-900">
                {claim.claimant_email ?? claim.owner_account_id}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Claimant note</dt>
              <dd className="text-slate-900">{claim.submitted.claimant_note ?? "—"}</dd>
            </div>
          </dl>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-900">Admin decision</h2>
          <label htmlFor="adminNote" className="mt-4 block text-sm font-medium text-slate-800">
            Admin note
          </label>
          <textarea
            id="adminNote"
            rows={4}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            value={adminNote}
            onChange={(event) => setAdminNote(event.target.value)}
            disabled={!isOpen || busyAction !== null}
            placeholder="Optional note for approval or rejection."
          />
          {isOpen ? (
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-60"
                disabled={busyAction !== null}
                onClick={() =>
                  void runAction(
                    "approve-new",
                    () =>
                      approveOwnerClaimNew(claim.claim_request_id, {
                        admin_note: adminNote.trim() || undefined,
                      }),
                    "Approve this claim as a new venue listing?",
                  )
                }
              >
                {busyAction === "approve-new" ? "Approving…" : "Approve as new venue"}
              </button>
              <button
                type="button"
                className="rounded border border-red-300 px-3 py-2 text-sm text-red-900 hover:bg-red-50 disabled:opacity-60"
                disabled={busyAction !== null}
                onClick={() =>
                  void runAction(
                    "reject",
                    () =>
                      rejectOwnerClaim(claim.claim_request_id, {
                        admin_note: adminNote.trim() || undefined,
                      }),
                    "Reject this claim request?",
                  )
                }
              >
                {busyAction === "reject" ? "Rejecting…" : "Reject"}
              </button>
              <button
                type="button"
                className="rounded border border-amber-300 px-3 py-2 text-sm text-amber-900 hover:bg-amber-50 disabled:opacity-60"
                disabled={busyAction !== null || !adminNote.trim()}
                onClick={() =>
                  void runAction(
                    "needs-more-info",
                    () =>
                      markOwnerClaimNeedsMoreInfo(claim.claim_request_id, {
                        admin_note: adminNote.trim(),
                      }),
                    "Mark this claim as needing more information from the owner?",
                  )
                }
              >
                {busyAction === "needs-more-info" ? "Saving…" : "Needs more info"}
              </button>
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-600">
              This claim is no longer open for review.
            </p>
          )}
        </section>
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-base font-semibold text-slate-900">Possible duplicate venues</h2>
        {claim.duplicate_candidates.length === 0 ? (
          <p className="mt-3 text-sm text-slate-600">
            No duplicate candidates were recorded for this submission.
          </p>
        ) : (
          <ul className="mt-4 space-y-4">
            {claim.duplicate_candidates.map((candidate) => (
              <li
                key={candidate.venue_id}
                className="rounded-lg border border-slate-200 p-4"
              >
                <p className="font-medium text-slate-900">
                  {candidate.display_name ?? "Unnamed venue"}
                </p>
                <p className="text-sm text-slate-700">
                  {candidate.address_line_1 ?? "No address"} ·{" "}
                  {formatCandidateLocation(candidate.locality_name, candidate.state_code)}
                </p>
                <p className="mt-1 text-xs text-slate-600">
                  Match score: {candidate.match_score ?? "—"} ·{" "}
                  {candidate.match_reason ?? "No reason recorded"}
                </p>
                {isOpen ? (
                  <button
                    type="button"
                    className="mt-3 rounded bg-slate-900 px-3 py-1.5 text-xs text-white hover:bg-slate-800 disabled:opacity-60"
                    disabled={busyAction !== null}
                    onClick={() =>
                      void runAction(
                        `approve-${candidate.venue_id}`,
                        () =>
                          approveOwnerClaimExisting(claim.claim_request_id, {
                            venue_id: candidate.venue_id,
                            admin_note: adminNote.trim() || undefined,
                          }),
                        `Approve this claim against ${candidate.display_name ?? "this venue"}?`,
                      )
                    }
                  >
                    {busyAction === `approve-${candidate.venue_id}`
                      ? "Approving…"
                      : "Approve against this venue"}
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
