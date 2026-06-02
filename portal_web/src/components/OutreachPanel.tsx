import { useState } from "react";

import { OutreachActionButtons } from "@/components/OutreachActionButtons";
import { StatusBadge } from "@/components/StatusBadge";
import {
  markFounderVenueCalled,
  markFounderVenueDoNotContact,
  markFounderVenueEmailed,
  markFounderVenueRejected,
  markFounderVenueReplied,
  markFounderVenueSignedUp,
  saveFounderVenueNotes,
  saveNotesWithOutreach,
  outreachNowIso,
} from "@/lib/outreach";
import { formatApiError } from "@/lib/api";
import type { FounderVenueLeadDetail, LeadDetailResponse } from "@/lib/types";

function formatDate(value: string | null) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

type Props = {
  lead: FounderVenueLeadDetail;
  notes: string;
  onNotesChange: (value: string) => void;
  onUpdated: (response: LeadDetailResponse) => void;
  onError: (message: string) => void;
  onSuccess: (message: string) => void;
};

export function OutreachPanel({
  lead,
  notes,
  onNotesChange,
  onUpdated,
  onError,
  onSuccess,
}: Props) {
  const [busy, setBusy] = useState(false);

  async function runAction(
    label: string,
    action: () => Promise<LeadDetailResponse>,
  ) {
    setBusy(true);
    onError("");
    try {
      const response = await action();
      onUpdated(response);
      onSuccess(label);
    } catch (err) {
      onError(formatApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleDnc() {
    const reason = window.prompt(
      `Mark "${lead.name}" as do-not-contact?\n\nOptional reason:`,
      "",
    );
    if (reason === null) return;
    if (
      !window.confirm(
        `Confirm do-not-contact for "${lead.name}". This is recorded on the lead and excluded from default exports.`,
      )
    ) {
      return;
    }
    await runAction("Marked do-not-contact.", () =>
      markFounderVenueDoNotContact(lead.id, reason.trim() || undefined),
    );
  }

  const contactedActions = [
    {
      id: "called",
      label: busy ? "Saving…" : "Mark called",
      disabled: busy,
      onClick: () =>
        void runAction("Marked as called.", () => markFounderVenueCalled(lead.id)),
    },
    {
      id: "emailed",
      label: busy ? "Saving…" : "Mark emailed",
      disabled: busy,
      onClick: () =>
        void runAction("Marked as emailed.", () => markFounderVenueEmailed(lead.id)),
    },
  ];

  const outcomeActions = [
    {
      id: "replied",
      label: "Mark replied",
      disabled: busy,
      onClick: () =>
        void runAction("Marked as replied.", () => markFounderVenueReplied(lead.id)),
    },
    {
      id: "signed_up",
      label: "Mark signed up",
      disabled: busy,
      onClick: () =>
        void runAction("Marked as signed up.", () => markFounderVenueSignedUp(lead.id)),
    },
    {
      id: "rejected",
      label: "Mark rejected",
      disabled: busy,
      onClick: () =>
        void runAction("Marked as rejected.", () => markFounderVenueRejected(lead.id)),
    },
  ];

  return (
    <section className="mb-6 rounded-lg border border-blue-200 bg-blue-50/50 p-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <h2 className="text-lg font-semibold">Outreach</h2>
        <StatusBadge status={lead.outreach_status} />
      </div>

      <dl className="mb-4 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-slate-500">Contact permission</dt>
          <dd className="font-medium">{lead.contact_permission_status}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Last contacted</dt>
          <dd className="font-medium">{formatDate(lead.last_contacted_at)}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-slate-500">Last channel</dt>
          <dd className="font-medium">{lead.last_contact_channel ?? "—"}</dd>
        </div>
      </dl>

      <div className="space-y-3">
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Contacted
          </p>
          <OutreachActionButtons
            layout="row"
            size="sm"
            variant="button"
            actions={contactedActions}
          />
        </div>
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Outcome
          </p>
          <OutreachActionButtons
            layout="row"
            size="sm"
            variant="button"
            actions={outcomeActions}
          />
        </div>
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Safety
          </p>
          <OutreachActionButtons
            layout="row"
            size="sm"
            variant="button"
            actions={[
              {
                id: "dnc",
                label: "Mark DNC",
                className: "border-red-300 text-red-800",
                disabled: busy,
                onClick: () => void handleDnc(),
              },
            ]}
          />
          <p className="mt-2 text-xs text-red-800">
            DNC removes this venue from normal outreach queues and default exports.
          </p>
        </div>
      </div>

      <div className="mt-4 border-t border-blue-200/80 pt-4">
        <label className="block text-sm font-medium text-slate-700">Outreach notes</label>
        <textarea
          className="mt-1 w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-sm"
          rows={4}
          value={notes}
          onChange={(e) => onNotesChange(e.target.value)}
          disabled={busy}
        />
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-50"
            onClick={() =>
              void runAction("Notes saved.", () => saveFounderVenueNotes(lead.id, notes))
            }
          >
            {busy ? "Saving…" : "Save notes"}
          </button>
          <button
            type="button"
            disabled={busy}
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-50"
            onClick={() =>
              void runAction("Notes saved and marked called.", () =>
                saveNotesWithOutreach(lead.id, notes, {
                  outreach_status: "called",
                  last_contacted_at: outreachNowIso(),
                  last_contact_channel: "phone",
                }),
              )
            }
          >
            Save notes + mark called
          </button>
          <button
            type="button"
            disabled={busy}
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-50"
            onClick={() =>
              void runAction("Notes saved and marked replied.", () =>
                saveNotesWithOutreach(lead.id, notes, {
                  outreach_status: "replied",
                  last_contacted_at: outreachNowIso(),
                  last_contact_channel: "email",
                }),
              )
            }
          >
            Save notes + mark replied
          </button>
          <button
            type="button"
            disabled={busy}
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-50"
            onClick={() =>
              void runAction("Notes saved and marked rejected.", () =>
                saveNotesWithOutreach(lead.id, notes, {
                  outreach_status: "rejected",
                  last_contacted_at: outreachNowIso(),
                  last_contact_channel: "phone",
                }),
              )
            }
          >
            Save notes + mark rejected
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Labels say “Mark emailed” — the portal does not send messages.
        </p>
      </div>
    </section>
  );
}
