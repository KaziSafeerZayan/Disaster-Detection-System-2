
                L_NO_TOUCH = false;
                L_DISABLE_3D = false;
            

    
    
            var map_910a1562f6943ed44f6883775257197d = L.map(
                "map_910a1562f6943ed44f6883775257197d",
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

            

        
    
            var pane_d869464f13d3c56a4472374039f8df7c = map_910a1562f6943ed44f6883775257197d.createPane(
                "satellite");
            pane_d869464f13d3c56a4472374039f8df7c.style.zIndex = 200;
            
                pane_d869464f13d3c56a4472374039f8df7c.style.pointerEvents = 'none';
            
        
    
            var tile_layer_8e9ee09ca8a6d10414b57329f4a41ff4 = L.tileLayer(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                {
  "minZoom": 0,
  "maxZoom": 18,
  "maxNativeZoom": 18,
  "noWrap": false,
  "attribution": "Esri \u0026mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
  "subdomains": "abc",
  "detectRetina": false,
  "tms": false,
  "opacity": 1,
  "pane": "satellite",
}

            );
        
    
            tile_layer_8e9ee09ca8a6d10414b57329f4a41ff4.addTo(map_910a1562f6943ed44f6883775257197d);
        
    
            var pane_b3fa0ed7e7f8cec2e40a3ea6c1752d32 = map_910a1562f6943ed44f6883775257197d.createPane(
                "waterways");
            pane_b3fa0ed7e7f8cec2e40a3ea6c1752d32.style.zIndex = 450;
            
                pane_b3fa0ed7e7f8cec2e40a3ea6c1752d32.style.pointerEvents = 'none';
            
        
    var vector_grid_protobuf_e2c50d222768d59cc1fd746890e4c7a3 = L.vectorGrid.protobuf(
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
    
            vector_grid_protobuf_e2c50d222768d59cc1fd746890e4c7a3.addTo(map_910a1562f6943ed44f6883775257197d);
        
    
            var layer_control_c47a9a71d0e1b48e722d6c485e3575bb_layers = {
                base_layers : {
                    "Esri Satellite" : tile_layer_8e9ee09ca8a6d10414b57329f4a41ff4,
                },
                overlays :  {
                    "Waterways \u00b7 rivers \u0026 lakes (mapped)" : vector_grid_protobuf_e2c50d222768d59cc1fd746890e4c7a3,
                },
            };
            let layer_control_c47a9a71d0e1b48e722d6c485e3575bb = L.control.layers(
                layer_control_c47a9a71d0e1b48e722d6c485e3575bb_layers.base_layers,
                layer_control_c47a9a71d0e1b48e722d6c485e3575bb_layers.overlays,
                {
  "position": "topright",
  "collapsed": true,
  "autoZIndex": true,
}
            ).addTo(map_910a1562f6943ed44f6883775257197d);

        
