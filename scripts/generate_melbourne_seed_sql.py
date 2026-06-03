"""
Emit idempotent dev seed SQL for Melbourne from dataCollection/melbourne_inner_seed_venues.json.
Run: python scripts/generate_melbourne_seed_sql.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "dataCollection" / "melbourne_inner_seed_venues.json"
OUT_DIR = ROOT / "database" / "sql" / "seeds"

VIC_REGION_ID = "11111111-1111-4111-8111-111111111103"
AUSTRALIA_ID = "11111111-1111-4111-8111-111111111101"
ATTR_FOOD = "33333333-3333-4333-8333-333333333301"
ATTR_STYLE = "33333333-3333-4333-8333-333333333302"
VAL_PUB = "44444444-4444-4444-8444-444444444401"
TZ = "Australia/Sydney"


def _slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "venue"


def locality_id_for(index: int) -> str:
    return f"22222222-2222-4222-8222-{index:012x}"


def _attr_id(venue_i: int, k: int) -> str:
    return f"66666666-6666-4666-8666-{venue_i:08x}{k:04x}"


def _reg_id(venue_i: int, k: int) -> str:
    return f"77777777-7777-4777-8777-{venue_i:08x}{k:04x}"


def _exc_id(venue_i: int) -> str:
    return f"88888888-8888-4888-8888-{venue_i:08x}0000"


def _spec_id(venue_i: int, sidx: int) -> str:
    return f"a3111111-1111-4111-8111-{venue_i:08x}{sidx:04x}"


def emit_recurring_special(
    lines: list[str],
    *,
    sid: str,
    venue_id: str,
    kind: str,
    short_label: str,
    headline: str,
    dows: list[int],
    w_start: str,
    w_end: str,
    cross_mid: bool,
) -> None:
    q = short_label.replace("'", "''")
    h = headline.replace("'", "''")
    arr = "array" + f"[{', '.join(str(d) for d in dows)}]" + "::smallint[]"
    lines.extend(
        [
            f"-- special {short_label!r} @ venue {venue_id[:8]}…",
            "insert into public.venue_published_structured_special (",
            "  id,",
            "  venue_id,",
            "  structured_kind,",
            "  schedule_class,",
            "  short_label,",
            "  catalog_record_status",
            ") values (",
            f"  '{sid}',",
            f"  '{venue_id}',",
            f"  '{kind}',",
            "  'recurring',",
            f"  '{q}',",
            "  'active'",
            ")",
            "on conflict (id) do update set",
            "  venue_id = excluded.venue_id,",
            "  structured_kind = excluded.structured_kind,",
            "  schedule_class = excluded.schedule_class,",
            "  short_label = excluded.short_label,",
            "  catalog_record_status = excluded.catalog_record_status,",
            "  updated_at = now ();",
            "",
            "insert into public.venue_published_structured_special_marketing_copy (",
            "  structured_special_id,",
            "  headline,",
            "  body",
            ")",
            "values (",
            f"  '{sid}',",
            f"  '{h}',",
            "  'Seeded recurring offer for filter + detail validation.'",
            ")",
            "on conflict (structured_special_id) do update set",
            "  headline = excluded.headline,",
            "  body = excluded.body,",
            "  updated_at = now ();",
            "",
            "insert into public.venue_published_special_recurring_pattern (",
            "  structured_special_id,",
            "  recurrence_kind,",
            "  anchor_timezone,",
            "  recurring_days_of_week,",
            "  window_start_time_local,",
            "  window_end_time_local,",
            "  crosses_local_midnight",
            ")",
            "values (",
            f"  '{sid}',",
            "  'weekly_local_time_window',",
            f"  '{TZ}',",
            f"  {arr},",
            f"  time '{w_start}',",
            f"  time '{w_end}',",
            f"  {str(cross_mid).lower()}",
            ")",
            "on conflict (structured_special_id) do update set",
            "  recurrence_kind = excluded.recurrence_kind,",
            "  anchor_timezone = excluded.anchor_timezone,",
            "  recurring_days_of_week = excluded.recurring_days_of_week,",
            "  window_start_time_local = excluded.window_start_time_local,",
            "  window_end_time_local = excluded.window_end_time_local,",
            "  crosses_local_midnight = excluded.crosses_local_midnight,",
            "  updated_at = now ();",
            "",
            "insert into public.venue_published_structured_special_validity (",
            "  structured_special_id,",
            "  offer_valid_from,",
            "  offer_valid_to,",
            "  validity_bounds_kind,",
            "  timing_signal_strength,",
            "  suppress_due_to_weak_or_stale_timing",
            ")",
            "values (",
            f"  '{sid}',",
            "  null,",
            "  null,",
            "  'unknown',",
            "  'strong',",
            "  false",
            ")",
            "on conflict (structured_special_id) do update set",
            "  offer_valid_from = excluded.offer_valid_from,",
            "  offer_valid_to = excluded.offer_valid_to,",
            "  validity_bounds_kind = excluded.validity_bounds_kind,",
            "  timing_signal_strength = excluded.timing_signal_strength,",
            "  suppress_due_to_weak_or_stale_timing = excluded.suppress_due_to_weak_or_stale_timing,",
            "  updated_at = now ();",
            "",
            "insert into public.venue_published_structured_special_discovery_eligibility (",
            "  structured_special_id,",
            "  safe_for_detail_display,",
            "  safe_for_card_badge,",
            "  safe_for_filter_search,",
            "  safe_for_active_now_ranking,",
            "  tier_notes",
            ")",
            "values (",
            f"  '{sid}',",
            "  true,",
            "  true,",
            "  true,",
            "  true,",
            "  'Seeded: all tiers for Stage 3 Melbourne set.'",
            ")",
            "on conflict (structured_special_id) do update set",
            "  safe_for_detail_display = excluded.safe_for_detail_display,",
            "  safe_for_card_badge = excluded.safe_for_card_badge,",
            "  safe_for_filter_search = excluded.safe_for_filter_search,",
            "  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,",
            "  tier_notes = excluded.tier_notes,",
            "  updated_at = now ();",
            "",
        ]
    )


def build_localities(subs: list[str]) -> str:
    lines = [
        "-- PubPlus — VIC + Melbourne inner suburbs (dev seed, idempotent).",
        "-- Source list from dataCollection/melbourne_inner_seed_venues.json",
        "",
        "begin;",
        "",
        "insert into public.geographic_region (",
        "  id,",
        "  parent_region_id,",
        "  name,",
        "  region_code,",
        "  region_level",
        ")",
        "values (",
        f"  '{VIC_REGION_ID}',",
        f"  '{AUSTRALIA_ID}',",
        "  'Victoria',",
        "  'VIC',",
        "  'state'",
        ")",
        "on conflict (id) do update set",
        "  parent_region_id = excluded.parent_region_id,",
        "  name = excluded.name,",
        "  region_code = excluded.region_code,",
        "  region_level = excluded.region_level;",
        "",
    ]
    for i, name in enumerate(sorted(subs, key=str.lower), start=1):
        lid = locality_id_for(i)
        slug = _slugify(name)
        esc = name.replace("'", "''")
        lines.extend(
            [
                "insert into public.locality (",
                "  id,",
                "  geographic_region_id,",
                "  name,",
                "  slug",
                ")",
                "values (",
                f"  '{lid}',",
                f"  '{VIC_REGION_ID}',",
                f"  '{esc}',",
                f"  '{slug}'",
                ")",
                "on conflict (id) do update set",
                "  geographic_region_id = excluded.geographic_region_id,",
                "  name = excluded.name,",
                "  slug = excluded.slug;",
                "",
            ]
        )
    lines.append("commit;")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    subs = data["suburbs"]
    loc_map: dict[str, str] = {}
    for i, name in enumerate(sorted(subs, key=str.lower), start=1):
        loc_map[name] = locality_id_for(i)

    (OUT_DIR / "dev_seed_reference_melbourne_localities.sql").write_text(
        build_localities(subs), encoding="utf-8"
    )

    venues: list[dict] = data["venues"]
    vl: list[str] = [
        "-- PubPlus — Melbourne inner-city test venues (Stage 3 discovery / open-now).",
        "-- Idempotent. Source: dataCollection/melbourne_inner_seed_venues.json",
        "--",
        "-- Roles: idx 1-3 late_night, 4-6 exception, 7-9 sparse+partial, 10-12 meal, 13-15 happy, 16-18 drink, else standard.",
        "",
        "begin;",
        "",
    ]
    vl.append("insert into public.venue (id) values")
    for i, v in enumerate(venues):
        c = "," if i < len(venues) - 1 else ""
        vl.append(f"  ('{v['venue_id']}'){c}")
    vl.append("on conflict (id) do nothing;")
    vl.append("")

    for v in venues:
        i = v["index"]
        vid = v["venue_id"]
        esc = v["business_name"].replace("'", "''")
        sl = f"{_slugify(v['business_name'])}-{_slugify(v['city'])}-{i:03d}"
        vl.extend(
            [
                "insert into public.venue_published_profile (",
                "  venue_id,",
                "  display_name,",
                "  slug,",
                "  discovery_eligibility_status,",
                "  operational_status",
                ")",
                "values (",
                f"  '{vid}',",
                f"  '{esc}',",
                f"  '{sl}',",
                "  'eligible',",
                "  'open'",
                ")",
                "on conflict (venue_id) do update set",
                "  display_name = excluded.display_name,",
                "  slug = excluded.slug,",
                "  discovery_eligibility_status = excluded.discovery_eligibility_status,",
                "  operational_status = excluded.operational_status,",
                "  updated_at = now ();",
                "",
            ]
        )
        vl.extend(
            [
                "insert into public.venue_published_descriptive_copy (",
                "  venue_id,",
                "  short_description,",
                "  long_description",
                ")",
                "values (",
                f"  '{vid}',",
                "  'Seeded inner-Melbourne dev venue.',",
                f"  '{esc} — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'",
                ")",
                "on conflict (venue_id) do update set",
                "  short_description = excluded.short_description,",
                "  long_description = excluded.long_description,",
                "  updated_at = now ();",
                "",
            ]
        )
        al = v["street"].replace("'", "''")
        vl.extend(
            [
                "insert into public.venue_published_location (",
                "  venue_id,",
                "  locality_id,",
                "  address_line_1,",
                "  postal_code,",
                "  country_code",
                ")",
                "values (",
                f"  '{vid}',",
                f"  '{loc_map[v['city']]}',",
                f"  '{al}',",
                f"  '{v['postal_code']}',",
                "  'AU'",
                ")",
                "on conflict (venue_id) do update set",
                "  locality_id = excluded.locality_id,",
                "  address_line_1 = excluded.address_line_1,",
                "  postal_code = excluded.postal_code,",
                "  country_code = excluded.country_code,",
                "  updated_at = now ();",
                "",
            ]
        )
        vl.extend(
            [
                "insert into public.venue_published_map_point (",
                "  venue_id,",
                "  latitude,",
                "  longitude,",
                "  coordinate_system,",
                "  precision_meters",
                ")",
                "values (",
                f"  '{vid}',",
                f"  {v['latitude']},",
                f"  {v['longitude']},",
                "  'WGS84',",
                "  40",
                ")",
                "on conflict (venue_id) do update set",
                "  latitude = excluded.latitude,",
                "  longitude = excluded.longitude,",
                "  coordinate_system = excluded.coordinate_system,",
                "  precision_meters = excluded.precision_meters,",
                "  updated_at = now ();",
                "",
            ]
        )
        vl.extend(
            [
                "insert into public.venue_published_attribute_value (",
                "  id,",
                "  venue_id,",
                "  attribute_definition_id,",
                "  allowed_value_id,",
                "  value_boolean,",
                "  value_numeric",
                ")",
                "values (",
                f"  ('{_attr_id(i, 1)}', '{vid}', '{ATTR_FOOD}', null, true, null),",
                f"  ('{_attr_id(i, 2)}', '{vid}', '{ATTR_STYLE}', '{VAL_PUB}', null, null)",
                ")",
                "on conflict (id) do update set",
                "  venue_id = excluded.venue_id,",
                "  attribute_definition_id = excluded.attribute_definition_id,",
                "  allowed_value_id = excluded.allowed_value_id,",
                "  value_boolean = excluded.value_boolean,",
                "  value_numeric = excluded.value_numeric,",
                "  updated_at = now ();",
                "",
            ]
        )

    for v in venues:
        i = v["index"]
        vid = v["venue_id"]
        roles: set[str] = set(v["stage3_roles"])

        hours_rows: list[str] = []
        if "late_night_crosses_midnight" in roles:
            hours_rows.append(
                f"  ('{_reg_id(i, 0)}', '{vid}', 5, time '17:00', time '02:00', true, 0::smallint)"
            )  # Fri
            hours_rows.append(
                f"  ('{_reg_id(i, 1)}', '{vid}', 6, time '12:00', time '01:00', true, 0::smallint)"
            )  # Sat
        elif "sparse_hours_partial_uncertainty" in roles:
            hours_rows.append(
                f"  ('{_reg_id(i, 0)}', '{vid}', 3, time '12:00', time '20:00', false, 0::smallint)"
            )  # Wed
        else:
            for k, (dow, o, cl) in enumerate(
                [
                    (1, "11:00", "23:00"),  # Mon
                    (3, "11:00", "23:00"),  # Wed
                    (5, "11:00", "23:00"),  # Fri
                ]
            ):
                hours_rows.append(
                    f"  ('{_reg_id(i, k)}', '{vid}', {dow},"
                    f" time '{o}', time '{cl}', false, 0::smallint)"
                )

        vl.append("insert into public.venue_hours_regular (")
        vl.append("  id,")
        vl.append("  venue_id,")
        vl.append("  day_of_week,")
        vl.append("  opens_at,")
        vl.append("  closes_at,")
        vl.append("  crosses_midnight,")
        vl.append("  sort_order")
        vl.append(") values")
        for j, row in enumerate(hours_rows):
            c = "," if j < len(hours_rows) - 1 else ""
            vl.append(row + c)
        vl.append("on conflict (id) do update set")
        vl.append("  venue_id = excluded.venue_id,")
        vl.append("  day_of_week = excluded.day_of_week,")
        vl.append("  opens_at = excluded.opens_at,")
        vl.append("  closes_at = excluded.closes_at,")
        vl.append("  crosses_midnight = excluded.crosses_midnight,")
        vl.append("  sort_order = excluded.sort_order,")
        vl.append("  updated_at = now ();")
        vl.append("")

        if "hours_exception" in roles:
            vl.extend(
                [
                    "insert into public.venue_hours_exception (",
                    "  id,",
                    "  venue_id,",
                    "  start_date,",
                    "  end_date,",
                    "  exception_kind,",
                    "  opens_at,",
                    "  closes_at,",
                    "  crosses_midnight,",
                    "  note",
                    ")",
                    "values (",
                    f"  '{_exc_id(i)}',",
                    f"  '{vid}',",
                    "  date '2020-01-01',",
                    "  date '2030-12-31',",
                    "  'modified_hours',",
                    "  time '10:00',",
                    "  time '22:00',",
                    "  false,",
                    "  'Seeded: long-ranged modified hours (exception overrides regular).'",
                    ")",
                    "on conflict (id) do update set",
                    "  venue_id = excluded.venue_id,",
                    "  start_date = excluded.start_date,",
                    "  end_date = excluded.end_date,",
                    "  exception_kind = excluded.exception_kind,",
                    "  opens_at = excluded.opens_at,",
                    "  closes_at = excluded.closes_at,",
                    "  crosses_midnight = excluded.crosses_midnight,",
                    "  note = excluded.note,",
                    "  updated_at = now ();",
                    "",
                ]
            )

        u = (
            "partial"
            if "sparse_hours_partial_uncertainty" in roles
            else "resolved_confident"
        )
        note = (
            "Seeded partial hours knowledge (sparse regular rows)"
            if u == "partial"
            else "Seeded confident hours snapshot"
        )
        vl.extend(
            [
                "insert into public.venue_hours_uncertainty (",
                "  venue_id,",
                "  uncertainty_level,",
                "  as_of,",
                "  notes",
                ")",
                "values (",
                f"  '{vid}',",
                f"  '{u}',",
                "  now(),",
                f"  '{note}'",
                ")",
                "on conflict (venue_id) do update set",
                "  uncertainty_level = excluded.uncertainty_level,",
                "  as_of = excluded.as_of,",
                "  notes = excluded.notes,",
                "  updated_at = now ();",
                "",
            ]
        )
        cst = "low" if u == "partial" else "medium"
        vl.extend(
            [
                "insert into public.venue_derived_operational_claim (",
                "  venue_id,",
                "  open_now_eligible,",
                "  claim_strength,",
                "  computed_at,",
                "  valid_until",
                ")",
                "values (",
                f"  '{vid}',",
                "  true,",
                f"  '{cst}',",
                "  now(),",
                "  null",
                ")",
                "on conflict (venue_id) do update set",
                "  open_now_eligible = excluded.open_now_eligible,",
                "  claim_strength = excluded.claim_strength,",
                "  computed_at = excluded.computed_at,",
                "  valid_until = excluded.valid_until;",
                "",
            ]
        )

    vl.append("commit;")
    vl.append("")
    (OUT_DIR / "dev_seed_melbourne_inner_venues.sql").write_text(
        "\n".join(vl) + "\n", encoding="utf-8"
    )

    # specials: meal 10-12, happy 13-15, drink 16-18
    sl: list[str] = [
        "-- Melbourne structured specials (idempotent; Stage 3 filters).",
        "-- Pairs with dev_seed_melbourne_inner_venues.sql (same venue_id block).",
        "",
        "begin;",
        "",
    ]
    for v in venues:
        i = v["index"]
        vid = v["venue_id"]
        if i in (10, 11, 12):
            emit_recurring_special(
                sl,
                sid=_spec_id(i, 1),
                venue_id=vid,
                kind="meal_special",
                short_label="Parma and pot night",
                headline="Recurring: Wednesday pub classic",
                dows=[3],  # Wed
                w_start="18:00",
                w_end="21:00",
                cross_mid=False,
            )
        elif i in (13, 14, 15):
            emit_recurring_special(
                sl,
                sid=_spec_id(i, 1),
                venue_id=vid,
                kind="happy_hour",
                short_label="Happy hour: house pour",
                headline="Thu–Sun happy hour",
                dows=[4, 5, 6, 0],  # Thu, Fri, Sat, Sun
                w_start="17:00",
                w_end="19:00",
                cross_mid=False,
            )
        elif i in (16, 17, 18):
            emit_recurring_special(
                sl,
                sid=_spec_id(i, 1),
                venue_id=vid,
                kind="drink_special",
                short_label="Tap jugs and pints",
                headline="Weekend jugs and selected pints",
                dows=[5, 6, 0],
                w_start="16:00",
                w_end="20:00",
                cross_mid=False,
            )
    sl.append("commit;")
    sl.append("")
    (OUT_DIR / "dev_seed_melbourne_inner_specials.sql").write_text(
        "\n".join(sl) + "\n", encoding="utf-8"
    )
    print("Wrote", OUT_DIR / "dev_seed_reference_melbourne_localities.sql")
    print("Wrote", OUT_DIR / "dev_seed_melbourne_inner_venues.sql")
    print("Wrote", OUT_DIR / "dev_seed_melbourne_inner_specials.sql")


if __name__ == "__main__":
    main()
