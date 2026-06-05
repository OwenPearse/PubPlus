import type {
  OwnerOnboardingStatus,
  OwnerVenueDetail,
  OwnerVenueListItem,
} from "@/shared/lib/api";

export const OWNER_HUB_HEADLINE = "Complete your listing";
export const OWNER_HUB_SUBHEAD =
  "Confirm the basics now. Add more detail whenever you can.";
export const OWNER_HUB_REVIEW_NOTE =
  "Changes are reviewed before they appear publicly.";

const ONBOARDING_STATUS_LABELS: Record<OwnerOnboardingStatus, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  submitted: "Submitted for review",
  needs_changes: "Needs changes",
  complete: "Complete",
};

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

export function venueHubStatusMessage(detail: OwnerVenueDetail): string | null {
  const outcome = detail.pending_review.review_outcome;
  if (outcome === "rejected" || outcome === "changes_requested") {
    return "Some changes need an update before they can be reviewed again.";
  }
  if (
    detail.pending_review.proposal_id &&
    (detail.pending_review.lifecycle_status === "in_review" ||
      detail.pending_review.submitted_at)
  ) {
    return "Submitted for review. Your changes will be reviewed before they appear publicly.";
  }
  if (detail.draft.proposal_id && detail.draft.lifecycle_status === "staged") {
    return "Saved as draft. You can come back anytime.";
  }
  if (detail.completeness.required_basics_complete) {
    return "Your basics are complete.";
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
