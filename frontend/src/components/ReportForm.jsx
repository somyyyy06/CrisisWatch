// src/components/ReportForm.jsx
import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "./ReportForm.css";

const API = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

function MiniPicker({ setLatLon }) {
  useMapEvents({
    click(e) {
      setLatLon([e.latlng.lat, e.latlng.lng]);
    },
  });
  return null;
}

export default function ReportForm() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [disasterType, setDisasterType] = useState("Flood");
  const [latLon, setLatLon] = useState([28.6139, 77.209]); // Default: Delhi
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) {
      setStatus("Please attach an image (jpg/png).");
      return;
    }
    setSubmitting(true);
    setStatus("Uploading...");

    try {
      const form = new FormData();
      form.append("title", title);
      form.append("description", description);
      form.append("disaster_type", disasterType);
      form.append("lon", latLon[1]);
      form.append("lat", latLon[0]);
      form.append("file", file);

      const resp = await fetch(`${API}/incidents/`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: form,
      });

      if (!resp.ok) {
        const text = await resp.text();
        setStatus("Upload failed: " + (text || resp.status));
      } else {
        const data = await resp.json();

        const safeLat = parseFloat(data.lat ?? latLon[0]);
        const safeLon = parseFloat(data.lon ?? latLon[1]);

        if (isNaN(safeLat) || isNaN(safeLon)) {
          throw new Error("Invalid coordinates from server");
        }

        const feature = {
          type: "Feature",
          properties: {
            id: data.id,
            title: data.title || title,
            description: data.description || description,
            disaster_type: data.disaster_type || disasterType,
            credibility_score:
              data.credibility_score ?? data.credibilityScore ?? 0.5,
            created_at: data.created_at || new Date().toISOString(),
            author_id: data.user_id || null,
          },
          geometry: {
            type: "Point",
            coordinates: [safeLon, safeLat],
          },
        };

        // Notify global listeners (map and stats)
        window.dispatchEvent(
          new CustomEvent("incident:created", { detail: feature })
        );

        window.dispatchEvent(
          new CustomEvent("incidents:update", {
            detail: { incidents: [feature] },
          })
        );

        setStatus("✅ Uploaded successfully — ID: " + data.id);
        setTitle("");
        setDescription("");
        setFile(null);
      }
    } catch (err) {
      console.error(err);
      setStatus("Error: " + err.message);
    } finally {
      setSubmitting(false);
    }
  }

  const markerIcon = L.icon({
    iconUrl:
      "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
    iconRetinaUrl:
      "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
    shadowUrl:
      "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
  });

  const isValidLatLon =
    Array.isArray(latLon) &&
    latLon.length === 2 &&
    !isNaN(latLon[0]) &&
    !isNaN(latLon[1]);

  return (
    <div className="report-form-container">
      <h2 className="report-form-title">➕ Report New Incident</h2>

      <form className="report-form" onSubmit={handleSubmit}>
        <label>Incident Title</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title..."
          required
        />

        <label>Incident Type</label>
        <select
          value={disasterType}
          onChange={(e) => setDisasterType(e.target.value)}
        >
          <option>Flood</option>
          <option>Earthquake</option>
          <option>Fire</option>
          <option>Crime</option>
          <option>Other</option>
        </select>

        <label>Location (click on the map)</label>
        <div className="map-box">
          <MapContainer center={latLon} zoom={6} className="map">
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <MiniPicker setLatLon={setLatLon} />
            {isValidLatLon && <Marker position={latLon} icon={markerIcon} />}
          </MapContainer>
        </div>

        <small className="coords">
          📍 Lat {latLon[0].toFixed(4)}, Lon {latLon[1].toFixed(4)}
        </small>

        <label>Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Brief description..."
          required
        />

        <label>Attach Image (jpg/png)</label>
        <input
          type="file"
          accept=".jpg,.jpeg,.png"
          onChange={(e) => setFile(e.target.files?.[0])}
          className="file-input"
          required
        />

        <div className="form-actions">
          <button type="submit" className="btn" disabled={submitting}>
            {submitting ? "Submitting..." : "Submit Report"}
          </button>
        </div>

        {status && <div className="form-status">{status}</div>}
      </form>
    </div>
  );
}
