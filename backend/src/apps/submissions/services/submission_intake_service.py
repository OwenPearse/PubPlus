"""
Consumer submission intake: workflow/proposal rows only (no published-truth mutation).
"""

from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from django.db import DatabaseError, connection, transaction

from common.auth.context import AuthContext
from common.consumer_account import get_or_create_consumer_account_id

MAX_NOTE_LEN = 2000

_DISCOVERY_ELIGIBILITY = frozenset(
    {"unknown", "eligible", "limited", "hidden", "retired"}
)
_OPERATIONAL_STATUS = frozenset(
    {"unknown", "open", "closed", "temporarily_closed", "seasonal"}
)
_UNCERTAINTY = frozenset(
    {"unknown", "partial", "weak_stale", "disputed", "resolved_confident"}
)

_API_DOMAIN_TO_TARGET = {
    "profile": "profile",
    "location": "geo",
    "attributes": "attributes",
    "hours": "hours",
}


def _bad_uuid(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    try:
        UUID(value)
    except (ValueError, TypeError):
        return True
    return False


def _venue_exists(venue_id: str) -> bool:
    with connection.cursor() as c:
        c.execute("SELECT 1 FROM public.venue WHERE id = %s::uuid", [venue_id])
        return c.fetchone() is not None


def _locality_and_region_ok(
    locality_id: str | None, region_id: str | None
) -> tuple[bool, str | None, str | None]:
    """
    Returns (ok, error_field, error_message). error_field is a request key
    (locality_id or geographic_region_id) when not ok.
    """
    if locality_id is None and region_id is None:
        return True, None, None
    if locality_id is not None:
        with connection.cursor() as c:
            c.execute(
                """
                SELECT geographic_region_id
                FROM public.locality
                WHERE id = %s::uuid
                """,
                [locality_id],
            )
            row = c.fetchone()
            if not row:
                return (
                    False,
                    "locality_id",
                    "locality_id does not reference an existing locality.",
                )
            if region_id is not None and str(row[0]) != region_id:
                return (
                    False,
                    "geographic_region_id",
                    "geographic_region_id does not match the locality's region.",
                )
        return True, None, None
    with connection.cursor() as c:
        c.execute(
            "SELECT 1 FROM public.geographic_region WHERE id = %s::uuid",
            [region_id],
        )
        if not c.fetchone():
            return (
                False,
                "geographic_region_id",
                "geographic_region_id does not reference an existing region.",
            )
    return True, None, None


def _attribute_fk_ok(
    attribute_definition_id: str, allowed_value_id: str | None
) -> bool:
    with connection.cursor() as c:
        c.execute(
            "SELECT 1 FROM public.venue_attribute_definition WHERE id = %s::uuid",
            [attribute_definition_id],
        )
        if not c.fetchone():
            return False
        if allowed_value_id is None:
            return True
        c.execute(
            """
            SELECT 1 FROM public.venue_attribute_allowed_value
            WHERE id = %s::uuid AND attribute_definition_id = %s::uuid
            """,
            [allowed_value_id, attribute_definition_id],
        )
        return c.fetchone() is not None


def _validate_note(note: Any) -> tuple[str | None, str | None]:
    if note is None:
        return None, None
    if not isinstance(note, str):
        return None, "note must be a string."
    if len(note) > MAX_NOTE_LEN:
        return None, f"note must be at most {MAX_NOTE_LEN} characters."
    return note, None


def _validate_profile_values(
    pv: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(pv, dict):
        return None, "proposed_values must be an object for domain profile."
    out: dict[str, Any] = {}
    for k, src in (
        ("display_name", "display_name"),
        ("slug", "slug"),
        ("short_description", "short_description"),
        ("long_description", "long_description"),
    ):
        if src in pv:
            v = pv[src]
            if v is not None and not isinstance(v, str):
                return None, f"{src} must be a string or null."
            if v is not None:
                out[k] = v
    for key, allowed, err in (
        (
            "discovery_eligibility_status",
            _DISCOVERY_ELIGIBILITY,
            "discovery_eligibility_status has an invalid value.",
        ),
        (
            "operational_status",
            _OPERATIONAL_STATUS,
            "operational_status has an invalid value.",
        ),
    ):
        if key in pv and pv[key] is not None:
            if not isinstance(pv[key], str) or pv[key] not in allowed:
                return None, err
            out[key] = pv[key]
    if not out:
        return None, "proposed_values must include at least one profile field."
    return out, None


def _validate_location_values(
    pv: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(pv, dict):
        return None, "proposed_values must be an object for domain location."
    out: dict[str, Any] = {}
    if "locality_id" in pv and pv["locality_id"] is not None:
        if _bad_uuid(pv["locality_id"]):
            return None, "locality_id must be a valid UUID string."
        out["locality_id"] = str(pv["locality_id"])
    for key, col in (
        ("address_line_1", "address_line_1"),
        ("address_line_2", "address_line_2"),
        ("postcode", "postal_code"),
    ):
        if key in pv and pv[key] is not None:
            v = pv[key]
            if not isinstance(v, str):
                return None, f"{key} must be a string or null."
            out[col] = v
    if "country_code" in pv and pv["country_code"] is not None:
        cc = pv["country_code"]
        if not isinstance(cc, str) or not re.fullmatch(r"[A-Za-z]{2}", cc):
            return None, "country_code must be a two-letter ISO 3166-1 alpha-2 code."
        out["country_code"] = cc.upper()
    for key in ("latitude", "longitude"):
        if key in pv and pv[key] is not None:
            v = pv[key]
            if not isinstance(v, (int, float)):
                return None, f"{key} must be a number or null."
            out[key] = float(v)
    if not out:
        return None, "proposed_values must include at least one location field."
    return out, None


def _validate_attributes_values(
    pv: Any,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    if not isinstance(pv, dict):
        return None, "proposed_values must be an object for domain attributes."
    items = pv.get("items")
    if not isinstance(items, list) or len(items) < 1:
        return None, "proposed_values.items must be a non-empty array."
    rows: list[dict[str, Any]] = []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            return None, f"proposed_values.items[{i}] must be an object."
        if "attribute_definition_id" not in it or _bad_uuid(it["attribute_definition_id"]):
            return None, f"proposed_values.items[{i}].attribute_definition_id is required."
        aid = str(it["attribute_definition_id"])
        av = it.get("allowed_value_id")
        if av is not None and _bad_uuid(av):
            return None, f"proposed_values.items[{i}].allowed_value_id is invalid."
        vb = it.get("value_boolean")
        vn = it.get("value_numeric")
        n_nonnull = sum(
            1
            for x in (av, vb, vn)
            if x is not None
        )
        if n_nonnull != 1:
            return None, (
                f"proposed_values.items[{i}] must set exactly one of "
                "allowed_value_id, value_boolean, or value_numeric."
            )
        if vb is not None and not isinstance(vb, bool):
            return None, f"proposed_values.items[{i}].value_boolean must be a boolean."
        if vn is not None and not isinstance(vn, (int, float)):
            return None, f"proposed_values.items[{i}].value_numeric must be a number."
        if not _attribute_fk_ok(aid, str(av) if av is not None else None):
            return None, (
                f"proposed_values.items[{i}] has an invalid "
                "attribute_definition_id or allowed_value_id for that definition."
            )
        row: dict[str, Any] = {
            "attribute_definition_id": aid,
            "allowed_value_id": str(av) if av is not None else None,
            "value_boolean": vb,
            "value_numeric": float(vn) if isinstance(vn, (int, float)) else None,
        }
        rows.append(row)
    return rows, None


def _validate_hours_values(
    pv: Any, note: str | None
) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(pv, dict):
        return None, "proposed_values must be an object for domain hours."
    reg = pv.get("regular_hours_json", [])
    exc = pv.get("exceptions_json", [])
    if reg is None:
        reg = []
    if exc is None:
        exc = []
    if not isinstance(reg, list) or not isinstance(exc, list):
        return None, "regular_hours_json and exceptions_json must be arrays."
    unc = pv.get("uncertainty_level", pv.get("proposed_uncertainty_level"))
    if unc is not None and (
        not isinstance(unc, str) or unc not in _UNCERTAINTY
    ):
        return None, "uncertainty_level (or proposed_uncertainty_level) is invalid."
    has_content = bool(reg) or bool(exc) or unc is not None or bool(
        (note or "").strip()
    )
    if not has_content:
        return None, "proposed_values for hours must include at least one of: regular hours, exceptions, uncertainty level, or a contextual note."
    return {
        "regular_hours_json": reg,
        "exceptions_json": exc,
        "uncertainty": unc,
    }, None


@transaction.atomic
def submit_consumer_correction(
    auth: AuthContext, body: dict[str, Any]
) -> tuple[dict | None, str, dict[str, list[str]] | None]:
    try:
        consumer_id = get_or_create_consumer_account_id(auth)
    except (ValueError, RuntimeError):
        return None, "invalid_auth_subject", None

    vid = body.get("venue_id")
    if vid is None or _bad_uuid(vid):
        return None, "validation_error", {
            "venue_id": ["A valid venue_id (UUID) is required."]
        }
    venue_id = str(vid)
    if not _venue_exists(venue_id):
        return None, "venue_not_found", None

    domain = body.get("domain")
    if not isinstance(domain, str) or domain not in _API_DOMAIN_TO_TARGET:
        return None, "validation_error", {
            "domain": [
                "domain must be one of: profile, location, attributes, hours; other domains are not supported yet."
            ]
        }

    note, nerr = _validate_note(body.get("note"))
    if nerr:
        return None, "validation_error", {"note": [nerr]}

    pv = body.get("proposed_values")
    if pv is None:
        return None, "validation_error", {
            "proposed_values": ["This field is required."]
        }

    add_profile_for_note = False
    if domain == "profile":
        pfields, err = _validate_profile_values(pv)
        if err or not pfields:
            return None, "validation_error", {
                "proposed_values": [err or "Invalid profile proposed_values."]
            }
        if note:
            ld = pfields.get("long_description", "")
            pfields["long_description"] = (
                f"{ld}\n{note}" if ld else note
            )
    elif domain == "location":
        pfields, err = _validate_location_values(pv)
        if err or not pfields:
            return None, "validation_error", {
                "proposed_values": [err or "Invalid location proposed_values."]
            }
        if note:
            a2 = pfields.get("address_line_2", "")
            pfields["address_line_2"] = (
                f"{a2}\n(Consumer note: {note})" if a2 else f"Consumer note: {note}"
            )
    elif domain == "attributes":
        items, err = _validate_attributes_values(pv)
        if err or not items:
            return None, "validation_error", {
                "proposed_values": [err or "Invalid attributes proposed_values."]
            }
        pfields = items
        if note:
            add_profile_for_note = True
    else:
        hpack, err = _validate_hours_values(pv, note)
        if err or not hpack:
            return None, "validation_error", {
                "proposed_values": [err or "Invalid hours proposed_values."]
            }
        pfields = hpack

    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_change_proposal (
                venue_id,
                actor_type,
                actor_consumer_account_id,
                channel,
                proposal_kind,
                submitted_at
            ) VALUES (
                %s::uuid, 'consumer', %s::uuid, 'app_consumer', 'field_family', now()
            ) RETURNING id
            """,
            [venue_id, str(consumer_id)],
        )
        proposal_id = c.fetchone()[0]

    tf = _API_DOMAIN_TO_TARGET[domain]
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_proposal_target (venue_change_proposal_id, target_family)
            VALUES (%s::uuid, %s)
            """,
            [str(proposal_id), tf],
        )
        if add_profile_for_note:
            c.execute(
                """
                INSERT INTO public.venue_proposal_target (venue_change_proposal_id, target_family)
                VALUES (%s::uuid, 'profile')
                """,
                [str(proposal_id)],
            )

    if domain == "profile":
        f = pfields
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO public.venue_proposal_staging_profile (
                    venue_change_proposal_id, venue_id,
                    proposed_display_name, proposed_slug,
                    proposed_discovery_eligibility_status, proposed_operational_status,
                    proposed_short_description, proposed_long_description
                ) VALUES (
                    %s::uuid, %s::uuid,
                    %s, %s, %s, %s, %s, %s
                )
                """,
                [
                    str(proposal_id),
                    venue_id,
                    f.get("display_name"),
                    f.get("slug"),
                    f.get("discovery_eligibility_status"),
                    f.get("operational_status"),
                    f.get("short_description"),
                    f.get("long_description"),
                ],
            )
    elif domain == "location":
        f = pfields
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO public.venue_proposal_staging_location (
                    venue_change_proposal_id, venue_id,
                    proposed_locality_id, proposed_address_line_1, proposed_address_line_2,
                    proposed_postal_code, proposed_country_code, proposed_latitude, proposed_longitude
                ) VALUES (
                    %s::uuid, %s::uuid,
                    %s::uuid, %s, %s, %s, %s, %s, %s
                )
                """,
                [
                    str(proposal_id),
                    venue_id,
                    f.get("locality_id"),
                    f.get("address_line_1"),
                    f.get("address_line_2"),
                    f.get("postal_code"),
                    f.get("country_code"),
                    f.get("latitude"),
                    f.get("longitude"),
                ],
            )
    elif domain == "attributes":
        for row in pfields:  # type: ignore[assignment]
            with connection.cursor() as c:
                c.execute(
                    """
                    INSERT INTO public.venue_proposal_staging_attribute (
                        venue_change_proposal_id, venue_id,
                        attribute_definition_id, allowed_value_id,
                        value_boolean, value_numeric
                    ) VALUES (
                        %s::uuid, %s::uuid, %s::uuid, %s, %s, %s
                    )
                    """,
                    [
                        str(proposal_id),
                        venue_id,
                        row["attribute_definition_id"],
                        row["allowed_value_id"],
                        row["value_boolean"],
                        row["value_numeric"],
                    ],
                )
        if add_profile_for_note and note:
            with connection.cursor() as c:
                c.execute(
                    """
                    INSERT INTO public.venue_proposal_staging_profile (
                        venue_change_proposal_id, venue_id, proposed_long_description
                    ) VALUES (%s::uuid, %s::uuid, %s)
                    """,
                    [str(proposal_id), venue_id, note],
                )
    else:
        f = pfields
        hnote = (note or "").strip() or None
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO public.venue_proposal_staging_hours (
                    venue_change_proposal_id, venue_id,
                    proposed_uncertainty_level,
                    regular_hours_json, exceptions_json, notes
                ) VALUES (
                    %s::uuid, %s::uuid, %s, %s::jsonb, %s::jsonb, %s
                )
                """,
                [
                    str(proposal_id),
                    venue_id,
                    f.get("uncertainty"),
                    json.dumps(f["regular_hours_json"]),
                    json.dumps(f["exceptions_json"]),
                    hnote,
                ],
            )

    _try_insert_submission_extension(str(proposal_id), str(consumer_id))

    return {
        "status": "received",
        "message": "Your submission has been received and will be reviewed.",
    }, "ok", None


def _try_insert_submission_extension(
    proposal_id: str, consumer_account_id: str
) -> None:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'consumer_submission_extension'
            """
        )
        if not c.fetchone():
            return
    try:
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO public.consumer_submission_extension (
                    venue_change_proposal_id, consumer_account_id, app_surface
                ) VALUES (%s::uuid, %s::uuid, %s)
                ON CONFLICT (venue_change_proposal_id) DO NOTHING
                """,
                [proposal_id, consumer_account_id, "app_consumer"],
            )
    except DatabaseError:
        return


@transaction.atomic
def submit_new_venue_suggestion(
    auth: AuthContext, body: dict[str, Any]
) -> tuple[dict | None, str, dict[str, list[str]] | None]:
    try:
        consumer_id = get_or_create_consumer_account_id(auth)
    except (ValueError, RuntimeError):
        return None, "invalid_auth_subject", None

    name = body.get("name")
    address_line_1 = body.get("address_line_1")
    if not isinstance(name, str) or not name.strip():
        return None, "validation_error", {"name": ["This field is required."]}
    if not isinstance(address_line_1, str) or not address_line_1.strip():
        return None, "validation_error", {
            "address_line_1": ["This field is required."]
        }

    note, nerr = _validate_note(body.get("note"))
    if nerr:
        return None, "validation_error", {"note": [nerr]}

    line_2 = body.get("address_line_2")
    if line_2 is not None and not isinstance(line_2, str):
        return None, "validation_error", {
            "address_line_2": ["Must be a string or null."]
        }
    loc_id = body.get("locality_id")
    reg_id = body.get("geographic_region_id")
    if loc_id is not None and _bad_uuid(loc_id):
        return None, "validation_error", {
            "locality_id": ["Must be a valid UUID string or null."]
        }
    if reg_id is not None and _bad_uuid(reg_id):
        return None, "validation_error", {
            "geographic_region_id": ["Must be a valid UUID string or null."]
        }
    if loc_id is not None:
        loc_id = str(loc_id)
    if reg_id is not None:
        reg_id = str(reg_id)

    ok, geo_field, geomsg = _locality_and_region_ok(
        loc_id, reg_id if reg_id is not None else None
    )
    if not ok and geomsg and geo_field:
        return None, "validation_error", {geo_field: [geomsg]}

    pc = body.get("postcode")
    if pc is not None and not isinstance(pc, str):
        return None, "validation_error", {"postcode": ["Must be a string or null."]}
    lat = body.get("latitude")
    lng = body.get("longitude")
    for coord, k in ((lat, "latitude"), (lng, "longitude")):
        if coord is not None and not isinstance(coord, (int, float)):
            return None, "validation_error", {k: ["Must be a number or null."]}
    ccode = body.get("country_code")
    if ccode is not None:
        if not isinstance(ccode, str) or not re.fullmatch(
            r"[A-Za-z]{2}", ccode
        ):
            return None, "validation_error", {
                "country_code": [
                    "If provided, must be a two-letter ISO 3166-1 alpha-2 code."
                ]
            }
        ccode = ccode.upper()

    with connection.cursor() as c:
        c.execute("INSERT INTO public.venue DEFAULT VALUES RETURNING id")
        new_venue_id = c.fetchone()[0]
        c.execute(
            """
            INSERT INTO public.venue_change_proposal (
                venue_id, actor_type, actor_consumer_account_id, channel, proposal_kind, submitted_at
            ) VALUES (
                %s::uuid, 'consumer', %s::uuid, 'app_consumer', 'whole_record', now()
            ) RETURNING id
            """,
            [str(new_venue_id), str(consumer_id)],
        )
        proposal_id = c.fetchone()[0]
        c.execute(
            """
            INSERT INTO public.venue_proposal_target (venue_change_proposal_id, target_family)
            VALUES
              (%s::uuid, 'profile'),
              (%s::uuid, 'geo')
            """,
            [str(proposal_id), str(proposal_id)],
        )
        c.execute(
            """
            INSERT INTO public.venue_proposal_staging_profile (
                venue_change_proposal_id, venue_id, proposed_display_name, proposed_operational_status,
                proposed_long_description
            ) VALUES (
                %s::uuid, %s::uuid, %s, 'open', %s
            )
            """,
            [
                str(proposal_id),
                str(new_venue_id),
                name.strip(),
                (note or "").strip() or None,
            ],
        )
        c.execute(
            """
            INSERT INTO public.venue_proposal_staging_location (
                venue_change_proposal_id, venue_id, proposed_locality_id,
                proposed_address_line_1, proposed_address_line_2, proposed_postal_code,
                proposed_country_code, proposed_latitude, proposed_longitude
            ) VALUES (
                %s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s
            )
            """,
            [
                str(proposal_id),
                str(new_venue_id),
                loc_id,
                address_line_1.strip(),
                (line_2 or "").strip() or None,
                (pc or "").strip() or None,
                ccode,
                float(lat) if lat is not None else None,
                float(lng) if lng is not None else None,
            ],
        )

    _try_insert_submission_extension(str(proposal_id), str(consumer_id))
    return {
        "status": "received",
        "message": "Your submission has been received and will be reviewed.",
    }, "ok", None
