from concurrent.futures import Future
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from src import weather_sources as sources
from src import monitor_runtime as monitor
from src.analytics_ui import stream_telemetry_html


NOW = datetime(2026, 10, 18, 15, tzinfo=timezone.utc)
BBOX = (89.4, 22.7, 89.7, 22.95)


def weather():
    return {"source": "test weather", "valid_at": NOW.isoformat(), "fetched_at": NOW.isoformat(),
            "rain_past24_mm": 1.0, "rain_next24_mm": 2.0, "temperature_c": 27.0}


def river():
    return {"source": "test river", "valid_date": NOW.date().isoformat(), "fetched_at": NOW.isoformat(),
            "discharge_m3s": 100.0, "peak_next3_m3s": 90.0, "change_next3_pct": -10.0,
            "past30_p75_m3s": 120.0}


class ImmediateExecutor:
    def submit(self, function):
        future = Future()
        try:
            future.set_result(function())
        except Exception as exc:
            future.set_exception(exc)
        return future


class WeatherParsingTests(unittest.TestCase):
    def test_missing_rain_is_unavailable_instead_of_zero(self):
        times = [(NOW + timedelta(hours=i)).replace(tzinfo=None).isoformat() for i in range(-30, 31)]
        values = [1.0] * len(times)
        payload = {"current": {"time": NOW.isoformat(), "temperature_2m": 27, "interval": 900},
                   "hourly": {"time": times, "precipitation": values}}
        parsed = sources.parse_weather(payload, NOW)
        self.assertEqual(parsed["rain_past24_mm"], 24)
        self.assertEqual(parsed["rain_next24_mm"], 24)
        self.assertIsNone(parsed["soil_moisture"])
        payload["hourly"]["precipitation"][35] = None
        self.assertIsNone(sources.parse_weather(payload, NOW)["rain_next24_mm"])

    def test_stale_weather_cannot_be_a_current_measurement(self):
        with self.assertRaises(ValueError):
            sources.parse_weather({"current": {"time": (NOW - timedelta(days=2)).isoformat()}}, NOW)

    def test_flood_screen_has_no_calibrated_probability(self):
        value = weather()
        self.assertIn("NO ELEVATED", sources.screen_conditions(value, river())["level"])
        value["rain_next24_mm"] = 50
        self.assertEqual(sources.screen_conditions(value, river())["level"], "WATCH")
        value["rain_next24_mm"] = 100
        signal = sources.screen_conditions(value, river())
        self.assertEqual(signal["level"], "ELEVATED RAINFALL SIGNAL")
        self.assertNotIn("probability", signal)
        self.assertEqual(sources.screen_conditions()["level"], "UNKNOWN")

    def test_text_similarity_is_not_a_negation_classifier(self):
        positive = "Khulna flood expected after heavy rainfall"
        negative = "Khulna no flood expected after heavy rainfall"
        scores = sources.text_similarity(positive, [positive, negative])
        self.assertGreater(scores[1], 0.7)
        self.assertLess(scores[1], scores[0])

    def test_stale_and_distant_reports_are_filtered_before_vector_ranking(self):
        def event(latitude, ended):
            return f'''<item><title>Khulna severe flood warning</title><pubDate>Sun, 18 Oct 2026 12:00:00 GMT</pubDate>
                <g:eventtype>FL</g:eventtype><g:todate>{ended}</g:todate>
                <g:datemodified>Sun, 18 Oct 2026 12:00:00 GMT</g:datemodified>
                <geo:point>{latitude} 89.54</geo:point><g:alertlevel>Red</g:alertlevel></item>'''
        xml = ('<rss xmlns:g="http://www.gdacs.org" xmlns:geo="http://www.georss.org/georss"><channel>'
               + event(22.85, "Sun, 18 Oct 2026 00:00:00 GMT")
               + event(22.85, "Sun, 18 Oct 2020 00:00:00 GMT")
               + event(45, "Sun, 18 Oct 2026 00:00:00 GMT") + '</channel></rss>')
        reports = sources.parse_reports(xml, 22.8456, 89.5403, "Khulna", NOW)
        self.assertEqual(reports["examined"], 3)
        self.assertEqual(len(reports["nearby"]), 1)
        self.assertEqual(sources.screen_conditions(reports=reports)["level"], "PUBLISHED FLOOD ALERT NEARBY")


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.patches = [patch.object(monitor, "_EXECUTOR", ImmediateExecutor()),
                        patch.object(monitor, "fetch_weather", return_value=weather()),
                        patch.object(monitor, "fetch_river", return_value=river()),
                        patch.object(monitor, "fetch_reports", return_value={"nearby": [], "examined": 9, "fetched_at": NOW.isoformat()})]
        self.active = [item.start() for item in self.patches]
        self.addCleanup(lambda: [item.stop() for item in reversed(self.patches)])
        self.state = {}

    def snapshot(self, now=NOW, region="Khulna Division, Bangladesh", end="2026-10-18"):
        return monitor.monitor_snapshot(self.state, region, BBOX, "2026-10-08", end, "public", lambda *args: {}, now)

    def test_ten_second_checks_reassess_real_data_without_inventing_observations(self):
        first = self.snapshot()
        second = self.snapshot(NOW + timedelta(seconds=10))
        self.assertEqual(second["cycle"], first["cycle"] + 1)
        self.assertNotEqual(first["checked_at"], second["checked_at"])
        self.assertEqual(second["weather"], first["weather"])
        self.active[1].assert_called_once()
        self.assertIn("no newer provider", second["history"][-1]["message"])
        self.assertEqual(second["mode"], "live")

    def test_demo_is_only_used_after_both_numerical_sources_fail(self):
        self.active[1].side_effect = RuntimeError("weather offline")
        first = self.snapshot()
        self.assertEqual(first["mode"], "live")  # River data still works.
        self.state.clear()
        self.active[2].side_effect = RuntimeError("river offline")
        fallback = self.snapshot()
        self.assertEqual(fallback["mode"], "demo")
        self.assertEqual(fallback["signal"]["level"], "UNKNOWN")
        html = stream_telemetry_html("Khulna", "2026-10-08", "2026-10-18", fallback)
        self.assertIn("SYNTHETIC VALUES", html)
        self.assertIn("Excluded from flood assessment", html)

    def test_verified_last_reading_is_preserved_during_a_source_outage(self):
        first = self.snapshot()
        self.active[1].side_effect = RuntimeError("weather offline")
        self.active[2].side_effect = RuntimeError("river offline")
        self.snapshot(NOW + timedelta(seconds=130))
        second = self.snapshot(NOW + timedelta(seconds=140))
        self.assertEqual(second["weather"], first["weather"])
        self.assertNotEqual(second["mode"], "demo")

    def test_target_change_discards_old_target_values(self):
        self.snapshot()
        self.active[1].side_effect = RuntimeError("new location unavailable")
        self.active[2].side_effect = RuntimeError("new location unavailable")
        next_target = self.snapshot(region="Dhaka Division, Bangladesh")
        self.assertIsNone(next_target["weather"])
        self.assertEqual(next_target["mode"], "demo")


if __name__ == "__main__":
    unittest.main()
