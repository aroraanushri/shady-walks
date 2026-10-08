import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
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

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function App() {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

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
        <div className="map-card"><div className="map-grid" /><span>Map exploration is next</span><small>Observed imagery will appear here</small></div>
      </section>
      {analysis && <section className="result">
        <div><p className="eyebrow">Observed result · {analysis.filename}</p><h2>{analysis.gvi_percent}% <span>visible greenery</span></h2><p>{analysis.limitation}</p><dl><div><dt>Vegetation pixels</dt><dd>{analysis.vegetation_pixels.toLocaleString()}</dd></div><div><dt>Valid pixels</dt><dd>{analysis.valid_pixels.toLocaleString()}</dd></div><div><dt>Runtime</dt><dd>{analysis.device}</dd></div></dl><p className="labels">Detected classes: {analysis.vegetation_labels.join(", ") || "none observed"}</p></div>
        <img src={`data:image/png;base64,${analysis.overlay_png_base64}`} alt="Segmentation overlay showing observed vegetation" />
      </section>}
      <section id="about" className="about"><p className="eyebrow">Built for honest exploration</p><h2>Observed, not imagined.</h2><p>ShadeShift distinguishes visible vegetation from unknown areas. It never turns a pixel score into a promise about temperature, shade, or comfort.</p></section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
