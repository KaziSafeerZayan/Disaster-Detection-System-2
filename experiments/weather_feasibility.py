"""Run public-feed latency and text-vector feasibility checks without credentials."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.weather_sources import fetch_weather, fetch_river, fetch_reports, text_similarity, screen_conditions


def main():
    latitude, longitude = 22.8456, 89.5403
    jobs = {
        "weather": lambda: fetch_weather(latitude, longitude, int(time.time() // 120)),
        "river": lambda: fetch_river(latitude, longitude, int(time.time() // 900)),
        "reports": lambda: fetch_reports(latitude, longitude, "Khulna", int(time.time() // 600)),
    }
    def timed(item):
        name, function = item
        started = time.monotonic()
        try:
            data = function()
            return name, {"seconds": round(time.monotonic() - started, 3), "data": data}
        except Exception as exc:
            return name, {"seconds": round(time.monotonic() - started, 3), "error": str(exc)}
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = dict(pool.map(timed, jobs.items()))
    positive = "Khulna flood expected after heavy rainfall"
    negative = "Khulna no flood expected after heavy rainfall"
    results["text_vector_experiment"] = {
        "method": "Sparse hashed unigram/bigram vectors; not a trained semantic model",
        "cases": [positive, negative], "similarities": text_similarity(positive, [positive, negative]),
        "finding": "Both sentences are topically similar despite opposite meaning. Similarity is not flood likelihood.",
    }
    results["signal"] = screen_conditions(*(results[key].get("data") for key in ("weather", "river", "reports")))
    output = ROOT / "logs" / "weather-feasibility-results.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(output)
    print(json.dumps({key: {k: v for k, v in value.items() if k != "data"}
                      for key, value in results.items()}, indent=2))


if __name__ == "__main__":
    main()
