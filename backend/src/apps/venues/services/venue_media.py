"""
Resolves public Supabase Storage URLs for venue media object keys.

Reads `venue_published_media` rows via `PublishedMediaRef` bundles. This module
stays the single place for URL building (no Django /media/ proxy by default).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from django.conf import settings

from common.storage import public_storage_object_url

from apps.venues.public_read.detail import PhotoItem
from apps.venues.services.published_venue_read import PublishedMediaRef


@dataclass(frozen=True)
class ResolvedMedia:
    hero_url: str | None
    photos: list[PhotoItem]


def _base_url() -> str:
    return str(settings.SUPABASE_URL)


def _bucket_for_ref(ref: PublishedMediaRef) -> str:
    if ref.storage_bucket:
        return ref.storage_bucket
    return getattr(
        settings,
        "SUPABASE_STORAGE_BUCKET_VENUE_MEDIA",
        getattr(settings, "SUPABASE_STORAGE_BUCKET_VENUES", "venues"),
    )


def resolve_hero_and_gallery(refs: list[PublishedMediaRef]) -> ResolvedMedia:
    if not refs:
        return ResolvedMedia(hero_url=None, photos=[])
    base = _base_url()
    items: list[PhotoItem] = []
    hero: str | None = None
    for r in sorted(refs, key=lambda x: (x.sort_order is not None, x.sort_order or 0)):
        bucket = _bucket_for_ref(r)
        u = public_storage_object_url(base, bucket, r.storage_object_path)
        is_hero = r.is_hero
        if is_hero and hero is None:
            hero = u
        items.append(
            PhotoItem(
                id=None,
                sort_order=r.sort_order,
                storage_object_path=r.storage_object_path,
                url=u,
                is_hero=r.is_hero,
            )
        )
    if hero is None and items:
        hero = items[0].url
        first = items[0]
        items[0] = replace(first, is_hero=True)
    return ResolvedMedia(hero_url=hero, photos=items)
