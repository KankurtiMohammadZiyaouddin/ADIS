export default function VideoForensicsPage() {
  return (
    <main className="flex-1 ml-[260px] flex flex-col min-w-0 bg-background h-screen">
      {/* TopNavBar (Shared Component) */}
      <header className="flex justify-between items-center h-14 px-gutter w-full bg-surface border-b border-outline-variant shrink-0 z-10">
        <div className="flex items-center gap-6 h-full">
          <nav className="flex items-center gap-6 h-full">
            <a className="text-on-surface-variant text-label-sm hover:text-primary transition-colors flex items-center h-full" href="#">Breadcrumbs</a>
            <a className="text-on-surface-variant text-label-sm hover:text-primary transition-colors flex items-center h-full" href="#">Cases</a>
            <a className="text-primary text-label-sm font-bold border-b-2 border-primary h-full flex items-center pt-[2px]" href="#">Evidence</a>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden lg:flex flex-col items-end mr-4 border-r border-outline-variant pr-4">
            <span className="text-label-sm text-on-surface-variant">Current Case: #4492</span>
            <span className="text-label-sm text-primary font-bold">Investigator</span>
          </div>
          <button className="text-on-surface-variant hover:text-primary transition-colors">
            <span className="material-symbols-outlined text-[20px]" data-icon="search">search</span>
          </button>
          <button className="text-on-surface-variant hover:text-primary transition-colors">
            <span className="material-symbols-outlined text-[20px]" data-icon="notifications">notifications</span>
          </button>
          <button className="text-on-surface-variant hover:text-primary transition-colors">
            <span className="material-symbols-outlined text-[20px]" data-icon="account_circle">account_circle</span>
          </button>
        </div>
      </header>
      {/* Workspace Layout */}
      <div className="flex-1 p-gutter flex gap-gutter overflow-hidden">
        {/* Left Column: Video Player & Timeline Grid */}
        <div className="flex-1 flex flex-col gap-unit min-w-0 h-full">
          {/* Video Player Container */}
          <div className="flex-1 bg-[#0a0f1a] rounded-xl border border-outline-variant overflow-hidden flex flex-col relative shadow-sm">
            {/* Video Header */}
            <div className="h-10 bg-surface/10 backdrop-blur-md absolute top-0 w-full flex items-center justify-between px-4 z-10 border-b border-outline-variant/30 text-white">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px]">videocam</span>
                <span className="text-label-sm opacity-80">EVID_4492_INTERVIEW_CAM2.mp4</span>
              </div>
              <div className="flex gap-2">
                <span className="px-2 py-0.5 bg-primary/20 text-primary-fixed text-label-sm rounded font-mono">1080p60</span>
                <span className="px-2 py-0.5 bg-error/20 text-error-container text-label-sm rounded font-bold">AI ALTERATION DETECTED</span>
              </div>
            </div>
            {/* Video Viewport */}
            <div className="flex-1 relative w-full h-full flex items-center justify-center bg-black">
              {/* Simulated Video Placeholder */}
              <div className="w-full h-full bg-cover bg-center absolute inset-0 opacity-80" data-alt="A highly detailed forensic analysis view of a digital video playing in a clinical software interface. The frame shows a medium shot of a person speaking, with overlayed bright green facial tracking meshes and analytical bounding boxes analyzing their micro-expressions and lip movements. The aesthetic is stark, technical, and high-contrast, utilizing deep blacks, bright analytical greens, and sterile white interface elements." style={{backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBTZt8Zq-_-maZ6yYb9IXFBS8OAdlAn7VSxmOdR_qhSem20D8DE0kEcf2_8_J7bheQp_DwHk1Qhu7i1CuQMZba4C4QIn0uNx4BwxMwP0gCfzcyUMnW15ycGG5KGvJFdsoxL7wrMvgT3mdOrwM-19-3hYf2-q5RENyNhb92FkHPT89Jiw3tMrXpTPV2bXV4N-87IGb93sSCOJNzDhxavBi-wXeCb4Q8y_wrIOmrEESbV-wqrH1SPaY4")'}} />
              {/* Overlay Artifacts (Simulating forensic analysis overlays) */}
              <div className="absolute inset-0 pointer-events-none p-8 flex items-center justify-center">
                <div className="border border-error/80 w-48 h-64 absolute rounded-sm z-10" style={{left: '45%', top: '20%'}}>
                  <div className="absolute -top-6 left-0 bg-error/90 text-on-error font-mono text-[10px] px-1">LIP-SYNC JITTER 87%</div>
                  <div className="w-2 h-2 border-l border-t border-error absolute top-0 left-0" />
                  <div className="w-2 h-2 border-r border-t border-error absolute top-0 right-0" />
                  <div className="w-2 h-2 border-l border-b border-error absolute bottom-0 left-0" />
                  <div className="w-2 h-2 border-r border-b border-error absolute bottom-0 right-0" />
                </div>
              </div>
            </div>
            {/* Playback Controls */}
            <div className="h-16 bg-surface border-t border-outline-variant flex items-center px-4 justify-between shrink-0">
              <div className="flex items-center gap-2">
                <button className="p-2 text-on-surface-variant hover:text-primary transition-colors hover:bg-surface-container rounded-full"><span className="material-symbols-outlined">skip_previous</span></button>
                <button className="p-2 text-on-surface-variant hover:text-primary transition-colors hover:bg-surface-container rounded-full"><span className="material-symbols-outlined">fast_rewind</span></button>
                <button className="p-2 bg-primary text-on-primary rounded-full hover:bg-primary-container hover:text-on-primary-container transition-colors shadow-sm"><span className="material-symbols-outlined" data-weight="fill">play_arrow</span></button>
                <button className="p-2 text-on-surface-variant hover:text-primary transition-colors hover:bg-surface-container rounded-full"><span className="material-symbols-outlined">fast_forward</span></button>
                <button className="p-2 text-on-surface-variant hover:text-primary transition-colors hover:bg-surface-container rounded-full"><span className="material-symbols-outlined">skip_next</span></button>
              </div>
              <div className="font-mono text-[13px] text-on-surface-variant">
                <span className="text-on-surface">00:02:14:15</span> / 00:05:30:00
              </div>
              <div className="flex items-center gap-3">
                <span className="text-label-sm text-on-surface-variant uppercase tracking-wider">Speed</span>
                <select className="bg-surface-container border-outline-variant text-body-sm rounded py-1 pl-2 pr-6 focus:ring-primary focus:border-primary">
                  <option>0.25x</option>
                  <option>0.5x</option>
                  <option selected>1.0x</option>
                  <option>2.0x</option>
                </select>
                <div className="w-px h-6 bg-outline-variant mx-2" />
                <button className="text-on-surface-variant hover:text-primary transition-colors"><span className="material-symbols-outlined text-[20px]">fullscreen</span></button>
              </div>
            </div>
          </div>
          {/* Frame Timeline & Anomaly Scrubber */}
          <div className="h-32 bg-surface rounded-xl border border-outline-variant p-4 flex flex-col justify-between shrink-0 shadow-sm">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-label-md text-on-surface uppercase tracking-widest">Forensic Timeline</h3>
              <div className="flex gap-4">
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-error" /><span className="text-label-sm text-on-surface-variant">Critical Anomaly</span></div>
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#f59e0b]" /><span className="text-label-sm text-on-surface-variant">Warning</span></div>
              </div>
            </div>
            {/* Timeline Track Container */}
            <div className="relative h-12 w-full bg-surface-container-low rounded border border-outline-variant/50 overflow-hidden cursor-crosshair">
              {/* Playhead */}
              <div className="absolute top-0 bottom-0 w-px bg-primary z-20 shadow-[0_0_8px_rgba(0,55,176,0.8)]" style={{left: '40%'}}>
                <div className="w-3 h-3 border border-primary bg-surface absolute -top-1.5 -left-1.5 rotate-45" />
              </div>
              {/* Time markings (Visual only) */}
              <div className="absolute inset-0 flex border-b border-outline-variant/30 opacity-50" style={{backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 19px, #c4c5d7 20px)'}} />
              {/* Anomaly Segments */}
              <div className="absolute top-0 bottom-0 bg-[#f59e0b]/30 border-l border-r border-[#f59e0b]" style={{left: '15%', width: '5%'}} title="Suspicious metadata gap" />
              <div className="absolute top-0 bottom-0 bg-error/30 border-l border-r border-error shadow-[inset_0_0_10px_rgba(186,26,26,0.2)]" style={{left: '38%', width: '12%'}} title="Deepfake audio/visual desync detected" />
              <div className="absolute top-0 bottom-0 bg-[#f59e0b]/30 border-l border-r border-[#f59e0b]" style={{left: '70%', width: '8%'}} />
              {/* Audio Waveform abstraction */}
              <div className="absolute bottom-0 w-full h-4 opacity-40 flex items-end gap-[1px]">
                {/* Generated randomly looking bars via CSS for visual texture */}
                <div className="w-1 h-3 bg-primary" /><div className="w-1 h-2 bg-primary" /><div className="w-1 h-4 bg-primary" /><div className="w-1 h-1 bg-primary" />
                <div className="w-1 h-2 bg-primary" /><div className="w-1 h-3 bg-primary" /><div className="w-1 h-2 bg-primary" /><div className="w-1 h-1 bg-primary" />
                {/* ... repeating pattern conceptually ... */}
                <div className="w-full h-full" style={{backgroundImage: 'repeating-linear-gradient(90deg, #0037b0 0px, #0037b0 2px, transparent 2px, transparent 4px)', opacity: '0.5'}} />
              </div>
            </div>
          </div>
        </div>
        {/* Right Column: Temporal Analysis & Verdict Panel */}
        <div className="w-[380px] flex flex-col gap-unit shrink-0 h-full overflow-hidden">
          {/* Temporal Analysis Tracks (Bento-style block) */}
          <div className="bg-surface border border-outline-variant rounded-xl p-4 flex flex-col gap-4 shadow-sm shrink-0">
            <div className="flex items-center gap-2 border-b border-outline-variant pb-2">
              <span className="material-symbols-outlined text-[18px] text-primary">monitoring</span>
              <h2 className="font-headline-sm text-headline-sm text-on-surface">Temporal Analysis</h2>
            </div>
            {/* Track 1: Face Tracking Confidence */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between items-end">
                <span className="text-label-md text-on-surface-variant">Facial Mesh Integrity</span>
                <span className="font-mono text-label-sm text-error font-bold">42% (Anomalous)</span>
              </div>
              <div className="h-8 w-full bg-surface-container rounded border border-outline-variant relative overflow-hidden flex items-end">
                {/* Graph line mock */}
                <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                  <path d="M0,20 L20,25 L35,15 L38,80 L42,90 L45,75 L50,85 L55,20 L80,15 L100,20" fill="none" stroke="#ba1a1a" strokeWidth={2} />
                </svg>
                {/* Current position indicator */}
                <div className="absolute top-0 bottom-0 w-px bg-primary/50" style={{left: '40%'}} />
              </div>
            </div>
            {/* Track 2: Lip-Sync Jitter */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between items-end">
                <span className="text-label-md text-on-surface-variant">Audio-Visual Desynchronization</span>
                <span className="font-mono text-label-sm text-error font-bold">HIGH VARIANCE</span>
              </div>
              <div className="h-8 w-full bg-surface-container rounded border border-outline-variant relative overflow-hidden flex items-end">
                <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                  <path d="M0,80 L35,85 L38,10 L40,20 L42,5 L46,30 L50,15 L52,80 L100,85" fill="none" stroke="#a73400" strokeWidth={2} />
                </svg>
                <div className="absolute top-0 bottom-0 w-px bg-primary/50" style={{left: '40%'}} />
              </div>
            </div>
          </div>
          {/* Anomaly Breakdown List */}
          <div className="flex-1 bg-surface border border-outline-variant rounded-xl flex flex-col shadow-sm overflow-hidden min-h-0">
            <div className="p-4 border-b border-outline-variant bg-surface-container-low flex justify-between items-center shrink-0">
              <h2 className="font-headline-sm text-[16px] text-on-surface font-semibold">Detected Anomalies</h2>
              <span className="px-2 py-0.5 bg-error-container text-on-error-container rounded text-label-sm font-bold">3 Flags</span>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-2">
              {/* Anomaly Item 1 */}
              <div className="p-3 border border-outline-variant rounded-lg bg-surface hover:border-primary transition-colors cursor-pointer flex flex-col gap-2 relative overflow-hidden group">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#f59e0b]" />
                <div className="flex justify-between items-start pl-2">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px] text-[#f59e0b]">warning</span>
                    <span className="text-label-md text-on-surface">Metadata Inconsistency</span>
                  </div>
                  <span className="font-mono text-label-sm text-on-surface-variant bg-surface-container px-1.5 rounded">00:00:45</span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant pl-2">Frame rate fluctuation not matching container encoding metadata. Possible splicing.</p>
              </div>
              {/* Anomaly Item 2 (Active/Critical) */}
              <div className="p-3 border border-error bg-error-container/10 rounded-lg cursor-pointer flex flex-col gap-2 relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-error" />
                <div className="flex justify-between items-start pl-2">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px] text-error">face</span>
                    <span className="text-label-md text-error font-bold">Face-Swap Artifacts</span>
                  </div>
                  <span className="font-mono text-label-sm text-on-surface-variant bg-surface-container px-1.5 rounded">00:02:14</span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface pl-2">Severe boundary blending failure around the jawline. High probability of diffusion model manipulation.</p>
                <div className="pl-2 mt-1 flex gap-2">
                  <span className="text-[10px] uppercase font-bold text-error tracking-wider border border-error/30 px-1 rounded bg-error/5">Conf: 98.4%</span>
                </div>
              </div>
              {/* Anomaly Item 3 */}
              <div className="p-3 border border-outline-variant rounded-lg bg-surface hover:border-primary transition-colors cursor-pointer flex flex-col gap-2 relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#f59e0b]" />
                <div className="flex justify-between items-start pl-2">
                  <div className="flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px] text-[#f59e0b]">graphic_eq</span>
                    <span className="text-label-md text-on-surface">Audio Noise Floor Shift</span>
                  </div>
                  <span className="font-mono text-label-sm text-on-surface-variant bg-surface-container px-1.5 rounded">00:03:55</span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant pl-2">Sudden drop in background ambient frequency spectrum.</p>
              </div>
            </div>
          </div>
          {/* Forensic Verdict Controls */}
          <div className="bg-surface-container-low border border-outline-variant rounded-xl p-4 shrink-0 shadow-sm">
            <h3 className="text-label-md text-on-surface-variant uppercase tracking-widest mb-3">Final Verdict</h3>
            <div className="grid grid-cols-3 gap-2">
              <button className="flex flex-col items-center justify-center py-3 border border-outline-variant bg-surface hover:bg-surface-container-highest transition-colors rounded-lg gap-1 group">
                <span className="material-symbols-outlined text-outline group-hover:text-primary transition-colors">check_circle</span>
                <span className="text-label-sm text-on-surface">Authentic</span>
              </button>
              <button className="flex flex-col items-center justify-center py-3 border-2 border-error bg-error/5 hover:bg-error/10 transition-colors rounded-lg gap-1">
                <span className="material-symbols-outlined text-error" data-weight="fill">gpp_bad</span>
                <span className="text-label-sm text-error font-bold">Manipulated</span>
              </button>
              <button className="flex flex-col items-center justify-center py-3 border border-outline-variant bg-surface hover:bg-surface-container-highest transition-colors rounded-lg gap-1 group">
                <span className="material-symbols-outlined text-outline group-hover:text-primary transition-colors">help</span>
                <span className="text-label-sm text-on-surface">Inconclusive</span>
              </button>
            </div>
            <button className="w-full mt-3 bg-secondary text-on-secondary py-2 rounded-lg text-label-md flex items-center justify-center gap-2 hover:opacity-90 transition-opacity">
              <span className="material-symbols-outlined text-[18px]">summarize</span>
              Generate Report
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}

