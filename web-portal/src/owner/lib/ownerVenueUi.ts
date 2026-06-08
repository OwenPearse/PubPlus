import type {
  OwnerOnboardingStatus,
  OwnerVenueCompletenessSection,
  OwnerVenueDetail,
  OwnerVenueListItem,
} from "@/shared/lib/api";

export const OWNER_HUB_HEADLINE = "Complete your listing";
export const OWNER_HUB_SUBHEAD =
  "Update descriptions and hours instantly. Request approval for name or address changes.";
export const OWNER_HUB_REVIEW_NOTE =
  "Name and address changes are reviewed before they appear on your listing.";
export const CORE_DETAILS_HUB_DESCRIPTION =
  "Update descriptions and hours instantly. Request approval for name or address changes.";

const ONBOARDING_STATUS_LABELS: Record<OwnerOnboardingStatus, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  submitted: "Submitted for review",
  needs_changes: "Needs changes",
  complete: "Complete",
};

const SECTION_STATUS_LABELS: Record<string, string> = {
  complete: "Complete",
  partial: "In progress",
  missing: "Not started",
  pending_review: "Pending review",
  deferred: "Coming later",
};

const NEXT_ACTION_SECTIONS: Array<{
  key: string;
  title: string;
  description: string;
}> = [
  {
    key: "core_details",
    title: "Complete pub details",
    description:
      "Add your short description and opening hours so customers know when to visit.",
  },
  {
    key: "features",
    title: "Add venue features",
    description:
      "Features like beer garden, dog friendly, and live music help customers find your pub.",
  },
  {
    key: "meal_specials",
    title: "Add meal specials",
    description:
      "Food specials like parma nights and Sunday roasts show what your pub offers.",
  },
  {
    key: "tap_list",
    title: "Add tap list & drinks",
    description:
      "List the beers, wines, and cocktails customers can expect when they visit.",
  },
  {
    key: "photos",
    title: "Add venue photos",
    description: "Photos help customers quickly understand the feel of your pub.",
  },
];

const IMPLEMENTED_SECTION_KEYS = new Set(
  NEXT_ACTION_SECTIONS.map((section) => section.key),
);

export function onboardingStatusLabel(status: OwnerOnboardingStatus): string {
  return ONBOARDING_STATUS_LABELS[status];
}

export function formatVenueLocation(
  localityName: string | null | undefined,
  stateCode: string | null | undefined,
): string {
  const parts = [localityName, stateCode].filter(Boolean);
  return parts.length > 0 ? parts.join(", ") : "Location not set";
}

export function sectionStatusLabel(status: string): string {
  return SECTION_STATUS_LABELS[status] ?? status;
}

export function sectionStatusBadgeClass(status: string): string {
  switch (status) {
    case "complete":
      return "bg-emerald-100 text-emerald-800";
    case "partial":
      return "bg-amber-100 text-amber-800";
    case "pending_review":
      return "bg-blue-100 text-blue-800";
    case "deferred":
      return "bg-slate-100 text-slate-500";
    default:
      return "bg-slate-100 text-slate-600";
  }
}

export function recommendedNextAction(
  detail: OwnerVenueDetail,
): { title: string; description: string } | null {
  for (const item of NEXT_ACTION_SECTIONS) {
    const section = detail.completeness.sections.find(
      (entry) => entry.key === item.key,
    );
    if (
      section &&
      section.available &&
      section.status !== "complete" &&
      section.status !== "deferred"
    ) {
      return {
        title: `Next recommended step: ${item.title}`,
        description: item.description,
      };
    }
  }

  const allImplementedComplete = detail.completeness.sections
    .filter((section) => IMPLEMENTED_SECTION_KEYS.has(section.key))
    .every(
      (section) =>
        !section.available ||
        section.status === "complete" ||
        section.status === "deferred",
    );

  if (allImplementedComplete) {
    return {
      title: "Your listing is looking good.",
      description: "You can keep updating it anytime.",
    };
  }

  return null;
}

export function venueHubStatusMessage(detail: OwnerVenueDetail): string | null {
  const outcome = detail.pending_review.review_outcome;
  if (outcome === "rejected" || outcome === "changes_requested") {
    return "Some changes need an update before they can be reviewed again.";
  }
  if (
    detail.pending_review.proposal_id &&
    detail.pending_review.lifecycle_status === "in_review" &&
    detail.pending_review.submitted_at
  ) {
    return "Name/address change pending review.";
  }
  return null;
}

export function listItemStatusMessage(item: OwnerVenueListItem): string | null {
  switch (item.onboarding_status) {
    case "submitted":
      return "Submitted for review.";
    case "needs_changes":
      return "Some changes need an update.";
    case "complete":
      return "Basics complete.";
    case "in_progress":
      return item.pending_proposal_count > 0 ? "Pending review." : "In progress.";
    default:
      return null;
  }
}

export function sectionIsDeferred(section: {
  available: boolean;
  status: string;
}): boolean {
  return !section.available || section.status === "deferred";
}

export function sectionHubDescription(section: OwnerVenueCompletenessSection): string | null {
  if (sectionIsDeferred(section)) {
    return "Coming later — you can skip this for now.";
  }
  if (section.key === "core_details") {
    return CORE_DETAILS_HUB_DESCRIPTION;
  }
  return null;
}
