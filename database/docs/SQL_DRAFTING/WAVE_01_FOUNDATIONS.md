# SQL drafting — Wave 1 (foundations)

## Scope

Wave 1 establishes durable anchors and reference structures that later published truth and workflow rows attach to. In this repo tranche, foundations are implemented across migrations **0001–0002**, **0003** (geography reference + published geo), **0005** (attribute definitions), and **0007** (`external_data_source` registry before intake).

## Tables introduced (by migration)

| Migration | Tables |
|-----------|--------|
| 0002 | `venue`, `consumer_account`, `owner_account`, `admin_account`, `business` |
| 0003 | `geographic_region`, `locality` |
| 0005 | `venue_attribute_definition`, `venue_attribute_allowed_value` |
| 0007 | `external_data_source` |

## Rules preserved

- **Canonical venue identity** (`venue`) is the root anchor for venue-linked published and workflow state.
- **Logical account domains** stay in separate tables (`consumer_account`, `owner_account`, `admin_account`); auth user IDs link to `auth.users` only.
- **Business** exists as a first-class org anchor without commercial columns in this tranche.
- **Geography reference** is structured (`geographic_region`, `locality`); published address/map live in Wave 2 migrations but depend on these FK targets.
- **Discovery definitions** are reference rows, not per-venue truth blobs.

## Deferred (not Wave 1)

- Consumer private feature tables (`consumer_profile`, saved lists, notification settings).
- Owner/business authority chain (memberships, management relationship, claims, verification, capability grants).
- Commercial/subscription columns on `business`.

## Follow-ups for later workers

- Seed `geographic_region`, `locality`, `venue_attribute_definition`, `external_data_source` with MVP rows.
- Add `updated_at` maintenance triggers if the product standardizes on automatic timestamps (optional).
