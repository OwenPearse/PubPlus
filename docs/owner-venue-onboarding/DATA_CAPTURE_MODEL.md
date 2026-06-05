# Data capture model — Owner venue onboarding

## Purpose

Map onboarding sections to Postgres tables and proposal staging—aligned with Stage 1 frozen API contract.

## Current stage

**Stage 1 complete.** Phase A captures `core_details` only via existing staging tables.

## Decisions

| Section | Phase A | Mechanism |
|---------|---------|-----------|
| Core pub info | ✅ | One proposal, targets `profile`, `geo`, `hours` |
| Contact (phone, email, website) | ❌ deferred | Planned tables below |
| Features | Phase B | `venue_proposal_staging_attribute` |
| Specials / taps | Phase B | Published tables exist; owner staging TBD |
| Events / menu / photos | Deferred | No schema |

- Descriptions live in **`venue_proposal_staging_profile`** (not separate `descriptive_copy` target for owner MVP)
- **No** `google_place_id` in owner capture
- **No** direct publish from owner APIs

## Assumptions

- `actor_type = 'owner'`, `channel = 'owner_portal'`
- Draft upsert on open `staged` owner proposal per venue (see contract)

## Open questions

- Contact migration naming: `venue_published_contact` vs `venue_published_contact_links`

## Dependencies

- `0007`, `0008`, `0019` migrations
- `OWNER_VENUE_API_CONTRACT.md` validation rules
- `STAGING_REVIEW_PUBLISH_AUDIT.md`

## Next downstream use

Backend intake mapper; Stage 3 form fields.

---

## Phase A — Core pub info field map

| UI / API field | Classification | Staging / published |
|----------------|----------------|---------------------|
| `display_name` | Review required | `venue_proposal_staging_profile` → `venue_published_profile` |
| `short_description`, `long_description` | Review required | staging profile → `venue_published_descriptive_copy` |
| `address_line_*`, `postal_code` | Review required | `venue_proposal_staging_location` → `venue_published_location` |
| `locality_id` | Review required (canonical FK) | staging → `venue_published_location.locality_id` |
| `latitude`, `longitude` | Review required | staging → `venue_published_map_point` |
| `opening_hours` | Review required | `venue_proposal_staging_hours` → `venue_hours_*` |
| `owner_confirms_management` | Submit gate only | Not persisted Phase A (validation + optional audit) |

## Contact fields — not in schema today (confirmed)

**Published:** none. `ContactLinksBlock.not_implemented = true` in `backend/src/apps/venues/public_read/detail.py`.

**Proposed addition (planning note only — no migration in Stage 1):**

```text
venue_published_contact (
  venue_id PK,
  phone text,
  email text,
  website text,
  updated_at
)

venue_proposal_staging_contact (
  venue_change_proposal_id,
  venue_id,
  proposed_phone,
  proposed_email,
  proposed_website,
  proposed_contact_person_name,
  proposed_contact_person_role
)

venue_proposal_target.target_family += 'contact'
```

| Field | Until migration |
|-------|-----------------|
| `phone`, `email`, `website` | Omit from Phase A API; UI hidden |
| `contact_person_name`, `contact_person_role` | Defer with contact family |

When added: all **review required**; validate per contract § Validation.

## Optional sections (unchanged from Stage 0)

### Features (Phase B)

Boolean keys from `dev_seed_mvp_filter_taxonomy.sql` — use `attribute_definition_id` / `stable_key` from reference API, not hardcoded labels in backend.

### Specials

`venue_published_structured_special.structured_kind`: `meal_special`, `happy_hour`, `drink_special`, `venue_offer`.

### Tap list

`venue_published_tap_offering` + `beverage_product_id`.

## Authority prerequisites

1. `owner_business_membership.membership_status = 'active'`
2. `business_venue_management_relationship.relationship_lifecycle = 'approved'`
3. Phase A+: `venue_capability_grant.capability_code = 'submit_restricted_changes_for_review'` (recommended enforce)

## Completeness (server-side, Phase A)

`required_basics_complete` when published or staged (open draft counts) has:

- `display_name`
- `address_line_1` + `locality_id`
- `short_description`
- hours: regular row OR `uncertainty_level` ≠ confident-empty OR hours `notes`

`completeness_percent`: weighted checklist (documented in contract) — not discovery quality score.
