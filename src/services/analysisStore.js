/**
 * ADIS Analysis Store
 * Persists all audio and video forensic analysis results to localStorage.
 * Provides read helpers consumed by DashboardPage for real statistics.
 */

const STORE_KEY = 'adis_analysis_history';
const MAX_ENTRIES = 200; // cap to avoid unbounded localStorage growth

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
 * Save a completed analysis result to the history store.
 * @param {'audio'|'video'|'image'} type
 * @param {string} filename
 * @param {'FAKE'|'REAL'|'INCONCLUSIVE'} verdict
 * @param {number} confidencePct  0-100
 * @param {boolean} simulated     true if result came from simulation fallback
 * @param {Object} [extra]        any additional fields (sha256, duration, model, etc.)
 */
export function saveAnalysisResult(type, filename, verdict, confidencePct, simulated, extra = {}) {
  try {
    const history = getAnalysisHistory();
    const record = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toISOString(),
      type,          // 'audio' | 'video' | 'image'
      filename,
      verdict,       // 'FAKE' | 'REAL' | 'INCONCLUSIVE'
      confidence: confidencePct,
      simulated,
      ...extra,
    };
    // Prepend (newest first) and trim to max
    const updated = [record, ...history].slice(0, MAX_ENTRIES);
    localStorage.setItem(STORE_KEY, JSON.stringify(updated));
    return record;
  } catch {
    return null;
  }
}

/**
 * Compute aggregate dashboard statistics from the stored history.
 * @returns {DashboardStats}
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

  // Average confidence for non-simulated FAKE detections
  const fakeReal = history.filter((r) => r.verdict === 'FAKE' && !r.simulated);
  const avgFakeConf = fakeReal.length
    ? fakeReal.reduce((s, r) => s + r.confidence, 0) / fakeReal.length
    : 0;

  // Last 7 days subset
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
    recentActivity: history.slice(0, 8), // newest 8 for activity timeline
  };
}

/**
 * Clear all stored analysis history (for testing / reset).
 */
export function clearAnalysisHistory() {
  localStorage.removeItem(STORE_KEY);
}
