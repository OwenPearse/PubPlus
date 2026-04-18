-- PubPlus — Wave 10 / Migration 0029
-- Documentation and consistency cleanup: comments, index notes, migration cross-references.
-- No table/column renames and no domain mixing.

-- ---------------------------------------------------------------------------
-- Emphasize companion 1:1 tables (already PK-linked; comments align wave docs)
-- ---------------------------------------------------------------------------
comment on table public.venue_published_structured_special_marketing_copy is
'Marketing/descriptive copy adjacent to structured specials; must not replace structured timing/offer truth (DL-017). One row per structured_special_id (PK).';

comment on table public.venue_published_structured_special_validity is
'Validity/timing layer for structured specials: distinct from catalog presence and from per-tier discovery eligibility. One row per structured_special_id (PK).';

comment on table public.venue_published_structured_special_discovery_eligibility is
'Independent discovery tiers; published/catalog presence does not imply any tier — especially active-now/ranking (DL-019). One row per structured_special_id (PK).';

comment on table public.venue_published_tap_offering_validity is
'Freshness and assertion strength for tap lines: distinct from catalog presence and from per-tier discovery eligibility. One row per tap_offering_id (PK).';

comment on table public.venue_published_tap_offering_discovery_eligibility is
'Independent discovery tiers; catalog presence does not imply any tier — especially strong current-tap claims. One row per tap_offering_id (PK).';

-- ---------------------------------------------------------------------------
-- Beverage reference: reinforce separation from venue state (DL-029)
-- ---------------------------------------------------------------------------
comment on table public.beverage_product is
'Product identity in the reference layer; does not encode whether any venue currently pours it (DL-029). No venue_id column by design.';
