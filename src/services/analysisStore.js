/**
 * ADIS Analysis Store
 * Persists all audio, video, and image forensic analysis results to SQLite DB (via backend API)
 * and maintains local state for real-time Dashboard, Reports, and Cross-Modal collaboration.
 */

const STORE_KEY = 'adis_analysis_history';
const MAX_ENTRIES = 200;

/**
 * Returns all stored analysis records, newest first.
 * @returns {Array<AnalysisRecord>}
 */
export function getAnalysisHistory() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

/**
 * Syncs database history from backend API (/api/history) into local store
 */
export async function syncBackendHistory() {
  try {
    const r = await fetch('/api/history?limit=200');
    if (r.ok) {
      const data = await r.json();
      if (data.success && Array.isArray(data.history) && data.history.length > 0) {
        const local = getAnalysisHistory();
        const mergedMap = new Map();
        
        // Populate with backend DB records first
        for (const item of data.history) {
          const key = item.id || item.analysis_id || item.sha256;
          if (key) mergedMap.set(key, item);
        }
        // Retain any un-synced local items
        for (const item of local) {
          const key = item.id || item.analysis_id || item.sha256;
          if (key && !mergedMap.has(key)) {
            mergedMap.set(key, item);
          }
        }

        const merged = Array.from(mergedMap.values()).slice(0, MAX_ENTRIES);
        localStorage.setItem(STORE_KEY, JSON.stringify(merged));
        return merged;
      }
    }
  } catch (err) {
    console.debug('[AnalysisStore] DB sync skipped (offline or server error):', err.message);
  }
  return getAnalysisHistory();
}

/**
 * Save a completed analysis result to the history store.
 */
export function saveAnalysisResult(type, filename, verdict, confidencePct, simulated, extra = {}) {
  try {
    const history = getAnalysisHistory();
    const record = {
      id: extra.analysis_id || `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toISOString(),
      type,          // 'audio' | 'video' | 'image'
      filename,
      verdict,       // 'FAKE' | 'REAL' | 'INCONCLUSIVE'
      confidence: confidencePct,
      simulated,
      ...extra,
    };
    const updated = [record, ...history].slice(0, MAX_ENTRIES);
    localStorage.setItem(STORE_KEY, JSON.stringify(updated));
    return record;
  } catch {
    return null;
  }
}

/**
 * Compute aggregate dashboard statistics from the stored history.
 */
export function getDashboardStats() {
  const history = getAnalysisHistory();

  const total      = history.length;
  const fakeCount  = history.filter((r) => r.verdict === 'FAKE').length;
  const realCount  = history.filter((r) => r.verdict === 'REAL').length;
  const audioCount = history.filter((r) => r.type === 'audio').length;
  const videoCount = history.filter((r) => r.type === 'video').length;
  const imageCount = history.filter((r) => r.type === 'image').length;
  const simCount   = history.filter((r) => r.simulated).length;
  const realModelCount = total - simCount;

  const fakeReal = history.filter((r) => r.verdict === 'FAKE' && !r.simulated);
  const avgFakeConf = fakeReal.length
    ? fakeReal.reduce((s, r) => s + r.confidence, 0) / fakeReal.length
    : 0;

  const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
  const last7 = history.filter((r) => new Date(r.timestamp).getTime() > sevenDaysAgo);

  return {
    total,
    fakeCount,
    realCount,
    audioCount,
    videoCount,
    imageCount,
    simCount,
    realModelCount,
    avgFakeConf: Math.round(avgFakeConf * 10) / 10,
    last7Days: last7.length,
    recentActivity: history.slice(0, 8),
  };
}

/**
 * Clear all stored analysis history from localStorage and backend DB.
 */
export function clearAnalysisHistory() {
  localStorage.removeItem(STORE_KEY);
  fetch('/api/history', { method: 'DELETE' }).catch(() => {});
}
