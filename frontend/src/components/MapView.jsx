// src/components/MapView.jsx
import React, { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";

const API = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";
const WS_BASE = process.env.REACT_APP_WS_URL || API; // e.g. http://127.0.0.1:8000

// severity thresholds by credibility_score
function severityFromCred(score = 0.5) {
  // tweak these thresholds as you want:
  // < 0.4 -> critical, 0.4 - 0.7 -> moderate, >=0.7 -> resolved (high confidence)
  if (score < 0.4) return "critical";
  if (score < 0.7) return "moderate";
  return "resolved";
}

function colorForSeverity(s) {
  if (s === "critical") return "#ff5858";
  if (s === "moderate") return "#f39c12";
  if (s === "resolved") return "#27ae60";
  return "#999";
}

function makeDivIcon(color) {
  return L.divIcon({
    className: "cw-marker",
    html: `<span style="
      display:inline-block;
      width:16px;
      height:16px;
      border-radius:50%;
      background:${color};
      box-shadow:0 0 0 6px rgba(0,0,0,0.25);
      border: 2px solid rgba(255,255,255,0.08)
    "></span>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

function toFeature(inc) {
  // Accept either GeoJSON feature or API incident object
  if (!inc) return null;
  if (inc.type === "Feature" && inc.geometry) return inc;
  // else assume object with lat/lon fields
  const lon = parseFloat(inc.lon ?? inc.longitude ?? (inc.geometry?.coordinates?.[0]));
  const lat = parseFloat(inc.lat ?? inc.latitude ?? (inc.geometry?.coordinates?.[1]));
  return {
    type: "Feature",
    geometry: { type: "Point", coordinates: [lon, lat] },
    properties: {
      id: inc.id,
      title: inc.title,
      description: inc.description,
      disaster_type: inc.disaster_type ?? inc.disasterType,
      credibility_score: parseFloat(inc.credibility_score ?? inc.credibilityScore ?? 0.5),
      created_at: inc.created_at ?? inc.createdAt ?? inc.properties?.created_at,
    },
  };
}

export default function MapView() {
  const [all, setAll] = useState([]); // full features
  const [visible, setVisible] = useState([]); // features after filters
  const [filters, setFilters] = useState({ types: [], severities: [], timeRange: "all" });
  const mapRef = useRef(null);

  useEffect(() => {
    loadIncidents();

    // filter change events from Sidebar
    const onFilter = (e) => {
      const f = e.detail || {};
      setFilters((prev) => {
        const merged = { ...prev, ...f };
        applyFilters(all, merged);
        return merged;
      });
    };
    window.addEventListener("map:filter", onFilter);

    // new incident created
    const onCreated = (e) => {
      const feature = toFeature(e.detail);
      if (!feature) return;
      setAll((prev) => {
        const next = [feature, ...prev];
        applyFilters(next, filters);
        // update counts
        publishCounts(next);
        return next;
      });
    };
    window.addEventListener("incident:created", onCreated);

    // zoom to incident event
    const onZoom = (ev) => {
      const d = ev.detail || {};
      if (mapRef.current && d.lat && d.lon) {
        mapRef.current.flyTo([d.lat, d.lon], d.zoom ?? 13, { duration: 0.8 });
      }
    };
    window.addEventListener("map:zoomTo", onZoom);

    return () => {
      window.removeEventListener("map:filter", onFilter);
      window.removeEventListener("incident:created", onCreated);
      window.removeEventListener("map:zoomTo", onZoom);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadIncidents() {
    try {
      const resp = await fetch(`${API}/incidents/geojson`);
      if (!resp.ok) {
        console.warn("Couldn't fetch incidents geojson:", resp.status);
        return;
      }
      const data = await resp.json();
      // data expected to be FeatureCollection
      const features = (data.features || []).map((f) => {
        // ensure credibility_score exists as numeric
        if (f.properties) {
          f.properties.credibility_score = parseFloat(f.properties.credibility_score ?? f.properties.credibility_score ?? 0.5);
        }
        return f;
      });
      setAll(features);
      applyFilters(features, filters);
      publishCounts(features);

      // try websocket (best-effort)
      tryWebsocket();
    } catch (err) {
      console.error("Error loading incidents:", err);
    }
  }

  function publishCounts(features) {
    const counts = { critical: 0, moderate: 0, resolved: 0, total: (features?.length || 0) };
    (features || []).forEach((f) => {
      const cred = parseFloat(f.properties?.credibility_score ?? 0.5);
      const sev = severityFromCred(cred);
      counts[sev] = (counts[sev] || 0) + 1;
    });
    window.dispatchEvent(new CustomEvent("incidents:update", { detail: { counts, incidents: features } }));
  }

  function applyFilters(features, f) {
    const { types = [], severities = [], timeRange = "all" } = f || {};
    const now = Date.now();
    const filtered = (features || []).filter((feat) => {
      if (!feat || !feat.properties || !feat.geometry) return false;
      // type filter
      if (types.length && !types.includes(feat.properties.disaster_type)) return false;
      // severity filter
      const cred = parseFloat(feat.properties?.credibility_score ?? 0.5);
      const sev = severityFromCred(cred);
      if (severities.length && !severities.includes(sev)) return false;
      // time range check
      if (timeRange && timeRange !== "all") {
        const created = new Date(feat.properties?.created_at || Date.now()).getTime();
        let cutoff = 0;
        if (timeRange === "24h") cutoff = now - 24 * 3600 * 1000;
        if (timeRange === "3d") cutoff = now - 3 * 24 * 3600 * 1000;
        if (timeRange === "1w") cutoff = now - 7 * 24 * 3600 * 1000;
        if (timeRange === "1m") cutoff = now - 30 * 24 * 3600 * 1000;
        if (cutoff && created < cutoff) return false;
      }
      return true;
    });
    setVisible(filtered);
  }

  // best-effort websocket consumer for realtime (if backend exposes /ws/incidents)
  function tryWebsocket() {
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const wsProto = WS_BASE.startsWith("https") ? "wss" : "ws";
      const base = WS_BASE.replace(/^https?:\/\//, "");
      const wsUrl = `${wsProto}://${base}/ws/incidents${token ? `?token=${token}` : ""}`;
      const ws = new WebSocket(wsUrl);
      ws.onmessage = (ev) => {
        try {
          const payload = JSON.parse(ev.data);
          // payload should be incident-like
          const feature = toFeature(payload);
          if (!feature) return;
          setAll((prev) => {
            const next = [feature, ...prev];
            applyFilters(next, filters);
            publishCounts(next);
            return next;
          });
        } catch (err) {
          /* ignore parse errors */
        }
      };
      ws.onopen = () => console.debug("WS connected:", wsUrl);
      ws.onclose = () => console.debug("WS disconnected");
      ws.onerror = () => console.debug("WS error");
    } catch (err) {
      // ignore
    }
  }

  // update counts whenever `all` changes (e.g., initial load)
  useEffect(() => {
    applyFilters(all, filters);
    publishCounts(all);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [all]);

  // map center default
  const defaultCenter = [28.6139, 77.2090];

  // create icon cache
  const iconCache = {};
  function getIconForFeature(f) {
    const cred = parseFloat(f.properties?.credibility_score ?? 0.5);
    const sev = severityFromCred(cred);
    const color = colorForSeverity(sev);
    if (!iconCache[color]) iconCache[color] = makeDivIcon(color);
    return iconCache[color];
  }

  return (
    <div style={{ height: "100%", width: "100%" }}>
      <MapContainer
        center={defaultCenter}
        zoom={6}
        style={{ height: "100%", width: "100%" }}
        whenCreated={(map) => { mapRef.current = map; }}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {visible.map((feat) => {
          const coords = feat.geometry?.coordinates || [0, 0];
          const lon = parseFloat(coords[0]);
          const lat = parseFloat(coords[1]);
          const id = feat.properties?.id ?? Math.random().toString(36).slice(2, 9);
          const icon = getIconForFeature(feat);
          return (
            <Marker key={id} position={[lat, lon]} icon={icon}>
              <Popup>
                <div style={{ minWidth: 220 }}>
                  <strong>{feat.properties?.title ?? "Untitled"}</strong>
                  <div style={{ fontSize: 13, color: "#c8d3e6", marginTop: 6 }}>{feat.properties?.description}</div>
                  <div style={{ marginTop: 8, fontSize: 12 }}>
                    <b>Type:</b> {feat.properties?.disaster_type ?? "—"}
                    <br />
                    <b>Credibility:</b> {(feat.properties?.credibility_score ?? 0).toFixed(2)}
                    <br />
                    <b>When:</b> {new Date(feat.properties?.created_at || Date.now()).toLocaleString()}
                  </div>
                  <div style={{ marginTop: 8 }}>
                    <button
                      className="btn ghost"
                      onClick={() => {
                        // zoom to this marker
                        if (mapRef.current) mapRef.current.flyTo([lat, lon], 13, { duration: 0.6 });
                        // also emit event so Sidebar can highlight
                        window.dispatchEvent(new CustomEvent("recent:select", { detail: { id: feat.properties?.id } }));
                      }}
                    >
                      Focus
                    </button>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
