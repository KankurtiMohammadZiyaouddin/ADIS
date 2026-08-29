import { useState, useRef } from 'react';
import { analyzeImageFile } from '../services/deepfakeService';
import { saveAnalysisResult } from '../services/analysisStore';

export default function ImageForensicsPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisStep, setAnalysisStep] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setError(null);
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile) return;
    setIsAnalyzing(true);
    setError(null);
    setAnalysisProgress(10);
    setAnalysisStep('Initializing neural pipeline...');

    try {
      const res = await analyzeImageFile(selectedFile, (pct, step) => {
        setAnalysisProgress(pct);
        setAnalysisStep(step);
      });

      setResult(res);
      // Save result to global store for Dashboard & Reports & Cross-Modal
      saveAnalysisResult(
        'image',
        res.originalName || selectedFile.name,
        res.verdict,
        res.confidence,
        res._simulated === true,
        {
          sha256: res.sha256,
          model: res.modelUsed,
          resolution: res.resolution,
          format: res.format,
        }
      );
    } catch (err) {
      console.error('Image analysis failed:', err);
      setError(err.message || 'Failed to complete image forensic scan.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <main className="flex-1 overflow-auto bg-background p-gutter flex gap-gutter flex-col xl:flex-row">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept="image/jpeg,image/jpg,image/png,image/webp,image/bmp,image/tiff"
        className="hidden"
      />

      {/* Center Canvas: Image Comparison */}
      <div className="flex-1 flex flex-col gap-gutter min-w-0">
        {/* Banner for Simulation Mode */}
        {result?._simulated && (
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-amber-400 text-body-sm flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">warning</span>
            <span>
              <strong>SIMULATION MODE:</strong> Backend was offline or unreachable. Results are simulated and randomly generated for demo purposes.
            </span>
          </div>
        )}

        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg flex-1 flex flex-col overflow-hidden min-h-[400px]">
          <div className="h-10 border-b border-outline-variant bg-surface-container flex items-center justify-between px-4 shrink-0">
            <span className="text-label-md text-on-surface">
              {selectedFile ? `Analysis Canvas: ${selectedFile.name}` : 'Analysis Canvas: Select Image'}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-3 py-1 bg-surface-container-highest border border-outline-variant rounded text-label-sm text-on-surface hover:bg-surface-container-low transition-colors flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-[16px]">file_upload</span>
                Select Image
              </button>
            </div>
          </div>

          <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4 min-h-0 bg-surface">
            {/* Original Image Display */}
            <div className="flex-1 flex flex-col border border-outline-variant rounded bg-surface-container-lowest relative overflow-hidden group min-h-[300px]">
              <div className="absolute top-2 left-2 bg-on-surface/80 text-surface-container-lowest px-2 py-1 rounded text-label-sm z-10">
                Original Image
              </div>
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="Uploaded evidence preview"
                  className="w-full h-full object-contain p-2"
                />
              ) : (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full h-full flex flex-col items-center justify-center cursor-pointer p-8 text-center text-on-surface-variant hover:text-on-surface transition-colors"
                >
                  <span className="material-symbols-outlined text-[48px] text-outline mb-2">add_photo_alternate</span>
                  <p className="text-body-md font-medium">Click to select an image for forensic scanning</p>
                  <p className="text-label-sm opacity-70 mt-1">Supports JPG, PNG, WEBP, BMP, TIFF (Up to 25MB)</p>
                </div>
              )}
            </div>

            {/* Error Level Analysis (ELA) / Heatmap View */}
            <div className="flex-1 flex flex-col border border-outline-variant rounded bg-surface-container-lowest relative overflow-hidden min-h-[300px]">
              <div className="absolute top-2 left-2 bg-on-surface/80 text-surface-container-lowest px-2 py-1 rounded text-label-sm z-10">
                Spatial &amp; Compression Heatmap
              </div>
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="Forensic ELA simulation"
                  className={`w-full h-full object-contain p-2 ${
                    result?.verdict === 'FAKE' ? 'filter contrast-150 saturate-200 hue-rotate-90' : 'filter contrast-110'
                  }`}
                />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center text-on-surface-variant">
                  <span className="material-symbols-outlined text-[48px] text-outline mb-2">blur_on</span>
                  <p className="text-body-md">Heatmap preview will generate after scan</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Panel: Metadata Summary */}
        <div className="h-44 bg-surface-container-lowest border border-outline-variant rounded-lg flex flex-col overflow-hidden shrink-0">
          <div className="h-8 border-b border-outline-variant bg-surface-container flex items-center px-4 text-label-md text-on-surface">
            Image Forensic Metadata Summary
          </div>
          <div className="p-3 overflow-y-auto">
            <table className="w-full text-body-sm font-body-sm text-left">
              <tbody>
                <tr className="border-b border-surface-variant">
                  <th className="py-1 text-on-surface-variant font-medium w-1/3">Filename</th>
                  <td className="py-1 text-on-surface">{selectedFile?.name || 'No file selected'}</td>
                </tr>
                <tr className="border-b border-surface-variant">
                  <th className="py-1 text-on-surface-variant font-medium">Resolution</th>
                  <td className="py-1 text-on-surface">{result?.resolution || 'N/A'}</td>
                </tr>
                <tr className="border-b border-surface-variant">
                  <th className="py-1 text-on-surface-variant font-medium">SHA-256 Hash</th>
                  <td className="py-1 font-mono text-xs text-on-surface truncate" title={result?.sha256}>
                    {result?.sha256 || 'Calculated during scan'}
                  </td>
                </tr>
                <tr>
                  <th className="py-1 text-on-surface-variant font-medium">Format / Model</th>
                  <td className="py-1 text-on-surface">
                    {result ? `${result.format} (${result.modelUsed})` : 'N/A'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Right Sidebar: Analysis Panel */}
      <div className="w-full xl:w-80 flex flex-col gap-gutter shrink-0">
        {/* Action Button Card */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-4">
          <button
            onClick={handleStartAnalysis}
            disabled={!selectedFile || isAnalyzing}
            className="w-full py-2.5 px-4 bg-primary text-on-primary rounded text-label-md font-semibold hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isAnalyzing ? (
              <>
                <span className="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                Analyzing Image...
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[18px]">psychology</span>
                Run Image Deepfake Scan
              </>
            )}
          </button>

          {isAnalyzing && (
            <div className="mt-3 space-y-1.5">
              <div className="flex justify-between text-label-sm text-on-surface-variant">
                <span>{analysisStep}</span>
                <span>{analysisProgress}%</span>
              </div>
              <div className="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                <div className="bg-primary h-full rounded-full transition-all duration-300" style={{ width: `${analysisProgress}%` }} />
              </div>
            </div>
          )}

          {error && (
            <div className="mt-3 p-2.5 bg-error/10 border border-error/30 rounded text-error text-body-sm">
              {error}
            </div>
          )}
        </div>

        {/* Probability Card */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-4">
          <h3 className="text-headline-sm font-headline-sm text-on-surface mb-4">Forensic Assessment</h3>

          <div className="mb-6">
            <div className="flex justify-between items-end mb-1">
              <span className="text-label-md text-on-surface-variant">Verdict</span>
              <span className={`text-title-lg font-title-lg ${result?.verdict === 'FAKE' ? 'text-error' : result?.verdict === 'REAL' ? 'text-primary' : 'text-on-surface'}`}>
                {result ? result.verdict : 'PENDING'}
              </span>
            </div>
            <div className="w-full bg-surface-variant rounded-full h-2 overflow-hidden">
              <div
                className={`h-2 rounded-full transition-all duration-700 ${result?.verdict === 'FAKE' ? 'bg-error' : 'bg-primary'}`}
                style={{ width: result ? `${result.confidence}%` : '0%' }}
              />
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between items-center text-body-sm">
              <span className="text-on-surface-variant">Confidence Score</span>
              <span className="font-mono font-semibold text-on-surface">{result ? `${result.confidence}%` : '—'}</span>
            </div>
            <div className="flex justify-between items-center text-body-sm">
              <span className="text-on-surface-variant">Fake Probability</span>
              <span className="font-mono text-error">{result ? `${result.probFake}%` : '—'}</span>
            </div>
            <div className="flex justify-between items-center text-body-sm">
              <span className="text-on-surface-variant">Real Probability</span>
              <span className="font-mono text-primary">{result ? `${result.probReal}%` : '—'}</span>
            </div>
            <div className="flex justify-between items-center text-body-sm">
              <span className="text-on-surface-variant">Processing Time</span>
              <span className="font-mono text-on-surface-variant">{result ? `${result.processingTimeMs} ms` : '—'}</span>
            </div>
          </div>

          {result && (
            <div className="mt-4 pt-3 border-t border-outline-variant space-y-2">
              <h4 className="text-label-sm text-on-surface-variant uppercase tracking-wider">Analysis Notes</h4>
              <p className="text-body-sm text-on-surface-variant leading-relaxed">
                {result.verdict === 'FAKE'
                  ? 'Model detected spatial and structural synthesis patterns consistent with deepfake generation.'
                  : result.verdict === 'REAL'
                  ? 'Model verified natural camera sensor characteristics and uniform spatial features.'
                  : 'Inconclusive score. Manual examination suggested.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
