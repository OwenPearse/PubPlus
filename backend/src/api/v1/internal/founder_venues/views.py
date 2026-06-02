from __future__ import annotations

import json
from dataclasses import asdict

from datetime import datetime, timezone

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.discovery.http import error_response
from apps.founder_venues.services.enrichment_service import (
    enrich_founder_venue_lead_from_website,
)
from apps.founder_venues.services.export_service import (
    export_founder_venue_leads_csv,
    parse_export_filters,
)
from apps.founder_venues.services.founder_fit_db import (
    get_top_founder_venue_leads,
    recompute_founder_fit_scores,
)
from apps.founder_venues.services.import_service import (
    VALID_SOURCE_TYPES,
    import_founder_venue_leads_csv,
)
from apps.founder_venues.services.lead_mutations import (
    mark_lead_do_not_contact,
    patch_founder_venue_lead,
)
from apps.founder_venues.services.lead_queries import (
    get_founder_venue_lead_detail,
    get_founder_venue_workspace_summary,
    list_founder_venue_leads,
    parse_list_filters,
)
from apps.founder_venues.services.lead_validation import (
    MAX_CSV_BYTES,
    MAX_RECOMPUTE_LIMIT,
    LeadNotFoundError,
    LeadValidationError,
)
from apps.internal_tools.services.moderation_write_service import (
    InternalOperatorResolutionError,
    ModerationWriteValidationError,
    resolve_admin_account_for_internal_operator,
)
from common.auth.guards import require_internal_admin_auth
from common.auth.request_context import get_auth_context


def _parse_json_body(request) -> dict:
    try:
        data = (
            json.loads(request.body)
            if isinstance(request.body, (bytes, bytearray)) and request.body
            else {}
        )
    except json.JSONDecodeError:
        raise LeadValidationError("Request body must be valid JSON.")
    if not isinstance(data, dict):
        raise LeadValidationError("Request body must be a JSON object.")
    return data


def _admin_account_id_optional(request) -> str | None:
    auth = get_auth_context(request)
    if auth is None:
        return None
    try:
        operator = resolve_admin_account_for_internal_operator(auth)
        return operator.admin_account_id
    except (InternalOperatorResolutionError, ModerationWriteValidationError):
        return None


def _import_result_payload(result) -> dict:
    return {
        "rows_processed": result.rows_processed,
        "leads_created": result.leads_created,
        "leads_updated": result.leads_updated,
        "duplicates_skipped": result.duplicates_skipped,
        "duplicates_needing_review": [asdict(d) for d in result.duplicates_needing_review],
        "invalid_rows": [asdict(r) for r in result.invalid_rows],
        "errors": result.errors,
        "dry_run": result.dry_run,
    }


def _recompute_result_payload(result) -> dict:
    return {
        "processed": result.processed,
        "updated": result.updated,
        "skipped": result.skipped,
        "dry_run": result.dry_run,
        "top_scores_preview": result.top_scores_preview,
        "errors": result.errors,
    }


@require_http_methods(["GET", "HEAD"])
@require_internal_admin_auth
def list_leads(request):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    try:
        filters = parse_list_filters(
            {k: request.GET.get(k, "") for k in request.GET.keys()}
        )
        payload = list_founder_venue_leads(filters)
    except LeadValidationError as exc:
        return error_response(
            code="validation_error",
            message=exc.message,
            status=400,
        )
    return JsonResponse(payload)


@require_http_methods(["GET", "HEAD"])
@require_internal_admin_auth
def workspace_summary(request):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    return JsonResponse(get_founder_venue_workspace_summary())


