"""Regression checks for real-data semantics, date changes, and source failures."""
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
import rasterio
from rasterio.transform import from_bounds

from src import live_analytics as analytics
from src.analytics_ui import telemetry_html


BBOX = (89.4, 22.7, 89.7, 22.95)


def scene(name, orbit, timestamp):
    return {"id": name, "assets": {"vv": {"href": f"https://example.test/{name}.tif"}},
            "properties": {"datetime": timestamp, "sar:instrument_mode": "IW",
                           "sat:relative_orbit": orbit, "sat:orbit_state": "ascending"}}


class LiveAnalyticsTests(unittest.TestCase):
    def setUp(self):
        analytics.public_scenes.clear()
        analytics._radar_grid.clear()

    def test_radar_power_is_converted_to_decibels_and_nodata_excluded(self):
        stats = analytics.power_statistics(np.array([[0.01, np.nan], [0.01, 0.0]]), BBOX)
        self.assertAlmostEqual(stats["mean_db"], -20.0)
        self.assertEqual(stats["valid_cells"], 2)
        self.assertEqual(stats["coverage_pct"], 50)
        with self.assertRaises(analytics.DataSourceUnavailable):
            analytics.power_statistics(np.zeros((2, 2)), BBOX)

    def test_date_changes_and_refresh_checks_query_the_correct_window(self):
        response = Mock()
        response.json.return_value = {"features": [], "links": []}
        with patch.object(analytics.requests, "get", return_value=response) as request:
            analytics.public_scenes(BBOX, "2026-10-10", "2026-10-10", 1)
            analytics.public_scenes(BBOX, "2026-10-10", "2026-10-10", 1)
            self.assertEqual(request.call_count, 1)
            self.assertEqual(request.call_args.kwargs["params"]["datetime"],
                             "2026-10-10T00:00:00Z/2026-10-10T23:59:59.999999Z")
            analytics.public_scenes(BBOX, "2026-10-09", "2026-10-10", 1)
            analytics.public_scenes(BBOX, "2026-10-09", "2026-10-10", 2)
            self.assertEqual(request.call_count, 3)
            with self.assertRaises(ValueError):
                analytics.public_scenes(BBOX, "2026-10-11", "2026-10-10", 2)
            self.assertEqual(request.call_count, 3)

    def test_empty_catalogue_does_not_invent_measurements(self):
        with patch.object(analytics, "_radar_grid") as raster:
            result = analytics.public_radar_summary({"items": [], "truncated": False}, BBOX)
        self.assertEqual(result["state"], "empty")
        self.assertNotIn("mean_db", result)
        raster.assert_not_called()

    def test_different_orbits_are_not_used_for_change_measurements(self):
        catalogue = {"items": [scene("new", 114, "2026-10-17T12:00:00Z"),
                               scene("old", 12, "2026-10-10T12:00:00Z")], "truncated": False}
        with patch.object(analytics, "_radar_grid", return_value=np.ones((2, 2))) as raster:
            result = analytics.public_radar_summary(catalogue, BBOX)
        self.assertIsNone(result["change_db"])
        self.assertEqual(raster.call_count, 1)

    def test_same_orbit_change_uses_only_common_valid_cells(self):
        catalogue = {"items": [scene("new", 114, "2026-10-17T12:00:00Z"),
                               scene("old", 114, "2026-10-10T12:00:00Z")], "truncated": False}
        current = np.array([[1.0, np.nan], [1.0, 1.0]])
        previous = np.array([[0.1, 0.1], [np.nan, 0.1]])
        with patch.object(analytics, "_radar_grid", side_effect=[current, previous]):
            result = analytics.public_radar_summary(catalogue, BBOX)
        self.assertAlmostEqual(result["change_db"], 10)
        self.assertEqual(result["baseline_at"], "2026-10-10T12:00:00Z")

    def test_cloud_raster_window_is_reprojected_onto_the_requested_grid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "radar.tif"
            with rasterio.open(path, "w", driver="GTiff", height=32, width=32, count=1,
                               dtype="float32", crs="EPSG:4326", transform=from_bounds(*BBOX, 32, 32),
                               nodata=-32768) as raster:
                raster.write(np.full((32, 32), 0.01, dtype="float32"), 1)
            with patch.object(analytics, "_signed_public_asset", return_value=str(path)):
                values = analytics._radar_grid("test", "https://example.test/file.tif", BBOX)
            self.assertEqual(values.shape, (192, 192))
            self.assertAlmostEqual(analytics.power_statistics(values, BBOX)["mean_db"], -20, places=5)

    def test_terrain_failure_does_not_hide_available_radar(self):
        with patch.object(analytics, "public_terrain_summary", side_effect=analytics.DataSourceUnavailable("offline")), \
             patch.object(analytics, "public_scenes", return_value={"items": [], "truncated": False}):
            result = analytics.public_analysis(BBOX, "2026-10-08", "2026-10-18", 1)
        self.assertEqual(result["terrain"]["state"], "unavailable")
        self.assertEqual(result["radar"]["state"], "empty")

    def test_southern_and_western_terrain_tiles_use_lower_left_coordinates(self):
        url = analytics._dem_url(-42, -123, 30)
        self.assertIn("S42_00_W123_00", url)

    def test_earth_engine_uses_the_correct_polarisation_field_and_includes_end_day(self):
        from src import gee_processor
        collection = Mock()
        for method in ("filterBounds", "filterDate", "filter", "select"):
            getattr(collection, method).return_value = collection
        with patch.object(gee_processor.ee.Geometry, "BBox"), \
             patch.object(gee_processor.ee, "ImageCollection", return_value=collection), \
             patch.object(gee_processor.ee.Filter, "eq"), \
             patch.object(gee_processor.ee.Filter, "listContains") as polarisation:
            gee_processor.sentinel1_collection(BBOX, "2026-10-10", "2026-10-10")
        collection.filterDate.assert_called_once_with("2026-10-10", "2026-10-11")
        polarisation.assert_called_once_with("transmitterReceiverPolarisation", "VV")

    def test_telemetry_escapes_source_errors_and_reports_missing_data(self):
        html = telemetry_html("<script>bad</script>", "2026-10-18", "2026-10-17", error="Choose valid dates")
        self.assertNotIn("<script>", html)
        self.assertIn('data-state="unavailable"', html)
        self.assertIn("Choose valid dates", html)
        self.assertNotIn("-14.2", html)


