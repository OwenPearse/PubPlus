# Wave 11 — Commercial / subscription adjacency (SQL drafting)

This tranche adds the **business-first commercial backbone** and **minimal sponsored overlay adjacency**, aligned with DL-024 and DL-030. It ships as migrations `0030`–`0032` after Wave 10 (`0027`–`0029`).

## Objectives

- Anchor **subscription and entitlements** on `business`, not `owner_account` or published venue truth.
- Provide **venue-scoped commercial overlays** only as secondary, junction-keyed state (via `business_venue_management_relationship`).
- Keep **sponsored/commercial placement** in separate tables that do not merge into specials, taps, or published profile truth.
- Apply **RLS** consistent with business-private data: members and admin may read; API clients do not get write policies (billing remains service-orchestrated).

## Migrations

| File | Role |
|------|------|
| `0030_business_subscription_backbone.sql` | `subscription_plan_reference` catalog + `business_subscription` (one row per business in v1). |
| `0031_business_entitlements_and_venue_overlays.sql` | `business_entitlement` + `business_venue_commercial_overlay`. |
| `0032_commercial_overlay_adjacency.sql` | `commercial_overlay_reference` + `business_commercial_overlay_attachment` + RLS for all Wave 11 tables. |

## Tables introduced

| Table | Purpose |
|-------|---------|
| `subscription_plan_reference` | Small plan catalog (`plan_code`, display name, active flag). |
| `business_subscription` | Current commercial subscription state per business; optional opaque billing-provider fields. |
| `business_entitlement` | Named entitlements with JSON payload for limits/toggles (`entitlement_code` + `entitlement_payload`). |
| `business_venue_commercial_overlay` | Per managed-venue overlay bundle keyed by `business_venue_management_relationship_id` + `overlay_scope`. |
| `commercial_overlay_reference` | Vocabulary row for overlay product kinds (sponsored placement, etc.). |
| `business_commercial_overlay_attachment` | Future-ready placement intent row (business scope, optional venue scope, validity window). |

## Subscription attachment model

- **Primary key path:** `business` ← `business_subscription` (unique `business_id`).
- **Plan link:** optional `subscription_plan_id` → `subscription_plan_reference`.
- **Lifecycle:** `subscription_status` uses commercial lifecycle values only (trialing, active, canceled, …), orthogonal to publish/moderation lifecycles.

## Venue overlays

- **Secondary path:** `business_venue_commercial_overlay` references **`business_venue_management_relationship`**, not published venue tables — the overlay is tied to the same junction that anchors authority, but **does not grant authority** and **does not encode truth or discovery tiers**.

## Separation from truth and authority

- No new columns on `venue_*published*` tables and no FKs from these commercial tables into published-truth or workflow-truth tables.
- Commercial tables do not reference `venue_capability_grant`, `venue_management_rights`, or verification state — **subscription does not imply permissions**; grants remain the permission spine.

## What was deliberately deferred

- Billing webhook/event ingestion, invoice line items, dunning automation.
- CRM, analytics, attribution, and conversion pipelines.
- Coupon/redemption, bookings-linked commerce, ad serving, and campaign workflow engines.
- Historical subscription timeline / audit tables (v1 uses a single current row per business).
- DB-enforced rule that `business_commercial_overlay_attachment.venue_id` is managed by the same business (validated in application/service to avoid brittle DDL).

## Verification

- `database/sql/checks/check_wave_11_commercial_subscription_adjacency.sql`
- Optional: extend `check_first_tranche_end_to_end.sql` when the Database Manager wants a single mega-check updated.

## Ordering

Apply after `0029` (lexical order: `0030` → `0031` → `0032`).
