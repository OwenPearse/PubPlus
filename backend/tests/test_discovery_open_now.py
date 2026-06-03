from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from apps.venues.services.published_venue_read import (
    PublishedCoreRow,
    PublishedExceptionHoursRow,
    PublishedRegularHoursRow,
    PublishedVenueReadBundle,
)
from services.discovery import compute_open_now


def _core(country: str) -> PublishedCoreRow:
    return PublishedCoreRow(
        venue_id="0" * 8 + "-0000-4000-8000-000000000000",
        display_name="T",
        slug="t",
        operational_status="open",
        suburb_name="X",
        address_line_1=None,
        address_line_2=None,
        postal_code=None,
        country_code=country,
        latitude=-35.0,
        longitude=149.0,
    )


class TestOpenNow(SimpleTestCase):
    def _utc(self, d: int, h: int) -> datetime:
        return datetime(2024, 1, d, h, 0, 0, tzinfo=timezone.utc)

    def test_regular_utc_venue_lunch(self) -> None:
        b = PublishedVenueReadBundle(
            core=_core("NZ"),
            descriptive=None,
            hours_regular=[
                PublishedRegularHoursRow(1, "12:00", "22:00", False, 0),
            ],
        )
        r = compute_open_now(
            b,
            hours_uncertainty_level="resolved_confident",
            at_utc=self._utc(1, 14),
        )
        self.assertTrue(r.public_open_now)
        self.assertFalse(r.public_open_now_uncomputed)

    def test_late_night_utc_cross_midnight_sunday_night(self) -> None:
        b = PublishedVenueReadBundle(
            core=_core("NZ"),
            descriptive=None,
            hours_regular=[
                PublishedRegularHoursRow(0, "20:00", "01:00", True, 0),
            ],
        )
        r = compute_open_now(
            b,
            hours_uncertainty_level="resolved_confident",
            at_utc=datetime(2024, 1, 1, 0, 30, 0, tzinfo=ZoneInfo("UTC")),
        )
        self.assertTrue(r.public_open_now)

    def test_exception_closed_all_day(self) -> None:
        b = PublishedVenueReadBundle(
            core=_core("NZ"),
            descriptive=None,
            hours_regular=[
                PublishedRegularHoursRow(1, "12:00", "22:00", False, 0),
            ],
            hours_exceptions=[
                PublishedExceptionHoursRow(
                    "2024-01-01",
                    "2024-01-01",
                    "closed_all_day",
                    None,
                    None,
                    False,
                    None,
                )
            ],
        )
        r = compute_open_now(
            b, hours_uncertainty_level=None, at_utc=self._utc(1, 15)
        )
        self.assertIs(r.public_open_now, False)
        self.assertFalse(r.public_open_now_uncomputed)

    def test_exception_modified_overrides(self) -> None:
        b = PublishedVenueReadBundle(
            core=_core("NZ"),
            descriptive=None,
            hours_regular=[
                PublishedRegularHoursRow(1, "10:00", "18:00", False, 0),
            ],
            hours_exceptions=[
                PublishedExceptionHoursRow(
                    "2024-01-15",
                    "2024-01-15",
                    "modified_hours",
                    "19:00",
                    "22:00",
                    False,
                    "late",
                )
            ],
        )
        r = compute_open_now(
            b,
            hours_uncertainty_level="resolved_confident",
            at_utc=datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc),
        )
        self.assertTrue(r.public_open_now)

    def test_partial_does_not_assert_open(self) -> None:
        b = PublishedVenueReadBundle(
            core=_core("NZ"),
            descriptive=None,
            hours_regular=[
                PublishedRegularHoursRow(1, "12:00", "22:00", False, 0),
            ],
        )
        r = compute_open_now(
            b, hours_uncertainty_level="partial", at_utc=self._utc(1, 15)
        )
        self.assertIsNone(r.public_open_now)
        self.assertTrue(r.public_open_now_uncomputed)

    def test_utc_venue_tuesday_slot(self) -> None:
        b = PublishedVenueReadBundle(
            core=_core("US"),
            descriptive=None,
            hours_regular=[
                PublishedRegularHoursRow(2, "10:00", "18:00", False, 0),
            ],
        )
        r = compute_open_now(
            b,
            hours_uncertainty_level="resolved_confident",
            at_utc=datetime(2024, 1, 2, 12, 0, 0, tzinfo=ZoneInfo("UTC")),
        )
        self.assertTrue(r.public_open_now)
        self.assertFalse(r.public_open_now_uncomputed)
