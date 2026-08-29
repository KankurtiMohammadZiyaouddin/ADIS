import { useState, useRef, useEffect } from 'react';
import { checkBackendHealth, predictDeepfakeImage, getHeatmapFullUrl } from '../services/detectionApi';

export default function ImageForensicsPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  
  // 5-Stage State Machine: 'IDLE' | 'IMAGE_SELECTED' | 'ANALYZING' | 'COMPLETED' | 'ERROR'
  const [analysisState, setAnalysisState] = useState('IDLE');
  
  const [apiResult, setApiResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [backendHealth, setBackendHealth] = useState({
    checking: true,
    online: false,
    modelLoaded: false,
    universalLoaded: false,
    xceptionLoaded: false,
    faceXrayLoaded: false,
  });

  const fileInputRef = useRef(null);

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth().then((res) => {
      if (res.online && res.data) {
        const models = res.data.models || {};
        setBackendHealth({
          checking: false,
          online: true,
          modelLoaded: res.data.model_loaded,
          universalLoaded: models.universal_fake_detect?.loaded ?? res.data.universal_fake_detect_loaded ?? false,
          xceptionLoaded: models.xceptionnet?.loaded ?? res.data.xception_loaded ?? false,
          faceXrayLoaded: models.face_xray?.loaded ?? res.data.face_xray_loaded ?? false,
        });
      } else {
        setBackendHealth({
          checking: false,
          online: false,
          modelLoaded: false,
          universalLoaded: false,
          xceptionLoaded: false,
          faceXrayLoaded: false,
        });
      }
    });
  }, []);

  // Reset function when selecting a new image
  const handleFileSelect = (file) => {
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    
    // Strict State Reset
    setAnalysisState('IMAGE_SELECTED');
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

  // Dispatch API inference scan across all 3 models on button click ONLY
  const handleRunScan = async () => {
    if (!selectedFile) {
      setErrorMessage("Please upload or select an image file first.");
      setAnalysisState('ERROR');
      return;
    }

    setAnalysisState('ANALYZING');
    setErrorMessage(null);
    setApiResult(null);

    try {
      const data = await predictDeepfakeImage(selectedFile, 'all');
      
      if (data.success && data.analysis_completed) {
        setApiResult(data);
        setAnalysisState('COMPLETED');
      } else {
        throw new Error(data.error || data.message || "Image analysis failed.");
      }
    } catch (err) {
      setErrorMessage(err.message || "Unable to connect to the detection server.");
      setAnalysisState('ERROR');
    }
  };

  // State derivation
  const isIdle = analysisState === 'IDLE';
  const isImageSelected = analysisState === 'IMAGE_SELECTED';
  const isAnalyzing = analysisState === 'ANALYZING';
  const isCompleted = analysisState === 'COMPLETED';
  const isError = analysisState === 'ERROR';

  const heatmapDisplayUrl = isCompleted && apiResult?.heatmap_url ? getHeatmapFullUrl(apiResult.heatmap_url) : null;
  const univRes = isCompleted ? apiResult?.results?.universal_fake_detect : null;
  const xcRes = isCompleted ? apiResult?.results?.xceptionnet : null;
  const xrayRes = isCompleted ? apiResult?.results?.face_xray : null;
  const overall = isCompleted ? apiResult?.overall_assessment : null;
  const timing = isCompleted ? apiResult?.timing : null;

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

      {/* Center Canvas: Image & Forensic Heatmap */}
      <div className="flex-1 flex flex-col gap-gutter min-w-0">
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg flex-1 flex flex-col overflow-hidden">
          <div className="h-10 border-b border-outline-variant bg-surface-container flex items-center justify-between px-4 shrink-0">
            <span className="text-label-md text-on-surface flex items-center gap-2">
              <span>Multi-Model Forensic Canvas: {selectedFile ? selectedFile.name : 'No image loaded'}</span>
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
            </div>
          </div>

          {/* Canvas Drag & Drop Area */}
          <div 
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="flex-1 flex gap-4 p-4 min-h-0 bg-surface relative"
          >
            {/* Original Uploaded Image Preview */}
            <div className="flex-1 flex flex-col border border-outline-variant rounded bg-surface-container-lowest relative overflow-hidden group">
              <div className="absolute top-2 left-2 bg-on-surface/80 text-surface-container-lowest px-2 py-1 rounded text-label-sm z-10">
                Uploaded Image Preview
              </div>
              
              {previewUrl ? (
                <img
                  className="w-full h-full object-contain p-2"
                  alt="Selected subject under analysis"
                  src={previewUrl}
                />
              ) : (
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full h-full flex flex-col items-center justify-center gap-2 text-on-surface-variant cursor-pointer hover:bg-surface-container-highest/40 transition-colors p-4"
                >
                  <span className="material-symbols-outlined text-outline" style={{ fontSize: 48 }}>add_photo_alternate</span>
                  <span className="text-body-md font-medium">Click or Drag & Drop Image Here</span>
                  <span className="text-label-sm text-outline">Supported formats: JPG, PNG, WEBP (Max 10MB)</span>
                </div>
              )}

              {previewUrl && (
                <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-primary text-on-primary px-3 py-1.5 rounded text-label-sm shadow-md"
                  >
                    Change Image
                  </button>
                </div>
              )}
            </div>

            {/* Forensic Heatmap Visualization Panel */}
            <div className="flex-1 flex flex-col border border-outline-variant rounded bg-surface-container-lowest relative overflow-hidden">
              <div className="absolute top-2 left-2 bg-on-surface/80 text-surface-container-lowest px-2 py-1 rounded text-label-sm z-10">
                Face-X-Ray Boundary Heatmap
              </div>

              {isAnalyzing ? (
                <div className="w-full h-full flex flex-col items-center justify-center gap-3 bg-surface-container-lowest">
                  <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                  <span className="text-body-sm font-medium text-on-surface">Running 3 deepfake detection models...</span>
                  <span className="text-label-sm text-on-surface-variant">UniversalFakeDetect • XceptionNet • Face-X-Ray</span>
                </div>
              ) : heatmapDisplayUrl ? (
                <img
                  className="w-full h-full object-contain p-2 filter contrast-125 saturate-150"
                  alt="Forensic boundary heatmap visualization"
                  src={heatmapDisplayUrl}
                />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center gap-2 text-on-surface-variant p-4 text-center">
                  <span className="material-symbols-outlined text-outline" style={{ fontSize: 40 }}>query_stats</span>
                  <span className="text-body-sm font-medium">
                    {xrayRes?.status === 'not_applicable' ? "Visualization Not Applicable (No Face Found)" : "Visualization Pending"}
                  </span>
                  <span className="text-label-sm text-outline max-w-xs">
                    {isIdle && "Select an image and click 'Analyze Image' to run all 3 detection models."}
                    {isImageSelected && "Click 'Analyze Image' to execute UniversalFakeDetect, XceptionNet, and Face-X-Ray."}
                    {isCompleted && xrayRes?.status === 'not_applicable' && "Face-X-Ray boundary map requires a face in the target image."}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Secondary Metadata & Model Status Panel */}
        <div className="h-44 flex gap-gutter shrink-0">
          <div className="flex-1 bg-surface-container-lowest border border-outline-variant rounded-lg flex flex-col overflow-hidden">
            <div className="h-8 border-b border-outline-variant bg-surface-container flex items-center justify-between px-4 text-label-md text-on-surface font-semibold">
              <span>System & Analysis Metadata</span>
              {isCompleted && timing && (
                <span className="text-label-sm text-primary font-normal">
                  Inference Timing: Universal ({timing.universal_ms}ms) | XceptionNet ({timing.xception_ms}ms) | Face-X-Ray ({timing.face_xray_ms}ms) | Total ({(timing.total_ms / 1000).toFixed(2)}s)
                </span>
              )}
            </div>
            <div className="p-3 overflow-y-auto">
              <table className="w-full text-body-sm font-body-sm text-left">
                <tbody>
                  <tr className="border-b border-surface-variant">
                    <th className="py-1 text-on-surface-variant font-medium w-1/3">Target Image File</th>
                    <td className="py-1 text-on-surface">{selectedFile ? selectedFile.name : 'None selected'}</td>
                  </tr>
                  <tr className="border-b border-surface-variant">
                    <th className="py-1 text-on-surface-variant font-medium">Detector Suite</th>
                    <td className="py-1 text-primary font-medium">UniversalFakeDetect + XceptionNet + Face-X-Ray (3 Independent Models)</td>
                  </tr>
                  <tr className="border-b border-surface-variant">
                    <th className="py-1 text-on-surface-variant font-medium">Backend Server Status</th>
                    <td className="py-1 text-on-surface">
                      {backendHealth.checking ? (
                        <span className="text-primary font-medium animate-pulse">Checking backend...</span>
                      ) : backendHealth.online ? (
                        <span className="text-green-600 font-medium">Online (FastAPI http://localhost:8000)</span>
                      ) : (
                        <span className="text-amber-600 font-medium">Offline / Server Unavailable</span>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <th className="py-1 text-on-surface-variant font-medium">Analysis Pipeline Status</th>
                    <td className="py-1 text-on-surface font-medium">
                      {isIdle && "No image loaded. Please select an image."}
                      {isImageSelected && "Image ready for analysis. Click 'Analyze Image' below."}
                      {isAnalyzing && <span className="text-primary animate-pulse">Running 3 detection models in parallel...</span>}
                      {isCompleted && <span className="text-green-600">All 3 model predictions completed in {(apiResult.timing?.total_ms / 1000).toFixed(2)}s</span>}
                      {isError && <span className="text-error">{errorMessage || "Analysis failed."}</span>}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Right Sidebar: Multi-Model Results & Verdict Panel */}
      <div className="w-96 flex flex-col gap-gutter shrink-0 overflow-y-auto">
        {/* Error Alert Banner */}
        {isError && (
          <div className="bg-error-container/30 border border-error p-3 rounded-lg text-body-sm text-on-surface flex items-start gap-2">
            <span className="material-symbols-outlined text-error shrink-0" style={{ fontSize: 18 }}>error</span>
            <div className="flex-1">
              <span className="font-semibold block text-error">Detection Error</span>
              {errorMessage || "Unable to connect to the detection server."}
            </div>
          </div>
        )}

        {/* OVERALL ASSESSMENT CARD */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-4">
          <h3 className="text-headline-sm font-headline-sm text-on-surface mb-1">OVERALL ASSESSMENT</h3>
          <p className="text-label-sm text-on-surface-variant mb-3">
            Transparent Multi-Detector Evidence Synthesis
          </p>

          {/* Verdict Status Badge */}
          <div className="mb-3 p-3 rounded-lg border flex items-center justify-between bg-surface">
            <div>
              <div className="text-label-sm text-on-surface-variant uppercase tracking-wider">Final Verdict</div>
              <div className={`text-title-md font-bold ${
                isCompleted 
                  ? (overall?.verdict === 'LIKELY MANIPULATED' || overall?.verdict === 'AI GENERATED IMAGE'
                      ? 'text-error' 
                      : (overall?.verdict === 'LIKELY AUTHENTIC' ? 'text-green-600' : 'text-amber-600'))
                  : 'text-on-surface-variant'
              }`}>
                {isCompleted ? overall?.verdict : 'NOT ANALYZED'}
              </div>
            </div>

            <div className={`px-2 py-1 rounded text-label-sm font-semibold ${
              isCompleted 
                ? (overall?.verdict === 'LIKELY MANIPULATED' || overall?.verdict === 'AI GENERATED IMAGE'
                    ? 'bg-error-container text-on-error-container' 
                    : (overall?.verdict === 'LIKELY AUTHENTIC' ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'))
                : 'bg-surface-variant text-on-surface-variant'
            }`}>
              {isCompleted ? overall?.verdict : (isAnalyzing ? 'Analyzing...' : isImageSelected ? 'Ready' : 'No Image')}
            </div>
          </div>

          {/* Summary & Evidence List */}
          {isCompleted && overall && (
            <div className="space-y-2 mb-3">
              <p className="text-body-sm text-on-surface bg-surface p-2.5 rounded border border-outline-variant font-medium">
                {overall.summary}
              </p>
              {overall.evidence && overall.evidence.length > 0 && (
                <div className="space-y-1">
                  <span className="text-label-sm text-on-surface-variant font-semibold uppercase tracking-wider block">Evidence Breakdown:</span>
                  <ul className="space-y-1 text-label-sm">
                    {overall.evidence.map((ev, idx) => (
                      <li key={idx} className="p-1.5 rounded bg-surface border border-outline-variant text-on-surface">
                        {ev}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* THREE INDIVIDUAL DETECTOR CARDS */}
        <div className="space-y-3">
          <h4 className="text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">
            Individual Model Results (3 Detectors)
          </h4>

          {/* DETECTOR CARD 1: UniversalFakeDetect */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-3.5 space-y-2">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-label-md text-on-surface font-bold block">1. UniversalFakeDetect</span>
                <span className="text-label-sm text-on-surface-variant">General AI Image Detection (CLIP ViT-L/14)</span>
              </div>
              <span className={`px-2 py-0.5 rounded text-label-sm font-semibold ${
                univRes?.status === 'completed'
                  ? 'bg-blue-100 text-blue-800'
                  : (univRes?.status === 'error' ? 'bg-error-container text-on-error-container' : 'bg-surface-variant text-on-surface-variant')
              }`}>
                {univRes ? univRes.status.toUpperCase() : 'READY'}
              </span>
            </div>

            {isCompleted && univRes?.status === 'completed' && (
              <div className="p-2 rounded bg-surface border border-outline-variant flex justify-between items-center text-body-sm">
                <span className="text-on-surface font-medium">Prediction:</span>
                <span className={`font-bold ${univRes.prediction === 'AI_GENERATED' ? 'text-error' : 'text-green-600'}`}>
                  {univRes.prediction === 'AI_GENERATED' ? 'AI GENERATED' : 'REAL PHOTO'} ({univRes.confidence.toFixed(1)}%)
                </span>
              </div>
            )}

            {isCompleted && univRes?.status === 'error' && (
              <div className="p-2 rounded bg-error-container/20 border border-error-container text-error text-label-sm">
                Error: {univRes.error || "Model checkpoint missing"}
              </div>
            )}
          </div>

          {/* DETECTOR CARD 2: XceptionNet */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-3.5 space-y-2">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-label-md text-on-surface font-bold block">2. XceptionNet</span>
                <span className="text-label-sm text-on-surface-variant">Deepfake Face Detection (FaceForensics++)</span>
              </div>
              <span className={`px-2 py-0.5 rounded text-label-sm font-semibold ${
                xcRes?.status === 'completed'
                  ? 'bg-blue-100 text-blue-800'
                  : (xcRes?.status === 'not_applicable' ? 'bg-amber-100 text-amber-800' : (xcRes?.status === 'error' ? 'bg-error-container text-on-error-container' : 'bg-surface-variant text-on-surface-variant'))
              }`}>
                {xcRes ? (xcRes.status === 'not_applicable' ? 'N/A (NO FACE)' : xcRes.status.toUpperCase()) : 'READY'}
              </span>
            </div>

            {isCompleted && xcRes?.status === 'completed' && (
              <div className="p-2 rounded bg-surface border border-outline-variant flex justify-between items-center text-body-sm">
                <span className="text-on-surface font-medium">Prediction:</span>
                <span className={`font-bold ${xcRes.prediction === 'FAKE' ? 'text-error' : 'text-green-600'}`}>
                  {xcRes.prediction} ({xcRes.confidence.toFixed(1)}%)
                </span>
              </div>
            )}

            {isCompleted && xcRes?.status === 'not_applicable' && (
              <div className="p-2 rounded bg-surface border border-outline-variant text-on-surface-variant text-label-sm">
                <span className="font-semibold block text-amber-700">Not Applicable</span>
                {xcRes.reason || "No face found in target image."}
              </div>
            )}

            {isCompleted && xcRes?.status === 'error' && (
              <div className="p-2 rounded bg-error-container/20 border border-error-container text-error text-label-sm">
                Error: {xcRes.error || "Model checkpoint missing"}
              </div>
            )}
          </div>

          {/* DETECTOR CARD 3: Face-X-Ray */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-3.5 space-y-2">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-label-md text-on-surface font-bold block">3. Face-X-Ray</span>
                <span className="text-label-sm text-on-surface-variant">Face Blending & Boundary Analysis</span>
              </div>
              <span className={`px-2 py-0.5 rounded text-label-sm font-semibold ${
                xrayRes?.status === 'completed'
                  ? 'bg-blue-100 text-blue-800'
                  : (xrayRes?.status === 'not_applicable' ? 'bg-amber-100 text-amber-800' : (xrayRes?.status === 'error' ? 'bg-error-container text-on-error-container' : 'bg-surface-variant text-on-surface-variant'))
              }`}>
                {xrayRes ? (xrayRes.status === 'not_applicable' ? 'N/A (NO FACE)' : xrayRes.status.toUpperCase()) : 'READY'}
              </span>
            </div>

            {isCompleted && xrayRes?.status === 'completed' && (
              <div className="p-2 rounded bg-surface border border-outline-variant flex justify-between items-center text-body-sm">
                <span className="text-on-surface font-medium">Prediction:</span>
                <span className={`font-bold ${xrayRes.prediction === 'FAKE' ? 'text-error' : 'text-green-600'}`}>
                  {xrayRes.prediction} ({xrayRes.confidence.toFixed(1)}%)
                </span>
              </div>
            )}

            {isCompleted && xrayRes?.status === 'not_applicable' && (
              <div className="p-2 rounded bg-surface border border-outline-variant text-on-surface-variant text-label-sm">
                <span className="font-semibold block text-amber-700">Not Applicable</span>
                {xrayRes.reason || "No face found in target image."}
              </div>
            )}

            {isCompleted && xrayRes?.status === 'error' && (
              <div className="p-2 rounded bg-error-container/20 border border-error-container text-error text-label-sm">
                Error: {xrayRes.error || "Model checkpoint missing"}
              </div>
            )}
          </div>
        </div>

        {/* Model Information Card */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-4">
          <h4 className="text-label-md text-on-surface font-semibold mb-2">Model Status & Architecture</h4>
          <div className="space-y-1 text-label-sm text-on-surface-variant">
            <div className="flex justify-between">
              <span>UniversalFakeDetect:</span>
              <span className={backendHealth.universalLoaded ? "text-green-600 font-medium" : "text-amber-600 font-medium"}>
                {backendHealth.universalLoaded ? "Loaded (fc_weights.pth)" : "Unavailable"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>XceptionNet:</span>
              <span className={backendHealth.xceptionLoaded ? "text-green-600 font-medium" : "text-amber-600 font-medium"}>
                {backendHealth.xceptionLoaded ? "Loaded (FF++_c23.pth)" : "Unavailable"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Face-X-Ray:</span>
              <span className={backendHealth.faceXrayLoaded ? "text-green-600 font-medium" : "text-amber-600 font-medium"}>
                {backendHealth.faceXrayLoaded ? "Loaded (face_xray.pth)" : "Unavailable"}
              </span>
            </div>
          </div>
        </div>

        {/* Action Button Card */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-4 flex flex-col justify-between">
          <div>
            <h3 className="text-label-md text-on-surface font-semibold mb-1">Inference Control</h3>
            <p className="text-label-sm text-on-surface-variant mb-3">
              {isIdle && "Please select an image file to start multi-model scan."}
              {isImageSelected && "Image loaded. Click 'Analyze Image' to execute all 3 detectors."}
              {isAnalyzing && "Model inference in progress across 3 models..."}
              {isCompleted && "Analysis finished. Select a new image or scan again."}
              {isError && "Scan failed. Select a valid image to try again."}
            </p>
          </div>

          <button
            onClick={handleRunScan}
            disabled={isIdle || isAnalyzing}
            className="w-full bg-secondary text-on-secondary py-2.5 rounded text-label-md font-semibold hover:opacity-90 transition-opacity flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
          >
            {isAnalyzing ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Analyzing Image... Running 3 Models...
              </>
            ) : isCompleted ? (
              <>
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>refresh</span>
                Analyze Again
              </>
            ) : (
              <>
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>search</span>
                Analyze Image
              </>
            )}
          </button>
        </div>
      </div>
    </main>
  );
}
