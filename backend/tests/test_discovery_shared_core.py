from django.test import SimpleTestCase

from services.discovery import DiscoveryMode, DiscoveryMvpFilters, build_discovery_sql


class TestSharedCore(SimpleTestCase):
    def test_list_and_map_share_published_from_spine(self) -> None:
        f1 = DiscoveryMvpFilters(
            lat=-34.0, lng=151.0, radius_m=1000.0
        )
        f1.validate(DiscoveryMode.LIST)
        a, _ = build_discovery_sql(DiscoveryMode.LIST, f1)
        f2 = DiscoveryMvpFilters(
            south=-35.0, north=-33.0, west=150.0, east=152.0
        )
        f2.validate(DiscoveryMode.MAP)
        b, _ = build_discovery_sql(DiscoveryMode.MAP, f2)
        for sql in (a, b):
            self.assertIn("venue_published_profile", sql)
            self.assertIn("venue_published_map_point", sql)
            self.assertIn("venue_published_location", sql)
            self.assertIn("locality", sql)

    def test_haversine_backend_distance_in_list(self) -> None:
        f1 = DiscoveryMvpFilters(
            lat=-34.0, lng=151.0, radius_m=500.0
        )
        f1.validate(DiscoveryMode.LIST)
        a, p = build_discovery_sql(DiscoveryMode.LIST, f1)
        self.assertIn("6371000", a)
        self.assertEqual(len(p), 7)
