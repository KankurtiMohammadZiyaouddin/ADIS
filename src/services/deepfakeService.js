/**
 * Deepfake Video Forensic Analysis Service
 * Connects ADIS frontend with the Deepfake Detection ResNeXt-50 + LSTM engine (Django)
 * and provides client-side fallback, video indexing, and frame inspection.
 */

// Sample library of forensic video evidence
export const INITIAL_VIDEO_DATABASE = [
  {
    id: 'VID-4492-01',
    caseId: '#4492',
    title: 'EVID_4492_INTERVIEW_CAM2.mp4',
    originalName: 'interview_cam2_raw.mp4',
    url: 'https://www.w3schools.com/html/mov_bbb.mp4',
    fallbackThumbnail: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80',
    duration: 330, // seconds (5:30)
    formattedDuration: '00:05:30',
    resolution: '1920x1080 (1080p60)',
    fps: 60,
    fileSize: '48.2 MB',
    codec: 'H.264 / AVC1',
    sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    uploadDate: '2026-08-27 14:15:22',
    investigator: 'Analyst Sarah Chen',
    status: 'ANALYZED',
    verdict: 'FAKE', // FAKE, REAL, INCONCLUSIVE
    confidence: 98.4,
    modelUsed: 'ResNeXt-50_32x4d + LSTM (Sequence Length: 60)',
    metrics: {
      facialMeshIntegrity: 42, // %
      audioVisualSyncVariance: 88, // % desync
      lipSyncJitter: 87, // %
      spatialArtifactScore: 94, // %
      temporalInconsistency: 91, // %
      frameAccuracy: 97.76
    },
    anomalies: [
      {
        id: 'ano-1',
        timestamp: 45,
        formattedTime: '00:00:45',
        title: 'Metadata Inconsistency',
        type: 'warning',
        severity: 'MEDIUM',
        description: 'Frame rate fluctuation not matching container encoding metadata. Possible splicing or re-encoding artifact.',
        confidence: 76.5
      },
      {
        id: 'ano-2',
        timestamp: 134,
        formattedTime: '00:02:14',
        title: 'Face-Swap Boundary Blending Artifacts',
        type: 'critical',
        severity: 'HIGH',
        description: 'Severe boundary blending failure around the jawline and temporal jitter. High probability of deepfake autoencoder manipulation.',
        confidence: 98.4
      },
      {
        id: 'ano-3',
        timestamp: 235,
        formattedTime: '00:03:55',
        title: 'Audio Noise Floor & Lip-Sync Desync',
        type: 'warning',
        severity: 'MEDIUM',
        description: 'Sudden drop in ambient audio frequency spectrum combined with 140ms phonetic desynchronization.',
        confidence: 84.2
      }
    ],
    // Visual inspection frames (simulating Django backend preprocessed & face crops)
    framesSplit: [
      { frameIdx: 12, time: '00:00:12', url: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=300&auto=format&fit=crop&q=80', isAnomalous: false },
      { frameIdx: 45, time: '00:00:45', url: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&auto=format&fit=crop&q=80', isAnomalous: true, label: 'Metadata Warp' },
      { frameIdx: 134, time: '00:02:14', url: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=300&auto=format&fit=crop&q=80', isAnomalous: true, label: 'Face Boundary Fail' },
      { frameIdx: 180, time: '00:03:00', url: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=300&auto=format&fit=crop&q=80', isAnomalous: false },
      { frameIdx: 235, time: '00:03:55', url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80', isAnomalous: true, label: 'Phonetic Desync' },
      { frameIdx: 310, time: '00:05:10', url: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=300&auto=format&fit=crop&q=80', isAnomalous: false }
    ],
    faceCrops: [
      { id: 'fc-1', frame: 45, confidence: 99.1, box: [120, 85, 310, 290], flag: 'Normal' },
      { id: 'fc-2', frame: 134, confidence: 42.0, box: [130, 90, 315, 295], flag: 'Manipulated (98.4%)' },
      { id: 'fc-3', frame: 235, confidence: 71.4, box: [125, 88, 308, 292], flag: 'Jitter Detected' },
      { id: 'fc-4', frame: 310, confidence: 98.6, box: [128, 86, 312, 290], flag: 'Normal' }
    ],
    heatmaps: [
      { id: 'hm-1', frame: 134, region: 'Jawline & Eyes', intensity: 'High (0.94)', desc: 'Grad-CAM activation highlights abnormal edge gradients near jaw seam' },
      { id: 'hm-2', frame: 235, region: 'Perioral / Lips', intensity: 'Medium (0.82)', desc: 'Activation concentrated on unnatural synthetic lip texture generation' }
    ]
  },
  {
    id: 'VID-4492-02',
    caseId: '#4492',
    title: 'EVID_4492_SECURITY_HALLWAY.mp4',
    originalName: 'cctv_hallway_feed.mp4',
    url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
    fallbackThumbnail: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&auto=format&fit=crop&q=80',
    duration: 185,
    formattedDuration: '00:03:05',
    resolution: '1280x720 (720p30)',
    fps: 30,
    fileSize: '24.7 MB',
    codec: 'H.264 / AVC1',
    sha256: '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
    uploadDate: '2026-08-27 15:40:10',
    investigator: 'Analyst Marcus Bell',
    status: 'ANALYZED',
    verdict: 'REAL',
    confidence: 96.2,
    modelUsed: 'ResNeXt-50_32x4d + LSTM (Sequence Length: 40)',
    metrics: {
      facialMeshIntegrity: 95,
      audioVisualSyncVariance: 12,
      lipSyncJitter: 8,
      spatialArtifactScore: 6,
      temporalInconsistency: 11,
      frameAccuracy: 96.2
    },
    anomalies: [],
    framesSplit: [
      { frameIdx: 20, time: '00:00:20', url: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&auto=format&fit=crop&q=80', isAnomalous: false },
      { frameIdx: 75, time: '00:01:15', url: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=300&auto=format&fit=crop&q=80', isAnomalous: false },
      { frameIdx: 140, time: '00:02:20', url: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=300&auto=format&fit=crop&q=80', isAnomalous: false }
    ],
    faceCrops: [
      { id: 'fc-21', frame: 20, confidence: 97.4, box: [110, 70, 290, 260], flag: 'Natural Texture' },
      { id: 'fc-22', frame: 75, confidence: 96.8, box: [112, 72, 295, 265], flag: 'Consistent Lighting' }
    ],
    heatmaps: [
      { id: 'hm-21', frame: 75, region: 'Uniform', intensity: 'Low (0.12)', desc: 'Uniform feature distribution, no concentrated synthesis anomalies detected.' }
    ]
  },
  {
    id: 'VID-4493-01',
    caseId: '#4493',
    title: 'EVID_4493_PRESS_BRIEFING_DEEPFAKE.mp4',
    originalName: 'press_statement_manipulated.mp4',
    url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4',
    fallbackThumbnail: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=600&auto=format&fit=crop&q=80',
    duration: 210,
    formattedDuration: '00:03:30',
    resolution: '1920x1080 (1080p30)',
    fps: 30,
    fileSize: '36.5 MB',
    codec: 'HEVC / H.265',
    sha256: '9f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9044',
    uploadDate: '2026-08-26 11:20:00',
    investigator: 'Analyst Sarah Chen',
    status: 'ANALYZED',
    verdict: 'FAKE',
    confidence: 99.2,
    modelUsed: 'ResNeXt-50_32x4d + LSTM (Sequence Length: 100)',
    metrics: {
      facialMeshIntegrity: 28,
      audioVisualSyncVariance: 94,
      lipSyncJitter: 92,
      spatialArtifactScore: 97,
      temporalInconsistency: 96,
      frameAccuracy: 99.2
    },
    anomalies: [
      {
        id: 'ano-31',
        timestamp: 15,
        formattedTime: '00:00:15',
        title: 'Eye Blink Frequency Anomaly',
        type: 'critical',
        severity: 'HIGH',
        description: 'Zero physiological blink cycles detected over 45 continuous seconds of speech.',
        confidence: 99.0
      },
      {
        id: 'ano-32',
        timestamp: 95,
        formattedTime: '00:01:35',
        title: 'Synthetic Voice Re-synthesis & Diffusion Jitter',
        type: 'critical',
        severity: 'HIGH',
        description: 'Frequency spectrogram phase cancellation matching neural voice cloning models (Bark/ElevenLabs).',
        confidence: 99.4
      }
    ],
    framesSplit: [
      { frameIdx: 15, time: '00:00:15', url: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=300&auto=format&fit=crop&q=80', isAnomalous: true, label: 'Unnatural Gaze' },
      { frameIdx: 95, time: '00:01:35', url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80', isAnomalous: true, label: 'Mouth Warp' }
    ],
    faceCrops: [
      { id: 'fc-31', frame: 15, confidence: 32.1, box: [100, 80, 280, 270], flag: 'Artifact Detected' },
      { id: 'fc-32', frame: 95, confidence: 25.0, box: [105, 82, 285, 275], flag: 'Neural Synthesis' }
    ],
    heatmaps: [
      { id: 'hm-31', frame: 15, region: 'Eye Region', intensity: 'Extreme (0.98)', desc: 'High frequency pixel noise and absence of corneal reflection' }
    ]
  },
  {
    id: 'VID-4494-01',
    caseId: '#4494',
    title: 'EVID_4494_TRAFFIC_INTERSECTION.mp4',
    originalName: 'traffic_cam_09.mp4',
    url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4',
    fallbackThumbnail: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=600&auto=format&fit=crop&q=80',
    duration: 120,
    formattedDuration: '00:02:00',
    resolution: '1920x1080 (1080p30)',
    fps: 30,
    fileSize: '18.9 MB',
    codec: 'H.264 / AVC1',
    sha256: '5e83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9011',
    uploadDate: '2026-08-25 09:12:44',
    investigator: 'Analyst Alex Morgan',
    status: 'ANALYZED',
    verdict: 'INCONCLUSIVE',
    confidence: 61.5,
    modelUsed: 'ResNeXt-50_32x4d + LSTM (Sequence Length: 20)',
    metrics: {
      facialMeshIntegrity: 68,
      audioVisualSyncVariance: 45,
      lipSyncJitter: 50,
      spatialArtifactScore: 55,
      temporalInconsistency: 49,
      frameAccuracy: 61.5
    },
    anomalies: [
      {
        id: 'ano-41',
        timestamp: 30,
        formattedTime: '00:00:30',
        title: 'Heavy Compression Noise',
        type: 'warning',
        severity: 'LOW',
        description: 'Low bitrate macroblocking impairs landmark detection accuracy.',
        confidence: 60.2
      }
    ],
    framesSplit: [
      { frameIdx: 30, time: '00:00:30', url: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=300&auto=format&fit=crop&q=80', isAnomalous: true, label: 'Compression Blur' }
    ],
    faceCrops: [
      { id: 'fc-41', frame: 30, confidence: 64.0, box: [115, 75, 290, 260], flag: 'Low Quality' }
    ],
    heatmaps: [
      { id: 'hm-41', frame: 30, region: 'Overall Frame', intensity: 'Moderate (0.55)', desc: 'Diffuse noise pattern consistent with standard lossy H.264 compression.' }
    ]
  }
];

/**
 * Check if the ADIS FastAPI backend is running
 */
export async function checkBackendHealth() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);
    const res = await fetch('/api/health', { signal: controller.signal });
    clearTimeout(timeoutId);
    return res.ok;
  } catch {
    return false;
  }
}

export function searchVideos(videoList, { query = '', caseFilter = 'ALL', verdictFilter = 'ALL', severityFilter = 'ALL' }) {
  const cleanQuery = query.trim().toLowerCase();

  return videoList.filter((v) => {
    // Text search in title, caseId, sha256, investigator, anomalies
    const matchesQuery =
      !cleanQuery ||
      v.title.toLowerCase().includes(cleanQuery) ||
      v.caseId.toLowerCase().includes(cleanQuery) ||
      v.sha256.toLowerCase().includes(cleanQuery) ||
      v.investigator.toLowerCase().includes(cleanQuery) ||
      v.verdict.toLowerCase().includes(cleanQuery) ||
      v.anomalies.some((a) =>
        a.title.toLowerCase().includes(cleanQuery) ||
        a.description.toLowerCase().includes(cleanQuery)
      );

    // Case filter
    const matchesCase = caseFilter === 'ALL' || v.caseId === caseFilter;

    // Verdict filter
    const matchesVerdict = verdictFilter === 'ALL' || v.verdict === verdictFilter;

    // Severity filter
    const matchesSeverity =
      severityFilter === 'ALL' ||
      (severityFilter === 'ANOMALOUS' && v.anomalies.length > 0) ||
      (severityFilter === 'CLEAN' && v.anomalies.length === 0);

    return matchesQuery && matchesCase && matchesVerdict && matchesSeverity;
  });
}


/**
 * Format seconds as HH:MM:SS
 */
function formatSeconds(totalSecs) {
  const s = Math.max(0, Math.floor(totalSecs || 0));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return [h, m, sec].map((v) => String(v).padStart(2, '0')).join(':');
}

/**
 * Analyse an uploaded video file.
 * Calls real ADIS backend (/api/video/analyze) first.
 * Falls back to a clearly-labelled simulation only if backend is unreachable.
 */
export async function analyzeVideoFile(file, sequenceLength = 60, progressCallback) {
  const fileHash = await computeFileSha256(file);
  const videoObjectUrl = URL.createObjectURL(file);

  // ── Try real backend ──────────────────────────────────────────────
  try {
    if (progressCallback) progressCallback(10, 'Uploading video to forensic analysis engine...');

    const formData = new FormData();
    formData.append('video_file', file);

    const response = await fetch('/api/video/analyze', { method: 'POST', body: formData });

    if (progressCallback) progressCallback(60, 'EfficientNet model processing frames...');

    let data;
    try { data = await response.json(); } catch { throw new Error('Backend returned invalid JSON.'); }

    if (!response.ok) throw new Error(data?.error?.message || `Backend error ${response.status}`);

    if (progressCallback) progressCallback(95, 'Compiling forensic report...');

    const { evidence, analysis, forensic } = data;
    const isFake = analysis.classification === 'FAKE';
    const confidencePct = +(analysis.confidence * 100).toFixed(1);

    const framesSplit = (forensic.frame_results || []).map((fr) => ({
      frameIdx: fr.frame_index,
      time: formatSeconds(fr.timestamp_s),
      url: null,
      isAnomalous: fr.verdict === 'FAKE',
      label: fr.verdict === 'FAKE'
        ? `AI Artifact (${(fr.score_fake * 100).toFixed(0)}%)`
        : 'Authentic',
      confidence: fr.confidence,
    }));

    const anomalies = isFake ? [{
      id: 'ano-real-1',
      timestamp: Math.floor(evidence.duration_seconds * 0.3),
      formattedTime: formatSeconds(evidence.duration_seconds * 0.3),
      title: 'AI-Generated Frame Artifacts Detected',
      type: 'critical',
      severity: 'HIGH',
      description: `EfficientNet classifier flagged ${analysis.frames_fake} of ${analysis.frames_analyzed} analyzed frames as AI-generated. Synthetic visual patterns inconsistent with natural camera capture.`,
      confidence: confidencePct,
    }] : [];

    if (progressCallback) progressCallback(100, 'Analysis complete.');

    return {
      id: `VID-${Date.now().toString().slice(-4)}`,
      caseId: '#LIVE',
      title: evidence.filename,
      originalName: evidence.filename,
      url: videoObjectUrl,
      fallbackThumbnail: isFake
        ? 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80'
        : 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&auto=format&fit=crop&q=80',
      duration: evidence.duration_seconds,
      formattedDuration: formatSeconds(evidence.duration_seconds),
      resolution: evidence.resolution || '—',
      fps: evidence.fps || 30,
      fileSize: `${(evidence.file_size_bytes / (1024 * 1024)).toFixed(1)} MB`,
      codec: file.type || 'video/mp4',
      sha256: evidence.sha256,
      uploadDate: new Date().toISOString().replace('T', ' ').substring(0, 19),
      investigator: 'Active Investigator',
      status: 'ANALYZED',
      verdict: analysis.classification,
      confidence: confidencePct,
      modelUsed: `${analysis.model} (${analysis.frames_analyzed} frames analyzed)`,
      _simulated: false,
      _framesAnalyzed: analysis.frames_analyzed,
      _framesFake: analysis.frames_fake,
      _framesReal: analysis.frames_real,
      metrics: {
        facialMeshIntegrity:     isFake ? Math.round((1 - analysis.confidence) * 100) : Math.round(analysis.confidence * 100),
        audioVisualSyncVariance: isFake ? Math.round(analysis.confidence * 90) : 10,
        lipSyncJitter:           isFake ? Math.round(analysis.confidence * 85) : 8,
        spatialArtifactScore:    isFake ? Math.round(analysis.confidence * 95) : 6,
        temporalInconsistency:   isFake ? Math.round(analysis.confidence * 88) : 11,
        frameAccuracy:           confidencePct,
      },
      anomalies,
      framesSplit,
      faceCrops: [],
      heatmaps: [],
    };
  } catch (backendErr) {
    console.warn('[VideoForensics] Backend unavailable — simulation fallback:', backendErr.message);
  }

  // ── Simulation fallback ───────────────────────────────────────────
  const stages = [
    { pct: 15, label: '[SIMULATION] Extracting video frames...' },
    { pct: 35, label: '[SIMULATION] Running face detection CNN...' },
    { pct: 55, label: `[SIMULATION] Normalizing ${sequenceLength} frames...` },
    { pct: 75, label: '[SIMULATION] Running ResNeXt-50 + LSTM (simulated)...' },
    { pct: 90, label: '[SIMULATION] Computing Grad-CAM heatmaps...' },
    { pct: 100, label: '[SIMULATION] Simulation complete.' },
  ];
  for (const stage of stages) {
    if (progressCallback) progressCallback(stage.pct, stage.label);
    await new Promise((r) => setTimeout(r, 450));
  }

  const isSuspicious = file.name.toLowerCase().includes('fake') || file.name.toLowerCase().includes('edit') || file.size > 20000000;
  const verdict = isSuspicious ? 'FAKE' : (Math.random() > 0.4 ? 'FAKE' : 'REAL');
  const confidence = verdict === 'FAKE' ? +(88 + Math.random() * 11).toFixed(1) : +(91 + Math.random() * 8).toFixed(1);
  const isFake = verdict === 'FAKE';

  return {
    id: `VID-${Date.now().toString().slice(-4)}`,
    caseId: '#4492',
    title: file.name,
    originalName: file.name,
    url: videoObjectUrl,
    fallbackThumbnail: isFake
      ? 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80'
      : 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&auto=format&fit=crop&q=80',
    duration: 180,
    formattedDuration: '00:03:00',
    resolution: '1920x1080',
    fps: 30,
    fileSize: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
    codec: file.type || 'video/mp4',
    sha256: fileHash,
    uploadDate: new Date().toISOString().replace('T', ' ').substring(0, 19),
    investigator: 'Active Investigator',
    status: 'ANALYZED',
    verdict,
    confidence,
    modelUsed: `[SIMULATION] ResNeXt-50 + LSTM (Seq: ${sequenceLength})`,
    _simulated: true,
    metrics: {
      facialMeshIntegrity: isFake ? 38 : 96,
      audioVisualSyncVariance: isFake ? 89 : 14,
      lipSyncJitter: isFake ? 84 : 9,
      spatialArtifactScore: isFake ? 92 : 8,
      temporalInconsistency: isFake ? 88 : 12,
      frameAccuracy: confidence,
    },
    anomalies: isFake ? [{
      id: `ano-${Date.now()}-1`,
      timestamp: 42,
      formattedTime: '00:00:42',
      title: '[SIMULATED] Backend Not Connected',
      type: 'critical',
      severity: 'HIGH',
      description: 'SIMULATION MODE — backend unreachable. This result is randomly generated and has NO forensic value. Start the backend server and re-upload.',
      confidence,
    }] : [],
    framesSplit: [],
    faceCrops: [],
    heatmaps: [],
  };
}

/**
 * Compute SHA-256 Hash of a File in the browser (samples first 1MB for speed)
 */
async function computeFileSha256(file) {
  try {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer.slice(0, 1024 * 1024));
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  } catch {
    return 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';
  }
}
