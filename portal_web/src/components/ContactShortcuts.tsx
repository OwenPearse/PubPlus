import { ExternalLink } from "@/components/ExternalLink";
import { copyTextToClipboard } from "@/lib/outreach";
import type { FounderVenueLeadDetail } from "@/lib/types";

type Props = {
  lead: FounderVenueLeadDetail;
  onCopied?: (label: string) => void;
};

function socialUrl(lead: FounderVenueLeadDetail): string | null {
  return lead.instagram_url?.trim() || lead.facebook_url?.trim() || null;
}

export function ContactShortcuts({ lead, onCopied }: Props) {
  async function copy(value: string, label: string) {
    try {
      await copyTextToClipboard(value);
      onCopied?.(`${label} copied.`);
    } catch {
      onCopied?.(`Could not copy ${label}.`);
    }
  }

  return (
    <section className="mb-6 rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="mb-3 text-lg font-semibold">Contact</h2>
      <dl className="space-y-3 text-sm">
        <div>
          <dt className="text-slate-500">Phone</dt>
          <dd className="mt-1 flex flex-wrap items-center gap-2">
            {lead.phone?.trim() ? (
              <>
                <span>{lead.phone}</span>
                <a href={`tel:${lead.phone.replace(/\s/g, "")}`} className="text-blue-700 underline">
                  Call
                </a>
                <button
                  type="button"
                  className="text-xs text-slate-600 underline"
                  onClick={() => void copy(lead.phone!, "Phone")}
                >
                  Copy
                </button>
              </>
            ) : (
              "—"
            )}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Email</dt>
          <dd className="mt-1 flex flex-wrap items-center gap-2">
            {lead.email?.trim() ? (
              <>
                <span>{lead.email}</span>
                <a href={`mailto:${lead.email}`} className="text-blue-700 underline">
                  Open mailto
                </a>
                <button
                  type="button"
                  className="text-xs text-slate-600 underline"
                  onClick={() => void copy(lead.email!, "Email")}
                >
                  Copy
                </button>
              </>
            ) : (
              "—"
            )}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Website</dt>
          <dd className="mt-1">
            {lead.website?.trim() ? (
              <ExternalLink href={lead.website}>Open website</ExternalLink>
            ) : (
              "—"
            )}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Instagram</dt>
          <dd className="mt-1">
            {lead.instagram_url?.trim() ? (
              <ExternalLink href={lead.instagram_url}>Open Instagram</ExternalLink>
            ) : (
              "—"
            )}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Facebook</dt>
          <dd className="mt-1">
            {lead.facebook_url?.trim() ? (
              <ExternalLink href={lead.facebook_url}>Open Facebook</ExternalLink>
            ) : (
              "—"
            )}
          </dd>
        </div>
        {socialUrl(lead) ? (
          <div>
            <dt className="text-slate-500">Social (first)</dt>
            <dd className="mt-1">
              <ExternalLink href={socialUrl(lead)!}>Open social</ExternalLink>
            </dd>
          </div>
        ) : null}
      </dl>
    </section>
  );
}
