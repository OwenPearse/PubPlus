const STATUS_STYLES: Record<string, string> = {
  not_contacted: "bg-slate-100 text-slate-800",
  queued: "bg-sky-100 text-sky-900",
  called: "bg-amber-100 text-amber-900",
  emailed: "bg-blue-100 text-blue-900",
  replied: "bg-emerald-100 text-emerald-900",
  signed_up: "bg-violet-100 text-violet-900",
  rejected: "bg-slate-200 text-slate-700",
  do_not_contact: "bg-red-100 text-red-900",
  submitted: "bg-sky-100 text-sky-900",
  under_review: "bg-amber-100 text-amber-900",
  closed: "bg-emerald-100 text-emerald-900",
  denied: "bg-red-100 text-red-900",
  draft: "bg-slate-100 text-slate-700",
};

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? "bg-slate-100 text-slate-800";
  return (
    <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${style}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
