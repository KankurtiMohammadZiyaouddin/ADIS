import { useState, useRef, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000';

export default function ImageForensicsPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [apiResult, setApiResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [backendHealth, setBackendHealth] = useState({
    online: false,
    universalLoaded: false,
    xceptionLoaded: false,
    faceXrayLoaded: false,
  });

  const fileInputRef = useRef(null);

  // Check backend health on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/health`)
      .then((res) => res.json())
      .then((data) => {
        setBackendHealth({
          online: true,
          universalLoaded: data.universal_fake_detect_loaded,
          xceptionLoaded: data.xception_loaded,
          faceXrayLoaded: data.face_xray_loaded,
        });
      })
      .catch(() => {
        setBackendHealth({
          online: false,
          universalLoaded: false,
          xceptionLoaded: false,
          faceXrayLoaded: false,
        });
      });
  }, []);

  // Handle file selection
  const handleFileSelect = (file) => {
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setApiResult(null);
    setErrorMessage(null);
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  // Dispatch POST /api/predict
  const handleRunScan = async () => {
    if (!selectedFile) {
      setErrorMessage("Please select or drop an image file first.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('detector', 'all');

    try {
      const response = await fetch(`${API_BASE_URL}/api/predict`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || "Failed to process image.");
      }

      setApiResult(data);
    } catch (err) {
      setErrorMessage(err.message || "Unable to reach backend API. Ensure FastAPI backend is running at http://localhost:8000.");
    } finally {
      setIsLoading(false);
    }
  };

  // Default mock image fallback
  const defaultOriginalImg = "https://lh3.googleusercontent.com/aida-public/AB6AXuAzghDlgaeyUL8F-vm52pY9Frqo-u2hE9ogT3KknCYBy78a-EJPq9K-QTQUCwrUGyLd1QXKenueYYy622vx9HxqcbLK8dcU9uZfSgjcEFfaKg4mwdB1xMBB8rl-dB6N95Tq8_3DMG2hNhN6UjO4FmOiSwkxoSUGHk2mlrEEf7yiwd3pWc17pwib-t8GLYBMEQlz38byJI4GDdb_-iNxIcqPP8BuFEjd3VyQ3FOQixY3NK6DzcEQuTk";
  const defaultHeatmapImg = "https://lh3.googleusercontent.com/aida-public/AB6AXuDLVuqNBofXi32qvbqusPM2RQhejmfFdnCWY48Cz5tqg4jb7coYHLIYMHJd6dHuBqoacebjPD0IjH47Ovga7AmXWRAQYIYoLtcWDHQGotI9rTu2tcWeWk5eBNW2R_c29QzHSzeKo9vAh50rLSSnLVCWI8fmxUN0ngzhaxJ-CJLsEqDooQ7as95fJ_gAjr1ooEytqcvKuvFqBHcx2jQlnl3jeiTIfEZbHEh6NfZ7uuZyU8JJiaF2h-A";

  const displayOriginal = previewUrl || defaultOriginalImg;
  const displayHeatmap = apiResult?.heatmap_url 
    ? `${API_BASE_URL}${apiResult.heatmap_url}` 
    : defaultHeatmapImg;

  const isFake = apiResult?.prediction === 'AI_GENERATED' || apiResult?.prediction === 'FAKE';
  const isReal = apiResult?.prediction === 'REAL' || apiResult?.prediction === 'REAL_PHOTO';
  const confidenceVal = apiResult ? apiResult.confidence : 94.72;

  const univRes = apiResult?.results?.universal_fake_detect;
  const xcRes = apiResult?.results?.xception;
  const xrayRes = apiResult?.results?.face_xray;

  return (
    <main className="flex-1 overflow-auto bg-background p-gutter flex gap-gutter">
      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleInputChange}
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
      />

      {/* Center Canvas: Image Comparison */}
      <div className="flex-1 flex flex-col gap-gutter min-w-0">
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg flex-1 flex flex-col overflow-hidden">
          <div className="h-10 border-b border-outline-variant bg-surface-container flex items-center justify-between px-4 shrink-0">
            <span className="text-label-md text-on-surface flex items-center gap-2">
              <span>Analysis Canvas: {selectedFile ? selectedFile.name : 'EV-882.jpg'}</span>
              <span 
                className={`w-2.5 h-2.5 rounded-full ${backendHealth.online ? 'bg-green-500' : 'bg-amber-500'}`} 
                title={backendHealth.online ? 'Backend API Online' : 'Backend Offline'} 
              />
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-2.5 py-1 bg-surface-container-highest hover:bg-surface-variant rounded text-label-sm text-on-surface flex items-center gap-1 transition-colors"
                title="Select Image File"
              >
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>upload_file</span>
                Select Image
              </button>
              <button className="p-1 hover:bg-surface-container-highest rounded text-on-surface-variant"><span className="material-symbols-outlined" style={{ fontSize: 18 }}>zoom_in</span></button>
              <button className="p-1 hover:bg-surface-container-highest rounded text-on-surface-variant"><span className="material-symbols-outlined" style={{ fontSize: 18 }}>zoom_out</span></button>
            </div>
          </div>

          {/* Drag & Drop Canvas Area */}
          <div 
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="flex-1 flex gap-4 p-4 min-h-0 bg-surface relative"
          >
            {/* Original Image Container */}
            <div className="flex-1 flex flex-col border border-outline-variant rounded bg-surface-container-lowest relative overflow-hidden group">
              <div className="absolute top-2 left-2 bg-on-surface/80 text-surface-container-lowest px-2 py-1 rounded text-label-sm z-10">
                Uploaded Image (Full Resolution)
              </div>
              <img
                className="w-full h-full object-contain p-2"
                alt="Selected image under analysis"
                src={displayOriginal}
              />
              <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-primary text-on-primary px-3 py-1.5 rounded text-label-sm shadow-md"
                >
                  Change Image
                </button>
              </div>
            </div>

            {/* Boundary / Forensic Heatmap Container */}
            <div className="flex-1 flex flex-col border border-outline-variant rounded bg-surface-container-lowest relative overflow-hidden">
              <div className="absolute top-2 left-2 bg-on-surface/80 text-surface-container-lowest px-2 py-1 rounded text-label-sm z-10">
                Forensic Boundary Heatmap
              </div>
              {isLoading ? (
                <div className="w-full h-full flex flex-col items-center justify-center gap-3 bg-surface-container-lowest">
                  <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                  <span className="text-body-sm text-on-surface-variant">Running UniversalFakeDetect, Xception & Face-X-Ray...</span>
                </div>
              ) : (
                <img
                  className="w-full h-full object-contain p-2 filter contrast-125 saturate-150"
                  alt="Forensic boundary heatmap visualization"
                  src={displayHeatmap}
                />
              )}
            </div>
          </div>
        </div>

        {/* Secondary Panel: Active Detectors & Models */}
        <div className="h-48 flex gap-gutter shrink-0">
          <div className="flex-1 bg-surface-container-lowest border border-outline-variant rounded-lg flex flex-col overflow-hidden">
            <div className="h-8 border-b border-outline-variant bg-surface-container flex items-center px-4 text-label-md text-on-surface">
              Active Detectors & Architecture Summary
            </div>
            <div className="p-3 overflow-y-auto">
              <table className="w-full text-body-sm font-body-sm text-left">
                <tbody>
                  <tr className="border-b border-surface-variant">
                    <th className="py-1 text-on-surface-variant font-medium w-1/3">1. General AI Image Detector</th>
                    <td className="py-1 text-primary font-medium">UniversalFakeDetect (CLIP ViT-L/14, CVPR 2023)</td>
                  </tr>
                  <tr className="border-b border-surface-variant">
                    <th className="py-1 text-on-surface-variant font-medium">2. Deepfake Face Detector</th>
                    <td className="py-1 text-on-surface font-medium">XceptionNet (FaceForensics++)</td>
                  </tr>
                  <tr className="border-b border-surface-variant">
                    <th className="py-1 text-on-surface-variant font-medium">3. Face Manipulation Detector</th>
                    <td className="py-1 text-on-surface font-medium">Face-X-Ray (Boundary Artifact Analysis)</td>
                  </tr>
                  <tr>
                    <th className="py-1 text-on-surface-variant font-medium">System Status</th>
                    <td className="py-1 text-on-surface">
                      {apiResult ? apiResult.message : (selectedFile ? "File loaded. Click 'Run Deepfake Scan'." : "Select or drop any image (photo, landscape, art, face).")}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Right Sidebar: Analysis Panel */}
      <div className="w-80 flex flex-col gap-gutter shrink-0">
        {/* Error Alert Banner if present */}
        {errorMessage && (
          <div className="bg-error-container/30 border border-error p-3 rounded-lg text-body-sm text-on-surface flex items-start gap-2">
            <span className="material-symbols-outlined text-error shrink-0" style={{ fontSize: 18 }}>error</span>
            <div className="flex-1">
              <span className="font-semibold block text-error">Detection Error</span>
              {errorMessage}
            </div>
          </div>
        )}

        {/* AI IMAGE ANALYSIS Card */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-4">
          <h3 className="text-headline-sm font-headline-sm text-on-surface mb-1">AI IMAGE ANALYSIS</h3>
          <p className="text-label-sm text-on-surface-variant mb-4">
            Multi-Model Evaluation Pipeline
          </p>

          {/* Overall Prediction Badge */}
          <div className="mb-4 p-3 rounded-lg border flex items-center justify-between bg-surface">
            <div>
              <div className="text-label-sm text-on-surface-variant uppercase tracking-wider">Overall Verdict</div>
              <div className={`text-title-lg font-bold ${isFake ? 'text-error' : isReal ? 'text-green-600' : 'text-on-surface'}`}>
                {apiResult ? (isFake ? 'AI GENERATED / FAKE' : 'AUTHENTIC PHOTO') : 'PENDING'}
              </div>
            </div>
            <div className={`px-2.5 py-1 rounded text-label-sm font-semibold ${isFake ? 'bg-error-container text-on-error-container' : isReal ? 'bg-green-100 text-green-800' : 'bg-surface-variant text-on-surface-variant'}`}>
              {isFake ? 'Likely Manipulated' : isReal ? 'Likely Authentic' : 'Ready'}
            </div>
          </div>

          {/* Overall Confidence Bar */}
          <div className="mb-4">
            <div className="flex justify-between items-end mb-1">
              <span className="text-label-md text-on-surface-variant">Confidence Score</span>
              <span className={`text-title-lg font-title-lg ${isFake ? 'text-error' : 'text-primary'}`}>
                {confidenceVal.toFixed(2)}%
              </span>
            </div>
            <div className="w-full bg-surface-variant rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${isFake ? 'bg-error' : 'bg-primary'}`}
                style={{ width: `${confidenceVal}%` }}
              />
            </div>
          </div>

          {/* Individual Detector Cards Breakdown */}
          <div className="space-y-2 mb-4">
            <h4 className="text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold border-b pb-1">
              Detector Breakdown
            </h4>

            {/* 1. UniversalFakeDetect Card */}
            <div className="p-2.5 rounded border border-outline-variant bg-surface space-y-1 text-body-sm">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-on-surface">UniversalFakeDetect</span>
                <span className={`font-bold ${univRes?.prediction === 'AI_GENERATED' ? 'text-error' : 'text-green-600'}`}>
                  {univRes ? (univRes.prediction === 'AI_GENERATED' ? 'AI GENERATED' : 'REAL PHOTO') : 'Ready'}
                </span>
              </div>
              <div className="text-label-sm text-on-surface-variant flex justify-between">
                <span>Arch: CLIP ViT-L/14</span>
                <span>Conf: {univRes ? `${univRes.confidence.toFixed(1)}%` : '--'}</span>
              </div>
            </div>

            {/* 2. XceptionNet Card */}
            <div className="p-2.5 rounded border border-outline-variant bg-surface space-y-1 text-body-sm">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-on-surface">XceptionNet</span>
                <span className={`font-bold ${xcRes?.prediction === 'FAKE' ? 'text-error' : 'text-green-600'}`}>
                  {xcRes ? xcRes.prediction : 'Ready'}
                </span>
              </div>
              <div className="text-label-sm text-on-surface-variant flex justify-between">
                <span>Model: FaceForensics++</span>
                <span>Conf: {xcRes ? `${xcRes.confidence.toFixed(1)}%` : '--'}</span>
              </div>
            </div>

            {/* 3. Face-X-Ray Card */}
            <div className="p-2.5 rounded border border-outline-variant bg-surface space-y-1 text-body-sm">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-on-surface">Face-X-Ray</span>
                <span className={`font-bold ${xrayRes?.prediction === 'FAKE' ? 'text-error' : 'text-green-600'}`}>
                  {xrayRes ? xrayRes.prediction : 'Ready'}
                </span>
              </div>
              <div className="text-label-sm text-on-surface-variant flex justify-between">
                <span>Boundary Analysis</span>
                <span>Conf: {xrayRes ? `${xrayRes.confidence.toFixed(1)}%` : '--'}</span>
              </div>
            </div>
          </div>

          {/* Model Analysis Text Message */}
          {apiResult && (
            <div className={`p-3 rounded border text-body-sm ${isFake ? 'bg-error-container/20 border-error-container text-on-surface' : 'bg-green-50 border-green-200 text-on-surface'}`}>
              <div className="font-semibold mb-1 flex items-center gap-1">
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  {isFake ? 'warning' : 'verified'}
                </span>
                {isFake ? 'Manipulation Warning' : 'Authenticity Notice'}
              </div>
              <p>{apiResult.message}</p>
            </div>
          )}
        </div>

        {/* Scan Action Card */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-4 flex-1">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-label-md text-on-surface font-semibold">Inference Control</h3>
            <button
              onClick={handleRunScan}
              disabled={isLoading}
              className="bg-secondary text-on-secondary px-3.5 py-1.5 rounded text-label-sm hover:opacity-90 transition-opacity flex items-center gap-1 disabled:opacity-50 shadow-sm"
            >
              {isLoading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>search</span>
                  Run Deepfake Scan
                </>
              )}
            </button>
          </div>

          <div className="text-body-sm text-on-surface-variant bg-surface p-3 rounded border border-outline-variant">
            <div className="font-medium text-on-surface mb-1">Coverage Scope:</div>
            <ul className="list-disc list-inside space-y-1 text-label-sm">
              <li>Universal fake detection for landscapes, art, photos & faces</li>
              <li>Face-swap & facial deepfake identification</li>
              <li>Pixel-level boundary anomaly mapping</li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  );
}
