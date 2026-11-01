# Satellite Assisted Flood Detection System

Satellite imagery with highlighted mapped waterways, optional Sentinel-1 radar imagery via Google Earth Engine, and the existing preset-based flood scenario calculations.

## Quick Start
1. Double-click `start.bat`. It prepares the local environment, starts the app in the background, and opens http://127.0.0.1:8501/ once the server is ready. You can close the launcher window. Opening `start.bat` again reuses the running app. After restarting your computer, run `start.bat` again before opening the address. Startup logs are saved in `logs/`.
2. Rivers, lakes, canals, and streams are highlighted in cyan by default. Use the map's existing layer menu to toggle **Waterways · rivers & lakes (mapped)**. This OpenStreetMap/OpenMapTiles overlay is hosted by [OpenFreeMap](https://openfreemap.org/) and works without a Google account. It shows mapped water features, not detected flooding; its detail depends on the map data and zoom level.
3. **Flood & Terrain Analytics** emits a check and an evidence-based summary every **10 seconds** while the page is open. Real weather and river forecasts load independently of the slower satellite analysis. The default sources need no account or API key. Internet access and provider availability are still required.
4. **Data sources & sign-in** offers an optional Google Earth Engine connection. Click its sign-in button, or double-click `authenticate.bat`, then complete Google's sign-in. Select **Google Earth Engine** afterward. Google requires a registered Earth Engine-enabled Cloud project and account permissions; see [Google's setup guide](https://developers.google.com/earth-engine/guides/auth).

The analytics reports the latest published observation inside the selected dates (both dates included), its acquisition time, sampled VV backscatter, valid grid coverage, measured elevation, and a derived slope. Public radar uses linear gamma0 power converted to decibels on a 192×192 analysis grid; the panel reports the actual sampling spacing. A change value is shown only when an earlier same-orbit observation has common valid pixels. The catalogue inspects up to 100 recent scenes and labels truncated counts with `+`.

## Weather-search feasibility prototype

The ten-second cycle reevaluates the latest source data and appends a status entry. A new check does not imply a new measurement. Weather queries are cached for 120 seconds, river forecasts for 15 minutes, reports for 10 minutes, and SAR discovery for 60 seconds. Network jobs run in the background, preserving available readings while another source is slow. Targets are the configured map-preset point/bounding box, not a validated division-wide hydrological area.

Sources tested without credentials:

- [Open-Meteo weather](https://open-meteo.com/en/docs): current model estimates, past/forecast 24-hour rainfall, rain probability and soil moisture. [MET Norway Locationforecast](https://api.met.no/weatherapi/locationforecast/2.0/documentation) is the independent weather backup.
- [GloFAS via Open-Meteo](https://open-meteo.com/en/docs/flood-api): daily modelled discharge and a three-day trend at the selected river-model cell. It is not an observed water-level gauge.
- [GDACS](https://www.gdacs.org/feed_reference.aspx): public report search, filtered to flood events ending/updated within seven days and event centroids within 100 km before text ranking. No matching report is not evidence of no flooding.
- [Sentinel-1 RTC](https://planetarycomputer.microsoft.com/dataset/sentinel-1-rtc) and [Copernicus DEM](https://registry.opendata.aws/copernicus-dem/): satellite observations and the static surface reference used above.

The text experiment uses local sparse hashed unigram/bigram vectors, with no external language-model service or learned semantic model. It ranked “flood expected” and “no flood expected” as highly similar, demonstrating why text-vector similarity must not become a flood probability. Text vectors rank recent nearby report candidates; numeric weather/river rules and structured published alert levels supply the screening explanation.

The prototype uses 44/88 mm per 24 hours as heavy/very-heavy rainfall indicators, following the BMD rainfall categories reproduced in [FFWC's summary](https://api.ffwc.gov.bd/assets/uploads/fsumm.pdf). A river-only watch requires both a 20% forecast rise and flow above its recent 30-day 75th percentile. Those discharge rules are experimental, not calibrated local flood thresholds. The output is a screening category and reason, never a probability or assurance that an area is safe. Coastal surge, upstream routing, embankments and local drainage are not modelled.

Verified real readings are retained if a provider subsequently fails, with source times shown. Only when both numerical feeds have completed and failed, with no retained numerical data and no nearby live report, does the panel show **DEMO — SYNTHETIC VALUES**. That synthetic temperature/rain preview changes on each check, is labelled at the point of display, and is excluded from flood assessment. It switches back when a real source recovers. DEMO is not needed when real data works.

Run the reproducible public-feed/text experiment with `.venv\Scripts\python.exe experiments\weather_feasibility.py`. Its timing, source responses and negation test are saved to `logs/weather-feasibility-results.json`. Run checks with `.venv\Scripts\python.exe -m unittest discover -s tests`.

Terrain is a static surface model, including vegetation and buildings, rather than a changing river/water-level sensor. Satellite observations arrive periodically and may be published with a delay; automatic checks do not imply a new acquisition every minute. An empty window, network failure, missing coverage, or required Earth Engine login is displayed explicitly. The analytics is an observation summary, not a validated flood classification or warning model.

The configured project is `flood-warning-system-511803`. To use another project, set `GEE_PROJECT_ID` before authenticating and launching the app (PowerShell):

```powershell
$env:GEE_PROJECT_ID = "your-earth-engine-project"
.\authenticate.bat
.\start.bat
```

The water-rise slider retains the original elevation subtraction, exposure percentages, and chart calculations. Slider updates leave the map in place. The existing header badges are unchanged; the telemetry panel now reports source measurements and connection status.

## Workspace and map appearance

The compact glass navigation includes a locally rendered rotating globe and an illustrative satellite orbit. Its pause button stops the motion; reduced-motion preferences are respected, and rendering pauses in hidden tabs. The globe uses bundled public-domain [Natural Earth land outlines](https://www.naturalearthdata.com/about/terms-of-use/), with no animation service or additional package dependency. The orbit is simulated and is not satellite tracking data.

The map's **Layers** menu offers satellite imagery, dark and light atlases, topographic mapping, optional place labels/borders, and the existing mapped waterways. **Display** offers Natural color, Crisp detail, Graphite, Blue steel, and Warm tone, plus terrain-shading opacity, a geographic coordinate grid, and a return-to-target action. Textures are visual filters, not spectral products or new measurements. Waterway and radar colors are independent. Appearance choices are remembered in local browser storage; **Reset display** restores the default imagery and natural color. Public Esri services provide the basemaps, labels, and hillshade, with attribution displayed on the map.
