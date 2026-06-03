from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict


@dataclass
class IdentityBlock:
    id: str
    name: str
    slug: str | None
    venue_type: str | None
    short_description: str | None
    long_description: str | None
    operational_status: str | None


@dataclass
class LocationBlock:
    suburb: str
    address_line_1: str | None
    address_line_2: str | None
    postal_code: str | None
    country_code: str
    latitude: float
    longitude: float


@dataclass
class RegularHoursRow:
    day_of_week: int
    opens_at: str
    closes_at: str
    crosses_midnight: bool
    sort_order: int


@dataclass
class HoursExceptionRow:
    start_date: str
    end_date: str
    exception_kind: str
    opens_at: str | None
    closes_at: str | None
    crosses_midnight: bool
    note: str | None


@dataclass
class HoursAndOpenBlock:
    """
    `open_now` is null until centralized computation exists.
    Raw hours are published public truth; do not infer open_now here.
    """

    open_now: bool | None
    open_now_uncomputed: bool
    regular: list[RegularHoursRow] = field(default_factory=list)
    exceptions: list[HoursExceptionRow] = field(default_factory=list)


@dataclass
class PhotoItem:
    """
    `storage_object_path` is the key within the configured public bucket
    (Supabase Storage), not a Django media path.
    `url` is a direct public storage URL when resolvable.
    """

    id: str | None
    sort_order: int | None
    storage_object_path: str | None
    url: str | None
    is_hero: bool


@dataclass
class PhotosBlock:
    hero_photo_url: str | None
    items: list[PhotoItem] = field(default_factory=list)


@dataclass
class FeatureItem:
    stable_key: str
    label: str
    value_code: str | None
    value_label: str | None
    value_boolean: bool | None


@dataclass
class FeaturesBlock:
    items: list[FeatureItem] = field(default_factory=list)


@dataclass
class SpecialItem:
    id: str
    structured_kind: str
    short_label: str
    headline: str | None


@dataclass
class SpecialsBlock:
    items: list[SpecialItem] = field(default_factory=list)


@dataclass
class EventItem:
    id: str
    title: str
    starts_at: str | None
    ends_at: str | None
    description: str | None


@dataclass
class EventsBlock:
    """
    No published venue events table in current schema; `items` stays empty
    until a `venue_published_*` event catalog exists.
    """

    items: list[EventItem] = field(default_factory=list)
    not_implemented: bool = True


@dataclass
class TapHighlight:
    id: str
    line_label: str
    product_name: str | None
    is_rotating: bool
    is_guest_tap: bool


@dataclass
class DrinksTapsBlock:
    highlights: list[TapHighlight] = field(default_factory=list)


@dataclass
class ContactLink:
    link_type: str
    value: str
    display_label: str | None


@dataclass
class ContactLinksBlock:
    """
    Placeholder until a published contact-links table is added; keep shape stable.
    """

    items: list[ContactLink] = field(default_factory=list)
    not_implemented: bool = True


@dataclass
class AuthenticatedActionsBlock:
    can_save: bool
    is_saved: bool | None
    save_requires_auth: bool


@dataclass
class PublicVenueDetail:
    identity: IdentityBlock
    location: LocationBlock
    hours: HoursAndOpenBlock
    photos: PhotosBlock
    features: FeaturesBlock
    specials: SpecialsBlock
    events: EventsBlock
    drinks: DrinksTapsBlock
    contact: ContactLinksBlock
    actions: AuthenticatedActionsBlock


def public_venue_detail_to_dict(d: PublicVenueDetail) -> dict[str, Any]:
    return {
        "identity": {
            "id": d.identity.id,
            "name": d.identity.name,
            "slug": d.identity.slug,
            "venue_type": d.identity.venue_type,
            "short_description": d.identity.short_description,
            "long_description": d.identity.long_description,
            "operational_status": d.identity.operational_status,
        },
        "location": {
            "suburb": d.location.suburb,
            "address_line_1": d.location.address_line_1,
            "address_line_2": d.location.address_line_2,
            "postal_code": d.location.postal_code,
            "country_code": d.location.country_code,
            "latitude": d.location.latitude,
            "longitude": d.location.longitude,
        },
        "hours": {
            "open_now": d.hours.open_now,
            "open_now_uncomputed": d.hours.open_now_uncomputed,
            "regular": [
                {
                    "day_of_week": r.day_of_week,
                    "opens_at": r.opens_at,
                    "closes_at": r.closes_at,
                    "crosses_midnight": r.crosses_midnight,
                    "sort_order": r.sort_order,
                }
                for r in d.hours.regular
            ],
            "exceptions": [
                {
                    "start_date": e.start_date,
                    "end_date": e.end_date,
                    "exception_kind": e.exception_kind,
                    "opens_at": e.opens_at,
                    "closes_at": e.closes_at,
                    "crosses_midnight": e.crosses_midnight,
                    "note": e.note,
                }
                for e in d.hours.exceptions
            ],
        },
        "photos": {
            "hero_photo_url": d.photos.hero_photo_url,
            "items": [
                {
                    "id": p.id,
                    "sort_order": p.sort_order,
                    "storage_object_path": p.storage_object_path,
                    "url": p.url,
                    "is_hero": p.is_hero,
                }
                for p in d.photos.items
            ],
        },
        "features": {
            "items": [
                {
                    "stable_key": f.stable_key,
                    "label": f.label,
                    "value_code": f.value_code,
                    "value_label": f.value_label,
                    "value_boolean": f.value_boolean,
                }
                for f in d.features.items
            ],
        },
        "specials": {
            "items": [
                {
                    "id": s.id,
                    "structured_kind": s.structured_kind,
                    "short_label": s.short_label,
                    "headline": s.headline,
                }
                for s in d.specials.items
            ],
        },
        "events": {
            "items": [
                {
                    "id": e.id,
                    "title": e.title,
                    "starts_at": e.starts_at,
                    "ends_at": e.ends_at,
                    "description": e.description,
                }
                for e in d.events.items
            ],
            "not_implemented": d.events.not_implemented,
        },
        "drinks": {
            "highlights": [
                {
                    "id": h.id,
                    "line_label": h.line_label,
                    "product_name": h.product_name,
                    "is_rotating": h.is_rotating,
                    "is_guest_tap": h.is_guest_tap,
                }
                for h in d.drinks.highlights
            ],
        },
        "contact": {
            "items": [
                {
                    "link_type": c.link_type,
                    "value": c.value,
                    "display_label": c.display_label,
                }
                for c in d.contact.items
            ],
            "not_implemented": d.contact.not_implemented,
        },
        "authenticated_actions": {
            "can_save": d.actions.can_save,
            "is_saved": d.actions.is_saved,
            "save_requires_auth": d.actions.save_requires_auth,
        },
    }


class PublicVenueDetailDict(TypedDict, total=False):
    identity: dict[str, Any]
    location: dict[str, Any]
    hours: dict[str, Any]
    photos: dict[str, Any]
    features: dict[str, Any]
    specials: dict[str, Any]
    events: dict[str, Any]
    drinks: dict[str, Any]
    contact: dict[str, Any]
    authenticated_actions: dict[str, Any]
