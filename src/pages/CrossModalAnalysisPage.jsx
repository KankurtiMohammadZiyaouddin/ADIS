import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAnalysisHistory } from '../services/analysisStore';
import { generateCrossModalReport } from '../services/reportGenerator';

// ─── helpers ────────────────────────────────────────────────────────────────
function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  const h = Math.floor(m / 60);
  if (h > 0) return `${h}h ago`;
  if (m > 0) return `${m}m ago`;
  return 'just now';
}

function ConfidenceBar({ value, color = 'bg-error' }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
        <div className={`${color} h-full rounded-full transition-all duration-700`} style={{ width: `${Math.min(100, value)}%` }} />
      </div>
      <span className="text-label-sm font-mono text-on-surface-variant">{value.toFixed(1)}%</span>
    </div>
  );
}

function VerdictBadge({ verdict, simulated }) {
  const cfg = {
    FAKE: 'bg-error/15 text-error border-error/30',
    REAL: 'bg-primary/10 text-primary border-primary/30',
    INCONCLUSIVE: 'bg-surface-container-high text-on-surface border-outline-variant',
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-label-sm border font-semibold ${cfg[verdict] || cfg.INCONCLUSIVE}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${verdict === 'FAKE' ? 'bg-error' : verdict === 'REAL' ? 'bg-primary' : 'bg-outline'}`} />
      {verdict}
      {simulated && <span className="text-[10px] opacity-60 ml-0.5">(sim)</span>}
    </span>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function CrossModalAnalysisPage() {
  const navigate = useNavigate();
  const [history, setHistory]               = useState([]);
  const [selectedImageId, setSelectedImageId] = useState('');
  const [selectedAudioId, setSelectedAudioId] = useState('');
  const [selectedVideoId, setSelectedVideoId] = useState('');

  // Backend fusion state
  const [fusionResult, setFusionResult]     = useState(null);
  const [isRunningFusion, setIsRunningFusion] = useState(false);
  const [fusionError, setFusionError]       = useState(null);

  useEffect(() => {
    const h = getAnalysisHistory();
    setHistory(h);
    const firstImage = h.find((r) => r.type === 'image');
    const firstAudio = h.find((r) => r.type === 'audio');
    const firstVideo = h.find((r) => r.type === 'video');
    if (firstImage) setSelectedImageId(firstImage.id);
    if (firstAudio) setSelectedAudioId(firstAudio.id);
    if (firstVideo) setSelectedVideoId(firstVideo.id);
  }, []);

  const imageRecords = history.filter((r) => r.type === 'image');
  const audioRecords = history.filter((r) => r.type === 'audio');
  const videoRecords = history.filter((r) => r.type === 'video');

  const selectedImage = history.find((r) => r.id === selectedImageId) || null;
  const selectedAudio = history.find((r) => r.id === selectedAudioId) || null;
  const selectedVideo = history.find((r) => r.id === selectedVideoId) || null;

  const hasSelection = selectedImage || selectedAudio || selectedVideo;

  /**
   * Run backend forensic fusion — the SINGLE source of truth.
   * The frontend NO LONGER calculates its own verdict.
   */
  const runBackendFusion = async () => {
    if (!hasSelection) return;
    setIsRunningFusion(true);
    setFusionError(null);
    setFusionResult(null);

    // Build modality payload for the backend
    const payload = {};

    if (selectedImage) {
      payload.image = {
        classification: selectedImage.verdict,
        confidence: selectedImage.confidence,  // % or 0-1, backend normalizes
        detector_name: selectedImage.model || 'Image Detector',
        model_name: selectedImage.model || 'EfficientNet',
        model_version: selectedImage.model_version || '1.0.0',
        framework: selectedImage.framework || 'PyTorch / HuggingFace Transformers',
        method: selectedImage.method || 'machine_learning',
        is_ai_model: selectedImage.is_ai_model !== false,
        fallback_used: selectedImage.fallback_used || false,
        filename: selectedImage.filename,
        sha256: selectedImage.sha256,
        timestamp: selectedImage.timestamp,
      };
    }

    if (selectedAudio) {
      payload.audio = {
        classification: selectedAudio.verdict,
        confidence: selectedAudio.confidence,
        detector_name: selectedAudio.model || 'Audio Detector',
        model_name: selectedAudio.model || 'YAMNet',
        model_version: selectedAudio.model_version || '1.0.0',
        framework: selectedAudio.framework || 'TensorFlow',
        method: selectedAudio.method || 'machine_learning',
        is_ai_model: selectedAudio.is_ai_model !== false,
        fallback_used: selectedAudio.fallback_used || false,
        filename: selectedAudio.filename,
        sha256: selectedAudio.sha256,
        timestamp: selectedAudio.timestamp,
      };
    }

    if (selectedVideo) {
      payload.video = {
        classification: selectedVideo.verdict,
        confidence: selectedVideo.confidence,
        detector_name: selectedVideo.model || 'Video Detector',
        model_name: selectedVideo.model || 'Frame-Sampled EfficientNet',
        model_version: selectedVideo.model_version || '1.5.0',
        framework: selectedVideo.framework || 'PyTorch / OpenCV',
        method: selectedVideo.method || 'machine_learning',
        is_ai_model: selectedVideo.is_ai_model !== false,
        fallback_used: selectedVideo.fallback_used || false,
        filename: selectedVideo.filename,
        sha256: selectedVideo.sha256,
        timestamp: selectedVideo.timestamp,
      };
    }

    try {
      const response = await fetch('/api/cross-modal/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error?.message || `Backend error ${response.status}`);
      }

      setFusionResult(data);
    } catch (err) {
      setFusionError(`Backend cross-modal fusion failed: ${err.message}. Ensure the ADIS backend is running.`);
    } finally {
      setIsRunningFusion(false);
    }
  };

  // Auto-run fusion when selection changes
  useEffect(() => {
    if (hasSelection) {
      runBackendFusion();
    } else {
      setFusionResult(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedImageId, selectedAudioId, selectedVideoId]);

  const handleExport = () => {
    if (!fusionResult) return;
    generateCrossModalReport(selectedAudio, selectedVideo, fusionResult, '#ADIS-LIVE');
  };

  const noHistory = imageRecords.length === 0 && audioRecords.length === 0 && videoRecords.length === 0;

  const assessment = fusionResult?.assessment;
  const assessmentConfPct = fusionResult ? Math.round((fusionResult.assessment_confidence || 0) * 100) : 0;

  return (
    <main className="flex-1 p-gutter lg:p-container-margin overflow-y-auto bg-background">

      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="mb-8 flex justify-between items-end flex-wrap gap-3">
        <div>
          <h2 className="text-display-lg font-display-lg text-on-surface">Cross-Modal Correlation</h2>
          <p className="text-body-lg font-body-lg text-on-surface-variant mt-2">
            Combine Image, Audio, and Video forensic results for a unified synthetic-media verdict.
          </p>
          <p className="text-body-sm text-on-surface-variant mt-1 flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[14px] text-primary">verified_user</span>
            Verdict is computed by the authoritative backend forensic_fusion.py — not by frontend averaging.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleExport}
            disabled={!fusionResult}
            className="px-4 py-2 border border-outline-variant bg-surface text-on-surface rounded text-label-md hover:bg-surface-container transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Export Report
          </button>
          <button
            onClick={() => { setSelectedImageId(''); setSelectedAudioId(''); setSelectedVideoId(''); setFusionResult(null); }}
            className="px-4 py-2 bg-secondary text-on-secondary rounded text-label-md hover:opacity-90 transition-opacity flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-[16px]">refresh</span>
            Reset
          </button>
        </div>
      </div>

      {/* ── No history state ─────────────────────────────────────── */}
      {noHistory && (
        <div className="glass-card rounded-xl p-10 flex flex-col items-center gap-4 text-center">
          <span className="material-symbols-outlined text-[48px] text-outline">join_inner</span>
          <div>
            <p className="text-title-lg font-title-lg text-on-surface">No analyses to correlate yet</p>
            <p className="text-body-md text-on-surface-variant mt-1">
              Run analyses on Image, Audio, or Video evidence. The results will appear here automatically.
            </p>
          </div>
          <div className="flex gap-3 flex-wrap justify-center">
            <button onClick={() => navigate('/image-forensics')} className="px-4 py-2 rounded text-label-md flex items-center gap-2 bg-secondary text-on-secondary hover:bg-secondary/90 transition-colors">
              <span className="material-symbols-outlined text-[18px]">image</span>Analyze Image
            </button>
            <button onClick={() => navigate('/audio-forensics')} className="px-4 py-2 rounded text-label-md flex items-center gap-2 bg-primary text-on-primary hover:bg-primary/90 transition-colors">
              <span className="material-symbols-outlined text-[18px]">graphic_eq</span>Analyze Audio
            </button>
            <button onClick={() => navigate('/video-forensics')} className="px-4 py-2 rounded text-label-md flex items-center gap-2 border border-outline-variant text-on-surface hover:bg-surface-container transition-colors">
              <span className="material-symbols-outlined text-[18px]">videocam</span>Analyze Video
            </button>
          </div>
        </div>
      )}

      {/* ── Evidence Selectors (3 Columns) ───────────────────────── */}
      {!noHistory && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter mb-gutter">
          {/* Image selector */}
          <div className="glass-card rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-secondary text-[20px]">image</span>
              <h3 className="text-title-md font-title-md text-on-surface">Image Evidence</h3>
            </div>
            {imageRecords.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-4 text-center">
                <p className="text-body-sm text-on-surface-variant">No image analyses yet.</p>
                <button onClick={() => navigate('/image-forensics')} className="text-label-sm text-primary hover:underline">
                  Run image analysis →
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {imageRecords.map((rec) => (
                  <button
                    key={rec.id}
                    onClick={() => setSelectedImageId(rec.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg border transition-colors flex items-start justify-between gap-2 ${
                      selectedImageId === rec.id
                        ? 'border-secondary bg-secondary/10'
                        : 'border-outline-variant bg-surface-container hover:bg-surface-container-high'
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="text-body-sm font-medium text-on-surface truncate">{rec.filename}</p>
                      <p className="text-label-sm text-on-surface-variant mt-0.5">{timeAgo(rec.timestamp)} · {rec.confidence}% confidence</p>
                    </div>
                    <VerdictBadge verdict={rec.verdict} simulated={rec.simulated} />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Audio selector */}
          <div className="glass-card rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-primary text-[20px]">graphic_eq</span>
              <h3 className="text-title-md font-title-md text-on-surface">Audio Evidence</h3>
            </div>
            {audioRecords.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-4 text-center">
                <p className="text-body-sm text-on-surface-variant">No audio analyses yet.</p>
                <button onClick={() => navigate('/audio-forensics')} className="text-label-sm text-primary hover:underline">
                  Run audio analysis →
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {audioRecords.map((rec) => (
                  <button
                    key={rec.id}
                    onClick={() => setSelectedAudioId(rec.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg border transition-colors flex items-start justify-between gap-2 ${
                      selectedAudioId === rec.id
                        ? 'border-primary bg-primary/10'
                        : 'border-outline-variant bg-surface-container hover:bg-surface-container-high'
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="text-body-sm font-medium text-on-surface truncate">{rec.filename}</p>
                      <p className="text-label-sm text-on-surface-variant mt-0.5">{timeAgo(rec.timestamp)} · {rec.confidence}% confidence</p>
                    </div>
                    <VerdictBadge verdict={rec.verdict} simulated={rec.simulated} />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Video selector */}
          <div className="glass-card rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-secondary text-[20px]">videocam</span>
              <h3 className="text-title-md font-title-md text-on-surface">Video Evidence</h3>
            </div>
            {videoRecords.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-4 text-center">
                <p className="text-body-sm text-on-surface-variant">No video analyses yet.</p>
                <button onClick={() => navigate('/video-forensics')} className="text-label-sm text-primary hover:underline">
                  Run video analysis →
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {videoRecords.map((rec) => (
                  <button
                    key={rec.id}
                    onClick={() => setSelectedVideoId(rec.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg border transition-colors flex items-start justify-between gap-2 ${
                      selectedVideoId === rec.id
                        ? 'border-secondary bg-secondary/10'
                        : 'border-outline-variant bg-surface-container hover:bg-surface-container-high'
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="text-body-sm font-medium text-on-surface truncate">{rec.filename}</p>
                      <p className="text-label-sm text-on-surface-variant mt-0.5">{timeAgo(rec.timestamp)} · {rec.confidence}% confidence</p>
                    </div>
                    <VerdictBadge verdict={rec.verdict} simulated={rec.simulated} />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Loading state ─────────────────────────────────────────── */}
      {isRunningFusion && (
        <div className="flex items-center justify-center gap-3 py-10 text-on-surface-variant">
          <span className="material-symbols-outlined animate-spin text-[24px]">progress_activity</span>
          <span className="text-body-md">Running authoritative backend forensic fusion…</span>
        </div>
      )}

      {/* ── Error state ───────────────────────────────────────────── */}
      {fusionError && !isRunningFusion && (
        <div className="mb-6 p-4 bg-error/10 border border-error/30 rounded-lg flex items-start gap-3">
          <span className="material-symbols-outlined text-error shrink-0">error</span>
          <div>
            <p className="text-label-md font-semibold text-error">Fusion Error</p>
            <p className="text-body-sm text-error/80 mt-1">{fusionError}</p>
          </div>
        </div>
      )}

      {/* ── Combined Result ──────────────────────────────────────── */}
      {fusionResult && !isRunningFusion && (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter">

          {/* Hero: Combined Verdict */}
          <div className={`col-span-1 md:col-span-4 lg:col-span-3 rounded-xl p-6 flex flex-col justify-between border shadow-sm ${
            assessment === 'FAKE' ? 'bg-error/5 border-error/20'
            : assessment === 'REAL' ? 'bg-primary/5 border-primary/20'
            : 'bg-surface-container border-outline-variant'
          }`}>
            <div>
              <h3 className="text-headline-sm font-headline-sm text-on-surface flex items-center gap-2">
                <span className={`material-symbols-outlined ${assessment === 'FAKE' ? 'text-error' : assessment === 'REAL' ? 'text-primary' : 'text-outline'}`}>
                  {assessment === 'FAKE' ? 'warning' : assessment === 'REAL' ? 'verified' : 'help'}
                </span>
                Combined Assessment
              </h3>
              <p className="text-body-sm text-on-surface-variant mt-1">Backend Authoritative Verdict</p>
              <p className="text-[10px] text-on-surface-variant mt-0.5 flex items-center gap-1">
                <span className="material-symbols-outlined text-[12px] text-primary">verified_user</span>
                forensic_fusion.py
              </p>
            </div>
            <div className="mt-8 mb-4">
              <div className="flex items-end gap-2 mb-2">
                <span className={`text-[48px] font-bold leading-none tracking-tight ${
                  assessment === 'FAKE' ? 'text-error' : assessment === 'REAL' ? 'text-primary' : 'text-on-surface'
                }`}>
                  {assessmentConfPct}<span className="text-[24px]">%</span>
                </span>
              </div>
              <div className="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${assessment === 'FAKE' ? 'bg-error' : assessment === 'REAL' ? 'bg-primary' : 'bg-outline'}`}
                  style={{ width: `${assessmentConfPct}%` }}
                />
              </div>
              <p className={`text-label-sm mt-2 font-bold uppercase tracking-wider ${
                assessment === 'FAKE' ? 'text-error' : assessment === 'REAL' ? 'text-primary' : 'text-on-surface-variant'
              }`}>
                {assessment === 'FAKE' ? 'High Confidence: Synthetic' : assessment === 'REAL' ? 'High Confidence: Authentic' : 'Inconclusive — Review Manually'}
              </p>
            </div>

            {/* Modality sources summary */}
            <div className="pt-4 border-t border-outline-variant mt-auto space-y-2 text-body-sm">
              {fusionResult.modality_sources && Object.entries(fusionResult.modality_sources).map(([modality, src]) => (
                <div key={modality} className="flex justify-between">
                  <span className="text-on-surface-variant text-xs capitalize">{modality}</span>
                  <span className={`font-mono font-semibold text-xs ${src.classification === 'FAKE' ? 'text-error' : src.classification === 'REAL' ? 'text-primary' : 'text-outline'}`}>
                    {src.classification} ({Math.round(src.confidence * 100)}%)
                    {src.fallback_used && ' ⚠'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Correlation Matrix */}
          <div className="col-span-1 md:col-span-8 lg:col-span-9 bg-surface border border-outline-variant rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6 flex-wrap gap-2">
              <h3 className="text-headline-sm font-headline-sm text-on-surface">Cross-Modal Analysis Matrix</h3>
              <div className="flex gap-2 flex-wrap">
                {!fusionResult.detector_agreement && (
                  <span className="flex items-center gap-1.5 px-3 py-1 bg-amber-500/15 border border-amber-500/30 rounded-full text-amber-400 text-label-sm font-semibold">
                    <span className="material-symbols-outlined text-[16px]">report_problem</span>
                    Modal Conflict Detected
                  </span>
                )}
                <span className="flex items-center gap-1.5 px-3 py-1 bg-primary/10 border border-primary/30 rounded-full text-primary text-label-sm font-semibold">
                  <span className="material-symbols-outlined text-[14px]">verified_user</span>
                  Backend Fusion
                </span>
              </div>
            </div>

            {/* Fallback warnings */}
            {fusionResult.fallback_warnings?.length > 0 && (
              <div className="mb-4 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg space-y-1">
                {fusionResult.fallback_warnings.map((w, i) => (
                  <p key={i} className="text-body-sm text-amber-200/90">{w}</p>
                ))}
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr>
                    {['Modality', 'File', 'Verdict', 'Confidence', 'Method'].map((h) => (
                      <th key={h} className="p-3 text-label-sm text-on-surface-variant bg-surface-container-low border-b border-outline-variant font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="text-body-sm font-body-sm text-on-surface">
                  {[
                    { modality: 'image', icon: 'image', color: 'text-secondary', rec: selectedImage },
                    { modality: 'audio', icon: 'graphic_eq', color: 'text-primary', rec: selectedAudio },
                    { modality: 'video', icon: 'videocam', color: 'text-secondary', rec: selectedVideo },
                  ].map(({ modality, icon, color, rec }) => {
                    const src = fusionResult.modality_sources?.[modality];
                    return (
                      <tr key={modality} className="hover:bg-primary/5 border-b border-outline-variant/50 transition-colors">
                        <td className="p-3 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center">
                              <span className={`material-symbols-outlined ${color} text-[16px]`}>{icon}</span>
                            </div>
                            <span className="font-medium capitalize">{modality}</span>
                          </div>
                        </td>
                        <td className="p-3 text-on-surface-variant truncate max-w-[140px]" title={rec?.filename}>
                          {rec ? rec.filename : <span className="italic opacity-50">Not selected</span>}
                        </td>
                        <td className="p-3">
                          {src ? <VerdictBadge verdict={src.classification} simulated={rec?.simulated} /> : '—'}
                        </td>
                        <td className="p-3">
                          {src ? <ConfidenceBar value={Math.round(src.confidence * 100)} color={src.classification === 'FAKE' ? 'bg-error' : src.classification === 'REAL' ? 'bg-primary' : 'bg-outline'} /> : '—'}
                        </td>
                        <td className="p-3 text-label-sm">
                          {src ? (
                            <span className={`px-2 py-0.5 rounded-full text-[10px] border ${src.is_ai_model ? 'text-primary border-primary/30 bg-primary/10' : 'text-amber-400 border-amber-500/30 bg-amber-500/10'}`}>
                              {src.fallback_used ? '⚠ Heuristic' : src.method === 'machine_learning' ? 'AI Model' : src.method}
                            </span>
                          ) : '—'}
                        </td>
                      </tr>
                    );
                  })}
                  {/* Combined row */}
                  <tr className={`font-semibold ${assessment === 'FAKE' ? 'bg-error/5' : assessment === 'REAL' ? 'bg-primary/5' : 'bg-surface-container-low'}`}>
                    <td className="p-3 py-4" colSpan={2}>
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-[16px] text-primary">verified_user</span>
                        <span>Backend Fusion Verdict</span>
                      </div>
                    </td>
                    <td className="p-3"><VerdictBadge verdict={assessment} simulated={false} /></td>
                    <td className="p-3"><ConfidenceBar value={assessmentConfPct} color={assessment === 'FAKE' ? 'bg-error' : assessment === 'REAL' ? 'bg-primary' : 'bg-outline'} /></td>
                    <td className="p-3 text-label-sm">
                      <span className="px-2 py-0.5 rounded-full text-[10px] border text-primary border-primary/30 bg-primary/10">
                        forensic_fusion.py
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Disagreement / conflict explanation */}
            {(fusionResult.disagreement_warning || !fusionResult.detector_agreement) && (
              <div className="mt-4 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg flex gap-3">
                <span className="material-symbols-outlined text-amber-400 shrink-0">report_problem</span>
                <div>
                  <p className="text-label-sm font-semibold text-amber-300">Modality Conflict — Manual Review Required</p>
                  <p className="text-body-sm text-amber-200/80 mt-1">
                    {fusionResult.disagreement_warning ||
                      'The selected evidence modalities returned conflicting verdicts. Perform secondary contextual analysis before final determination.'}
                  </p>
                </div>
              </div>
            )}

            {/* Disclaimer */}
            <p className="mt-4 text-body-sm text-on-surface-variant/70 italic">
              {fusionResult.disclaimer}
            </p>
          </div>
        </div>
      )}

      <div className="h-8" />
    </main>
  );
}
