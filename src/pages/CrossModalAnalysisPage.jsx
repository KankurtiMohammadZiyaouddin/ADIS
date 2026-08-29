import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAnalysisHistory } from '../services/analysisStore';
import { generateCrossModalReport } from '../services/reportGenerator';

// ─── helpers ────────────────────────────────────────────────────────────────
function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  const h = Math.floor(m / 60);
  if (h  > 0) return `${h}h ago`;
  if (m  > 0) return `${m}m ago`;
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

// ─── Combined verdict logic ───────────────────────────────────────────────
function computeCrossModal(audio, video) {
  if (!audio && !video) return null;

  // Weighted average: if both present, each 50%; if solo, 100%
  let fakeProbability = 0;
  let sources = [];

  if (audio) {
    const aConf = audio.verdict === 'FAKE' ? audio.confidence : 100 - audio.confidence;
    fakeProbability += audio.verdict === 'FAKE' ? aConf / 100 : (100 - aConf) / 100;
    sources.push({ label: 'Audio (YamNet)', weight: 0.5, conf: audio.confidence, verdict: audio.verdict });
  }
  if (video) {
    const vConf = video.verdict === 'FAKE' ? video.confidence : 100 - video.confidence;
    fakeProbability += video.verdict === 'FAKE' ? vConf / 100 : (100 - vConf) / 100;
    sources.push({ label: 'Video (EfficientNet)', weight: 0.5, conf: video.confidence, verdict: video.verdict });
  }

  // Normalise to number of sources
  fakeProbability = (fakeProbability / sources.length) * 100;

  let combined;
  if (fakeProbability >= 60)        combined = 'FAKE';
  else if (fakeProbability <= 35)   combined = 'REAL';
  else                              combined = 'INCONCLUSIVE';

  // Conflict detection
  const conflicting = audio && video && audio.verdict !== video.verdict;

  return { fakeProbability, combined, conflicting, sources };
}