@require_http_methods(["GET", "PATCH", "HEAD"])
@require_internal_admin_auth
def lead_detail_or_patch(request, lead_id: str):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    if request.method == "GET":
        try:
            payload = get_founder_venue_lead_detail(lead_id)
        except LeadValidationError as exc:
            return error_response(
                code="validation_error", message=exc.message, status=400
            )
        except LeadNotFoundError:
            return error_response(
                code="not_found", message="Founder venue lead not found.", status=404
            )
        return JsonResponse(payload)

    try:
        body = _parse_json_body(request)
        payload = patch_founder_venue_lead(
            lead_id,
            body,
            admin_account_id=_admin_account_id_optional(request),
        )
    except LeadValidationError as exc:
        return error_response(
            code="validation_error", message=exc.message, status=400
        )
    except LeadNotFoundError:
        return error_response(
            code="not_found", message="Founder venue lead not found.", status=404
        )
    return JsonResponse(payload)


@require_http_methods(["POST", "HEAD"])
@require_internal_admin_auth
def mark_do_not_contact(request, lead_id: str):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    try:
        body = _parse_json_body(request)
        reason = body.get("reason")
        if reason is not None and not isinstance(reason, str):
            raise LeadValidationError("reason must be a string.")
        payload = mark_lead_do_not_contact(
            lead_id,
            reason=reason,
            admin_account_id=_admin_account_id_optional(request),
        )
    except LeadValidationError as exc:
        return error_response(
            code="validation_error", message=exc.message, status=400
        )
    except LeadNotFoundError:
        return error_response(
            code="not_found", message="Founder venue lead not found.", status=404
        )
    return JsonResponse(payload)


@require_http_methods(["POST", "HEAD"])
@require_internal_admin_auth
def import_leads(request):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    try:
        body = _parse_json_body(request)
        csv_text = body.get("csv_text")
        if not isinstance(csv_text, str) or not csv_text.strip():
            raise LeadValidationError("csv_text is required.")

        encoded = csv_text.encode("utf-8")
        if len(encoded) > MAX_CSV_BYTES:
            raise LeadValidationError(
                f"csv_text exceeds maximum size of {MAX_CSV_BYTES} bytes."
            )

        source_type = body.get("source_type", "csv_import")
        if source_type not in VALID_SOURCE_TYPES:
            raise LeadValidationError(f"Invalid source_type: {source_type}")

        source_name = body.get("source_name")
        source_url = body.get("source_url")
        if source_name is not None and not isinstance(source_name, str):
            raise LeadValidationError("source_name must be a string.")
        if source_url is not None and not isinstance(source_url, str):
            raise LeadValidationError("source_url must be a string.")

        update_existing = bool(body.get("update_existing", False))
        dry_run = bool(body.get("dry_run", False))

        result = import_founder_venue_leads_csv(
            csv_text,
            source_type=source_type,
            source_name=source_name,
            source_url=source_url,
            imported_by_admin_account_id=_admin_account_id_optional(request),
            update_existing=update_existing,
            dry_run=dry_run,
        )
        status = 200 if not result.errors else 400
        return JsonResponse(_import_result_payload(result), status=status)
    except LeadValidationError as exc:
        return error_response(
            code="validation_error", message=exc.message, status=400
        )


@require_http_methods(["POST", "HEAD"])
@require_internal_admin_auth
def recompute_scores(request):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    try:
        body = _parse_json_body(request)
        lead_ids = body.get("lead_ids")
        state = body.get("state")
        limit = body.get("limit")
        dry_run = bool(body.get("dry_run", False))

        parsed_lead_ids: list[str] | None = None
        if lead_ids is not None:
            if not isinstance(lead_ids, list):
                raise LeadValidationError("lead_ids must be an array of UUID strings.")
            parsed_lead_ids = [str(x) for x in lead_ids]

        parsed_state = None
        if state is not None:
            if not isinstance(state, str) or not state.strip():
                raise LeadValidationError("state must be a non-empty string.")
            parsed_state = state.strip().upper()

        parsed_limit = None
        if limit is not None:
            if not isinstance(limit, int):
                raise LeadValidationError("limit must be an integer.")
            if limit < 1 or limit > MAX_RECOMPUTE_LIMIT:
                raise LeadValidationError(
                    f"limit must be between 1 and {MAX_RECOMPUTE_LIMIT}."
                )
            parsed_limit = limit

        if not parsed_lead_ids and not parsed_state and parsed_limit is None:
            raise LeadValidationError(
                "Provide at least one of lead_ids, state, or limit to constrain recompute."
            )

        result = recompute_founder_fit_scores(
            lead_ids=parsed_lead_ids,
            state=parsed_state,
            limit=parsed_limit,
            dry_run=dry_run,
        )
        return JsonResponse(_recompute_result_payload(result))
    except LeadValidationError as exc:
        return error_response(
            code="validation_error", message=exc.message, status=400
        )


