"""
Assembles public venue read models from published truth only.

`open_now` is always left null; set `open_now_uncomputed` on card / hours block
until the shared `open_now` service exists (see docs/OPEN_NOW_AND_DISCOVERY_RULES).
"""

from __future__ import annotations

from dataclasses import replace
from typing import TypeAlias
from uuid import UUID

from common.auth.context import AuthContext
from common.geo import distance_m

from apps.venues.public_read.card import PublicVenueCard, public_venue_card_to_dict
from apps.venues.public_read.detail import (
    ContactLinksBlock,
    DrinksTapsBlock,
    EventsBlock,
    FeaturesBlock,
    FeatureItem,
    HoursAndOpenBlock,
    HoursExceptionRow,
    IdentityBlock,
    LocationBlock,
    PhotosBlock,
    PublicVenueDetail,
    RegularHoursRow,
    SpecialItem,
    SpecialsBlock,
    TapHighlight,
    public_venue_detail_to_dict,
)
from apps.venues.services.published_venue_read import (
    PublishedVenueReadBundle,
    get_published_hours_uncertainty,
    load_published_venue_read_bundle,
)
from apps.venues.services import save_enrichment
from apps.venues.services.venue_media import resolve_hero_and_gallery

VenueId: TypeAlias = UUID | str

VENUE_TYPE_KEY = "venue_style"


def _address_line_short(bundle: PublishedVenueReadBundle) -> str:
    c = bundle.core
    parts = [p for p in (c.address_line_1, c.address_line_2) if p]
    if parts:
        return ", ".join(parts)
    return c.suburb_name


def _venue_type_value(attrs: list) -> str | None:
    for a in attrs:
        if a.stable_key == VENUE_TYPE_KEY and a.value_code is not None:
            return a.value_code
    for a in attrs:
        if a.stable_key == VENUE_TYPE_KEY and a.value_label is not None:
            return a.value_label
    return None


def _feature_badges(attrs: list) -> list[str]:
    out: list[str] = []
    for a in attrs:
        if not a.is_discovery_driving:
            continue
        if a.stable_key == VENUE_TYPE_KEY:
            continue
        if a.value_boolean is not None and a.value_boolean is True:
            out.append(a.definition_label)
        elif a.value_label:
            out.append(a.value_label)
    return out


def _specials_summary_lines(specials: list, limit: int = 3) -> list[str]:
    out: list[str] = []
    for s in specials[:limit]:
        if s.headline and s.headline.strip():
            out.append(s.headline.strip())
        else:
            out.append(f"{s.short_label} ({s.structured_kind})")
    return out


def _drink_highlights(taps: list, limit: int = 3) -> list[str]:
    out: list[str] = []
    for t in taps[:limit]:
        label = t.product_name or t.unstructured_line_label
        if not label:
            continue
        out.append(label)
    return out


def _tap_line_label(t) -> str:
    return t.product_name or t.unstructured_line_label or "Drink list"


def bundle_to_public_venue_card(
    bundle: PublishedVenueReadBundle,
    *,
    origin_lat: float | None = None,
    origin_lon: float | None = None,
) -> PublicVenueCard:
    core = bundle.core
    res = resolve_hero_and_gallery(bundle.media_refs)
    dist: float | None = None
    if origin_lat is not None and origin_lon is not None:
        dist = round(
            distance_m(origin_lat, origin_lon, core.latitude, core.longitude), 1
        )
    return PublicVenueCard(
        id=core.venue_id,
        name=core.display_name,
        venue_type=_venue_type_value(bundle.attributes),
        suburb=core.suburb_name,
        address_short=_address_line_short(bundle),
        latitude=core.latitude,
        longitude=core.longitude,
        hero_photo_url=res.hero_url,
        open_now=None,
        open_now_uncomputed=True,
        distance_m=dist,
        feature_badges=_feature_badges(bundle.attributes),
        specials_summary=_specials_summary_lines(bundle.specials),
        events_summary=[],
        drink_highlights=_drink_highlights(bundle.taps),
        is_saved=None,
    )


def build_public_venue_card(
    venue_id: VenueId,
    *,
    origin_lat: float | None = None,
    origin_lon: float | None = None,
    auth: AuthContext | None = None,
) -> PublicVenueCard | None:
    bundle = load_published_venue_read_bundle(venue_id)
    if not bundle:
        return None
    c = bundle_to_public_venue_card(
        bundle, origin_lat=origin_lat, origin_lon=origin_lon
    )
    return save_enrichment.apply_save_to_card(c, auth=auth, venue_id=c.id)


def _detail_features_items(attrs) -> list[FeatureItem]:
    return [
        FeatureItem(
            stable_key=a.stable_key,
            label=a.definition_label,
            value_code=a.value_code,
            value_label=a.value_label,
            value_boolean=a.value_boolean,
        )
        for a in attrs
    ]


