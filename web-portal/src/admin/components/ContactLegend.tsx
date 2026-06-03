export function ContactLegend() {
  return (
    <p className="text-xs text-slate-600">
      <span className="font-medium text-slate-700">Contact:</span>{" "}
      <span className="inline-flex items-center gap-2">
        <span>
          <abbr title="Phone" className="no-underline">
            P
          </abbr>{" "}
          = phone
        </span>
        <span>
          <abbr title="Website" className="no-underline">
            W
          </abbr>{" "}
          = website
        </span>
        <span>
          <abbr title="Email" className="no-underline">
            E
          </abbr>{" "}
          = email
        </span>
        <span>
          <abbr title="Social" className="no-underline">
            S
          </abbr>{" "}
          = Instagram or Facebook
        </span>
      </span>
    </p>
  );
}
