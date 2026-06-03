type Props = {
  phone?: string | null;
  website?: string | null;
  email?: string | null;
  instagram_url?: string | null;
  facebook_url?: string | null;
  enrichment_status?: string;
  outreach_status?: string;
};

function Dot({ active, label }: { active: boolean; label: string }) {
  return (
    <span
      title={label}
      className={`inline-flex h-6 w-6 items-center justify-center rounded text-xs font-medium ${
        active ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-400"
      }`}
    >
      {label}
    </span>
  );
}

export function ContactIndicators({
  phone,
  website,
  email,
  instagram_url,
  facebook_url,
  enrichment_status,
  outreach_status,
}: Props) {
  const hasSocial = Boolean(
    (instagram_url && instagram_url.trim()) || (facebook_url && facebook_url.trim()),
  );

  return (
    <div className="flex flex-wrap items-center gap-1">
      <Dot active={Boolean(phone?.trim())} label="P" />
      <Dot active={Boolean(website?.trim())} label="W" />
      <Dot active={Boolean(email?.trim())} label="E" />
      <Dot active={hasSocial} label="S" />
      {enrichment_status === "needs_review" ? (
        <span className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-900">
          review
        </span>
      ) : null}
      {enrichment_status === "enriched" ? (
        <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-900">
          enriched
        </span>
      ) : null}
      {outreach_status === "do_not_contact" ? (
        <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-900">DNC</span>
      ) : null}
    </div>
  );
}
