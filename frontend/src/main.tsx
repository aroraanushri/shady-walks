import { StrictMode, useCallback, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./styles.css";

type Analysis = {
  filename: string;
  gvi_percent: number;
  vegetation_pixels: number;
  valid_pixels: number;
  vegetation_labels: string[];
  device: string;
  overlay_png_base64: string;
  limitation: string;
};

type MapillaryImage = {
  id: string;
  longitude: number;
  latitude: number;
  captured_at: number | null;
  thumb_1024_url: string | null;
  attribution: string;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function App() {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [mapError, setMapError] = useState("");
  const [images, setImages] = useState<MapillaryImage[]>([]);
  const [selectedImage, setSelectedImage] = useState<MapillaryImage | null>(null);

  const loadImages = useCallback(async (bounds: L.LatLngBounds) => {
    setMapError("");
    const params = new URLSearchParams({
      west: String(bounds.getWest()),
      south: String(bounds.getSouth()),
      east: String(bounds.getEast()),
      north: String(bounds.getNorth()),
      limit: "10",
    });
    try {
      const response = await fetch(`${API_URL}/api/mapillary/images?${params}`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Imagery lookup failed.");
      setImages(payload.images);
    } catch (reason) {
      setImages([]);
      setMapError(reason instanceof Error ? reason.message : "Imagery lookup failed.");
    }
  }, []);

  async function analyze(file: File) {
    setBusy(true);
    setError("");
    setAnalysis(null);
    const form = new FormData();
    form.append("image", file);
    try {
      const response = await fetch(`${API_URL}/api/analyze`, { method: "POST", body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Analysis failed.");
      setAnalysis(payload);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Analysis failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <nav><strong>ShadeShift</strong><span>Find the greener way home</span><a href="#about">About</a></nav>
      <section className="hero">
        <div>
          <p className="eyebrow">Pune pilot · VIT Pune</p>
          <h1>See the green<br /><em>between the steps.</em></h1>
          <p className="lede">Upload a street-level photograph and measure observed vegetation with a local SegFormer model.</p>
          <label className="upload">
            {busy ? "Analyzing image…" : "Upload a photograph"}
            <input type="file" accept="image/jpeg,image/png,image/webp" disabled={busy} onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) void analyze(file);
            }} />
          </label>
          {error && <p className="error">{error}</p>}
        </div>
        <MapPanel images={images} selectedImage={selectedImage} onSelect={setSelectedImage} onLoad={loadImages} error={mapError} />
      </section>
      {selectedImage?.thumb_1024_url && <section className="image-inspector">
        <p className="eyebrow">Mapillary image · {selectedImage.attribution}</p>
        <img src={selectedImage.thumb_1024_url} alt={`Mapillary street image ${selectedImage.id}`} />
        <p>Captured: {selectedImage.captured_at ? new Date(selectedImage.captured_at).toLocaleString() : "Unknown date"} · Coordinates: {selectedImage.latitude.toFixed(5)}, {selectedImage.longitude.toFixed(5)}</p>
        <button className="secondary" onClick={async () => {
          const response = await fetch(selectedImage.thumb_1024_url!);
          const blob = await response.blob();
          await analyze(new File([blob], `mapillary-${selectedImage.id}.jpg`, { type: blob.type }));
        }}>Analyze this image</button>
      </section>}
      {analysis && <section className="result">
        <div><p className="eyebrow">Observed result · {analysis.filename}</p><h2>{analysis.gvi_percent}% <span>visible greenery</span></h2><p>{analysis.limitation}</p><dl><div><dt>Vegetation pixels</dt><dd>{analysis.vegetation_pixels.toLocaleString()}</dd></div><div><dt>Valid pixels</dt><dd>{analysis.valid_pixels.toLocaleString()}</dd></div><div><dt>Runtime</dt><dd>{analysis.device}</dd></div></dl><p className="labels">Detected classes: {analysis.vegetation_labels.join(", ") || "none observed"}</p></div>
        <img src={`data:image/png;base64,${analysis.overlay_png_base64}`} alt="Segmentation overlay showing observed vegetation" />
      </section>}
      <section id="about" className="about"><p className="eyebrow">Built for honest exploration</p><h2>Observed, not imagined.</h2><p>ShadeShift distinguishes visible vegetation from unknown areas. It never turns a pixel score into a promise about temperature, shade, or comfort.</p></section>
    </main>
  );
}

function MapPanel({ images, selectedImage, onSelect, onLoad, error }: {
  images: MapillaryImage[];
  selectedImage: MapillaryImage | null;
  onSelect: (image: MapillaryImage) => void;
  onLoad: (bounds: L.LatLngBounds) => Promise<void>;
  error: string;
}) {
  const mapElement = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const markers = useRef<L.LayerGroup | null>(null);
  useEffect(() => {
    if (!mapElement.current || map.current) return;
    map.current = L.map(mapElement.current).setView([18.5204, 73.8567], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map.current);
    markers.current = L.layerGroup().addTo(map.current);
    void onLoad(map.current.getBounds());
    return () => { map.current?.remove(); map.current = null; };
  }, [onLoad]);
  useEffect(() => {
    if (!markers.current) return;
    markers.current.clearLayers();
    images.forEach((image) => {
      const marker = L.marker([image.latitude, image.longitude]).bindTooltip(
        `${image.attribution} · ${image.captured_at ? new Date(image.captured_at).toLocaleDateString() : "date unknown"}`
      );
      marker.on("click", () => onSelect(image));
      marker.addTo(markers.current!);
    });
  }, [images, onSelect]);
  return <div className="map-card map-panel">
    <div ref={mapElement} className="leaflet-map" />
    <button className="map-load" onClick={() => map.current && void onLoad(map.current.getBounds())}>Load imagery in this area</button>
    {error ? <p className="map-message error">{error}</p> : <p className="map-message">{images.length ? `${images.length} permitted image locations loaded` : "No imagery loaded for this area"}</p>}
    {selectedImage && <span className="selected-pin">Selected: {selectedImage.id}</span>}
  </div>;
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
