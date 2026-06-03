# PubPlus — Migration run order (drafted first tranche)

## Rule

Apply migrations in **lexical filename order** under `database/supabase/migrations/`. Supabase and most migration runners sort `0001` … `0033` correctly; do not reorder files to “optimize” unless you are resolving an explicit dependency bug.

## Files (0001–0033)

| Order | File | SQL drafting wave (approx.) |
|------:|------|-------------------------------|
| 1 | `0001_extensions_and_base_types.sql` | 1 |
| 2 | `0002_canonical_venue_backbone.sql` | 1 |
| 3 | `0003_published_geography_core.sql` | 1 |
| 4 | `0004_published_venue_profile_core.sql` | 2 |
| 5 | `0005_discovery_attribute_foundations.sql` | 2 |
| 6 | `0006_hours_and_exceptions_foundations.sql` | 2 |
| 7 | `0007_raw_intake_and_proposals.sql` | 3 |
| 8 | `0008_reviews_publish_lineage.sql` | 3 |
| 9 | `0009_provenance_evidence_audit_minimums.sql` | 3 |
| 10 | `0010_consumer_profile_and_private_preferences.sql` | 4 |
| 11 | `0011_saved_lists_and_membership.sql` | 4 |
| 12 | `0012_consumer_authenticated_submissions.sql` | 4 |
| 13 | `0013_owner_business_membership.sql` | 5 |
| 14 | `0014_business_venue_management_relationships.sql` | 5 |
| 15 | `0015_claims_verification_and_management_rights.sql` | 5 |
| 16 | `0016_venue_scoped_permission_grants.sql` | 5 |
| 17 | `0017_rls_public_truth_reads.sql` | 6 |
| 18 | `0018_rls_consumer_private_state.sql` | 6 |
| 19 | `0019_rls_owner_business_authority.sql` | 6 |
| 20 | `0020_rls_workflow_audit_admin_boundaries.sql` | 6 |
| 21 | `0021_structured_specials_backbone.sql` | 8 |
| 22 | `0022_recurring_offers_and_one_off_promotions.sql` | 8 |
| 23 | `0023_specials_validity_and_eligibility.sql` | 8 |
| 24 | `0024_beverage_reference_backbone.sql` | 9 (tap list) |
| 25 | `0025_venue_tap_offering_state.sql` | 9 |
| 26 | `0026_tap_validity_freshness_and_eligibility.sql` | 9 |
| 27 | `0027_post_wave_constraints_and_indexes.sql` | 10 |
| 28 | `0028_optional_invariant_hardening.sql` | 10 |
| 29 | `0029_schema_cleanup_and_consistency.sql` | 10 |
| 30 | `0030_business_subscription_backbone.sql` | 11 |
| 31 | `0031_business_entitlements_and_venue_overlays.sql` | 11 |
| 32 | `0032_commercial_overlay_adjacency.sql` | 11 (RLS for Wave 11) |
| 33 | `0033_founder_venue_leads.sql` | Founder venue lead research (internal ops) |

## Planning doc vs migration numbers

`recommended_migration_schema_build_order.md` uses **product wave names** (e.g. “Wave 8 — Tap List”) that do not always match **SQL drafting wave numbers** (specials already consumed migration numbers `0021`–`0023`, so tap list is drafted as Wave 9 in SQL notes). Treat the **file order above** as authoritative for apply order; treat planning docs as domain sequencing intent.

## After apply

1. Run per-wave checks for any domain you touch, plus `check_first_tranche_end_to_end.sql`.
2. On a full fresh apply of `0001`–`0033`, run `check_full_schema_readiness.sql` for a single cross-cutting pass.

See `WAVE_12_FINAL_READINESS_REVIEW.md` and `SQL_DRAFTING_NOTES.md` for verification and seed ordering.

**Railway production (Stage 5C):** apply via `supabase db push` on the Supabase project that matches Railway `DATABASE_URL`; operator checklist — [../RAILWAY_STAGE_5C_DB_READINESS.md](../RAILWAY_STAGE_5C_DB_READINESS.md).
