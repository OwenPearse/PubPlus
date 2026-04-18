# SQL drafting notes — Tranche 1 (Waves 1–9 + Wave 10 cleanup)

This file records **implementation-level** choices made while staying within locked architecture. It does not reopen planning decisions.

## Migration ordering

Migrations `0001`–`0029` apply in lexical order. Dependencies:

- Published tables reference `venue` and geography/attribute reference rows created earlier.
- Workflow tables reference account anchors from `0002`.
- `0008` depends on proposals from `0007`; `0009` depends on `proposal_review` from `0008`.
- `0010`–`0012` (Wave 4) depend on `consumer_account`, `venue`, `locality`, `geographic_region`, and `venue_change_proposal`.
- `0013`–`0016` (Wave 5) depend on `owner_account`, `admin_account`, `business`, and `venue`. `0015` adds `venue_claim_request` and then adds `business_venue_management_relationship.source_venue_claim_request_id`. `0016` depends on `business_venue_management_relationship` and `owner_account`.
- `0017`–`0020` (Wave 6 RLS) depend on all tables above; apply after `0016`. Helpers `current_consumer_account_id`, `current_owner_account_id`, `owner_is_member_of_business`, `current_admin_account_id`, `is_admin_session` are `SECURITY INVOKER` / `STABLE` and are granted to `anon` and `authenticated` for policy evaluation (calling them without a matching account row returns null/false).
- `0021`–`0023` (Wave 8 structured specials) depend on `venue` from `0002`. `0022` depends on `0021`; `0023` depends on `0021`–`0022`. Published-special tables get **SELECT-only** RLS in `0023` (parity with `0017`); they are **not** included in migration `0017`’s policy list.
- `0024`–`0026` (Wave 9 tap list backbone) depend on `venue` from `0002`. `0025` depends on `0024` (tap offering references `beverage_product`). `0026` depends on `0025` (validity/eligibility children). **SELECT-only** RLS for all new tap + beverage reference tables is added in `0026` only (same pattern as specials: `0021`–`0022` without RLS, `0023` applies RLS). Planning doc `recommended_migration_schema_build_order.md` lists “Tap List” after specials; SQL drafting numbers that slice **Wave 9** because specials already occupy Wave 8 (`0021`–`0023`).
- `0027`–`0029` (Wave 10 post-wave cleanup / hardening) depend on `0026`. `0027` adds FK/workflow/catalog indexes; `0028` adds two low-risk CHECK constraints (recurring DOW values; `fully_bounded` validity bounds); `0029` refreshes table comments for companion/reference clarity without changing shapes.

## Wave 10 — Post-wave cleanup and hardening (`0027`–`0029`)

- **No new domains:** indexes, two optional CHECKs, and comment alignment only — see `WAVE_10_POST_WAVE_CLEANUP_AND_HARDENING.md`.
- **Subtype completeness** (recurring vs one-off child rows vs `schedule_class`) remains **publish/service validated**; Wave 10 deliberately does not add cross-table triggers or exclusion constraints.
- **Verification:** `database/sql/checks/check_wave_10_post_wave_cleanup_and_hardening.sql`; `check_first_tranche_end_to_end.sql` includes an extended table-presence section when `0021+` is applied.

## Enum / CHECK vs lookup tables

- **Stable, small vocabularies** (actor type, channel, proposal lifecycle, publish event kind, evidence kind, hours uncertainty) use `TEXT` + `CHECK` lists in v1.
- **Evolving or admin-editable** vocabularies use tables: `venue_attribute_allowed_value`, `external_data_source`, geography nodes.

## Publish boundary

- DDL cannot enforce “no direct writes” to published tables; **RLS + service role** must implement DL-008. Migration `0009` documents the intended posture; migration `0017` adds **SELECT-only** policies for published-truth tables and leaves **no** `INSERT`/`UPDATE`/`DELETE` policies for `anon`/`authenticated`.

## Staging hours JSON

- `venue_proposal_staging_hours.regular_hours_json` / `exceptions_json` store proposal packages before normalization. Publish workflows must validate shape and write to `venue_hours_regular` / `venue_hours_exception` / `venue_hours_uncertainty`.

## Attribute value integrity

- `venue_published_attribute_value.allowed_value_id` references `venue_attribute_allowed_value.id` only; ensuring the value belongs to the same `attribute_definition_id` as the row is left to **publish validation** (composite FK possible in a follow-up migration).

## Supabase / auth

