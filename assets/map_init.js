// map_init.js — MapLibre Initialisierung für Mineral Intelligence
(function() {
  // Popup + Karten-CSS injizieren
  var style = document.createElement('style');
  style.textContent = `
    .maplibregl-popup-content {
      background: #1E1C18 !important;
      color: #E8E0D0 !important;
      border: 1px solid #3A3530;
      border-radius: 6px;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 11px;
      padding: 10px 14px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.6);
      min-width: 200px;
    }
    .maplibregl-popup-close-button {
      color: #B8A898 !important;
      font-size: 16px;
    }
    .maplibregl-popup-tip { border-top-color: #3A3530 !important; }
    .maplibregl-ctrl-group { background: #1E1C18 !important; border: 1px solid #3A3530 !important; }
    .maplibregl-ctrl button { color: #B8A898 !important; }
  `;
  document.head.appendChild(style);

  function init() {
    var container = document.getElementById('map-container');
    var bridge = document.getElementById('map-state-bridge');

    if (!container || !bridge || typeof maplibregl === 'undefined') {
      setTimeout(init, 200);
      return;
    }
    if (window._mineralMap) return;

    window._mineralMap = new maplibregl.Map({
      container: 'map-container',
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json',
      center: [10.0, 62.0],
      zoom: 6,
    });

    window._mineralMap.addControl(new maplibregl.NavigationControl(), 'top-right');
    window._mineralMap.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right');

    var lastCfg = null;

    function syncLayers() {
      var bridge = document.getElementById('map-state-bridge');
      if (!bridge) return;
      var cfgStr = bridge.getAttribute('data-config');
      if (!cfgStr || cfgStr === lastCfg || cfgStr === 'null') return;
      lastCfg = cfgStr;
      try {
        var cfg = JSON.parse(cfgStr);
        applyLayers(cfg);
      } catch(e) { console.error('cfg parse error:', e); }
    }

    var BASEMAPS = {
      dark: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      light: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      satellite: {
        version: 8,
        sources: {
          esri: {
            type: 'raster',
            tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
            tileSize: 256,
            maxzoom: 23,
            attribution: '© Esri, Maxar, Earthstar Geographics'
          },
          labels: {
            type: 'raster',
            tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'],
            tileSize: 256,
            maxzoom: 23,
          }
        },
        layers: [
          { id: 'esri-sat', type: 'raster', source: 'esri' },
          { id: 'esri-labels', type: 'raster', source: 'labels' }
        ]
      }
    };

    var currentBasemap = null;

    function applyLayers(cfg) {
      var map = window._mineralMap;

      // Basemap wechseln falls nötig
      var newBasemap = cfg.basemap || 'dark';
      if (newBasemap !== currentBasemap) {
        currentBasemap = newBasemap;
        map.setStyle(BASEMAPS[newBasemap]);
        map.once('style.load', function() { addDataLayers(cfg); });
        return;
      }

      if (!map.isStyleLoaded()) {
        map.once('style.load', function(){ addDataLayers(cfg); });
        return;
      }
      addDataLayers(cfg);
    }

    function addDataLayers(cfg) {
      var map = window._mineralMap;

      // Alle NGU-Layer-IDs sammeln
      var nguIds = ['malm_forekomst_flate','malm_registrering_flate',
        'industri_forekomst_flate','industri_forekomst_punkt',
        'industri_registrering_flate','industri_registrering_punkt',
        'malm_forekomst_punkt','malm_registrering_punkt'];
      var layersToRemove = ['e29-fill','e29-line','bergr-fill','bergr-line','dmf'];
      nguIds.forEach(function(id){ layersToRemove.push(id+'-fill'); layersToRemove.push(id+'-line'); layersToRemove.push(id+'-circle'); });
      layersToRemove.forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); });
      var sourcesToRemove = ['e29','bergr','dmf'];
      nguIds.forEach(function(id){ sourcesToRemove.push(id); });
      sourcesToRemove.forEach(function(id){ if (map.getSource(id)) map.removeSource(id); });
      map.getStyle().layers.forEach(function(l){
        if (l.id && l.id.startsWith('wms-')) {
          map.removeLayer(l.id);
          if (map.getSource(l.id)) map.removeSource(l.id);
        }
      });
      var leg = document.getElementById('age-legend');
      if (leg) leg.remove();

      // WMS Layer
      (cfg.wms_layers || []).forEach(function(lyr) {
        var sid = 'wms-' + lyr.id;
        map.addSource(sid, {
          type: 'raster',
          tiles: [lyr.url + 'SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=' + lyr.layer
            + '&FORMAT=image/png&TRANSPARENT=true&WIDTH=256&HEIGHT=256&CRS=EPSG:3857&BBOX={bbox-epsg-3857}'],
          tileSize: 256
        });
        map.addLayer({ id: sid, type: 'raster', source: sid, paint: { 'raster-opacity': lyr.opacity } });
      });

      // Element29 Claims
      if (cfg.show_e29 && cfg.e29_geojson) {
        try {
          var e29 = JSON.parse(cfg.e29_geojson);
          map.addSource('e29', { type: 'geojson', data: e29 });
          map.addLayer({ id: 'e29-fill', type: 'fill', source: 'e29',
            paint: { 'fill-color': '#E74C3C', 'fill-opacity': 0.4 } });
          map.addLayer({ id: 'e29-line', type: 'line', source: 'e29',
            paint: { 'line-color': '#FF0000', 'line-width': 2 } });
          var e29Popup = new maplibregl.Popup({ maxWidth: '280px', closeButton: false, closeOnClick: false });
          map.on('mouseenter', 'e29-fill', function(e) {
            map.getCanvas().style.cursor = 'pointer';
            var p = e.features[0].properties;
            var labels = {
              'tillatelsesnummer': '📋 Nr.',
              'rettighetnavn': '📌 Name',
              'rettighethaver': '🏢 Inhaber',
              'rettighetstype': '📁 Typ',
              'status': '✅ Status',
              'mineral': '⚗️ Mineral',
              'kommunenavn': '🏘️ Kommune',
              'areal_m2': '📐 Areal m²'
            };
            var html = '<b style="color:#E74C3C;font-size:12px">Element29 Claim</b><br/><br/>';
            Object.keys(labels).forEach(function(k){
              if (p[k] && p[k] !== 'nan') {
                html += '<span style="color:#6B6560">' + labels[k] + '</span> '
                     + '<span style="color:#E8E0D0">' + p[k] + '</span><br/>';
              }
            });
            e29Popup.setLngLat(e.lngLat).setHTML(html).addTo(map);
          });
          map.on('mouseleave', 'e29-fill', function() {
            map.getCanvas().style.cursor = '';
            e29Popup.remove();
          });
        } catch(ex) { console.error('e29 error:', ex); }
      }

      // Bergrettigheter
      if (cfg.show_bergr && cfg.bergr_geojson) {
        try {
          var bd = JSON.parse(cfg.bergr_geojson);
          map.addSource('bergr', { type: 'geojson', data: bd });
          map.addLayer({ id: 'bergr-fill', type: 'fill', source: 'bergr',
            paint: { 'fill-color': ['get','_fill'], 'fill-opacity': 0.3 } });
          map.addLayer({ id: 'bergr-line', type: 'line', source: 'bergr',
            paint: { 'line-color': '#5C4A32', 'line-width': 0.8 } });
          map.on('click', 'bergr-fill', function(e) {
            var p = e.features[0].properties;
            var html = '<b style="color:#C8A850">Bergrettighet</b><br/>';
            ['Rettighetshaver','Rettighetsnavn','Rettighetstype','Mottatt','Godkjent'].forEach(function(k){
              if (p[k] && p[k] !== 'nan') html += k + ': <b>' + p[k] + '</b><br/>';
            });
            new maplibregl.Popup().setLngLat(e.lngLat).setHTML(html).addTo(map);
          });
        } catch(ex) { console.error('bergr error:', ex); }
      }

      // DMF Live WMS
      if (cfg.show_dmf_live) {
        map.addSource('dmf', { type: 'raster',
          tiles: ['https://kart.dirmin.no/dirmin/services/Bergrettigheter/MapServer/WmsServer?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=Bergrettigheter&FORMAT=image/png&TRANSPARENT=true&WIDTH=256&HEIGHT=256&SRS=EPSG:3857&BBOX={bbox-epsg-3857}'],
          tileSize: 256 });
        map.addLayer({ id: 'dmf', type: 'raster', source: 'dmf', paint: { 'raster-opacity': 0.55 } });
      }

      // NGU Lagerstätten — lazy fetch per layer
      if (cfg.ngu_show) {
        Object.keys(cfg.ngu_show).forEach(function(key) {
          var show = cfg.ngu_show[key];
          if (!show) return;
          // Already loaded?
          if (map.getSource(key)) return;
          // Fetch from assets
          fetch('/ngu/' + key + '.geojson')
            .then(function(r) { return r.json(); })
            .then(function(data) {
              if (!map.getSource(key)) {
          try {
            if (!data.features || data.features.length === 0) return;
            map.addSource(key, { type: 'geojson', data: data });
            var geomType = data.features[0].geometry ? data.features[0].geometry.type : '';
            var isPoint = geomType === 'Point' || geomType === 'MultiPoint';

            if (isPoint) {
              map.addLayer({
                id: key + '-circle', type: 'circle', source: key,
                paint: {
                  'circle-color': ['get', '_fill'],
                  'circle-radius': 5,
                  'circle-opacity': 0.85,
                  'circle-stroke-color': '#12100E',
                  'circle-stroke-width': 0.8,
                }
              });
              // Hover popup for points
              var pPopup = new maplibregl.Popup({ maxWidth: '260px', closeButton: false, closeOnClick: false });
              map.on('mouseenter', key + '-circle', function(e) {
                map.getCanvas().style.cursor = 'pointer';
                var p = e.features[0].properties;
                var html = '<b style="color:' + (p._fill||'#C8A850') + ';font-size:12px">'
                  + (p.objekttype||key) + '</b><br/><br/>';
                ['navnRastoffobj','forekomstNummer','ressursType_tekst'].forEach(function(k){
                  if (p[k] && p[k] !== '') html += '<span style="color:#6B6560">' + k + '</span>: <span style="color:#E8E0D0">' + p[k] + '</span><br/>';
                });
                pPopup.setLngLat(e.lngLat).setHTML(html).addTo(map);
              });
              map.on('mouseleave', key + '-circle', function() {
                map.getCanvas().style.cursor = '';
                pPopup.remove();
              });
            } else {
              // Polygon
              map.addLayer({
                id: key + '-fill', type: 'fill', source: key,
                paint: { 'fill-color': ['get','_fill'], 'fill-opacity': 0.35 }
              });
              map.addLayer({
                id: key + '-line', type: 'line', source: key,
                paint: { 'line-color': ['get','_fill'], 'line-width': 1.2, 'line-opacity': 0.8 }
              });
              // Hover popup for polygons
              var fPopup = new maplibregl.Popup({ maxWidth: '260px', closeButton: false, closeOnClick: false });
              map.on('mouseenter', key + '-fill', function(e) {
                map.getCanvas().style.cursor = 'pointer';
                var p = e.features[0].properties;
                var html = '<b style="color:' + (p._fill||'#C8A850') + ';font-size:12px">'
                  + (p.objekttype||key) + '</b><br/><br/>';
                ['navnRastoffobj','forekomstNummer','ressursType_tekst'].forEach(function(k){
                  if (p[k] && p[k] !== '') html += '<span style="color:#6B6560">' + k + '</span>: <span style="color:#E8E0D0">' + p[k] + '</span><br/>';
                });
                fPopup.setLngLat(e.lngLat).setHTML(html).addTo(map);
              });
              map.on('mouseleave', key + '-fill', function() {
                map.getCanvas().style.cursor = '';
                fPopup.remove();
              });
            }
              } catch(ex) { console.error('NGU layer error ' + key, ex); }
              }
            })
            .catch(function(ex) { console.error('NGU fetch error ' + key, ex); });
        });
      }

      // Center map
      map.jumpTo({ center: cfg.center, zoom: cfg.zoom });
    }  // end addDataLayers

    window._mineralMap.on('load', function() { syncLayers(); });
    setInterval(syncLayers, 500);
  }

  // Starten sobald DOM bereit
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
