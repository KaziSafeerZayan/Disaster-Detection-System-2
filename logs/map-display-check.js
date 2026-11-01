
                L_NO_TOUCH = false;
                L_DISABLE_3D = false;
            

    
    
            var map_99c0140beea51ab49420e0355f6af78c = L.map(
                "map_99c0140beea51ab49420e0355f6af78c",
                {
                    center: [22.8456, 89.5403],
                    crs: L.CRS.EPSG3857,
                    ...{
  "zoom": 10,
  "zoomControl": true,
  "preferCanvas": false,
}

                }
            );

            

        
    
            var pane_416c0850248ab7ea3ebb0a162818e35f = map_99c0140beea51ab49420e0355f6af78c.createPane(
                "satellite");
            pane_416c0850248ab7ea3ebb0a162818e35f.style.zIndex = 200;
            
                pane_416c0850248ab7ea3ebb0a162818e35f.style.pointerEvents = 'none';
            
        
    
            var tile_layer_556d48a7eee452d28190a64c39898e48 = L.tileLayer(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                {
  "minZoom": 0,
  "maxZoom": 22,
  "maxNativeZoom": 19,
  "noWrap": false,
  "attribution": "Tiles \u0026copy; Esri, Vantor, Earthstar Geographics, and the GIS User Community",
  "subdomains": "abc",
  "detectRetina": false,
  "tms": false,
  "opacity": 1,
  "pane": "satellite",
}

            );
        
    
            tile_layer_556d48a7eee452d28190a64c39898e48.addTo(map_99c0140beea51ab49420e0355f6af78c);
        
    
            var tile_layer_61da1908a70725c7cb5cb86d4a354427 = L.tileLayer(
                "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
                {
  "minZoom": 0,
  "maxZoom": 22,
  "maxNativeZoom": 19,
  "noWrap": false,
  "attribution": "Tiles \u0026copy; Esri, HERE, Garmin, \u003ca href=\"https://www.openstreetmap.org/copyright\"\u003e\u0026copy; OpenStreetMap\u003c/a\u003e contributors, and the GIS user community",
  "subdomains": "abc",
  "detectRetina": false,
  "tms": false,
  "opacity": 1,
  "pane": "satellite",
}

            );
        
    
            var tile_layer_457ea618cb985da5b8597082640d0ebd = L.tileLayer(
                "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
                {
  "minZoom": 0,
  "maxZoom": 22,
  "maxNativeZoom": 19,
  "noWrap": false,
  "attribution": "Tiles \u0026copy; Esri, HERE, Garmin, \u003ca href=\"https://www.openstreetmap.org/copyright\"\u003e\u0026copy; OpenStreetMap\u003c/a\u003e contributors, and the GIS user community",
  "subdomains": "abc",
  "detectRetina": false,
  "tms": false,
  "opacity": 1,
  "pane": "satellite",
}

            );
        
    
            var tile_layer_383950fd241f786544a7fc329e1d97da = L.tileLayer(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
                {
  "minZoom": 0,
  "maxZoom": 22,
  "maxNativeZoom": 19,
  "noWrap": false,
  "attribution": "Tiles \u0026copy; Esri, HERE, Garmin, Intermap, increment P Corp., GEBCO, USGS, FAO, NPS, NRCAN, GeoBase, IGN, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), OpenStreetMap contributors, and the GIS User Community",
  "subdomains": "abc",
  "detectRetina": false,
  "tms": false,
  "opacity": 1,
  "pane": "satellite",
}

            );
        
    
            var pane_fe85ac938a33e56b42ab81f5ee5a03a3 = map_99c0140beea51ab49420e0355f6af78c.createPane(
                "map-labels");
            pane_fe85ac938a33e56b42ab81f5ee5a03a3.style.zIndex = 460;
            
                pane_fe85ac938a33e56b42ab81f5ee5a03a3.style.pointerEvents = 'none';
            
        
    
            var tile_layer_3b6d063fd168b629d1ff0b75e889c808 = L.tileLayer(
                "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
                {
  "minZoom": 0,
  "maxZoom": 22,
  "maxNativeZoom": 19,
  "noWrap": false,
  "attribution": "Tiles \u0026copy; Esri, HERE, Garmin, \u003ca href=\"https://www.openstreetmap.org/copyright\"\u003e\u0026copy; OpenStreetMap\u003c/a\u003e contributors, and the GIS user community",
  "subdomains": "abc",
  "detectRetina": false,
  "tms": false,
  "opacity": 1,
  "pane": "map-labels",
}

            );
        
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
    const step = map.getZoom() >= 11 ? .02 : map.getZoom() >= 8 ? .1 : map.getZoom() >= 5 ? 1 : 10;
    const west = Math.max(-540, bounds.getWest()), east = Math.min(540, bounds.getEast());
    const south = Math.max(-85, bounds.getSouth()), north = Math.min(85, bounds.getNorth());
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
})(map_99c0140beea51ab49420e0355f6af78c, {"Satellite imagery":tile_layer_556d48a7eee452d28190a64c39898e48,"Dark atlas":tile_layer_61da1908a70725c7cb5cb86d4a354427,"Light atlas":tile_layer_457ea618cb985da5b8597082640d0ebd,"Topographic":tile_layer_383950fd241f786544a7fc329e1d97da}, [22.8456, 89.5403, 10]);
    
            var pane_9a5236e628076244960855534f5cd142 = map_99c0140beea51ab49420e0355f6af78c.createPane(
                "waterways");
            pane_9a5236e628076244960855534f5cd142.style.zIndex = 450;
            
                pane_9a5236e628076244960855534f5cd142.style.pointerEvents = 'none';
            
        
    var vector_grid_protobuf_50e00b3b26183cd2fcad1605ce82b7aa = L.vectorGrid.protobuf(
                'https://tiles.openfreemap.org/planet/latest/{z}/{x}/{y}.pbf',
                    {
        pane: 'waterways',
        rendererFactory: L.canvas.tile,
        interactive: false,
        maxNativeZoom: 14,
        maxZoom: 22,
        attribution: '<a href="https://openfreemap.org">OpenFreeMap</a> · <a href="https://openmaptiles.org">© OpenMapTiles</a> · <a href="https://www.openstreetmap.org/copyright">© OpenStreetMap</a>',
        vectorTileLayerStyles: {
            aerodrome_label: [], aeroway: [], boundary: [], building: [],
            housenumber: [], landcover: [], landuse: [], mountain_peak: [],
            park: [], place: [], poi: [], transportation: [], transportation_name: [],
            water_name: [],
            water: function(properties) {
                if (properties.class === 'ocean') return [];
                return {
                    fill: true, fillColor: '#49cce3', fillOpacity: 0.42,
                    color: '#8ae8f2', opacity: 0.75, weight: 0.65
                };
            },
            waterway: function(properties, zoom) {
                if (properties.brunnel === 'tunnel') return [];
                return {
                    color: '#8ae8f2', opacity: 0.95,
                    weight: properties.class === 'river' ? Math.max(1.4, Math.min(3.2, (zoom - 5) * 0.3)) : 1.25
                };
            }
        }
    }
            );
    
            vector_grid_protobuf_50e00b3b26183cd2fcad1605ce82b7aa.addTo(map_99c0140beea51ab49420e0355f6af78c);
        
    
            var layer_control_f00b35ea477a54dc807d125171ba161d_layers = {
                base_layers : {
                    "Satellite imagery" : tile_layer_556d48a7eee452d28190a64c39898e48,
                    "Dark atlas" : tile_layer_61da1908a70725c7cb5cb86d4a354427,
                    "Light atlas" : tile_layer_457ea618cb985da5b8597082640d0ebd,
                    "Topographic" : tile_layer_383950fd241f786544a7fc329e1d97da,
                },
                overlays :  {
                    "Place labels \u0026 borders" : tile_layer_3b6d063fd168b629d1ff0b75e889c808,
                    "Waterways \u00b7 rivers \u0026 lakes (mapped)" : vector_grid_protobuf_50e00b3b26183cd2fcad1605ce82b7aa,
                },
            };
            let layer_control_f00b35ea477a54dc807d125171ba161d = L.control.layers(
                layer_control_f00b35ea477a54dc807d125171ba161d_layers.base_layers,
                layer_control_f00b35ea477a54dc807d125171ba161d_layers.overlays,
                {
  "position": "topright",
  "collapsed": true,
  "autoZIndex": true,
}
            ).addTo(map_99c0140beea51ab49420e0355f6af78c);

        
