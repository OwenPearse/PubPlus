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
    with connection.cursor() as c:
        c.execute(
            """
            SELECT EXISTS (
              SELECT 1
              FROM public.saved_list_membership m
              INNER JOIN public.saved_list s ON s.id = m.saved_list_id
              INNER JOIN public.consumer_account cac ON cac.id = s.consumer_account_id
              WHERE m.venue_id = %s
                AND cac.auth_user_id = %s::uuid
                AND s.is_archived = false
            ) AS in_list
            """,
            [str(venue_id), auth.subject],
        )
        row = c.fetchone()
        if not row:
            return False
        return bool(row[0])


def apply_save_to_card(
    card: PublicVenueCard, *, auth: AuthContext | None, venue_id: str
) -> PublicVenueCard:
    if auth is None:
        return replace(card, is_saved=None)
    return replace(
        card,
        is_saved=venue_id_in_any_user_list(venue_id=venue_id, auth=auth),
    )


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
