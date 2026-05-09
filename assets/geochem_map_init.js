/**
 * geochem_map_init.js
 * MapLibre GL Layer für Geochemie + Geophysik Anomalien
 * Ablegen unter: assets/geochem_map_init.js
 */

(function () {
  "use strict";

  let map = null;
  let currentConfig = null;

  // Farbe nach Anomalie-Score
  function scoreColor(score) {
    if (score === null || score === undefined) return "#3A3530";
    if (score > 70) return "#E74C3C";
    if (score > 40) return "#C8A850";
    return "#5D8A6B";
  }

  // Farbe nach Elementwert (relativ zu p50/p95)
  function elementColor(val, p50, p95) {
    if (val === null || val === undefined) return "#3A3530";
    const norm = Math.min((val - p50) / Math.max(p95 - p50, 0.001), 1);
    if (norm > 0.8) return "#E74C3C";
    if (norm > 0.5) return "#C8A850";
    if (norm > 0.2) return "#5D8A6B";
    return "#2A4A35";
  }

  // Perzentile berechnen
  function percentile(arr, p) {
    const sorted = [...arr].sort((a, b) => a - b);
    const idx = Math.floor((p / 100) * sorted.length);
    return sorted[Math.min(idx, sorted.length - 1)];
  }

  function initMap() {
    const container = document.getElementById("geochem-map-container");
    if (!container) return;

    map = new maplibregl.Map({
      container: "geochem-map-container",
      style: {
        version: 8,
        sources: {
          "carto-dark": {
            type: "raster",
            tiles: [
              "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution: "© CARTO © OpenStreetMap",
          },
        },
        layers: [
          {
            id: "carto-dark-layer",
            type: "raster",
            source: "carto-dark",
            minzoom: 0,
            maxzoom: 22,
          },
        ],
      },
      center: [9.6, 59.65], // Kongsberg
      zoom: 9,
    });

    map.on("load", () => {
      if (currentConfig) applyConfig(currentConfig);
    });
  }

  function applyConfig(config) {
    if (!map || !map.isStyleLoaded()) return;

    // ── Geochemie Layer ──────────────────────────────────────────────────────
    updateGeochemLayer(config);

    // ── EM Layer ─────────────────────────────────────────────────────────────
    updateGeophysLayer("em", config.em_data, config.show_em, "#4FC3F7");

    // ── Mag Layer ────────────────────────────────────────────────────────────
    updateGeophysLayer("mag", config.mag_data, config.show_mag, "#CE93D8");

    // ── Rad Layer ────────────────────────────────────────────────────────────
    updateGeophysLayer("rad", config.rad_data, config.show_rad, "#A5D6A7");
  }

  function updateGeochemLayer(config) {
    const sourceId = "geochem-source";
    const layerId  = "geochem-layer";
    const heatId   = "geochem-heat";

    // Daten filtern
    let features = (config.geochem_data?.features || []).filter((f) => {
      const p = f.properties;
      if (config.medium_filter !== "Alle" && p.Medium !== config.medium_filter)
        return false;
      if ((p.anomaly_score || 0) < config.score_min)
        return false;
      return true;
    });

    // Elementwerte für Farbgebung sammeln
    const el = config.element_filter || "Au";
    const vals = features
      .map((f) => f.properties[el])
      .filter((v) => v !== null && v !== undefined && !isNaN(v))
      .map(Number);
    const p50 = percentile(vals, 50);
    const p95 = percentile(vals, 95);

    const geojson = { type: "FeatureCollection", features };

    // Source
    if (map.getSource(sourceId)) {
      map.getSource(sourceId).setData(geojson);
    } else {
      map.addSource(sourceId, { type: "geojson", data: geojson });
    }

    // Heatmap Layer (niedrige Zoom-Level)
    if (!map.getLayer(heatId)) {
      map.addLayer({
        id: heatId,
        type: "heatmap",
        source: sourceId,
        maxzoom: 11,
        paint: {
          "heatmap-weight": [
            "interpolate", ["linear"],
            ["get", "anomaly_score"], 0, 0, 100, 1,
          ],
          "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 5, 0.5, 10, 2],
          "heatmap-color": [
            "interpolate", ["linear"], ["heatmap-density"],
            0, "rgba(18,16,14,0)",
            0.2, "rgba(93,138,107,0.6)",
            0.5, "rgba(200,168,80,0.8)",
            0.8, "rgba(231,76,60,0.9)",
            1, "rgba(255,255,255,1)",
          ],
          "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 5, 15, 11, 25],
          "heatmap-opacity": config.show_geochem ? 0.8 : 0,
        },
      });
    } else {
      map.setPaintProperty(heatId, "heatmap-opacity", config.show_geochem ? 0.8 : 0);
    }

    // Punkte Layer (hohe Zoom-Level)
    if (!map.getLayer(layerId)) {
      map.addLayer({
        id: layerId,
        type: "circle",
        source: sourceId,
        minzoom: 10,
        paint: {
          "circle-radius": [
            "interpolate", ["linear"], ["zoom"],
            10, 4, 14, 8,
          ],
          "circle-color": [
            "case",
            [">", ["get", "anomaly_score"], 70], "#E74C3C",
            [">", ["get", "anomaly_score"], 40], "#C8A850",
            "#5D8A6B",
          ],
          "circle-opacity": config.show_geochem ? 0.85 : 0,
          "circle-stroke-width": 1,
          "circle-stroke-color": "#12100E",
          "circle-stroke-opacity": config.show_geochem ? 0.5 : 0,
        },
      });

      // Klick → Popup
      map.on("click", layerId, (e) => {
        const p = e.features[0].properties;
        const html = buildPopupHtml(p, el);
        // An Reflex State übergeben (via custom event)
        document.dispatchEvent(
          new CustomEvent("geochem-popup", { detail: html })
        );
      });

      map.on("mouseenter", layerId, () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", layerId, () => {
        map.getCanvas().style.cursor = "";
      });
    } else {
      map.setPaintProperty(layerId, "circle-opacity", config.show_geochem ? 0.85 : 0);
      map.setPaintProperty(layerId, "circle-stroke-opacity", config.show_geochem ? 0.5 : 0);
    }
  }

  function updateGeophysLayer(type, data, visible, color) {
    const sourceId = `${type}-source`;
    const layerId  = `${type}-layer`;
    const geojson  = data || { type: "FeatureCollection", features: [] };

    if (map.getSource(sourceId)) {
      map.getSource(sourceId).setData(geojson);
    } else {
      map.addSource(sourceId, { type: "geojson", data: geojson });
    }

    if (!map.getLayer(layerId)) {
      map.addLayer({
        id: layerId,
        type: "circle",
        source: sourceId,
        paint: {
          "circle-radius": 3,
          "circle-color": color,
          "circle-opacity": visible ? 0.6 : 0,
          "circle-stroke-width": 0,
        },
      });
    } else {
      map.setPaintProperty(layerId, "circle-opacity", visible ? 0.6 : 0);
    }
  }

  function buildPopupHtml(p, el) {
    const rows = [
      ["SampleID", p.SampleID],
      ["Medium",   p.Medium],
      ["Quelle",   p._quelle],
      ["Jahr",     p.FieldYear],
      ["Score",    p.anomaly_score !== undefined ? `<b style="color:#C8A850">${Number(p.anomaly_score).toFixed(1)}</b>` : "—"],
      [el,         p[el] !== undefined ? `${Number(p[el]).toFixed(4)} ppm` : "—"],
      ["Au",       p.Au  !== undefined ? `${Number(p.Au).toFixed(4)} ppm`  : "—"],
      ["Cu",       p.Cu  !== undefined ? `${Number(p.Cu).toFixed(1)} ppm`  : "—"],
      ["Ni",       p.Ni  !== undefined ? `${Number(p.Ni).toFixed(1)} ppm`  : "—"],
    ];
    return rows
      .map(
        ([k, v]) =>
          `<div style="display:flex;justify-content:space-between;
            font-family:'IBM Plex Mono',monospace;font-size:10px;
            padding:2px 0;border-bottom:1px solid #2A2520;color:#E8E0D0">
            <span style="color:#6B6560">${k}</span>
            <span>${v ?? "—"}</span>
          </div>`
      )
      .join("");
  }

  // ── State-Bridge Polling ──────────────────────────────────────────────────

  function pollStateBridge() {
    const bridge = document.getElementById("geochem-state-bridge");
    if (!bridge) return;

    const raw = bridge.getAttribute("data-config");
    if (!raw || raw === currentConfig) return;

    currentConfig = raw;
    try {
      const config = JSON.parse(raw);
      if (map && map.isStyleLoaded()) {
        applyConfig(config);
      }
    } catch (e) {
      console.error("geochem config parse error:", e);
    }
  }

  // ── Init ──────────────────────────────────────────────────────────────────

  function waitAndInit() {
    if (typeof maplibregl === "undefined") {
      setTimeout(waitAndInit, 200);
      return;
    }
    initMap();
    setInterval(pollStateBridge, 400);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", waitAndInit);
  } else {
    waitAndInit();
  }
})();
