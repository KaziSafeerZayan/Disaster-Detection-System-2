((map, basemaps, home) => {
  const container = map.getContainer();
  const storageKey = 'flooder-map-display-v1';
  const defaults = { base: 'Satellite imagery', texture: 'natural', relief: 0, grid: false };
  let preferences = { ...defaults };
  try { preferences = { ...defaults, ...JSON.parse(localStorage.getItem(storageKey) || '{}') }; } catch (_) { /* Storage is optional. */ }
  const textures = {
    natural: 'none',
    crisp: 'saturate(.8) contrast(1.2) brightness(1.06)',
    graphite: 'grayscale(1) contrast(1.12) brightness(.82)',
    blueprint: 'grayscale(1) sepia(1) hue-rotate(145deg) saturate(1.45) contrast(1.12)',
    warm: 'saturate(.55) sepia(.38) contrast(1.12)'
  };
  if (!basemaps[preferences.base]) preferences.base = defaults.base;
  if (!textures[preferences.texture]) preferences.texture = defaults.texture;
  preferences.relief = Math.max(0, Math.min(65, Number(preferences.relief) || 0));
  preferences.grid = preferences.grid === true;
  const shadePane = map.createPane('terrain-shading');
  shadePane.style.zIndex = 300; shadePane.style.pointerEvents = 'none';
  const relief = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}', {
    pane: 'terrain-shading', opacity: 0, maxNativeZoom: 16, maxZoom: 22,
    attribution: 'Hillshade &copy; Esri, Vantor, Airbus DS, USGS, NGA, NASA, CGIAR and the GIS User Community'
  });
  const gridPane = map.createPane('coordinate-grid');
  gridPane.style.zIndex = 410; gridPane.style.pointerEvents = 'none';
  const grid = L.layerGroup();
  const Display = L.Control.extend({
    options: { position: 'topright' },
    onAdd() {
      const node = L.DomUtil.create('div', 'map-display leaflet-control');
      node.innerHTML = `<button class="map-display-toggle" type="button" aria-expanded="false" aria-controls="map-display-panel" title="Map appearance">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" aria-hidden="true"><path d="M2 4h12M2 8h12M2 12h12M5 2v4m6 0v4m-5 0v4"/></svg>Display</button>
        <section id="map-display-panel" class="map-display-panel" aria-label="Map appearance" hidden>
          <div class="map-panel-heading">Surface & texture</div>
          <label class="map-control-label" for="map-texture">Visual texture</label>
          <select id="map-texture" aria-describedby="map-texture-note">
            <option value="natural">Natural color</option><option value="crisp">Crisp detail</option>
            <option value="graphite">Graphite</option><option value="blueprint">Blue steel</option><option value="warm">Warm tone</option>
          </select>
          <div class="map-range-heading"><label for="map-relief">Terrain shading</label><output for="map-relief">0%</output></div>
          <input id="map-relief" type="range" min="0" max="65" step="5" value="0" aria-label="Terrain shading opacity">
          <label class="map-grid-toggle"><input type="checkbox" id="map-grid">Coordinate grid</label>
          <p id="map-texture-note">Display styling only. Waterways and radar retain their own colors.</p>
          <div class="map-display-actions"><button type="button" data-map-home>Center target</button><button type="button" data-map-reset>Reset display</button></div>
        </section>`;
      L.DomEvent.disableClickPropagation(node); L.DomEvent.disableScrollPropagation(node);
      this.element = node;
      return node;
    }
  });
  const display = new Display().addTo(map);
  const node = display.element;
  const toggle = node.querySelector('.map-display-toggle');
  const panel = node.querySelector('section');
  const texture = node.querySelector('select');
  const shade = node.querySelector('[type="range"]');
  const gridInput = node.querySelector('[type="checkbox"]');
  const save = () => { try { localStorage.setItem(storageKey, JSON.stringify(preferences)); } catch (_) { /* Private browsing remains functional. */ } };
  function openPanel(open, focus = false) {
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    if (focus) (open ? texture : toggle).focus();
  }
  toggle.addEventListener('click', () => openPanel(panel.hidden));
  node.addEventListener('keydown', event => {
    if (event.key === 'Escape') { openPanel(false, true); event.stopPropagation(); }
  });
  document.addEventListener('pointerdown', event => { if (!node.contains(event.target)) openPanel(false); });
  function updateGrid() {
    grid.clearLayers();
    if (!preferences.grid) return;
    const bounds = map.getBounds();
    const west = Math.max(-540, bounds.getWest()), east = Math.min(540, bounds.getEast());
    const south = Math.max(-85, bounds.getSouth()), north = Math.min(85, bounds.getNorth());
    const interval = Math.max(.00001, Math.min(east - west, north - south) / 7);
    const power = 10 ** Math.floor(Math.log10(interval));
    const mantissa = interval / power;
    const step = (mantissa <= 1 ? 1 : mantissa <= 2 ? 2 : mantissa <= 5 ? 5 : 10) * power;
    const style = { pane: 'coordinate-grid', color: '#99ced8', weight: .6, opacity: .45, dashArray: '2 6', interactive: false };
    // Bound the number of gridlines even at unusual viewport sizes or world wraps.
    for (let lon = Math.ceil(west / step) * step, n = 0; lon < east && n < 80; lon += step, n++) L.polyline([[south, lon], [north, lon]], style).addTo(grid);
    for (let lat = Math.ceil(south / step) * step, n = 0; lat < north && n < 80; lat += step, n++) L.polyline([[lat, west], [lat, east]], style).addTo(grid);
  }
  function apply() {
    map.getPane('satellite').style.filter = textures[preferences.texture];
    container.dataset.texture = preferences.texture;
    texture.value = preferences.texture; shade.value = preferences.relief;
    node.querySelector('output').value = `${preferences.relief}%`;
    if (preferences.relief > 0) { if (!map.hasLayer(relief)) relief.addTo(map); relief.setOpacity(preferences.relief / 100); }
    else if (map.hasLayer(relief)) map.removeLayer(relief);
    gridInput.checked = preferences.grid;
    if (preferences.grid) { if (!map.hasLayer(grid)) grid.addTo(map); updateGrid(); }
    else if (map.hasLayer(grid)) map.removeLayer(grid);
  }
  function changeBase(name) {
    Object.entries(basemaps).forEach(([label, layer]) => {
      if (label === name) { if (!map.hasLayer(layer)) layer.addTo(map); }
      else if (map.hasLayer(layer)) map.removeLayer(layer);
    });
  }
  texture.addEventListener('change', () => { preferences.texture = texture.value; apply(); save(); });
  shade.addEventListener('input', () => { preferences.relief = +shade.value; apply(); save(); });
  gridInput.addEventListener('change', () => { preferences.grid = gridInput.checked; apply(); save(); });
  node.querySelector('[data-map-home]').addEventListener('click', () => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) map.setView(home.slice(0, 2), home[2]);
    else map.flyTo(home.slice(0, 2), home[2], { duration: 1.2 });
  });
  node.querySelector('[data-map-reset]').addEventListener('click', () => {
    preferences = { ...defaults }; changeBase(preferences.base); apply(); save(); updateReadout();
  });
  const Readout = L.Control.extend({
    options: { position: 'bottomleft' },
    onAdd() { this.element = L.DomUtil.create('div', 'map-view-readout'); this.element.setAttribute('aria-label', 'Map view coordinates'); return this.element; }
  });
  const readout = new Readout().addTo(map);
  L.control.scale({ position: 'bottomleft', imperial: false, maxWidth: 100 }).addTo(map);
  function updateReadout() {
    const point = map.getCenter();
    readout.element.textContent = `${point.lat.toFixed(3)}° / ${point.wrap().lng.toFixed(3)}° · Z${map.getZoom()} · ${preferences.base}`;
  }
  map.on('baselayerchange', event => { preferences.base = event.name; save(); updateReadout(); });
  map.on('moveend zoomend', () => { updateReadout(); updateGrid(); });
  // Let Folium finish registering the existing layer chooser before restoring a preference.
  requestAnimationFrame(() => { changeBase(preferences.base); apply(); updateReadout(); });
})(__FLOODER_MAP__, __FLOODER_BASEMAPS__, __FLOODER_HOME__);
