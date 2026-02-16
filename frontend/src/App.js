// src/App.js
import React, { useState, useEffect } from "react";
import MapView from "./components/MapView";
import Topbar from "./components/Topbar";
import Sidebar from "./components/Sidebar";
import RightPanel from "./components/RightPanel";
import ReportModal from "./components/ReportModal";
import AuthModal from "./components/AuthModal";
import TopStats from "./components/TopStats";
import IncidentsSocket from "./components/IncidentsSocket";
import { API_BASE } from "./config/api";
import "./App.css";

export default function App() {
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [authInitialMode, setAuthInitialMode] = useState("login");
  const [metrics, setMetrics] = useState(null);
  const [feed, setFeed] = useState([]); // ✅ new state for live feed

  // Fetch dashboard summary metrics
  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const res = await fetch(`${API_BASE}/metrics/summary`);
        if (!res.ok) return;
        const data = await res.json();
        if (mounted) setMetrics(data);
      } catch (err) {
        // ignore
      }
    }
    load();
    const id = setInterval(load, 20000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, []);

  // ✅ Fetch live feed for RightPanel
  useEffect(() => {
    let mounted = true;
    async function fetchFeed() {
      try {
        const res = await fetch(`${API_BASE}/feed/live`);
        if (!res.ok) return;
        const data = await res.json();
        if (mounted) setFeed(data);
      } catch (err) {
        console.error("Feed fetch failed:", err);
      }
    }
    fetchFeed();
    const id = setInterval(fetchFeed, 60000); // poll every 60s
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, []);

  function openAuth(mode = "login") {
    setAuthInitialMode(mode);
    setIsAuthOpen(true);
  }

  return (
    <div className="app-root">
      <IncidentsSocket />

      <Topbar
        onOpenReport={() => setIsReportOpen(true)}
        onOpenAuth={(mode) => openAuth(mode)}
        metrics={metrics}
      />

      <TopStats metrics={metrics} />

      {/* 🚀 Removed IncidentStatusBar completely */}

      <div className="container">
        <div className="layout">
          <aside className="col sidebar-col">
            <Sidebar />
          </aside>

          <main className="col main-col">
            <div className="map-card">
              <MapView />
            </div>
          </main>

          <aside className="col right-col">
            {/* ✅ Pass feed data to RightPanel */}
            <RightPanel metrics={metrics} feed={feed} />
          </aside>
        </div>
      </div>

      <ReportModal
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
      />

      <AuthModal
        isOpen={isAuthOpen}
        initialMode={authInitialMode}
        onClose={() => setIsAuthOpen(false)}
        onAuth={() => {
          setTimeout(() => {
            fetch(`${API}/metrics/summary`)
              .then((r) => r.json())
              .then((d) => setMetrics(d))
              .catch(() => {});
          }, 200);
        }}
      />
    </div>
  );
}
