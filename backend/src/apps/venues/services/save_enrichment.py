"""
Optional authenticated save-state for public read payloads.

Reads from `saved_list` / `saved_list_membership` (consumer private state) only
when a verified auth subject is present. Does not implement write APIs.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from django.db import connection

from common.auth.context import AuthContext

from apps.venues.public_read.card import PublicVenueCard
from apps.venues.public_read.detail import AuthenticatedActionsBlock, PublicVenueDetail


def venue_id_in_any_user_list(*, venue_id: UUID | str, auth: AuthContext) -> bool:
    return map_venue_ids_in_any_user_list(venue_ids=[str(venue_id)], auth=auth).get(
        str(venue_id), False
    )


def map_venue_ids_in_any_user_list(
    *, venue_ids: list[str], auth: AuthContext
) -> dict[str, bool]:
    ids = [str(v) for v in venue_ids if v]
    if not ids:
        return {}
    with connection.cursor() as c:
        placeholders = ",".join(["%s"] * len(ids))
        c.execute(
            f"""
            SELECT DISTINCT m.venue_id::text
            FROM public.saved_list_membership m
            INNER JOIN public.saved_list s ON s.id = m.saved_list_id
            INNER JOIN public.consumer_account cac ON cac.id = s.consumer_account_id
            WHERE m.venue_id IN ({placeholders})
              AND cac.auth_user_id = %s::uuid
              AND s.is_archived = false
            """,
            [*ids, auth.subject],
        )
        saved_ids = {str(row[0]) for row in c.fetchall()}
    return {vid: vid in saved_ids for vid in ids}


def apply_save_to_card(
    card: PublicVenueCard, *, auth: AuthContext | None, venue_id: str
) -> PublicVenueCard:
    if auth is None:
        return replace(card, is_saved=None)
    return replace(
        card,
        is_saved=venue_id_in_any_user_list(venue_id=venue_id, auth=auth),
    )


def apply_save_to_cards(
    cards: list[PublicVenueCard], *, auth: AuthContext | None
) -> list[PublicVenueCard]:
    if auth is None:
        return [replace(card, is_saved=None) for card in cards]
    saved_map = map_venue_ids_in_any_user_list(
        venue_ids=[card.id for card in cards], auth=auth
    )
    return [replace(card, is_saved=saved_map.get(card.id, False)) for card in cards]


def build_actions_block(*, auth: AuthContext | None, is_saved: bool | None) -> AuthenticatedActionsBlock:
    if auth is None:
        return AuthenticatedActionsBlock(
            can_save=False, is_saved=None, save_requires_auth=True
        )
    return AuthenticatedActionsBlock(
        can_save=True,
        is_saved=is_saved if is_saved is not None else False,
        save_requires_auth=False,
    )


def apply_save_to_detail(detail: PublicVenueDetail, *, auth: AuthContext | None) -> PublicVenueDetail:
    subject = str(detail.identity.id)
    if auth is None:
        is_saved: bool | None = None
    else:
        is_saved = venue_id_in_any_user_list(venue_id=subject, auth=auth)
    return replace(
        detail,
        actions=build_actions_block(auth=auth, is_saved=is_saved),
    )
