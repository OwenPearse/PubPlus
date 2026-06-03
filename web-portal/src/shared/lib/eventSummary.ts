const OUTREACH_EVENT_TYPES = new Set([
  "outreach_status_changed",
  "lead_patched",
  "marked_do_not_contact",
  "imported",
  "enriched",
]);

export function isOutreachRelatedEvent(eventType: string): boolean {
  return OUTREACH_EVENT_TYPES.has(eventType) || eventType.includes("outreach");
}

export function formatEventMetadata(metadata: Record<string, unknown>): string {
  const keys = Object.keys(metadata);
  if (keys.length === 0) return "—";

  const preferred = [
    "outreach_status",
    "last_contact_channel",
    "last_contacted_at",
    "field",
    "reason",
    "dry_run",
    "source_type",
  ];
  const ordered = [
    ...preferred.filter((k) => k in metadata),
    ...keys.filter((k) => !preferred.includes(k)),
  ].slice(0, 5);

  return ordered
    .map((k) => {
      const v = metadata[k];
      if (v == null || v === "") return null;
      return `${k.replace(/_/g, " ")}: ${String(v)}`;
    })
    .filter(Boolean)
    .join(" · ");
}

export function formatEventTypeLabel(eventType: string): string {
  return eventType.replace(/_/g, " ");
}
