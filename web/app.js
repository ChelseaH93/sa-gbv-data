const config = window.SA_GBV_CONFIG || {};
const baseUrl = (config.R2_BASE_URL || "").replace(/\/$/, "");
const status = document.getElementById("status");

const layers = {
  precincts: {
    file: "precincts.pmtiles",
    sourceLayer: "saps_precincts",
    paint: { "fill-color": "#4f6d7a", "fill-opacity": 0.08, "fill-outline-color": "#6e9aaa" }
  },
  crime: {
    file: "saps_crime_enriched.pmtiles",
    sourceLayer: "saps_crime",
    paint: { "fill-color": ["interpolate", ["linear"], ["coalesce", ["get", "count"], 0], 0, "#f1f5f9", 10, "#f59e0b", 100, "#dc2626"], "fill-opacity": 0.5 }
  },
  municipal: {
    file: "municipal_wards.pmtiles",
    sourceLayer: "municipal_wards",
    paint: { "line-color": "#0f766e", "line-width": 1.3, "line-opacity": 0.75 }
  },
  census: {
    file: "census_sal.pmtiles",
    sourceLayer: "census_sal",
    paint: { "fill-color": "#8b5cf6", "fill-opacity": 0.12, "fill-outline-color": "#a78bfa" }
  },
  osm: {
    file: "osm_risk.pmtiles",
    sourceLayer: "osm_risk",
    paint: { "circle-color": "#e11d48", "circle-radius": 4, "circle-opacity": 0.8 }
  },
  tcc: {
    file: "tcc_centres.pmtiles",
    sourceLayer: "tcc_centres",
    paint: { "circle-color": "#0891b2", "circle-radius": 6, "circle-stroke-color": "#ecfeff", "circle-stroke-width": 1.5 }
  },
  mobility: {
    file: "mobility_shapes.pmtiles",
    sourceLayer: "mobility_shapes",
    paint: { "line-color": "#d97706", "line-width": 2, "line-opacity": 0.8 }
  }
};

if (!baseUrl || baseUrl.includes("YOUR-R2-PUBLIC-DOMAIN")) {
  status.textContent = "Set the R2 URL in config.js";
  status.classList.add("error");
}

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

const map = new maplibregl.Map({
  container: "map",
  style: {
    version: 8,
    sources: {
      osm: {
        type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution: "© OpenStreetMap contributors"
      }
    },
    layers: [{ "id": "osm-basemap", "type": "raster", "source": "osm", "paint": { "raster-opacity": 0.82 } }]
  },
  center: [24.0, -29.0],
  zoom: 4.2,
  maxZoom: 15,
  attributionControl: true
});

map.addControl(new maplibregl.NavigationControl(), "bottom-right");

map.on("load", () => {
  if (!baseUrl || baseUrl.includes("YOUR-R2-PUBLIC-DOMAIN")) return;
  let loaded = 0;
  Object.entries(layers).forEach(([key, layer]) => {
    const sourceId = `source-${key}`;
    const layerId = `layer-${key}`;
    map.addSource(sourceId, { type: "vector", url: `pmtiles://${baseUrl}/${layer.file}` });
    const type = key === "municipal" ? "line" : key === "osm" ? "circle" : "fill";
    map.addLayer({ id: layerId, type, source: sourceId, "source-layer": layer.sourceLayer, paint: layer.paint });
    loaded += 1;
  });
  status.textContent = `${loaded} layers available`;
});

document.querySelectorAll("input[data-layer]").forEach((input) => {
  input.addEventListener("change", (event) => {
    const layerId = `layer-${event.target.dataset.layer}`;
    if (map.getLayer(layerId)) map.setLayoutProperty(layerId, "visibility", event.target.checked ? "visible" : "none");
  });
});
