from django.test import SimpleTestCase

from services.discovery import (
    DiscoveryFilterError,
    DiscoveryMode,
    DiscoveryMvpFilters,
    build_discovery_sql,
)


class TestFilters(SimpleTestCase):
    def test_viewport_incomplete_fails(self) -> None:
        f = DiscoveryMvpFilters(
            south=-34.0, north=None, west=150.0, east=152.0
        )
        with self.assertRaises(DiscoveryFilterError) as ctx:
            f.validate(DiscoveryMode.MAP)
        self.assertEqual(ctx.exception.code, "viewport_incomplete")

    def test_map_requires_viewport(self) -> None:
        f = DiscoveryMvpFilters()
        with self.assertRaises(DiscoveryFilterError) as ctx:
            f.validate(DiscoveryMode.MAP)
        self.assertEqual(ctx.exception.code, "map_needs_viewport")

    def test_list_accepts_q(self) -> None:
        f = DiscoveryMvpFilters(q="pizza")
        f.validate(DiscoveryMode.LIST)
        self.assertTrue(f.has_q())

    def test_combined_viewport_and_radius_fails(self) -> None:
        f = DiscoveryMvpFilters(
            south=-35.0,
            north=-33.0,
            west=150.0,
            east=152.0,
            lat=-34.0,
            lng=151.0,
            radius_m=500.0,
        )
        with self.assertRaises(DiscoveryFilterError) as ctx:
            f.validate(DiscoveryMode.MAP)
        self.assertEqual(ctx.exception.code, "location_with_viewport")

    def test_events_fails(self) -> None:
        f = DiscoveryMvpFilters(require_published_events=True)
        with self.assertRaises(DiscoveryFilterError) as ctx:
            f.validate(DiscoveryMode.LIST)
        self.assertEqual(ctx.exception.code, "events_unavailable")

    def test_list_accepts_suburb(self) -> None:
        f = DiscoveryMvpFilters(suburb="Sydney")
        f.validate(DiscoveryMode.LIST)

    def test_radius_only_rejects_location_incomplete(self) -> None:
        f = DiscoveryMvpFilters(radius_m=5000.0)
        with self.assertRaises(DiscoveryFilterError) as ctx:
            f.validate(DiscoveryMode.LIST)
        self.assertEqual(ctx.exception.code, "location_incomplete")

    def test_lat_lng_without_radius_rejects_location_incomplete(self) -> None:
        f = DiscoveryMvpFilters(lat=-37.81, lng=144.96)
        with self.assertRaises(DiscoveryFilterError) as ctx:
            f.validate(DiscoveryMode.LIST)
        self.assertEqual(ctx.exception.code, "location_incomplete")

    def test_list_sql_mentions_haversine_in_radius_mode(self) -> None:
        f = DiscoveryMvpFilters(lat=-34.0, lng=151.0, radius_m=4000.0)
        f.validate(DiscoveryMode.LIST)
        sql, params = build_discovery_sql(DiscoveryMode.LIST, f)
        self.assertIn("6371000", sql)
        self.assertGreater(len(params), 0)

    def test_map_sql_uses_bounds_only(self) -> None:
        f = DiscoveryMvpFilters(
            south=-35.0,
            north=-33.0,
            west=150.0,
            east=152.0,
        )
        f.validate(DiscoveryMode.MAP)
        sql, _p = build_discovery_sql(DiscoveryMode.MAP, f)
        self.assertIn("BETWEEN", sql)
        self.assertNotIn("6371000", sql)
