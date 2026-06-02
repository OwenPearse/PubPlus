"""Result types for founder venue website enrichment."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class WebsiteEnrichmentCandidate:
    field_name: str
    raw_value: str
    normalized_value: str | None
    source_url: str
    confidence: int
    contact_safety_class: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WebsiteEnrichmentResult:
    lead_id: str
    fetched_urls: list[str] = field(default_factory=list)
    candidates: list[WebsiteEnrichmentCandidate] = field(default_factory=list)
    product_signals: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    fields_promoted: list[str] = field(default_factory=list)
    enrichment_status: str | None = None
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "fetched_urls": list(self.fetched_urls),
            "candidates": [c.to_dict() for c in self.candidates],
            "product_signals": list(self.product_signals),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "fields_promoted": list(self.fields_promoted),
            "enrichment_status": self.enrichment_status,
            "dry_run": self.dry_run,
        }