- Account tables reference `auth.users(id)`. Migrations assume Supabase Auth is present.

## Wave 4 — Consumer private state (0010–0012)

- **`consumer_profile` scope**: minimal display/support fields only; do not treat this table as the future container for personalization, history, or social features (deferred per MVP guidance — add separate tables later if product requires them).
- **Split tables vs one blob**: `consumer_profile`, `consumer_default_location_preference`, and `consumer_notification_settings` are separate 1:1 tables keyed by `consumer_account_id` to keep domains explicit (Worker B / DL-023).
- **Default location nullability**: both `default_locality_id` and `default_geographic_region_id` may be null to represent “cleared”; the app decides whether one or both are required for a valid preference.
- **Quiet hours**: stored as local `time without time zone` pairs; timezone for interpretation is not in-schema in v1.
- **Push toggle**: `push_notifications_opt_in` names product push channel consent distinctly from email/SMS columns.
- **Saved lists**: list-native model only — `saved_list` + `saved_list_membership` to `venue`; optional `position` on membership for ordering; `is_archived` on lists without a separate archive table.
- **Submissions**: `venue_change_proposal` remains the spine for truth-impacting packages. `consumer_submission_extension` is optional 1:1 metadata; `consumer_workflow_submission` covers non-proposal authenticated intake. Actor alignment between extension and `actor_consumer_account_id` is enforced in application code.

## Wave 5 — Owner / business authority (0013–0016)

- **Membership vs venue authority**: `owner_business_membership` is only owner↔business; it does not reference `venue` and does not grant venue-scoped capabilities (DL-021).
- **Managed-venue junction**: `business_venue_management_relationship` is the sole attachment point for `venue_capability_grant` rows; there is no `owner_account`→`venue` permission edge.
- **v1 shape vs future history**: migration `0014` uses one row per `(business_id, venue_id)` with a lifecycle column—that is a **convenience for early reads**, not a schema invariant. Later workers may replace or supplement that with a history-heavy or split-table model if needed; architecture still requires an explicit business↔venue management link and distinct claim / verification / rights / grants.
- **Claim vs relationship vs verification vs rights vs grants**: modeled as `venue_claim_request`, `business_venue_management_relationship` (+ optional claim pointers), `venue_verification_state`, `venue_management_rights`, and `venue_capability_grant` respectively—no collapsed “claim status = access” table.
- **Companion rows**: `venue_verification_state` and `venue_management_rights` use `business_venue_management_relationship_id` as the primary key (1:1) for clear current-state reads.
- **Authority audit**: `venue_authority_decision` records human authority outcomes; `venue_authority_event` is append-only and must not replace `venue_capability_grant` for live permission checks (DL-022).
- **Coarse capabilities**: `venue_capability_grant.capability_code` uses a short CHECK list aligned to Worker B examples; not a granular ACL.
- **DDL limits**: membership-in-business when filing claims or receiving grants is not enforced with composite FKs—validate in application or a later constraint/trigger if required.

## Wave 6 — RLS and permission guardrails (0017–0020)

- **Public truth reads**: `0017` enables RLS on published-truth tables with `SELECT` for `anon` and `authenticated`; all client writes remain denied by default (no write policies). `service_role` bypasses RLS for publish/ETL.
- **Consumer domain**: `0018` scopes private tables and consumer-actor proposals/staging to `current_consumer_account_id()`; `consumer_account` is self-`SELECT` only (no client insert policy — provisioning stays service/trigger-led).
- **Owner domain**: `0019` scopes business and authority-chain reads through non-removed `owner_business_membership` and managed-venue rows; `venue_claim_request` updates are **initiator-only**; team-wide edits stay backend/service.
- **Admin vs service**: `0020` adds **admin-session `SELECT`** on workflow/audit/evidence/raw intake and broad read on proposals/staging/authority/business tables; **no** admin policies on consumer-private tables in v1 (support tooling should use `service_role` until a dedicated policy tranche exists).
- **Orchestration actors**: proposals may use `actor_type = 'system' | 'source'` — **no** matching client policies here; those rows are service/ingestion only.
- **JWT / metadata**: policies use `auth.uid()` and account tables only — not `user_metadata` (Supabase security guidance).
- **RLS helpers**: Wave 6 adds only a **minimal** set of `SECURITY INVOKER` helpers; **later workers should avoid turning policy logic into a sprawling helper-function ecosystem** unless there is a **clear, concrete need** (readability/auditability or repeated predicates that are error-prone to copy). Prefer inline conditions or tightly scoped additions.

