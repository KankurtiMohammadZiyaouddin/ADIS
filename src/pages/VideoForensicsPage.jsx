import { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  INITIAL_VIDEO_DATABASE,
  searchVideos,
  analyzeVideoFile,
  checkBackendHealth
} from '../services/deepfakeService';

export default function VideoForensicsPage() {
  const [searchParams] = useSearchParams();
  const initialVideoId = searchParams.get('videoId');

  // Video Database & Search State
  const [videoList, setVideoList] = useState(INITIAL_VIDEO_DATABASE);
  const [selectedVideo, setSelectedVideo] = useState(() => {
    if (initialVideoId) {
      const match = INITIAL_VIDEO_DATABASE.find((v) => v.id === initialVideoId);
      if (match) return match;
    }
    return INITIAL_VIDEO_DATABASE[0];
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [caseFilter, setCaseFilter] = useState('ALL');
  const [verdictFilter, setVerdictFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [isSearchDrawerOpen, setIsSearchDrawerOpen] = useState(false);

  // Player State
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(selectedVideo.duration || 330);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [isMuted, setIsMuted] = useState(false);
  const [activeAnomaly, setActiveAnomaly] = useState(null);
  const [videoError, setVideoError] = useState(false);

  // Inspection Tabs State: 'temporal' | 'frames' | 'faces' | 'heatmaps'
  const [activeTab, setActiveTab] = useState('temporal');

  // Verdict & Notes
  const [verdict, setVerdict] = useState(selectedVideo.verdict);
  const [investigatorNotes, setInvestigatorNotes] = useState(
    'Facial boundary blending artifacts detected around the jaw perimeter at timestamp 00:02:14. Audio-visual phonetic desync confirms deepfake neural synthesis.'
  );
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportCopied, setReportCopied] = useState(false);

  // Upload Modal & Analysis Pipeline State
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [sequenceLength, setSequenceLength] = useState(60);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisStepLabel, setAnalysisStepLabel] = useState('');

  // Backend Connectivity State
  const [isBackendConnected, setIsBackendConnected] = useState(false);

  // Check Django Backend connectivity on mount
  useEffect(() => {
    checkBackendHealth().then((alive) => {
      setIsBackendConnected(alive);
    });
  }, []);

  // Sync selected video changes
  useEffect(() => {
    if (selectedVideo) {
      setVerdict(selectedVideo.verdict);
      setCurrentTime(0);
      setIsPlaying(false);
      setActiveAnomaly(selectedVideo.anomalies?.[0] || null);
      if (videoRef.current) {
        videoRef.current.currentTime = 0;
      }
    }
  }, [selectedVideo]);

  // Reset videoError when selected video changes
  useEffect(() => {
    setVideoError(false);
  }, [selectedVideo]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);

      // Check if current time hits an anomaly segment
      const hit = selectedVideo.anomalies?.find(
        (a) => Math.abs(a.timestamp - video.currentTime) < 2.5
      );
      setActiveAnomaly(hit || null);

      // Draw dynamic face-tracking bounding box on overlay canvas
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Simulated facial coordinates with organic micro-movement
        const wobbleX = Math.sin(video.currentTime * 3) * 6;
        const wobbleY = Math.cos(video.currentTime * 2) * 4;

        const boxWidth = canvas.width * 0.32;
        const boxHeight = canvas.height * 0.52;
        const boxX = (canvas.width - boxWidth) / 2 + wobbleX;
        const boxY = (canvas.height - boxHeight) / 2.6 + wobbleY;

        const isFake = selectedVideo.verdict === 'FAKE';
        const color = isFake ? '#ef4444' : '#10b981';

        // Draw outer bounding box
        ctx.strokeStyle = color;
        ctx.lineWidth = 2.5;
        ctx.setLineDash([]);
        ctx.strokeRect(boxX, boxY, boxWidth, boxHeight);

        // Draw Corner Highlights (Forensic Crosshairs)
        const cl = 14;
        ctx.lineWidth = 4;
        // Top-left
        ctx.beginPath();
        ctx.moveTo(boxX, boxY + cl);
        ctx.lineTo(boxX, boxY);
        ctx.lineTo(boxX + cl, boxY);
        ctx.stroke();
        // Top-right
        ctx.beginPath();
        ctx.moveTo(boxX + boxWidth - cl, boxY);
        ctx.lineTo(boxX + boxWidth, boxY);
        ctx.lineTo(boxX + boxWidth, boxY + cl);
        ctx.stroke();
        // Bottom-left
        ctx.beginPath();
        ctx.moveTo(boxX, boxY + boxHeight - cl);
        ctx.lineTo(boxX, boxY + boxHeight);
        ctx.lineTo(boxX + cl, boxY + boxHeight);
        ctx.stroke();
        // Bottom-right
        ctx.beginPath();
        ctx.moveTo(boxX + boxWidth - cl, boxY + boxHeight);
        ctx.lineTo(boxX + boxWidth, boxY + boxHeight);
        ctx.lineTo(boxX + boxWidth, boxY + boxHeight - cl);
        ctx.stroke();

        // Draw Landmark Mesh Points
        ctx.fillStyle = isFake ? 'rgba(239, 68, 68, 0.75)' : 'rgba(16, 185, 129, 0.75)';
        const landmarks = [
          [boxX + boxWidth * 0.32, boxY + boxHeight * 0.35], // Left Eye
          [boxX + boxWidth * 0.68, boxY + boxHeight * 0.35], // Right Eye
          [boxX + boxWidth * 0.50, boxY + boxHeight * 0.52], // Nose Tip
          [boxX + boxWidth * 0.35, boxY + boxHeight * 0.72], // Mouth Left
          [boxX + boxWidth * 0.65, boxY + boxHeight * 0.72], // Mouth Right
          [boxX + boxWidth * 0.50, boxY + boxHeight * 0.80], // Chin
        ];
        landmarks.forEach(([lx, ly]) => {
          ctx.beginPath();
          ctx.arc(lx, ly, 3.5, 0, Math.PI * 2);
          ctx.fill();
        });

        // Draw Mesh Connecting Lines
        ctx.strokeStyle = isFake ? 'rgba(239, 68, 68, 0.35)' : 'rgba(16, 185, 129, 0.35)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(landmarks[0][0], landmarks[0][1]);
        ctx.lineTo(landmarks[1][0], landmarks[1][1]);
        ctx.lineTo(landmarks[2][0], landmarks[2][1]);
        ctx.closePath();
        ctx.stroke();

        // Draw Bounding Box Header Badge
        ctx.fillStyle = color;
        ctx.fillRect(boxX, boxY - 26, boxWidth, 26);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 12px monospace';
        ctx.fillText(
          `${selectedVideo.verdict}: ${selectedVideo.confidence}% CONF`,
          boxX + 8,
          boxY - 8
        );

        // Draw Active Anomaly Tag if inside segment
        if (hit) {
          ctx.fillStyle = 'rgba(239, 68, 68, 0.9)';
          ctx.fillRect(boxX, boxY + boxHeight + 4, boxWidth, 22);
          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 10px monospace';
          ctx.fillText(`FLAG: ${hit.title.substring(0, 24)}...`, boxX + 6, boxY + boxHeight + 18);
        }
      }
    };

    const handleLoadedMetadata = () => {
      setDuration(video.duration || selectedVideo.duration || 180);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('ended', () => setIsPlaying(false));

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };
  }, [selectedVideo]);

  // Video Controls
  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {
        // Fallback for autoplay policy
        setIsPlaying(true);
      });
    }
  };

  const handleSeek = (newTime) => {
    if (videoRef.current) {
      videoRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const stepFrame = (secondsOffset) => {
    if (videoRef.current) {
      const nextTime = Math.max(0, Math.min(duration, videoRef.current.currentTime + secondsOffset));
      videoRef.current.currentTime = nextTime;
      setCurrentTime(nextTime);
    }
  };

  const handleSpeedChange = (speed) => {
    setPlaybackSpeed(speed);
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
    }
  };

  const jumpToAnomaly = (anomaly) => {
    handleSeek(anomaly.timestamp);
    setActiveAnomaly(anomaly);
  };

  // Video Upload & Deepfake Detection Execution
  const handleStartAnalysis = async () => {
    if (!uploadFile) return;
    setIsAnalyzing(true);
    setAnalysisProgress(5);
    setAnalysisStepLabel('Initializing neural analysis pipeline...');

    try {
      const analyzedResult = await analyzeVideoFile(
        uploadFile,
        sequenceLength,
        (pct, label) => {
          setAnalysisProgress(pct);
          setAnalysisStepLabel(label);
        }
      );

      // Add newly analyzed video to repository and select it
      setVideoList((prev) => [analyzedResult, ...prev]);
      setSelectedVideo(analyzedResult);
      setVerdict(analyzedResult.verdict);
      setIsAnalyzing(false);
      setUploadModalOpen(false);
      setUploadFile(null);
    } catch (err) {
      console.error('Analysis failed:', err);
      setIsAnalyzing(false);
    }
  };

  // Filtered Video Evidence List
  const filteredVideos = searchVideos(videoList, {
    query: searchQuery,
    caseFilter,
    verdictFilter,
    severityFilter
  });

  // Unique Case IDs for filter dropdown
  const uniqueCases = ['ALL', ...Array.from(new Set(videoList.map((v) => v.caseId)))];

  // Helper formatting for time (seconds -> HH:MM:SS)
  const formatTime = (secs) => {
    const s = Math.floor(secs || 0);
    const hours = Math.floor(s / 3600);
    const minutes = Math.floor((s % 3600) / 60);
    const seconds = s % 60;
    const pad = (n) => n.toString().padStart(2, '0');
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  };

  return (
    <main className="flex-1 flex flex-col min-w-0 bg-background h-screen overflow-hidden">

      {/* ── Simulation Mode Warning Banner ─────────────────────────── */}
      {selectedVideo?._simulated && (
        <div className="shrink-0 bg-amber-500/15 border-b border-amber-500/40 px-4 py-2.5 flex items-center gap-3">
          <span className="material-symbols-outlined text-amber-400 text-[20px] shrink-0">warning</span>
          <div className="flex-1 min-w-0">
            <span className="text-amber-300 font-semibold text-label-sm">Simulation Mode — Results Are Random</span>
            <span className="text-amber-200/80 text-label-sm ml-2">
              The forensic backend is not reachable. These scores are NOT from a real AI model.
              Start the backend server and re-upload the video to get real results.
            </span>
          </div>
          <button
            onClick={() => setUploadModalOpen(true)}
            className="shrink-0 px-3 py-1 bg-amber-500 text-black rounded text-label-sm font-semibold hover:bg-amber-400 transition-colors"
          >
            Re-Upload
          </button>
        </div>
      )}

      {/* Top Search & Evidence Selector Toolbar */}
      <div className="h-14 px-4 bg-surface border-b border-outline-variant flex items-center justify-between shrink-0 gap-4">
        {/* Left: Video Search Bar */}
        <div className="flex items-center gap-3 flex-1 max-w-xl">
          <div className="relative flex-1">
            <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-on-surface-variant">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search videos by name, case ID, hash, or anomaly..."
              className="w-full bg-surface-container-low border border-outline-variant rounded-lg pl-9 pr-4 py-1.5 text-body-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:border-primary transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-2.5 text-on-surface-variant hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-[16px]">close</span>
              </button>
            )}
          </div>

          {/* Quick Case Filter */}
          <select
            value={caseFilter}
            onChange={(e) => setCaseFilter(e.target.value)}
            className="bg-surface-container border border-outline-variant text-body-sm text-on-surface rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-primary"
          >
            {uniqueCases.map((c) => (
              <option key={c} value={c}>
                {c === 'ALL' ? 'All Cases' : `Case ${c}`}
              </option>
            ))}
          </select>

          {/* Quick Verdict Filter */}
          <select
            value={verdictFilter}
            onChange={(e) => setVerdictFilter(e.target.value)}
            className="bg-surface-container border border-outline-variant text-body-sm text-on-surface rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-primary"
          >
            <option value="ALL">All Verdicts</option>
            <option value="FAKE">Deepfakes (Manipulated)</option>
            <option value="REAL">Authentic</option>
            <option value="INCONCLUSIVE">Inconclusive</option>
          </select>
        </div>

        {/* Right: Actions, Video Selector Drawer Toggle & Upload */}
        <div className="flex items-center gap-2">
          {/* Backend Status Pill */}
          <div
            className={`hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-label-sm border ${
              isBackendConnected
                ? 'bg-primary/10 text-primary border-primary/30'
                : 'bg-surface-container-highest text-on-surface-variant border-outline-variant'
            }`}
            title={
              isBackendConnected
                ? 'Django PyTorch ResNeXt50+LSTM Backend is online'
                : 'Running on Standalone Forensic Engine'
            }
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isBackendConnected ? 'bg-primary animate-pulse' : 'bg-outline'
              }`}
            />
            <span>
              {isBackendConnected ? 'Django AI Backend Online' : 'Standalone Forensic Engine'}
            </span>
          </div>

          {/* Video Repository Browser Drawer Button */}
          <button
            onClick={() => setIsSearchDrawerOpen(!isSearchDrawerOpen)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-label-md border transition-colors ${
              isSearchDrawerOpen
                ? 'bg-primary text-on-primary border-primary'
                : 'bg-surface border-outline-variant text-on-surface hover:bg-surface-container'
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">video_library</span>
            <span>Evidence List ({filteredVideos.length})</span>
          </button>

          {/* Upload & Run Deepfake Detection Button */}
          <button
            onClick={() => setUploadModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-primary text-on-primary rounded-lg text-label-md font-medium hover:bg-primary/90 transition-all shadow-sm"
          >
            <span className="material-symbols-outlined text-[18px]">upload_file</span>
            <span>Analyze Video</span>
          </button>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Main Forensic Canvas */}
        <div className="flex-1 p-4 flex gap-4 overflow-hidden">
          {/* Left Column: Interactive Video Player & Timeline */}
          <div className="flex-1 flex flex-col gap-3 min-w-0 h-full overflow-hidden">
            {/* Video Player Box */}
            <div className="flex-1 bg-[#050811] rounded-xl border border-outline-variant overflow-hidden flex flex-col relative shadow-md">
              {/* Video Info Header Bar */}
              <div className="h-10 bg-surface/80 backdrop-blur-md absolute top-0 w-full flex items-center justify-between px-4 z-20 border-b border-outline-variant/40 text-on-surface">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="material-symbols-outlined text-[18px] text-primary">videocam</span>
                  <span className="text-label-md font-mono font-medium truncate">
                    {selectedVideo.title}
                  </span>
                  <span className="text-label-sm text-on-surface-variant hidden sm:inline">
                    ({selectedVideo.caseId})
                  </span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="px-2 py-0.5 bg-surface-container-highest text-on-surface-variant text-[11px] rounded font-mono border border-outline-variant">
                    {selectedVideo.resolution}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-[11px] rounded font-bold uppercase tracking-wider ${
                      selectedVideo.verdict === 'FAKE'
                        ? 'bg-error/20 text-error border border-error/30'
                        : selectedVideo.verdict === 'REAL'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {selectedVideo.verdict === 'FAKE'
                      ? `AI MANIPULATION DETECTED (${selectedVideo.confidence}%)`
                      : selectedVideo.verdict === 'REAL'
                      ? `AUTHENTIC VIDEO (${selectedVideo.confidence}%)`
                      : `INCONCLUSIVE (${selectedVideo.confidence}%)`}
                  </span>
                </div>
              </div>

              {/* Viewport: Video & Face Tracking Canvas Overlay */}
              <div className="flex-1 relative w-full h-full flex items-center justify-center bg-black overflow-hidden pt-10">
                <video
                  ref={videoRef}
                  src={selectedVideo.url}
                  poster={selectedVideo.fallbackThumbnail}
                  className={`max-h-full max-w-full object-contain ${videoError ? 'hidden' : ''}`}
                  playsInline
                  muted={isMuted}
                  onClick={togglePlay}
                  onError={() => setVideoError(true)}
                />

                {/* No-video fallback when URL fails (e.g. no internet / CORS) */}
                {videoError && (
                  <div className="flex flex-col items-center justify-center gap-4 text-center px-6">
                    <span className="material-symbols-outlined text-[48px] text-outline">videocam_off</span>
                    <div>
                      <p className="text-label-md font-semibold text-on-surface-variant">Sample Video Unavailable</p>
                      <p className="text-body-sm text-outline mt-1 max-w-xs">
                        The demo video could not be loaded (network or CORS restriction).<br/>
                        <strong className="text-primary">Upload your own video</strong> using the &ldquo;Analyze Video&rdquo; button to run the deepfake detector.
                      </p>
                    </div>
                    <button
                      onClick={() => setUploadModalOpen(true)}
                      className="mt-1 px-4 py-2 bg-primary text-on-primary rounded-lg text-body-sm font-medium hover:bg-primary/90 flex items-center gap-2"
                    >
                      <span className="material-symbols-outlined text-[18px]">upload</span>
                      Upload Video File
                    </button>
                  </div>
                )}

                {/* Dynamic Facial Mesh & Landmark Tracking Overlay Canvas */}
                <canvas
                  ref={canvasRef}
                  width={640}
                  height={360}
                  className="absolute inset-0 w-full h-full object-contain pointer-events-none z-10"
                />

                {/* Floating Active Anomaly Alert Badge */}
                {activeAnomaly && (
                  <div className="absolute bottom-4 left-4 bg-surface/90 backdrop-blur-md border border-error/80 rounded-lg p-2.5 max-w-sm shadow-xl z-20 flex items-start gap-2.5 animate-fadeIn">
                    <span className="material-symbols-outlined text-error text-[20px] shrink-0 mt-0.5">
                      gpp_bad
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-label-sm font-bold text-error">
                          {activeAnomaly.title}
                        </span>
                        <span className="font-mono text-[10px] bg-error/20 text-error px-1 rounded">
                          {activeAnomaly.formattedTime}
                        </span>
                      </div>
                      <p className="text-body-sm text-on-surface text-[11px] leading-snug mt-0.5">
                        {activeAnomaly.description}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Playback Controls & Frame Scrubber */}
              <div className="h-14 bg-surface border-t border-outline-variant flex items-center px-4 justify-between shrink-0 z-20 gap-3">
                {/* Play, Step, Seek Buttons */}
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => stepFrame(-1)}
                    title="Previous Frame / Second (-1s)"
                    className="p-1.5 text-on-surface-variant hover:text-primary transition-colors hover:bg-surface-container rounded-lg"
                  >
                    <span className="material-symbols-outlined text-[20px]">replay_10</span>
                  </button>
                  <button
                    onClick={togglePlay}
                    className="p-2 bg-primary text-on-primary rounded-full hover:bg-primary/90 transition-all shadow-sm"
                    title={isPlaying ? 'Pause Video' : 'Play Video'}
                  >
                    <span className="material-symbols-outlined text-[22px]" data-weight="fill">
                      {isPlaying ? 'pause' : 'play_arrow'}
                    </span>
                  </button>
                  <button
                    onClick={() => stepFrame(1)}
                    title="Next Frame / Second (+1s)"
                    className="p-1.5 text-on-surface-variant hover:text-primary transition-colors hover:bg-surface-container rounded-lg"
                  >
                    <span className="material-symbols-outlined text-[20px]">forward_10</span>
                  </button>
                </div>

                {/* Time Display & Scrubbing Slider */}
                <div className="flex-1 flex items-center gap-3 max-w-md">
                  <span className="font-mono text-[12px] text-on-surface shrink-0">
                    {formatTime(currentTime)}
                  </span>
                  <input
                    type="range"
                    min="0"
                    max={duration || 100}
                    step="0.1"
                    value={currentTime}
                    onChange={(e) => handleSeek(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-surface-container-highest rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                  <span className="font-mono text-[12px] text-on-surface-variant shrink-0">
                    {formatTime(duration)}
                  </span>
                </div>

                {/* Speed, Volume, Fullscreen */}
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 bg-surface-container rounded-lg px-2 py-0.5 border border-outline-variant">
                    <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">
                      Speed
                    </span>
                    <select
                      value={playbackSpeed}
                      onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
                      className="bg-transparent border-0 text-label-sm text-on-surface focus:outline-none cursor-pointer"
                    >
                      <option value={0.25}>0.25x</option>
                      <option value={0.5}>0.5x</option>
                      <option value={1.0}>1.0x</option>
                      <option value={2.0}>2.0x</option>
                    </select>
                  </div>

                  <button
                    onClick={() => setIsMuted(!isMuted)}
                    className="p-1.5 text-on-surface-variant hover:text-primary transition-colors hover:bg-surface-container rounded-lg"
                    title={isMuted ? 'Unmute' : 'Mute'}
                  >
                    <span className="material-symbols-outlined text-[20px]">
                      {isMuted ? 'volume_off' : 'volume_up'}
                    </span>
                  </button>

                  <button
                    onClick={() => {
                      if (videoRef.current) {
                        if (document.fullscreenElement) {
                          document.exitFullscreen();
                        } else {
                          videoRef.current.requestFullscreen();
                        }
                      }
                    }}
                    className="p-1.5 text-on-surface-variant hover:text-primary transition-colors hover:bg-surface-container rounded-lg"
                    title="Toggle Fullscreen"
                  >
                    <span className="material-symbols-outlined text-[20px]">fullscreen</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Forensic Timeline & Clickable Anomaly Scrubber */}
            <div className="h-28 bg-surface rounded-xl border border-outline-variant p-3 flex flex-col justify-between shrink-0 shadow-sm">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[18px]">timeline</span>
                  <h3 className="text-label-md text-on-surface font-semibold uppercase tracking-wider">
                    Forensic Anomaly Scrubber
                  </h3>
                </div>
                <div className="flex items-center gap-3 text-[11px]">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-error" />
                    <span className="text-on-surface-variant">Critical Deepfake Signal</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                    <span className="text-on-surface-variant">Suspicious Jitter / Metadata</span>
                  </div>
                </div>
              </div>

              {/* Interactive Timeline Track */}
              <div
                className="relative h-12 w-full bg-surface-container-lowest rounded-lg border border-outline-variant overflow-hidden cursor-pointer"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const clickX = e.clientX - rect.left;
                  const ratio = Math.max(0, Math.min(1, clickX / rect.width));
                  handleSeek(ratio * duration);
                }}
              >
                {/* Current Playhead */}
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-primary z-30 shadow-[0_0_8px_rgba(0,102,255,0.9)]"
                  style={{
                    left: `${Math.min(100, Math.max(0, (currentTime / (duration || 1)) * 100))}%`
                  }}
                >
                  <div className="w-3 h-3 bg-primary border-2 border-white rounded-full absolute -top-1.5 -left-1.5 shadow" />
                </div>

                {/* Acoustic Desynchronization Waveform pattern */}
                <div
                  className="absolute inset-0 opacity-20 flex items-center"
                  style={{
                    backgroundImage:
                      'repeating-linear-gradient(90deg, #3b82f6 0px, #3b82f6 2px, transparent 2px, transparent 5px)'
                  }}
                />

                {/* Anomaly Highlight Blocks (Clickable) */}
                {selectedVideo.anomalies?.map((ano) => {
                  const leftPct = (ano.timestamp / (duration || 1)) * 100;
                  const isCritical = ano.type === 'critical';
                  const isCurActive = activeAnomaly?.id === ano.id;

                  return (
                    <div
                      key={ano.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        jumpToAnomaly(ano);
                      }}
                      className={`absolute top-0 bottom-0 z-20 flex flex-col items-center justify-center px-1 border-l border-r transition-all group ${
                        isCritical
                          ? 'bg-error/30 border-error hover:bg-error/50'
                          : 'bg-amber-500/30 border-amber-400 hover:bg-amber-500/50'
                      } ${isCurActive ? 'ring-2 ring-white z-30' : ''}`}
                      style={{
                        left: `${leftPct}%`,
                        width: '6%'
                      }}
                      title={`${ano.title} at ${ano.formattedTime}`}
                    >
                      <span
                        className={`material-symbols-outlined text-[14px] ${
                          isCritical ? 'text-error' : 'text-amber-400'
                        } group-hover:scale-125 transition-transform`}
                      >
                        {isCritical ? 'error' : 'warning'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Model Inspection, Anomaly Breakdown & Verdict Panel */}
          <div className="w-[410px] flex flex-col gap-3 shrink-0 h-full overflow-hidden">
            {/* Model Inspection Tabs Header */}
            <div className="bg-surface border border-outline-variant rounded-xl p-3 shadow-sm flex flex-col gap-3 shrink-0">
              <div className="flex items-center justify-between border-b border-outline-variant pb-2">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px] text-primary">psychology</span>
                  <h2 className="text-label-md font-semibold text-on-surface">
                    Deepfake Neural Inspection
                  </h2>
                </div>
                <span className="text-[10px] font-mono bg-surface-container px-2 py-0.5 rounded text-on-surface-variant">
                  ResNeXt50+LSTM
                </span>
              </div>

              {/* Tab Navigation */}
              <div className="grid grid-cols-4 gap-1 bg-surface-container-low p-1 rounded-lg">
                <button
                  onClick={() => setActiveTab('temporal')}
                  className={`py-1.5 rounded text-[11px] font-medium transition-colors ${
                    activeTab === 'temporal'
                      ? 'bg-primary text-on-primary shadow-sm'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Metrics
                </button>
                <button
                  onClick={() => setActiveTab('frames')}
                  className={`py-1.5 rounded text-[11px] font-medium transition-colors ${
                    activeTab === 'frames'
                      ? 'bg-primary text-on-primary shadow-sm'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Frames
                </button>
                <button
                  onClick={() => setActiveTab('faces')}
                  className={`py-1.5 rounded text-[11px] font-medium transition-colors ${
                    activeTab === 'faces'
                      ? 'bg-primary text-on-primary shadow-sm'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Face Crops
                </button>
                <button
                  onClick={() => setActiveTab('heatmaps')}
                  className={`py-1.5 rounded text-[11px] font-medium transition-colors ${
                    activeTab === 'heatmaps'
                      ? 'bg-primary text-on-primary shadow-sm'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Heatmaps
                </button>
              </div>
            </div>

            {/* Tab Contents Container */}
            <div className="flex-1 bg-surface border border-outline-variant rounded-xl flex flex-col shadow-sm overflow-hidden min-h-0">
              {/* Tab 1: Temporal & Spatial Metrics */}
              {activeTab === 'temporal' && (
                <div className="flex-1 overflow-y-auto p-3 space-y-3.5">
                  {/* Metric 1: Facial Mesh Integrity */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-label-sm text-on-surface-variant">
                        Facial Mesh Integrity
                      </span>
                      <span
                        className={`font-mono text-label-sm font-bold ${
                          selectedVideo.metrics?.facialMeshIntegrity < 50
                            ? 'text-error'
                            : 'text-emerald-400'
                        }`}
                      >
                        {selectedVideo.metrics?.facialMeshIntegrity}%{' '}
                        {selectedVideo.metrics?.facialMeshIntegrity < 50
                          ? '(Anomalous)'
                          : '(Authentic)'}
                      </span>
                    </div>
                    <div className="w-full bg-surface-container-highest h-2 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          selectedVideo.metrics?.facialMeshIntegrity < 50
                            ? 'bg-error'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${selectedVideo.metrics?.facialMeshIntegrity}%` }}
                      />
                    </div>
                  </div>

                  {/* Metric 2: Audio-Visual Sync Variance */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-label-sm text-on-surface-variant">
                        Audio-Visual Desynchronization
                      </span>
                      <span
                        className={`font-mono text-label-sm font-bold ${
                          selectedVideo.metrics?.audioVisualSyncVariance > 50
                            ? 'text-error'
                            : 'text-emerald-400'
                        }`}
                      >
                        {selectedVideo.metrics?.audioVisualSyncVariance}%{' '}
                        {selectedVideo.metrics?.audioVisualSyncVariance > 50
                          ? '(High Variance)'
                          : '(Synced)'}
                      </span>
                    </div>
                    <div className="w-full bg-surface-container-highest h-2 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          selectedVideo.metrics?.audioVisualSyncVariance > 50
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${selectedVideo.metrics?.audioVisualSyncVariance}%` }}
                      />
                    </div>
                  </div>

                  {/* Metric 3: Spatial Artifact Score (ResNeXt-50) */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-label-sm text-on-surface-variant">
                        ResNeXt-50 Spatial Artifacts
                      </span>
                      <span className="font-mono text-label-sm font-bold text-primary">
                        {selectedVideo.metrics?.spatialArtifactScore}% Artifact Density
                      </span>
                    </div>
                    <div className="w-full bg-surface-container-highest h-2 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all"
                        style={{ width: `${selectedVideo.metrics?.spatialArtifactScore}%` }}
                      />
                    </div>
                  </div>

                  {/* Metric 4: LSTM Temporal Sequence Continuity */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-label-sm text-on-surface-variant">
                        LSTM Temporal Inconsistency
                      </span>
                      <span className="font-mono text-label-sm font-bold text-amber-400">
                        {selectedVideo.metrics?.temporalInconsistency}% Inconsistency
                      </span>
                    </div>
                    <div className="w-full bg-surface-container-highest h-2 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-400 rounded-full transition-all"
                        style={{ width: `${selectedVideo.metrics?.temporalInconsistency}%` }}
                      />
                    </div>
                  </div>

                  {/* Flagged Anomalies Mini-List */}
                  <div className="pt-2 border-t border-outline-variant">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="text-label-sm font-semibold text-on-surface">
                        Detected Anomalies ({selectedVideo.anomalies?.length || 0})
                      </h4>
                      <span className="text-[10px] text-on-surface-variant">
                        Click anomaly to jump
                      </span>
                    </div>
                    <div className="space-y-2">
                      {selectedVideo.anomalies?.length ? (
                        selectedVideo.anomalies.map((ano) => (
                          <div
                            key={ano.id}
                            onClick={() => jumpToAnomaly(ano)}
                            className={`p-2.5 border rounded-lg cursor-pointer transition-colors flex flex-col gap-1 ${
                              activeAnomaly?.id === ano.id
                                ? 'bg-error/10 border-error'
                                : 'bg-surface-container-low border-outline-variant hover:border-primary'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-1.5">
                                <span
                                  className={`material-symbols-outlined text-[16px] ${
                                    ano.type === 'critical' ? 'text-error' : 'text-amber-400'
                                  }`}
                                >
                                  {ano.type === 'critical' ? 'error' : 'warning'}
                                </span>
                                <span className="text-label-sm font-medium text-on-surface">
                                  {ano.title}
                                </span>
                              </div>
                              <span className="font-mono text-[10px] bg-surface-container px-1.5 py-0.5 rounded text-on-surface-variant">
                                {ano.formattedTime}
                              </span>
                            </div>
                            <p className="text-[11px] text-on-surface-variant leading-tight">
                              {ano.description}
                            </p>
                          </div>
                        ))
                      ) : (
                        <div className="p-3 text-center text-body-sm text-emerald-400 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                          <span className="material-symbols-outlined text-[20px] block mb-1">
                            verified
                          </span>
                          No critical anomalies or deepfake signatures detected.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: Sequence Frames Split View */}
              {activeTab === 'frames' && (
                <div className="flex-1 overflow-y-auto p-3">
                  <div className="flex justify-between items-center mb-2.5">
                    <span className="text-label-sm text-on-surface-variant font-medium">
                      Extracted Frame Sequence
                    </span>
                    <span className="text-[11px] text-on-surface-variant">
                      {selectedVideo.framesSplit?.length || 0} Keyframes
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {selectedVideo.framesSplit?.map((f, idx) => (
                      <div
                        key={idx}
                        className={`rounded-lg border overflow-hidden bg-surface-container-low flex flex-col relative group ${
                          f.isAnomalous ? 'border-error ring-1 ring-error/50' : 'border-outline-variant'
                        }`}
                      >
                        <img
                          src={f.url}
                          alt={`Frame ${f.frameIdx}`}
                          className="w-full h-24 object-cover group-hover:scale-105 transition-transform"
                        />
                        <div className="p-1.5 flex justify-between items-center text-[10px] bg-surface">
                          <span className="font-mono text-on-surface font-semibold">
                            #{f.frameIdx} ({f.time})
                          </span>
                          {f.isAnomalous && (
                            <span className="text-error font-bold px-1 rounded bg-error/10">
                              {f.label || 'Manipulated'}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 3: Cropped Faces View */}
              {activeTab === 'faces' && (
                <div className="flex-1 overflow-y-auto p-3">
                  <div className="flex justify-between items-center mb-2.5">
                    <span className="text-label-sm text-on-surface-variant font-medium">
                      Cropped Face Crops (Face Recognition)
                    </span>
                    <span className="text-[11px] text-on-surface-variant">
                      112x112 Normalization
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {selectedVideo.faceCrops?.map((fc) => (
                      <div
                        key={fc.id}
                        className="p-2 border border-outline-variant rounded-lg bg-surface-container-low flex flex-col gap-1.5"
                      >
                        <div className="flex justify-between items-center">
                          <span className="font-mono text-[11px] text-on-surface">
                            Frame #{fc.frame}
                          </span>
                          <span
                            className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                              fc.flag.includes('Manipulated') || fc.flag.includes('Artifact')
                                ? 'bg-error/10 text-error'
                                : 'bg-emerald-500/10 text-emerald-400'
                            }`}
                          >
                            {fc.flag}
                          </span>
                        </div>
                        <div className="bg-black rounded h-20 flex items-center justify-center border border-outline-variant overflow-hidden relative">
                          <img
                            src={selectedVideo.fallbackThumbnail}
                            alt="Face Crop"
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute inset-2 border border-primary/60 border-dashed rounded" />
                        </div>
                        <div className="flex justify-between text-[10px] text-on-surface-variant">
                          <span>Quality: {fc.confidence}%</span>
                          <span>BBox: [{fc.box?.join(', ')}]</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 4: Attention Heatmaps View (Grad-CAM) */}
              {activeTab === 'heatmaps' && (
                <div className="flex-1 overflow-y-auto p-3 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-label-sm text-on-surface-variant font-medium">
                      Grad-CAM Activation Heatmaps
                    </span>
                    <span className="text-[11px] text-primary font-mono">Spatial Focus</span>
                  </div>
                  {selectedVideo.heatmaps?.map((hm) => (
                    <div
                      key={hm.id}
                      className="p-3 border border-outline-variant rounded-lg bg-surface-container-low flex flex-col gap-2"
                    >
                      <div className="flex justify-between items-center">
                        <span className="text-label-sm font-semibold text-on-surface">
                          Region: {hm.region}
                        </span>
                        <span className="font-mono text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded">
                          Intensity: {hm.intensity}
                        </span>
                      </div>
                      {/* Gradient visual representing heatmap activation */}
                      <div className="h-20 rounded-lg relative overflow-hidden flex items-center justify-center border border-outline-variant">
                        <img
                          src={selectedVideo.fallbackThumbnail}
                          alt="Heatmap base"
                          className="w-full h-full object-cover"
                        />
                        <div
                          className="absolute inset-0 opacity-70 mix-blend-color-dodge"
                          style={{
                            background:
                              'radial-gradient(circle at 50% 60%, rgba(239,68,68,0.95) 0%, rgba(245,158,11,0.8) 35%, rgba(59,130,246,0.3) 70%, transparent 100%)'
                          }}
                        />
                        <span className="absolute bottom-1 right-2 text-[9px] font-mono text-white/90 bg-black/60 px-1 rounded">
                          Grad-CAM Map
                        </span>
                      </div>
                      <p className="text-[11px] text-on-surface-variant leading-snug">
                        {hm.desc}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Verdict Controls & Report Generator */}
            <div className="bg-surface-container-low border border-outline-variant rounded-xl p-3 shrink-0 shadow-sm flex flex-col gap-2.5">
              <h3 className="text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">
                Forensic Verdict & Audit
              </h3>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => setVerdict('REAL')}
                  className={`flex flex-col items-center justify-center py-2 rounded-lg border transition-all ${
                    verdict === 'REAL'
                      ? 'border-emerald-500 bg-emerald-500/15 text-emerald-400 font-bold'
                      : 'border-outline-variant bg-surface text-on-surface hover:bg-surface-container'
                  }`}
                >
                  <span className="material-symbols-outlined text-[20px]">verified</span>
                  <span className="text-[11px] mt-0.5">Authentic</span>
                </button>

                <button
                  onClick={() => setVerdict('FAKE')}
                  className={`flex flex-col items-center justify-center py-2 rounded-lg border transition-all ${
                    verdict === 'FAKE'
                      ? 'border-error bg-error/15 text-error font-bold'
                      : 'border-outline-variant bg-surface text-on-surface hover:bg-surface-container'
                  }`}
                >
                  <span className="material-symbols-outlined text-[20px]" data-weight="fill">
                    gpp_bad
                  </span>
                  <span className="text-[11px] mt-0.5">Manipulated</span>
                </button>

                <button
                  onClick={() => setVerdict('INCONCLUSIVE')}
                  className={`flex flex-col items-center justify-center py-2 rounded-lg border transition-all ${
                    verdict === 'INCONCLUSIVE'
                      ? 'border-amber-500 bg-amber-500/15 text-amber-400 font-bold'
                      : 'border-outline-variant bg-surface text-on-surface hover:bg-surface-container'
                  }`}
                >
                  <span className="material-symbols-outlined text-[20px]">help_center</span>
                  <span className="text-[11px] mt-0.5">Inconclusive</span>
                </button>
              </div>

              <button
                onClick={() => setReportModalOpen(true)}
                className="w-full bg-primary text-on-primary py-2 rounded-lg text-label-md flex items-center justify-center gap-2 hover:bg-primary/90 transition-all shadow-sm"
              >
                <span className="material-symbols-outlined text-[18px]">summarize</span>
                Generate Forensic Report
              </button>
            </div>
          </div>
        </div>

        {/* Video Evidence Repository Drawer (Slide-out) */}
        {isSearchDrawerOpen && (
          <aside className="w-84 border-l border-outline-variant bg-surface flex flex-col h-full z-30 shadow-2xl animate-fadeIn">
            <div className="p-3 border-b border-outline-variant flex items-center justify-between bg-surface-container-low">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[20px]">folder_open</span>
                <h3 className="text-label-md font-semibold text-on-surface">Video Evidence Library</h3>
              </div>
              <button
                onClick={() => setIsSearchDrawerOpen(false)}
                className="p-1 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>

            {/* Filter Tabs within Drawer */}
            <div className="p-2 border-b border-outline-variant bg-surface">
              <div className="flex gap-1">
                {['ALL', 'ANOMALOUS', 'CLEAN'].map((s) => (
                  <button
                    key={s}
                    onClick={() => setSeverityFilter(s)}
                    className={`flex-1 py-1 rounded text-[11px] font-medium transition-colors ${
                      severityFilter === s
                        ? 'bg-primary text-on-primary'
                        : 'bg-surface-container text-on-surface-variant hover:text-on-surface'
                    }`}
                  >
                    {s === 'ALL' ? 'All' : s === 'ANOMALOUS' ? 'Manipulated' : 'Clean'}
                  </button>
                ))}
              </div>
            </div>

            {/* Video List */}
            <div className="flex-1 overflow-y-auto p-2 space-y-2">
              {filteredVideos.length ? (
                filteredVideos.map((v) => {
                  const isSelected = selectedVideo.id === v.id;
                  const isFake = v.verdict === 'FAKE';
                  return (
                    <div
                      key={v.id}
                      onClick={() => {
                        setSelectedVideo(v);
                      }}
                      className={`p-3 rounded-xl border cursor-pointer transition-all flex flex-col gap-2 ${
                        isSelected
                          ? 'border-primary bg-primary/10 shadow-sm'
                          : 'border-outline-variant bg-surface-container-low hover:border-primary/50'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex items-center gap-1.5 min-w-0">
                          <span
                            className={`material-symbols-outlined text-[18px] ${
                              isFake ? 'text-error' : 'text-emerald-400'
                            }`}
                          >
                            {isFake ? 'gpp_bad' : 'verified'}
                          </span>
                          <span className="font-mono text-label-sm font-semibold text-on-surface truncate">
                            {v.title}
                          </span>
                        </div>
                        <span className="font-mono text-[10px] text-on-surface-variant bg-surface-container px-1.5 py-0.5 rounded shrink-0">
                          {v.caseId}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-on-surface-variant">
                        <span>Duration: {v.formattedDuration}</span>
                        <span
                          className={`font-bold ${
                            isFake ? 'text-error' : 'text-emerald-400'
                          }`}
                        >
                          {v.verdict} ({v.confidence}%)
                        </span>
                      </div>

                      <div className="text-[10px] font-mono text-outline truncate">
                        SHA256: {v.sha256.substring(0, 18)}...
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="p-4 text-center text-on-surface-variant text-body-sm">
                  No matching video evidence found.
                </div>
              )}
            </div>
          </aside>
        )}
      </div>

      {/* Upload Video & Run Deepfake Detection Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-outline-variant rounded-2xl w-full max-w-lg shadow-2xl p-5 flex flex-col gap-4 animate-scaleUp">
            <div className="flex justify-between items-center border-b border-outline-variant pb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[22px]">video_settings</span>
                <h3 className="text-title-md font-bold text-on-surface">
                  Analyze Digital Video Evidence
                </h3>
              </div>
              {!isAnalyzing && (
                <button
                  onClick={() => setUploadModalOpen(false)}
                  className="p-1 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container"
                >
                  <span className="material-symbols-outlined text-[20px]">close</span>
                </button>
              )}
            </div>

            {!isAnalyzing ? (
              <>
                {/* File Dropzone */}
                <label className="border-2 border-dashed border-outline-variant hover:border-primary rounded-xl p-6 bg-surface-container-lowest flex flex-col items-center justify-center text-center cursor-pointer transition-colors">
                  <input
                    type="file"
                    accept="video/mp4,video/webm,video/quicktime,video/avi"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        setUploadFile(e.target.files[0]);
                      }
                    }}
                  />
                  <span className="material-symbols-outlined text-[36px] text-primary mb-2">
                    cloud_upload
                  </span>
                  <p className="text-body-md font-medium text-on-surface">
                    {uploadFile ? uploadFile.name : 'Click to select or drag & drop video file'}
                  </p>
                  <p className="text-body-sm text-on-surface-variant mt-1">
                    {uploadFile
                      ? `${(uploadFile.size / (1024 * 1024)).toFixed(2)} MB • ${uploadFile.type || 'video/mp4'}`
                      : 'Supports MP4, WebM, MOV, AVI (Max 150MB)'}
                  </p>
                </label>

                {/* Model Configuration Options (Matches ResNeXt-50 + LSTM) */}
                <div className="space-y-3 bg-surface-container-low p-3.5 rounded-xl border border-outline-variant">
                  <div className="flex justify-between items-center">
                    <span className="text-label-sm font-semibold text-on-surface">
                      LSTM Sequence Length
                    </span>
                    <span className="font-mono text-label-sm text-primary font-bold">
                      {sequenceLength} Frames
                    </span>
                  </div>
                  <div className="grid grid-cols-5 gap-2">
                    {[10, 20, 40, 60, 100].map((len) => (
                      <button
                        key={len}
                        type="button"
                        onClick={() => setSequenceLength(len)}
                        className={`py-1.5 rounded-lg text-label-sm font-mono border transition-all ${
                          sequenceLength === len
                            ? 'bg-primary text-on-primary border-primary font-bold shadow-sm'
                            : 'bg-surface border-outline-variant text-on-surface hover:bg-surface-container'
                        }`}
                      >
                        {len} f
                      </button>
                    ))}
                  </div>
                  <p className="text-[11px] text-on-surface-variant leading-relaxed">
                    Higher sequence length increases temporal anomaly detection accuracy for subtle face-swaps and phonetic desynchronization.
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setUploadModalOpen(false)}
                    className="px-4 py-2 border border-outline-variant rounded-lg text-body-sm text-on-surface hover:bg-surface-container"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    disabled={!uploadFile}
                    onClick={handleStartAnalysis}
                    className="px-5 py-2 bg-primary text-on-primary rounded-lg text-body-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 shadow"
                  >
                    <span className="material-symbols-outlined text-[18px]">play_arrow</span>
                    Start Deepfake Analysis
                  </button>
                </div>
              </>
            ) : (
              /* Analysis In-Progress Animation */
              <div className="py-8 flex flex-col items-center justify-center text-center space-y-4">
                <div className="relative w-16 h-16 flex items-center justify-center">
                  <div className="w-16 h-16 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                  <span className="material-symbols-outlined text-primary text-[24px] absolute">
                    psychology
                  </span>
                </div>
                <div>
                  <h4 className="text-title-md font-bold text-on-surface">
                    Processing Video Through ResNeXt50 + LSTM
                  </h4>
                  <p className="text-body-sm text-on-surface-variant font-mono mt-1">
                    {analysisStepLabel}
                  </p>
                </div>
                <div className="w-full max-w-sm bg-surface-container-highest h-2.5 rounded-full overflow-hidden">
                  <div
                    className="bg-primary h-full rounded-full transition-all duration-300"
                    style={{ width: `${analysisProgress}%` }}
                  />
                </div>
                <span className="font-mono text-label-sm text-primary font-bold">
                  {analysisProgress}% Complete
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Forensic Report Export Modal */}
      {reportModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-outline-variant rounded-2xl w-full max-w-2xl shadow-2xl p-6 flex flex-col gap-4 animate-scaleUp max-h-[85vh]">
            <div className="flex justify-between items-center border-b border-outline-variant pb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[24px]">description</span>
                <h3 className="text-title-md font-bold text-on-surface">
                  Forensic Chain-of-Custody & Audit Report
                </h3>
              </div>
              <button
                onClick={() => {
                  setReportModalOpen(false);
                  setReportCopied(false);
                }}
                className="p-1 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 font-mono text-body-sm bg-surface-container-lowest p-4 rounded-xl border border-outline-variant text-on-surface">
              <div className="border-b border-outline-variant pb-2">
                <p className="text-primary font-bold text-[14px]">
                  =======================================================
                </p>
                <p className="text-primary font-bold text-[14px]">
                  AUTOMATED DEEPFAKE INVESTIGATION REPORT
                </p>
                <p className="text-primary font-bold text-[14px]">
                  =======================================================
                </p>
                <p>Case ID: {selectedVideo.caseId}</p>
                <p>Evidence ID: {selectedVideo.id}</p>
                <p>File: {selectedVideo.title}</p>
                <p>SHA-256 Hash: {selectedVideo.sha256}</p>
                <p>Timestamp: {new Date().toISOString()}</p>
                <p>Analyst: {selectedVideo.investigator}</p>
              </div>

              <div>
                <p className="font-bold text-on-surface underline">NEURAL MODEL CLASSIFICATION:</p>
                <p>Architecture: {selectedVideo.modelUsed}</p>
                <p>
                  Classification Verdict:{' '}
                  <span
                    className={
                      verdict === 'FAKE'
                        ? 'text-error font-bold'
                        : verdict === 'REAL'
                        ? 'text-emerald-400 font-bold'
                        : 'text-amber-400 font-bold'
                    }
                  >
                    {verdict}
                  </span>
                </p>
                <p>Confidence: {selectedVideo.confidence}%</p>
                <p>Facial Mesh Integrity: {selectedVideo.metrics?.facialMeshIntegrity}%</p>
                <p>Audio-Visual Sync Variance: {selectedVideo.metrics?.audioVisualSyncVariance}%</p>
                <p>Lip-Sync Jitter Score: {selectedVideo.metrics?.lipSyncJitter}%</p>
              </div>

              <div>
                <p className="font-bold text-on-surface underline">DETECTED ANOMALIES ({selectedVideo.anomalies?.length}):</p>
                {selectedVideo.anomalies?.map((ano, i) => (
                  <p key={ano.id} className="text-[12px]">
                    [{i + 1}] @ {ano.formattedTime} - {ano.title} ({ano.severity}): {ano.description}
                  </p>
                ))}
              </div>

              <div>
                <p className="font-bold text-on-surface underline">INVESTIGATOR NOTES & FINDINGS:</p>
                <textarea
                  value={investigatorNotes}
                  onChange={(e) => setInvestigatorNotes(e.target.value)}
                  className="w-full bg-surface border border-outline-variant rounded p-2 text-body-sm text-on-surface mt-1 focus:outline-none focus:border-primary"
                  rows={3}
                />
              </div>
            </div>

            <div className="flex justify-between items-center pt-2">
              <span className="text-[11px] text-on-surface-variant font-mono">
                Cryptographically Sealed (SHA-256 Verified)
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(
                      `ADIS DEEPFAKE REPORT - CASE ${selectedVideo.caseId}\nFILE: ${selectedVideo.title}\nVERDICT: ${verdict} (${selectedVideo.confidence}%)\nHASH: ${selectedVideo.sha256}\nNOTES: ${investigatorNotes}`
                    );
                    setReportCopied(true);
                    setTimeout(() => setReportCopied(false), 2000);
                  }}
                  className="px-4 py-2 border border-outline-variant rounded-lg text-body-sm text-on-surface hover:bg-surface-container flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">
                    {reportCopied ? 'check' : 'content_copy'}
                  </span>
                  {reportCopied ? 'Copied!' : 'Copy Summary'}
                </button>
                <button
                  onClick={() => {
                    const blob = new Blob(
                      [
                        `=======================================================\nADIS FORENSIC REPORT\n=======================================================\nCase ID: ${selectedVideo.caseId}\nEvidence ID: ${selectedVideo.id}\nFilename: ${selectedVideo.title}\nSHA256: ${selectedVideo.sha256}\nModel: ${selectedVideo.modelUsed}\nVerdict: ${verdict} (Confidence: ${selectedVideo.confidence}%)\n\nAnomalies:\n${selectedVideo.anomalies?.map((a) => `- [${a.formattedTime}] ${a.title}: ${a.description}`).join('\n')}\n\nInvestigator Notes:\n${investigatorNotes}\n`
                      ],
                      { type: 'text/plain' }
                    );
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `Forensic_Report_${selectedVideo.id}.txt`;
                    a.click();
                  }}
                  className="px-4 py-2 bg-primary text-on-primary rounded-lg text-body-sm font-medium hover:bg-primary/90 transition-all flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">download</span>
                  Export Audit Log
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
