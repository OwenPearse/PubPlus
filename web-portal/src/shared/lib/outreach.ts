import {
  markLeadDoNotContact,
  patchFounderVenueLead,
} from "@/shared/lib/api";
import type { FounderVenueLeadListItem, LeadDetailResponse, PatchableLeadField } from "@/shared/lib/types";

export const OUTREACH_STATUSES = [
  "not_contacted",
  "queued",
  "called",
  "emailed",
  "replied",
  "signed_up",
  "rejected",
  "do_not_contact",
] as const;

export type OutreachStatus = (typeof OUTREACH_STATUSES)[number];

export const CONTACT_CHANNELS = [
  "phone",
  "email",
  "instagram",
  "facebook",
  "website_form",
  "in_person",
  "other",
] as const;

export type ContactChannel = (typeof CONTACT_CHANNELS)[number];

const TERMINAL_OUTREACH: OutreachStatus[] = ["do_not_contact", "rejected", "signed_up"];

const NEXT_LEAD_STATUSES: OutreachStatus[] = ["not_contacted", "queued"];

export function outreachNowIso(): string {
  return new Date().toISOString();
}

type OutreachPatch = Partial<
  Pick<
    Record<PatchableLeadField, string | null>,
    "outreach_status" | "last_contacted_at" | "last_contact_channel" | "notes"
  >
>;

async function patchOutreach(leadId: string, body: OutreachPatch) {
  return patchFounderVenueLead(leadId, body);
}

export function markFounderVenueQueued(leadId: string) {
  return patchOutreach(leadId, { outreach_status: "queued" });
}

export function markFounderVenueCalled(leadId: string) {
  return patchOutreach(leadId, {
    outreach_status: "called",
    last_contacted_at: outreachNowIso(),
    last_contact_channel: "phone",
  });
}

export function markFounderVenueEmailed(leadId: string) {
  return patchOutreach(leadId, {
    outreach_status: "emailed",
    last_contacted_at: outreachNowIso(),
    last_contact_channel: "email",
  });
}

export function markFounderVenueReplied(leadId: string) {
  return patchOutreach(leadId, {
    outreach_status: "replied",
    last_contacted_at: outreachNowIso(),
    last_contact_channel: "email",
  });
}

export function markFounderVenueRejected(leadId: string) {
  return patchOutreach(leadId, {
    outreach_status: "rejected",
    last_contacted_at: outreachNowIso(),
    last_contact_channel: "phone",
  });
}

export function markFounderVenueSignedUp(leadId: string) {
  return patchOutreach(leadId, {
    outreach_status: "signed_up",
    last_contacted_at: outreachNowIso(),
    last_contact_channel: "phone",
  });
}

export function markFounderVenueDoNotContact(leadId: string, reason?: string) {
  return markLeadDoNotContact(leadId, reason);
}

export function saveFounderVenueNotes(leadId: string, notes: string) {
  return patchFounderVenueLead(leadId, {
    notes: notes.trim() === "" ? null : notes,
  });
}

export function saveNotesWithOutreach(
  leadId: string,
  notes: string,
  outreach: OutreachPatch,
) {
  return patchFounderVenueLead(leadId, {
    notes: notes.trim() === "" ? null : notes,
    ...outreach,
  });
}

export function mergeLeadFromDetail(
  item: FounderVenueLeadListItem,
  response: LeadDetailResponse,
): FounderVenueLeadListItem & { last_contacted_at?: string | null } {
  const { lead } = response;
  return {
    ...item,
    outreach_status: lead.outreach_status,
    contact_permission_status: lead.contact_permission_status,
    founder_fit_score: lead.founder_fit_score,
    confidence_score: lead.confidence_score,
    updated_at: lead.updated_at,
    last_contacted_at: lead.last_contacted_at,
    last_contact_channel: lead.last_contact_channel,
  };
}

export function isNextBestLeadCandidate(lead: FounderVenueLeadListItem): boolean {
  const status = lead.outreach_status as OutreachStatus;
  if (TERMINAL_OUTREACH.includes(status)) return false;
  return NEXT_LEAD_STATUSES.includes(status);
}

export function findNextBestLeadId(items: FounderVenueLeadListItem[]): string | null {
  const match = items.find(isNextBestLeadCandidate);
  return match?.id ?? null;
}

export function findNextLeadIdInList(
  leadIds: string[],
  currentId: string,
): string | null {
  const idx = leadIds.indexOf(currentId);
  if (idx < 0 || idx >= leadIds.length - 1) return null;
  return leadIds[idx + 1] ?? null;
}

export async function copyTextToClipboard(text: string): Promise<void> {
  await navigator.clipboard.writeText(text);
}
