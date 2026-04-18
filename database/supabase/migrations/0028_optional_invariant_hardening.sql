-- PubPlus — Wave 10 / Migration 0028
-- Low-risk CHECK hardening for invariants previously documented as app-enforced.
-- Does not enforce recurring vs one-off subtype completeness (still publish/service responsibility).

-- ---------------------------------------------------------------------------
-- Recurring pattern: weekday integers must stay within the documented 0–6 convention
-- ---------------------------------------------------------------------------
alter table public.venue_published_special_recurring_pattern
add constraint recurring_pattern_dow_values_in_week
check (
  recurring_days_of_week <@ array[0, 1, 2, 3, 4, 5, 6]::smallint[]
);

comment on constraint recurring_pattern_dow_values_in_week on public.venue_published_special_recurring_pattern is
'Each element must be a weekday index 0=Sunday … 6=Saturday (aligns with column comment and app validation).';

-- ---------------------------------------------------------------------------
-- Specials validity: “fully_bounded” must carry both endpoints (name ↔ data agreement)
-- ---------------------------------------------------------------------------
alter table public.venue_published_structured_special_validity
add constraint venue_published_structured_special_validity_fully_bounded_requires_bounds
check (
  validity_bounds_kind <> 'fully_bounded'
  or (
    offer_valid_from is not null
    and offer_valid_to is not null
  )
);

comment on constraint venue_published_structured_special_validity_fully_bounded_requires_bounds on public.venue_published_structured_special_validity is
'When validity_bounds_kind is fully_bounded, both offer_valid_from and offer_valid_to must be set; other kinds remain partially app-interpreted.';
