// src/components/ReportForm.jsx
import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "./ReportForm.css";
import { API_BASE } from "../config/api";

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
  const [latLon, setLatLon] = useState([28.6139, 77.209]);
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

      const resp = await fetch(`${API_BASE}/incidents/submit`, {
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

        window.dispatchEvent(
          new CustomEvent("incident:created", { detail: feature })
        );

        window.dispatchEvent(
          new CustomEvent("incidents:update", {
            detail: { incidents: [feature] },
          })
        );

        setStatus("Uploaded successfully. ID: " + data.id);
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
      <div className="report-header">
        <div className="report-icon">+</div>
        <div>
          <h2 className="report-form-title">Report new incident</h2>
          <p className="report-subtitle">
            Share verified details to alert the response team.
          </p>
        </div>
      </div>

      <form className="report-form" onSubmit={handleSubmit}>
        <div className="report-section">
          <p className="section-title">Incident details</p>
          <div className="report-grid">
            <div className="report-field">
              <label>Incident title</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Power outage near downtown"
                required
              />
            </div>

            <div className="report-field">
              <label>Incident type</label>
              <select
                value={disasterType}
                onChange={(e) => setDisasterType(e.target.value)}
              >
                <option>Flood</option>
                <option>Earthquake</option>
                <option>Fire</option>
                <option>Crime</option>
                <option>Traffic</option>
                <option>Power Outage</option>
                <option>Other</option>
              </select>
            </div>
          </div>
        </div>

        <div className="report-section">
          <p className="section-title">Location</p>
          <label>Click on the map to drop a pin</label>
          <div className="map-box">
            <MapContainer center={latLon} zoom={6} className="map">
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <MiniPicker setLatLon={setLatLon} />
              {isValidLatLon && <Marker position={latLon} icon={markerIcon} />}
            </MapContainer>
          </div>

          <div className="coords-row">
            <span>Lat {latLon[0].toFixed(4)}</span>
            <span>Lon {latLon[1].toFixed(4)}</span>
          </div>
        </div>

        <div className="report-section">
          <p className="section-title">Description and evidence</p>
          <div className="report-field">
            <label>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is happening, who is impacted, and when did it start?"
              required
            />
          </div>

          <div className="report-field">
            <label>Upload photo</label>
            <div className="file-input">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              <span>{file ? file.name : "Attach a clear image (jpg/png)"}</span>
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button className="btn" type="submit" disabled={submitting}>
            {submitting ? "Submitting..." : "Submit report"}
          </button>
          {status ? <div className="form-status">{status}</div> : null}
        </div>
      </form>
    </div>
  );
}
