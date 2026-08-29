import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import RiskChart from '../components/RiskChart';
import { getDashboardStats, clearAnalysisHistory } from '../services/analysisStore';

const TYPE_ICON  = { audio: 'graphic_eq', video: 'videocam', image: 'image' };
const TYPE_LABEL = { audio: 'Audio', video: 'Video', image: 'Image' };

function timeAgo(isoString) {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins  = Math.floor(diff / 60000);
  const hrs   = Math.floor(mins / 60);
  const days  = Math.floor(hrs / 24);
  if (days  > 0) return `${days}d ago`;
  if (hrs   > 0) return `${hrs}h ago`;
  if (mins  > 0) return `${mins}m ago`;
  return 'just now';
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [backendOk, setBackendOk] = useState(null); // null=checking, true, false

  // Load stats on mount and whenever localStorage changes
  const refresh = () => setStats(getDashboardStats());
  useEffect(() => {
    refresh();
    // Re-read every 5 seconds so results from other tabs appear
    const interval = setInterval(refresh, 5000);
    window.addEventListener('storage', refresh);
    return () => { clearInterval(interval); window.removeEventListener('storage', refresh); };
  }, []);

  // Check backend health
  useEffect(() => {
    fetch('/api/health')
      .then((r) => setBackendOk(r.ok))
      .catch(() => setBackendOk(false));
  }, []);

  const hasData = stats && stats.total > 0;

  return (
    <main className="flex-1 overflow-y-auto p-gutter space-y-gutter">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="flex justify-between items-end mb-6 flex-wrap gap-3">
        <div>
          <h2 className="text-display-lg font-display-lg text-on-surface mb-1">Overview</h2>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Real-time forensic analysis statistics from this session.
          </p>
        </div>
        <div className="flex gap-2 items-center">
          {/* Backend status */}
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-label-sm border ${
            backendOk === null ? 'bg-surface-container text-on-surface-variant border-outline-variant'
            : backendOk ? 'bg-primary/10 text-primary border-primary/30'
            : 'bg-error/10 text-error border-error/30'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${
              backendOk === null ? 'bg-outline' : backendOk ? 'bg-primary animate-pulse' : 'bg-error'
            }`} />
            {backendOk === null ? 'Checking…' : backendOk ? 'Backend Online' : 'Backend Offline'}
          </div>
          {hasData && (
            <button
              onClick={() => { if (window.confirm('Clear all analysis history?')) { clearAnalysisHistory(); refresh(); } }}
              className="flex items-center gap-1.5 bg-surface border border-outline-variant px-3 py-1.5 rounded text-label-md text-on-surface-variant hover:bg-surface-container hover:text-error transition-colors"
            >
              <span className="material-symbols-outlined text-[16px]">delete_sweep</span>
              Reset
            </button>
          )}
        </div>
      </div>

      {/* ── No-data state ───────────────────────────────────────────── */}
      {!hasData && (
        <div className="glass-card rounded-xl p-10 flex flex-col items-center gap-4 text-center">
          <span className="material-symbols-outlined text-[48px] text-outline">analytics</span>
          <div>
            <p className="text-title-lg font-title-lg text-on-surface">No analyses yet</p>
            <p className="text-body-md text-on-surface-variant mt-1">
              Run your first audio or video forensic analysis and the stats will appear here in real time.
            </p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => navigate('/audio-forensics')} className="btn-primary px-4 py-2 rounded text-label-md flex items-center gap-2 bg-primary text-on-primary hover:bg-primary/90 transition-colors">
              <span className="material-symbols-outlined text-[18px]">graphic_eq</span>Analyze Audio
            </button>
            <button onClick={() => navigate('/video-forensics')} className="px-4 py-2 rounded text-label-md flex items-center gap-2 border border-outline-variant text-on-surface hover:bg-surface-container transition-colors">
              <span className="material-symbols-outlined text-[18px]">videocam</span>Analyze Video
            </button>
          </div>
        </div>
      )}

      {/* ── KPI Grid ────────────────────────────────────────────────── */}
      {hasData && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-gutter">
            {/* Total Analyses */}
            <div className="glass-card rounded-xl p-4 flex flex-col justify-between h-[120px]">
              <div className="flex justify-between items-start">
                <span className="text-label-md text-on-surface-variant">Total Analyses</span>
                <span className="material-symbols-outlined text-outline text-[20px]">analytics</span>
              </div>
              <div>
                <div className="text-headline-md font-headline-md text-on-surface">{stats.total}</div>
                <div className="text-label-sm text-on-surface-variant mt-0.5">
                  {stats.audioCount} audio · {stats.videoCount} video · {stats.imageCount} image
                </div>
              </div>
            </div>

            {/* Deepfakes Detected */}
            <div className="glass-card rounded-xl p-4 flex flex-col justify-between h-[120px] border-error/20 bg-error/5">
              <div className="flex justify-between items-start">
                <span className="text-label-md text-error">Deepfakes Detected</span>
                <span className="material-symbols-outlined text-error text-[20px]">warning</span>
              </div>
              <div>
                <div className="text-headline-md font-headline-md text-error">{stats.fakeCount}</div>
                <div className="text-label-sm text-error/70 mt-0.5">
                  {stats.total > 0 ? Math.round(stats.fakeCount / stats.total * 100) : 0}% of all analyses
                </div>
              </div>
            </div>

            {/* Authentic */}
            <div className="glass-card rounded-xl p-4 flex flex-col justify-between h-[120px]">
              <div className="flex justify-between items-start">
                <span className="text-label-md text-on-surface-variant">Authentic Files</span>
                <span className="material-symbols-outlined text-outline text-[20px]">verified</span>
              </div>
              <div>
                <div className="text-headline-md font-headline-md text-on-surface">{stats.realCount}</div>
                <div className="text-label-sm text-on-surface-variant mt-0.5">
                  {stats.total > 0 ? Math.round(stats.realCount / stats.total * 100) : 0}% passed verification
                </div>
              </div>
            </div>

            {/* Avg confidence */}
            <div className="glass-card rounded-xl p-4 flex flex-col justify-between h-[120px]">
              <div className="flex justify-between items-start">
                <span className="text-label-md text-on-surface-variant">Avg Fake Confidence</span>
                <span className="material-symbols-outlined text-outline text-[20px]">percent</span>
              </div>
              <div>
                <div className="text-headline-md font-headline-md text-on-surface">
                  {stats.realModelCount > 0 ? `${stats.avgFakeConf}%` : '—'}
                </div>
                <div className="text-label-sm text-on-surface-variant mt-0.5">
                  {stats.realModelCount} real model run{stats.realModelCount !== 1 ? 's' : ''}
                  {stats.simCount > 0 ? ` · ${stats.simCount} simulated` : ''}
                </div>
              </div>
            </div>
          </div>

          {/* ── Main content row ─────────────────────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter mt-gutter">

            {/* Activity Feed */}
            <div className="lg:col-span-2 glass-card rounded-xl flex flex-col overflow-hidden">
              <div className="p-4 border-b border-outline-variant flex justify-between items-center bg-surface-container-lowest">
                <h3 className="text-title-lg font-title-lg text-on-surface">Recent Analysis Activity</h3>
                <div className="flex gap-2">
                  <button onClick={() => navigate('/audio-forensics')} className="text-label-sm text-primary flex items-center gap-1">
                    + Audio <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                  </button>
                  <button onClick={() => navigate('/video-forensics')} className="text-label-sm text-primary flex items-center gap-1 ml-3">
                    + Video <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low border-b border-outline-variant">
                      <th className="py-2 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">Type</th>
                      <th className="py-2 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">File</th>
                      <th className="py-2 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">Verdict</th>
                      <th className="py-2 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">Confidence</th>
                      <th className="py-2 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">When</th>
                    </tr>
                  </thead>
                  <tbody className="text-body-sm font-body-sm divide-y divide-outline-variant bg-surface-container-lowest">
                    {stats.recentActivity.map((rec) => (
                      <tr key={rec.id} className="hover:bg-primary/5 transition-colors">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1.5 text-on-surface-variant">
                            <span className="material-symbols-outlined text-[16px]">{TYPE_ICON[rec.type] || 'description'}</span>
                            <span className="text-label-sm">{TYPE_LABEL[rec.type] || rec.type}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-on-surface font-medium truncate max-w-[180px]" title={rec.filename}>
                          {rec.filename}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-label-sm ${
                            rec.verdict === 'FAKE'
                              ? 'bg-error/15 text-error'
                              : rec.verdict === 'REAL'
                              ? 'bg-primary/10 text-primary'
                              : 'bg-surface-container-high text-on-surface'
                          }`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${
                              rec.verdict === 'FAKE' ? 'bg-error' : rec.verdict === 'REAL' ? 'bg-primary' : 'bg-outline'
                            }`} />
                            {rec.verdict}
                            {rec.simulated && <span className="text-[10px] opacity-60 ml-0.5">(sim)</span>}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${rec.verdict === 'FAKE' ? 'bg-error' : 'bg-primary'}`}
                                style={{ width: `${Math.min(100, rec.confidence)}%` }}
                              />
                            </div>
                            <span className="text-label-sm text-on-surface-variant">{rec.confidence}%</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-on-surface-variant">{timeAgo(rec.timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Right side panel */}
            <div className="flex flex-col gap-gutter">
              {/* Risk Distribution */}
              <div className="glass-card rounded-xl p-4 flex flex-col h-[280px]">
                <h3 className="text-title-lg font-title-lg text-on-surface mb-2">Risk Distribution</h3>
                <div className="flex-1 relative flex items-center justify-center">
                  <RiskChart fakeCount={stats.fakeCount} realCount={stats.realCount} />
                </div>
              </div>

              {/* Model breakdown */}
              <div className="glass-card rounded-xl p-4 flex-1">
                <h3 className="text-title-lg font-title-lg text-on-surface mb-4">Analysis Breakdown</h3>
                <div className="space-y-3">
                  {[
                    { label: 'Audio (YamNet)', count: stats.audioCount, icon: 'graphic_eq', color: 'bg-primary' },
                    { label: 'Video (EfficientNet)', count: stats.videoCount, icon: 'videocam', color: 'bg-secondary' },
                    { label: 'Image', count: stats.imageCount, icon: 'image', color: 'bg-tertiary' },
                  ].map(({ label, count, icon, color }) => (
                    <div key={label} className="flex items-center gap-3">
                      <span className="material-symbols-outlined text-on-surface-variant text-[18px]">{icon}</span>
                      <div className="flex-1">
                        <div className="flex justify-between text-label-sm text-on-surface mb-1">
                          <span>{label}</span><span>{count}</span>
                        </div>
                        <div className="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`${color} h-full rounded-full transition-all duration-700`}
                            style={{ width: stats.total > 0 ? `${(count / stats.total) * 100}%` : '0%' }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                  {stats.simCount > 0 && (
                    <p className="text-label-sm text-on-surface-variant pt-2 border-t border-outline-variant">
                      ⚠️ {stats.simCount} result{stats.simCount !== 1 ? 's' : ''} from simulation (backend was offline)
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      <div className="h-8" />
    </main>
  );
}