@require_http_methods(["GET", "HEAD"])
@require_internal_admin_auth
def top_leads(request):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    try:
        state = (request.GET.get("state") or "").strip().upper() or None
        suburb = (request.GET.get("suburb") or "").strip() or None
        limit_raw = request.GET.get("limit") or "100"
        try:
            limit = int(limit_raw)
        except (TypeError, ValueError) as exc:
            raise LeadValidationError("limit must be an integer.") from exc
        if limit < 1 or limit > 200:
            raise LeadValidationError("limit must be between 1 and 200.")

        include_dnc = (request.GET.get("include_do_not_contact") or "").lower() in (
            "true",
            "1",
            "yes",
        )
        items = get_top_founder_venue_leads(
            state=state,
            suburb=suburb,
            limit=limit,
            include_do_not_contact=include_dnc,
        )
        return JsonResponse({"items": items})
    except LeadValidationError as exc:
        return error_response(
            code="validation_error", message=exc.message, status=400
        )


@require_http_methods(["POST", "HEAD"])
@require_internal_admin_auth
def enrich_lead_website(request, lead_id: str):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    try:
        body = _parse_json_body(request)
        dry_run = bool(body.get("dry_run", False))
        result = enrich_founder_venue_lead_from_website(
            lead_id,
            requested_by_admin_account_id=_admin_account_id_optional(request),
            dry_run=dry_run,
        )
        status = 200
        if result.errors and not result.fetched_urls:
            status = 400
        return JsonResponse(result.to_dict(), status=status)
    except LeadValidationError as exc:
        return error_response(
            code="validation_error", message=exc.message, status=400
        )
    except LeadNotFoundError:
        return error_response(
            code="not_found", message="Founder venue lead not found.", status=404
        )


@require_http_methods(["GET", "HEAD"])
@require_internal_admin_auth
def export_leads_csv(request):
    if request.method == "HEAD":
        return HttpResponse(status=200, content_type="text/csv")
    try:
        filters = parse_export_filters(
            {k: request.GET.get(k, "") for k in request.GET.keys()}
        )
        result = export_founder_venue_leads_csv(
            state=filters.state,
            suburb=filters.suburb,
            postcode=filters.postcode,
            search=filters.search,
            enrichment_status=filters.enrichment_status,
            outreach_status=filters.outreach_status,
            contact_permission_status=filters.contact_permission_status,
            score_min=filters.score_min,
            confidence_min=filters.confidence_min,
            missing_email=filters.missing_email,
            missing_phone=filters.missing_phone,
            missing_website=filters.missing_website,
            needs_review=filters.needs_review,
            include_do_not_contact=filters.include_do_not_contact,
            include_suppressed=filters.include_suppressed,
            include_unsafe_emails=filters.include_unsafe_emails,
            include_raw_notes=filters.include_raw_notes,
            limit=filters.limit,
            offset=filters.offset,
            exported_by_admin_account_id=_admin_account_id_optional(request),
        )
    except LeadValidationError as exc:
        return error_response(
            code="validation_error",
            message=exc.message,
            status=400,
        )

    date_stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename = f"pubplus_founder_venues_{date_stamp}.csv"
    response = HttpResponse(result.csv_text, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