// ─── Main component ───────────────────────────────────────────────────────
export default function CrossModalAnalysisPage() {
  const navigate = useNavigate();
  const [history, setHistory]       = useState([]);
  const [selectedAudioId, setSelectedAudioId] = useState('');
  const [selectedVideoId, setSelectedVideoId] = useState('');

  useEffect(() => {
    const h = getAnalysisHistory();
    setHistory(h);
    // Auto-select most recent audio + video
    const firstAudio = h.find((r) => r.type === 'audio');
    const firstVideo = h.find((r) => r.type === 'video');
    if (firstAudio) setSelectedAudioId(firstAudio.id);
    if (firstVideo) setSelectedVideoId(firstVideo.id);
  }, []);

  const audioRecords = history.filter((r) => r.type === 'audio');
  const videoRecords = history.filter((r) => r.type === 'video');

  const selectedAudio = history.find((r) => r.id === selectedAudioId) || null;
  const selectedVideo = history.find((r) => r.id === selectedVideoId) || null;

  const result = computeCrossModal(selectedAudio, selectedVideo);

  // Export combined report as PDF
  const handleExport = () => {
    if (!result) return;
    generateCrossModalReport(selectedAudio, selectedVideo, result, '#ADIS-LIVE');
  };

  const noHistory = audioRecords.length === 0 && videoRecords.length === 0;

  return (
    <main className="flex-1 p-gutter lg:p-container-margin overflow-y-auto bg-background">

      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="mb-8 flex justify-between items-end flex-wrap gap-3">
        <div>
          <h2 className="text-display-lg font-display-lg text-on-surface">Cross-Modal Correlation</h2>
          <p className="text-body-lg font-body-lg text-on-surface-variant mt-2">
            Combine audio and video forensic results for a unified synthetic-media verdict.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleExport}
            disabled={!result}
            className="px-4 py-2 border border-outline-variant bg-surface text-on-surface rounded text-label-md hover:bg-surface-container transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Export Report
          </button>
          <button
            onClick={() => { setSelectedAudioId(''); setSelectedVideoId(''); }}
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
              Run at least one audio and one video analysis first. The results will appear here automatically.
            </p>
          </div>
          <div className="flex gap-3 flex-wrap justify-center">
            <button onClick={() => navigate('/audio-forensics')} className="px-4 py-2 rounded text-label-md flex items-center gap-2 bg-primary text-on-primary hover:bg-primary/90 transition-colors">
              <span className="material-symbols-outlined text-[18px]">graphic_eq</span>Analyze Audio
            </button>
            <button onClick={() => navigate('/video-forensics')} className="px-4 py-2 rounded text-label-md flex items-center gap-2 border border-outline-variant text-on-surface hover:bg-surface-container transition-colors">
              <span className="material-symbols-outlined text-[18px]">videocam</span>Analyze Video
            </button>
          </div>
        </div>
      )}

      {/* ── Evidence Selectors ───────────────────────────────────── */}
      {!noHistory && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter mb-gutter">
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

      {/* ── Combined Result ──────────────────────────────────────── */}
      {result && (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter">

          {/* Hero: Combined Verdict */}
          <div className={`col-span-1 md:col-span-4 lg:col-span-3 rounded-xl p-6 flex flex-col justify-between border shadow-sm ${
            result.combined === 'FAKE' ? 'bg-error/5 border-error/20'
            : result.combined === 'REAL' ? 'bg-primary/5 border-primary/20'
            : 'bg-surface-container border-outline-variant'
          }`}>
            <div>
              <h3 className="text-headline-sm font-headline-sm text-on-surface flex items-center gap-2">
                <span className={`material-symbols-outlined ${result.combined === 'FAKE' ? 'text-error' : result.combined === 'REAL' ? 'text-primary' : 'text-outline'}`}>
                  {result.combined === 'FAKE' ? 'warning' : result.combined === 'REAL' ? 'verified' : 'help'}
                </span>
                Combined Assessment
              </h3>
              <p className="text-body-sm text-on-surface-variant mt-1">AI Manipulation Probability</p>
            </div>
            <div className="mt-8 mb-4">
              <div className="flex items-end gap-2 mb-2">
                <span className={`text-[48px] font-bold leading-none tracking-tight ${
                  result.combined === 'FAKE' ? 'text-error' : result.combined === 'REAL' ? 'text-primary' : 'text-on-surface'
                }`}>
                  {result.fakeProbability.toFixed(0)}<span className="text-[24px]">%</span>
                </span>
              </div>
              <div className="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${result.combined === 'FAKE' ? 'bg-error' : result.combined === 'REAL' ? 'bg-primary' : 'bg-outline'}`}
                  style={{ width: `${result.fakeProbability}%` }}
                />
              </div>
              <p className={`text-label-sm mt-2 font-bold uppercase tracking-wider ${
                result.combined === 'FAKE' ? 'text-error' : result.combined === 'REAL' ? 'text-primary' : 'text-on-surface-variant'
              }`}>
                {result.combined === 'FAKE' ? 'High Confidence: Synthetic' : result.combined === 'REAL' ? 'High Confidence: Authentic' : 'Inconclusive — Review Manually'}
              </p>
            </div>
            <div className="pt-4 border-t border-outline-variant mt-auto space-y-2 text-body-sm">
              {result.sources.map((s) => (
                <div key={s.label} className="flex justify-between">
                  <span className="text-on-surface-variant">{s.label}</span>
                  <span className={`font-mono font-semibold ${s.verdict === 'FAKE' ? 'text-error' : 'text-primary'}`}>
                    {(s.conf / 100).toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Correlation Matrix */}
          <div className="col-span-1 md:col-span-8 lg:col-span-9 bg-surface border border-outline-variant rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-headline-sm font-headline-sm text-on-surface">Cross-Modal Analysis Matrix</h3>
              {result.conflicting && (
                <span className="flex items-center gap-1.5 px-3 py-1 bg-amber-500/15 border border-amber-500/30 rounded-full text-amber-400 text-label-sm font-semibold">
                  <span className="material-symbols-outlined text-[16px]">report_problem</span>
                  Modal Conflict Detected
                </span>
              )}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr>
                    {['Modality', 'File', 'Model Verdict', 'Confidence', 'Contribution'].map((h) => (
                      <th key={h} className="p-3 text-label-sm text-on-surface-variant bg-surface-container-low border-b border-outline-variant font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="text-body-sm font-body-sm text-on-surface">
                  {/* Audio row */}
                  <tr className="hover:bg-primary/5 border-b border-outline-variant/50 transition-colors">
                    <td className="p-3 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <span className="material-symbols-outlined text-primary text-[16px]">graphic_eq</span>
                        </div>
                        <span className="font-medium">Audio</span>
                      </div>
                    </td>
                    <td className="p-3 text-on-surface-variant truncate max-w-[120px]" title={selectedAudio?.filename}>
                      {selectedAudio ? selectedAudio.filename : <span className="italic opacity-50">Not selected</span>}
                    </td>
                    <td className="p-3">{selectedAudio ? <VerdictBadge verdict={selectedAudio.verdict} simulated={selectedAudio.simulated} /> : '—'}</td>
                    <td className="p-3">{selectedAudio ? <ConfidenceBar value={selectedAudio.confidence} color={selectedAudio.verdict === 'FAKE' ? 'bg-error' : 'bg-primary'} /> : '—'}</td>
                    <td className="p-3 text-on-surface-variant text-label-sm">
                      {selectedAudio ? `${(selectedAudio.confidence / 2).toFixed(1)}% weight` : '—'}
                    </td>
                  </tr>
                  {/* Video row */}
                  <tr className="hover:bg-primary/5 border-b border-outline-variant/50 transition-colors">
                    <td className="p-3 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-secondary/10 flex items-center justify-center">
                          <span className="material-symbols-outlined text-secondary text-[16px]">videocam</span>
                        </div>
                        <span className="font-medium">Video</span>
                      </div>
                    </td>
                    <td className="p-3 text-on-surface-variant truncate max-w-[120px]" title={selectedVideo?.filename}>
                      {selectedVideo ? selectedVideo.filename : <span className="italic opacity-50">Not selected</span>}
                    </td>
                    <td className="p-3">{selectedVideo ? <VerdictBadge verdict={selectedVideo.verdict} simulated={selectedVideo.simulated} /> : '—'}</td>
                    <td className="p-3">{selectedVideo ? <ConfidenceBar value={selectedVideo.confidence} color={selectedVideo.verdict === 'FAKE' ? 'bg-error' : 'bg-primary'} /> : '—'}</td>
                    <td className="p-3 text-on-surface-variant text-label-sm">
                      {selectedVideo ? `${(selectedVideo.confidence / 2).toFixed(1)}% weight` : '—'}
                    </td>
                  </tr>
                  {/* Combined row */}
                  <tr className={`font-semibold ${result.combined === 'FAKE' ? 'bg-error/5' : result.combined === 'REAL' ? 'bg-primary/5' : 'bg-surface-container-low'}`}>
                    <td className="p-3 py-4" colSpan={2}>
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-[16px] text-on-surface-variant">join_inner</span>
                        <span>Combined (Weighted Average)</span>
                      </div>
                    </td>
                    <td className="p-3"><VerdictBadge verdict={result.combined} simulated={false} /></td>
                    <td className="p-3"><ConfidenceBar value={result.fakeProbability} color={result.combined === 'FAKE' ? 'bg-error' : result.combined === 'REAL' ? 'bg-primary' : 'bg-outline'} /></td>
                    <td className="p-3 text-on-surface-variant text-label-sm">Final verdict</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Conflict explanation */}
            {result.conflicting && (
              <div className="mt-4 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg flex gap-3">
                <span className="material-symbols-outlined text-amber-400 shrink-0">report_problem</span>
                <div>
                  <p className="text-label-sm font-semibold text-amber-300">Modality Conflict — Manual Review Required</p>
                  <p className="text-body-sm text-amber-200/80 mt-1">
                    The audio and video models returned opposite verdicts. This can indicate partial manipulation
                    (e.g. voice cloned onto a real video, or vice versa) or a model limitation.
                    Consider re-running both analyses with a fresh file before drawing conclusions.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Bottom: insight panel */}
          <div className="col-span-1 md:col-span-12 bg-surface border border-outline-variant rounded-xl p-6 flex flex-col lg:flex-row gap-6 shadow-sm">
            <div className="w-full lg:w-1/3 flex flex-col justify-center">
              <h4 className="text-title-lg font-title-lg text-on-surface mb-2">Forensic Interpretation</h4>
              <p className="text-body-sm text-on-surface-variant mb-4">
                {result.combined === 'FAKE'
                  ? 'Both or majority of modalities indicate synthetic generation. The combined score exceeds the 60% FAKE threshold. Recommend flagging this evidence for further investigation.'
                  : result.combined === 'REAL'
                  ? 'Both or majority of modalities indicate authentic content. The combined score falls below the 35% FAKE threshold. Evidence appears genuine based on available models.'
                  : 'The combined score falls in the inconclusive zone (35%–60%). This may indicate partial manipulation, model uncertainty, or conflicting signals between modalities.'}
              </p>
              <div className="bg-surface-container p-4 rounded border border-outline-variant border-dashed space-y-2">
                <div className="flex justify-between">
                  <span className="text-label-sm text-on-surface-variant">FAKE threshold</span>
                  <span className="text-label-sm font-mono text-error">≥ 60%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-label-sm text-on-surface-variant">REAL threshold</span>
                  <span className="text-label-sm font-mono text-primary">≤ 35%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-label-sm text-on-surface-variant">Current score</span>
                  <span className={`text-label-sm font-mono font-bold ${result.combined === 'FAKE' ? 'text-error' : result.combined === 'REAL' ? 'text-primary' : 'text-on-surface'}`}>
                    {result.fakeProbability.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
            <div className="w-full lg:w-2/3 flex flex-col gap-3">
              <h4 className="text-title-md font-title-md text-on-surface">Individual Model Scores</h4>
              {result.sources.map((s) => (
                <div key={s.label} className="flex items-center gap-4">
                  <span className="text-body-sm text-on-surface-variant w-44 shrink-0">{s.label}</span>
                  <div className="flex-1 bg-surface-container-highest h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${s.verdict === 'FAKE' ? 'bg-error' : 'bg-primary'}`}
                      style={{ width: `${s.conf}%` }}
                    />
                  </div>
                  <span className={`text-label-sm font-mono w-16 text-right ${s.verdict === 'FAKE' ? 'text-error' : 'text-primary'}`}>{s.conf}%</span>
                  <VerdictBadge verdict={s.verdict} simulated={false} />
                </div>
              ))}
            </div>
          </div>

        </div>
      )}

      <div className="h-8" />
    </main>
  );
}
