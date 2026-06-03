import {
  formatEventMetadata,
  formatEventTypeLabel,
  isOutreachRelatedEvent,
} from "@/shared/lib/eventSummary";
import type { LeadEvent } from "@/shared/lib/types";

function formatWhen(value: string | null) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function EventsTable({ events }: { events: LeadEvent[] }) {
  return (
    <section className="mb-6 overflow-x-auto rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="mb-3 text-lg font-semibold">Activity</h2>
      {events.length === 0 ? (
        <p className="text-sm text-slate-500">No events recorded.</p>
      ) : (
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b text-xs uppercase text-slate-500">
              <th className="px-2 py-1">Event</th>
              <th className="px-2 py-1">When</th>
              <th className="px-2 py-1">Summary</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => {
              const outreach = isOutreachRelatedEvent(e.event_type);
              return (
                <tr
                  key={e.id}
                  className={`border-b border-slate-100 ${outreach ? "bg-blue-50/40" : ""}`}
                >
                  <td className="px-2 py-2 font-medium">
                    {formatEventTypeLabel(e.event_type)}
                    {outreach ? (
                      <span className="ml-1 text-xs font-normal text-blue-700">outreach</span>
                    ) : null}
                  </td>
                  <td className="whitespace-nowrap px-2 py-2 text-xs text-slate-600">
                    {formatWhen(e.created_at)}
                  </td>
                  <td className="max-w-md px-2 py-2 text-xs text-slate-700">
                    {formatEventMetadata(e.metadata)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
