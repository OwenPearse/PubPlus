# Data capture model — Owner venue onboarding

## Purpose

Map onboarding sections to Postgres tables—distinguishing **direct published writes** vs **restricted proposal staging**. Aligned with `OWNER_EDIT_POLICY.md`.

## Current stage

**Stage 4.2 complete.** Descriptions and hours write published tables directly via owner PATCH; restricted identity/location uses `POST restricted-change-requests` → proposal staging.

## Decisions

| Section | Mechanism | Admin review |
|---------|-----------|--------------|
| Descriptions | **Direct** → `venue_published_descriptive_copy` | No |
| Opening hours | **Direct** → `venue_hours_*` | No |
| Contact | **Direct** → `venue_published_contact` *(migration)* | No |
| Features | **Direct** → `venue_published_attribute_value` | No |
| Specials / taps | **Direct** → published specials/tap tables | No |
| Identity (name) | **Restricted** → staging → publish | Yes |
| Location / map | **Restricted** → staging → publish | Yes |
| Claim / relationship | **Authority** tables — admin only | Yes |

- **Do not delete** proposal/staging tables; repurpose for restricted + future moderation
- **No** `google_place_id` in owner capture
- `actor_type = 'owner'`, `channel = 'owner_portal'` for restricted proposals only

### Superseded (pre–Stage 4)

> ~~No direct publish from owner APIs~~ — operational families write published tables via Django service role after capability check.

## Assumptions

- Audit via `audit_event` (`action = 'owner_direct_edit'`) on every direct write
- Optional `venue_published_row_history` snapshot before overwrite (Stage 4.1b)
- Completeness reads published truth, not staged operational data

## Open questions

- Contact migration naming: `venue_published_contact` vs `venue_published_contact_links` (unchanged)
- Whether descriptive copy changes should emit `venue_publish_event` lineage rows in 4.1 or defer to 4.3

## Dependencies

- Migrations `0003`–`0008`, `0019`, `0021`, `0025` (published + staging)
- `OWNER_EDIT_POLICY.md` field classification
- `OWNER_VENUE_API_CONTRACT.md` validation rules

## Next downstream use

Stage 4.2 form field zones shipped (`OwnerVenueBasicsPage`); contact migration ticket next.

---

## Direct-edit field map

| UI / API field | Published storage | Notes |
|----------------|-------------------|-------|
| `short_description`, `long_description` | `venue_published_descriptive_copy` | PATCH operational-profile |
| `opening_hours.*` | `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty` | PATCH hours; transactional replace |
| `phone`, `email`, `website` | `venue_published_contact` *(planned)* | Extend operational-profile PATCH |
| Feature toggles | `venue_published_attribute_value` | Reference `attribute_definition_id` |
| Meal specials | `venue_published_structured_special` + validity/eligibility | PUT replace-set |
| Tap list | `venue_published_tap_offering` + validity/eligibility | PUT replace-set |

## Restricted proposal field map

| UI / API field | Staging | Published target (on admin publish) |
|----------------|---------|-------------------------------------|
| `display_name` | `venue_proposal_staging_profile.proposed_display_name` | `venue_published_profile` |
| `address_line_*`, `postal_code`, `country_code` | `venue_proposal_staging_location` | `venue_published_location` |
| `locality_id` | staging location | `venue_published_location.locality_id` |
| `latitude`, `longitude` | staging location | `venue_published_map_point` |

**Proposal header:** `venue_change_proposal` + `venue_proposal_target` (`profile`, `geo` only — **no `hours` target** for restricted-only proposals).

## Contact fields — not in schema today

**Published:** none. `ContactLinksBlock.not_implemented = true` in `detail.py`.

**Proposed addition (planning — migration in Stage 4.3+):**

```text
venue_published_contact (
  venue_id PK,
  phone text,
  email text,
  website text,
  updated_at
)
```

| Field | Until migration |
|-------|-----------------|
| `phone`, `email`, `website` | Omit from UI/API; `contact.supported: false` |

When added: **direct-edit** (not proposal); validate per contract § Validation.

## Authority prerequisites

1. `owner_business_membership.membership_status = 'active'`
2. `business_venue_management_relationship.relationship_lifecycle = 'approved'`
3. **Direct edit:** `venue_capability_grant.capability_code = 'manage_published_venue_operations'`
4. **Restricted request:** `venue_capability_grant.capability_code = 'submit_restricted_changes_for_review'`

## Completeness (server-side)

`required_basics_complete` when **published** has:

- `display_name` (profile)
- `address_line_1` + `locality_id` (location)
- `short_description` (descriptive copy)
- hours: regular row OR non-confident uncertainty OR hours notes

`completeness_percent`: weighted checklist from published truth — not discovery quality score.

`onboarding_status`: no longer `submitted` for operational-only work; `submitted` reserved for open **restricted** proposals.