def bundle_to_public_venue_detail(
    bundle: PublishedVenueReadBundle, *, auth: AuthContext | None
) -> PublicVenueDetail:
    core = bundle.core
    desc = bundle.descriptive
    res = resolve_hero_and_gallery(bundle.media_refs)
    identity = IdentityBlock(
        id=core.venue_id,
        name=core.display_name,
        slug=core.slug,
        venue_type=_venue_type_value(bundle.attributes),
        short_description=desc.short_description if desc else None,
        long_description=desc.long_description if desc else None,
        operational_status=core.operational_status,
    )
    location = LocationBlock(
        suburb=core.suburb_name,
        address_line_1=core.address_line_1,
        address_line_2=core.address_line_2,
        postal_code=core.postal_code,
        country_code=core.country_code,
        latitude=core.latitude,
        longitude=core.longitude,
    )
    regular = [
        RegularHoursRow(
            day_of_week=r.day_of_week,
            opens_at=r.opens_at,
            closes_at=r.closes_at,
            crosses_midnight=r.crosses_midnight,
            sort_order=r.sort_order,
        )
        for r in bundle.hours_regular
    ]
    exceptions = [
        HoursExceptionRow(
            start_date=e.start_date,
            end_date=e.end_date,
            exception_kind=e.exception_kind,
            opens_at=e.opens_at,
            closes_at=e.closes_at,
            crosses_midnight=e.crosses_midnight,
            note=e.note,
        )
        for e in bundle.hours_exceptions
    ]
    hours = HoursAndOpenBlock(
        open_now=None,
        open_now_uncomputed=True,
        regular=regular,
        exceptions=exceptions,
    )
    photos = PhotosBlock(hero_photo_url=res.hero_url, items=list(res.photos))
    features = FeaturesBlock(items=_detail_features_items(bundle.attributes))
    specials = SpecialsBlock(
        items=[
            SpecialItem(
                id=s.id, structured_kind=s.structured_kind, short_label=s.short_label, headline=s.headline
            )
            for s in bundle.specials
        ]
    )
    events = EventsBlock()
    drinks = DrinksTapsBlock(
        highlights=[
            TapHighlight(
                id=t.id,
                line_label=_tap_line_label(t),
                product_name=t.product_name,
                is_rotating=t.is_rotating,
                is_guest_tap=t.is_guest_tap,
            )
            for t in bundle.taps
        ]
    )
    contact = ContactLinksBlock()
    is_saved: bool | None
    if auth is None:
        is_saved = None
    else:
        is_saved = save_enrichment.venue_id_in_any_user_list(venue_id=core.venue_id, auth=auth)
    actions = save_enrichment.build_actions_block(auth=auth, is_saved=is_saved)
    return PublicVenueDetail(
        identity=identity,
        location=location,
        hours=hours,
        photos=photos,
        features=features,
        specials=specials,
        events=events,
        drinks=drinks,
        contact=contact,
        actions=actions,
    )


def apply_open_now_to_detail(
    detail: PublicVenueDetail, *, bundle: PublishedVenueReadBundle
) -> PublicVenueDetail:
    from services.discovery.open_now import compute_open_now

    open_res = compute_open_now(
        bundle,
        hours_uncertainty_level=get_published_hours_uncertainty(bundle.core.venue_id),
    )
    return replace(
        detail,
        hours=replace(
            detail.hours,
            open_now=open_res.public_open_now,
            open_now_uncomputed=open_res.public_open_now_uncomputed,
        ),
    )


def build_public_venue_detail(
    venue_id: VenueId, *, auth: AuthContext | None = None
) -> PublicVenueDetail | None:
    bundle = load_published_venue_read_bundle(venue_id)
    if not bundle:
        return None
    detail = bundle_to_public_venue_detail(bundle, auth=auth)
    return apply_open_now_to_detail(detail, bundle=bundle)


def public_venue_card_dict(
    venue_id: VenueId,
    *,
    origin_lat: float | None = None,
    origin_lon: float | None = None,
    auth: AuthContext | None = None,
) -> dict | None:
    c = build_public_venue_card(
        venue_id, origin_lat=origin_lat, origin_lon=origin_lon, auth=auth
    )
    if not c:
        return None
    return public_venue_card_to_dict(c)


def public_venue_detail_dict(
    venue_id: VenueId, *, auth: AuthContext | None = None
) -> dict | None:
    d = build_public_venue_detail(venue_id, auth=auth)
    if not d:
        return None
    return public_venue_detail_to_dict(d)


def open_now_not_implemented_payload_hint() -> dict:
    return {
        "open_now": None,
        "open_now_uncomputed": True,
        "integration": "open_now is populated by a future shared discovery service, not in Stage 2.",
    }