class AnalyticsInteractionTests(unittest.TestCase):
    def test_date_change_starts_analysis_and_preserves_scenario(self):
        from streamlit.testing.v1 import AppTest
        from src import analytics_ui

        result = {"provider": "public", "checked_at": "2026-10-18T14:00:00+00:00",
                  "terrain": {"state": "unavailable", "message": "Terrain unavailable in test"},
                  "radar": {"state": "empty", "message": "No radar scene in this test window"}}
        stream = {"checked_at": "2026-10-18T14:00:00+00:00", "cycle": 1, "mode": "loading",
                  "coordinates": (22.8456, 89.5403), "signal": {"level": "UNKNOWN", "reason": "Sources loading"},
                  "satellite": result, "history": [], "source_errors": {}}
        with patch.object(analytics_ui, "monitor_snapshot", return_value=stream) as monitor:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app" / "app.py"), default_timeout=20).run()
            self.assertFalse(app.exception)
            self.assertEqual(monitor.call_count, 1)
            app.date_input[0].set_value(date(2026, 10, 1)).run()
            self.assertFalse(app.exception)
            self.assertEqual(monitor.call_args.args[3], "2026-10-01")
            app.slider[0].set_value(0.5).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.metric[0].value, "2.7 meters")
            self.assertTrue(any("5,950,000" in text.value for text in app.markdown))
            self.assertEqual(len(app._fragment_storage._fragments), 2)


if __name__ == "__main__":
    unittest.main()
