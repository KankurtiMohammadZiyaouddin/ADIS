import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAnalysisHistory } from '../services/analysisStore';
import { generateSingleReport, generateBulkReport } from '../services/reportGenerator';

const TYPE_ICON  = { audio: 'graphic_eq', video: 'videocam', image: 'image_search' };
const TYPE_LABEL = { audio: 'Audio Analysis', video: 'Video Analysis', image: 'Image Analysis' };

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  const h = Math.floor(m / 60);
  const d = Math.floor(h / 24);
  if (d > 0) return `${d}d ago`;
  if (h > 0) return `${h}h ago`;
  if (m > 0) return `${m}m ago`;
  return 'just now';
}

function VerdictBadge({ verdict }) {
  const cfg = {
    FAKE: 'bg-error/15 text-error border-error/30',
    REAL: 'bg-primary/10 text-primary border-primary/30',
    INCONCLUSIVE: 'bg-surface-container-high text-on-surface border-outline-variant',
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-label-sm font-semibold ${cfg[verdict] || cfg.INCONCLUSIVE}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${verdict === 'FAKE' ? 'bg-error' : verdict === 'REAL' ? 'bg-primary' : 'bg-outline'}`} />
      {verdict}
    </span>
  );
}

export default function ReportsPage() {
  const navigate = useNavigate();
  const [history, setHistory]             = useState([]);
  const [selectedId, setSelectedId]       = useState(null);
  const [generating, setGenerating]       = useState(false);
  const [lastGenerated, setLastGenerated] = useState(null);

  useEffect(() => {
    const h = getAnalysisHistory();
    setHistory(h);
    if (h.length > 0) setSelectedId(h[0].id);
  }, []);

  const selected = history.find((r) => r.id === selectedId) || null;

  const handleGenerateSingle = async () => {
    if (!selected) return;
    setGenerating(true);
    try {
      generateSingleReport(selected, '#ADIS-LIVE');
      setLastGenerated(`ADIS_Report_${selected.type}_${Date.now().toString().slice(-6)}.pdf`);
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateBulk = async () => {
    if (!history.length) return;
    setGenerating(true);
    try {
      generateBulkReport(history);
      setLastGenerated(`ADIS_Bulk_Report.pdf`);
    } finally {
      setGenerating(false);
    }
  };

  const noHistory = history.length === 0;

  return (
    <main className="flex-1 overflow-y-auto p-gutter min-h-screen bg-background">
      <div className="max-w-[1600px] mx-auto grid grid-cols-1 xl:grid-cols-12 gap-6">

        {/* ── Left Column: Analysis Records List ─────────────────────── */}
        <div className="xl:col-span-5 flex flex-col gap-6">
          <div className="flex justify-between items-end">
            <div>
              <h2 className="text-headline-md font-headline-md text-on-surface">Analysis Records</h2>
              <p className="text-body-sm font-body-sm text-on-surface-variant mt-1">
                Select a record to preview and export as PDF.
              </p>
            </div>
            <button
              onClick={handleGenerateBulk}
              disabled={noHistory || generating}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-surface border border-outline-variant text-on-surface rounded text-label-sm hover:bg-surface-container transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-[16px]">download</span>
              Bulk PDF
            </button>
          </div>

          <div className="glass-card rounded-xl overflow-hidden">
            {noHistory ? (
              <div className="p-10 flex flex-col items-center gap-4 text-center">
                <span className="material-symbols-outlined text-[48px] text-outline">description</span>
                <div>
                  <p className="text-title-md font-title-md text-on-surface">No analyses yet</p>
                  <p className="text-body-sm text-on-surface-variant mt-1">
                    Run audio or video forensic analyses — they'll appear here ready to export.
                  </p>
                </div>
                <div className="flex gap-3 flex-wrap justify-center">
                  <button onClick={() => navigate('/audio-forensics')}
                    className="px-4 py-2 rounded text-label-md flex items-center gap-2 bg-primary text-on-primary hover:bg-primary/90 transition-colors">
                    <span className="material-symbols-outlined text-[16px]">graphic_eq</span>Analyze Audio
                  </button>
                  <button onClick={() => navigate('/video-forensics')}
                    className="px-4 py-2 rounded text-label-md flex items-center gap-2 border border-outline-variant text-on-surface hover:bg-surface-container transition-colors">
                    <span className="material-symbols-outlined text-[16px]">videocam</span>Analyze Video
                  </button>
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-surface-container-low border-b border-outline-variant">
                    <tr>
                      {['Type', 'Filename', 'Verdict', 'When'].map((h) => (
                        <th key={h} className="py-2.5 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant bg-surface-container-lowest">
                    {history.map((rec) => (
                      <tr
                        key={rec.id}
                        onClick={() => setSelectedId(rec.id)}
                        className={`cursor-pointer transition-colors ${
                          selectedId === rec.id
                            ? 'bg-primary/10 border-l-2 border-l-primary'
                            : 'hover:bg-primary/5'
                        }`}
                      >
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1.5">
                            <span className="material-symbols-outlined text-on-surface-variant text-[16px]">
                              {TYPE_ICON[rec.type] || 'description'}
                            </span>
                            <span className="text-label-sm text-on-surface-variant">{TYPE_LABEL[rec.type] || rec.type}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-body-sm text-on-surface font-medium truncate max-w-[140px]" title={rec.filename}>
                          {rec.filename}
                        </td>
                        <td className="py-3 px-4"><VerdictBadge verdict={rec.verdict} /></td>
                        <td className="py-3 px-4 text-body-sm text-on-surface-variant whitespace-nowrap">{timeAgo(rec.timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* ── Right Column: Report Preview + Export ───────────────────── */}
        <div className="xl:col-span-7 flex flex-col gap-6">

          {/* Header */}
          <div className="flex justify-between items-end">
            <div>
              <h2 className="text-headline-md font-headline-md text-on-surface">Report Preview</h2>
              <p className="text-body-sm font-body-sm text-on-surface-variant mt-1">
                Review the details before exporting to PDF.
              </p>
            </div>
            <button
              onClick={handleGenerateSingle}
              disabled={!selected || generating}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary rounded text-label-md hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {generating ? (
                <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
              ) : (
                <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
              )}
              {generating ? 'Generating…' : 'Download PDF'}
            </button>
          </div>

          {!selected ? (
            <div className="glass-card rounded-xl p-10 flex flex-col items-center gap-3 text-center flex-1">
              <span className="material-symbols-outlined text-[48px] text-outline">picture_as_pdf</span>
              <p className="text-title-md text-on-surface">Select a record to preview</p>
              <p className="text-body-sm text-on-surface-variant">Click any row on the left to preview its report.</p>
            </div>
          ) : (
            /* ── Report preview card ─────────────────────────────────── */
            <div className="glass-card rounded-xl overflow-hidden flex-1">

              {/* Preview header (mimics PDF header bar) */}
              <div className="bg-[#1A1E25] px-6 py-3 flex justify-between items-center border-b border-outline-variant">
                <div>
                  <span className="text-primary text-label-sm font-bold tracking-widest uppercase">ADIS Forensic Report</span>
                  <span className="text-on-surface-variant text-label-sm ml-3">· CONFIDENTIAL</span>
                </div>
                <span className="text-on-surface-variant text-label-sm font-mono">
                  {new Date().toISOString().substring(0, 10)}
                </span>
              </div>

              <div className="p-6 space-y-6">
                {/* Title */}
                <div className="text-center pb-4 border-b border-outline-variant">
                  <h3 className="text-title-xl font-bold text-on-surface">
                    {TYPE_LABEL[selected.type] || 'Forensic Analysis'} Report
                  </h3>
                  <p className="text-body-sm text-on-surface-variant mt-1">
                    Advanced Digital Investigation Suite
                  </p>
                </div>

                {/* Verdict hero */}
                <div className={`rounded-xl p-5 border text-center ${
                  selected.verdict === 'FAKE' ? 'bg-error/10 border-error/30'
                  : selected.verdict === 'REAL' ? 'bg-primary/10 border-primary/30'
                  : 'bg-surface-container border-outline-variant'
                }`}>
                  <p className="text-label-sm text-on-surface-variant mb-2 uppercase tracking-wider">AI Verdict</p>
                  <div className="flex items-end justify-center gap-2 mb-2">
                    <span className={`text-5xl font-bold leading-none ${
                      selected.verdict === 'FAKE' ? 'text-error' : selected.verdict === 'REAL' ? 'text-primary' : 'text-on-surface'
                    }`}>
                      {selected.confidence}<span className="text-2xl">%</span>
                    </span>
                  </div>
                  <div className="w-full max-w-[240px] mx-auto bg-surface-container-highest h-2 rounded-full overflow-hidden mb-3">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${selected.verdict === 'FAKE' ? 'bg-error' : 'bg-primary'}`}
                      style={{ width: `${selected.confidence}%` }}
                    />
                  </div>
                  <VerdictBadge verdict={selected.verdict} />
                  {selected.simulated && (
                    <p className="text-amber-400 text-label-sm mt-2">⚠ Simulation — no forensic value</p>
                  )}
                </div>

                {/* Evidence Metadata */}
                <div>
                  <h4 className="text-label-md font-semibold text-on-surface-variant uppercase tracking-wider mb-3">
                    Evidence Metadata
                  </h4>
                  <div className="space-y-2">
                    {[
                      { label: 'Filename',   value: selected.filename },
                      { label: 'Type',       value: TYPE_LABEL[selected.type] || selected.type },
                      { label: 'Model',      value: selected.model || 'ADIS AI Model' },
                      { label: 'Analyzed',   value: selected.timestamp ? new Date(selected.timestamp).toLocaleString() : 'Unknown' },
                      { label: 'SHA-256',    value: selected.sha256 || 'Not recorded' },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex items-start gap-3 py-2 border-b border-outline-variant/50">
                        <span className="text-body-sm text-on-surface-variant w-24 shrink-0">{label}</span>
                        <span className="text-body-sm text-on-surface font-medium break-all">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Interpretation */}
                <div>
                  <h4 className="text-label-md font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                    Forensic Interpretation
                  </h4>
                  <p className="text-body-sm text-on-surface leading-relaxed bg-surface-container rounded p-3 border border-outline-variant">
                    {selected.verdict === 'FAKE'
                      ? `The AI model classified this ${selected.type} file as SYNTHETIC / MANIPULATED with ${selected.confidence}% confidence. The evidence exhibits statistical patterns inconsistent with authentic ${selected.type} capture. Recommend flagging as potentially fabricated.`
                      : selected.verdict === 'REAL'
                      ? `The AI model classified this ${selected.type} file as AUTHENTIC with ${selected.confidence}% confidence. No significant synthetic artifacts were detected.`
                      : `The AI model returned an INCONCLUSIVE result. Manual review by a qualified forensic examiner is required.`
                    }
                  </p>
                </div>

                {/* Disclaimer */}
                <div className="bg-surface-container-low border border-outline-variant rounded p-3">
                  <p className="text-label-sm text-on-surface-variant leading-relaxed">
                    <span className="font-semibold text-on-surface">Legal Disclaimer: </span>
                    This report is produced automatically by ADIS. AI forensic results are probabilistic and must be validated by a qualified human examiner before any legal use.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Last generated notification */}
          {lastGenerated && (
            <div className="flex items-center gap-3 px-4 py-3 bg-primary/10 border border-primary/30 rounded-xl">
              <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
              <div>
                <p className="text-label-sm font-semibold text-primary">PDF Downloaded</p>
                <p className="text-label-sm text-on-surface-variant">{lastGenerated}</p>
              </div>
              <button onClick={() => setLastGenerated(null)} className="ml-auto text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
          )}

        </div>
      </div>
      <div className="h-8" />
    </main>
  );
}
