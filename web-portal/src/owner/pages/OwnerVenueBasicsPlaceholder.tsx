import { Link, useParams } from "react-router-dom";

/** Stage 3 will replace this with the core pub details form. */
export function OwnerVenueBasicsPlaceholder() {
  const { venueId } = useParams<{ venueId: string }>();

  return (
    <div className="max-w-lg space-y-4">
      <h1 className="text-xl font-bold text-slate-900">Pub details</h1>
      <p className="text-sm text-slate-600">
        The pub details form is coming in the next release. Use the checklist to track progress in
        the meantime.
      </p>
      {venueId ? (
        <Link
          to={`/owner/venues/${venueId}`}
          className="inline-block text-sm font-medium text-slate-900 underline"
        >
          ← Back to checklist
        </Link>
      ) : null}
    </div>
  );
}