## Wave 7 — Verification + dev/demo seeds (first tranche)

Shipped alongside migrations `0001`–`0020` (see `WAVE_07_VERIFICATION_AND_SEEDS.md` and `FIRST_TRANCHE_OVERVIEW.md`); extended by Waves 8–10 checks as migrations grew.

- **Checks:** `database/sql/checks/check_wave_01_foundations.sql` … `check_wave_06_rls_and_permission_guardrails.sql`, `check_wave_08_specials_promotions.sql`, `check_wave_09_tap_list_backbone.sql`, `check_wave_10_post_wave_cleanup_and_hardening.sql`, plus `check_first_tranche_end_to_end.sql`.
- **Seeds:** `database/sql/seeds/dev_seed_reference_minimum.sql`, `dev_seed_demo_venues.sql`, `dev_seed_demo_accounts_and_relationships.sql`, composed by `database/supabase/seed.sql`.

**Later workers:** extend seeds with new reference data as needed; avoid duplicating large “fake prod” datasets. Keep auth + published direct-insert demos clearly labeled as **local/dev only** in docs (RLS still blocks normal clients from mutating published truth).

## Wave 8 — Structured specials / promotions (`0021`–`0023`)

- **Truth vs copy:** `venue_published_structured_special` carries structured kind, schedule class, and a short structured `short_label` for UI/list identity. Long-form marketing text is **only** in `venue_published_structured_special_marketing_copy`.
- **Recurring vs one-off:** `schedule_class` plus separate subtype tables preserves DL-018; v1 does not add a DB trigger enforcing “exactly one subtype row matches `schedule_class`” — publish pipelines should validate (or a later migration adds a deferred constraint/trigger).
- **DOW convention:** `venue_published_special_recurring_pattern.recurring_days_of_week` uses **0 = Sunday … 6 = Saturday** (documented on column); align validation and any future ISO-8601 alternative in one place if product standardizes differently.
- **Validity vs tiers:** `venue_published_structured_special_validity` and `venue_published_structured_special_discovery_eligibility` are split so “weak timing” and “where it may appear” are not collapsed. No CHECK forces `safe_for_active_now_ranking` ⇒ `safe_for_filter_search` — conservative derivation stays explicit in application logic.
- **RLS:** Wave 8 policies are added in `0023` only; migration `0017` is unchanged — if you reset DBs often, apply `0021`–`0023` after `0017` so specials tables are covered.

**Supabase CLI:** ensure `seed.sql` path matches your project layout if the CLI config points at a different `supabase/` directory than `database/supabase/`.

## Wave 9 — Tap list backbone (`0024`–`0026`)

- **Reference vs offering:** `beverage_product` (with optional `beverage_brewery` / `beverage_style`) holds **identity**; `venue_published_tap_offering` holds **venue-specific** state. No `venue_id` on product rows (DL-029).
- **Traits vs identity:** `is_rotating`, `is_guest_tap`, `is_limited_run` are **only** on `venue_published_tap_offering` — they are not proof of a specific current SKU (rules 20–21).
- **Unstructured label:** `unstructured_line_label` is for display/context; pairing with discovery filters should require structured `beverage_product_id` + tier gates, not text alone (DL-005).
- **Validity vs tiers:** `venue_published_tap_offering_validity` and `venue_published_tap_offering_discovery_eligibility` are split so freshness and “where it may appear” are not collapsed. **`safe_for_strong_current_tap_claim`** is the strongest present-tense tier — analogous in spirit to `safe_for_active_now_ranking` on specials, but named for tap semantics. No CHECK forces tier implications; conservative derivation stays in application logic.
- **RLS:** Wave 9 policies live in `0026` only; migration `0017` is unchanged — reset DBs must apply `0024`–`0026` after `0017` so tap tables are covered.
- **Demo seed:** `database/sql/seeds/dev_seed_demo_taps.sql` — optional include alongside venue seeds; not added to `seed.sql` in this tranche.

## Non-blocking review items

- Whether `day_of_week` should follow ISO-8601 Monday-first instead of US Sunday-first.
- Whether `audit_event` should be partitioned or replaced with product analytics pipeline for high volume.
- Whether `consumer_notification_settings` should add a stored IANA timezone name once quiet hours need DB-level comparisons.
- Whether `availability_truth_state` should later align to a shared enum with other dynamic domains (hours/specials) for operational analytics only — v1 uses tap-local CHECK text.
