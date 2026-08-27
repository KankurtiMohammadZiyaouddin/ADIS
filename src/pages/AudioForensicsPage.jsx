export default function AudioForensicsPage() {
  return (
    <main className="flex-1 p-spacious p-container-margin overflow-y-auto">
      {/* Header Section */}
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h2 className="text-headline-md font-headline-md text-on-surface mb-1">EVD-883-AUDIO.wav</h2>
          <p className="text-body-sm font-body-sm text-on-surface-variant flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px]">schedule</span> Duration: 00:02:45 | 
            <span className="material-symbols-outlined text-[16px]">mic</span> 44.1 kHz, 16-bit Mono
          </p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-surface text-primary border border-outline-variant rounded hover:bg-surface-container-highest text-label-md transition-colors flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">download</span> Export Report
          </button>
          <button className="px-4 py-2 bg-secondary text-on-secondary rounded hover:opacity-90 text-label-md transition-colors flex items-center gap-2 shadow-sm">
            <span className="material-symbols-outlined text-[18px]">memory</span> Run AI Deep Scan
          </button>
        </div>
      </div>
      {/* Bento Grid Layout */}
      <div className="grid grid-cols-12 gap-gutter">
        {/* Main Viewer Area (Col 1-8) */}
        <div className="col-span-8 flex flex-col gap-gutter">
          {/* Waveform Viewer */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-padding-default flex flex-col h-[240px] relative overflow-hidden">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-title-lg font-title-lg text-on-surface">Waveform Analysis</h3>
              <div className="flex gap-2">
                <button className="p-1 bg-surface-container rounded border border-outline-variant hover:bg-surface-container-highest"><span className="material-symbols-outlined text-[18px]">zoom_in</span></button>
                <button className="p-1 bg-surface-container rounded border border-outline-variant hover:bg-surface-container-highest"><span className="material-symbols-outlined text-[18px]">zoom_out</span></button>
              </div>
            </div>
            {/* Simulated Waveform */}
            <div className="flex-1 bg-surface-container-low rounded border border-outline-variant relative flex items-center overflow-hidden">
              {/* Axis/Grid lines */}
              <div className="absolute inset-0 flex flex-col justify-between py-2 opacity-20 pointer-events-none">
                <div className="border-b border-primary w-full h-px" />
                <div className="border-b border-primary w-full h-px" />
                <div className="border-b border-primary w-full h-px" />
              </div>
              {/* Fake Waveform SVG */}
              <div className="w-full h-24 flex items-center px-2 space-x-0.5" id="waveform-container">
                {/* JS will populate this with bars */}
              </div>
              {/* Scrubber */}
              <div className="absolute top-0 bottom-0 left-1/3 w-px bg-error z-10 flex flex-col items-center group cursor-ew-resize">
                <div className="w-2 h-2 bg-error rounded-full -mt-1" />
                <div className="absolute -top-6 bg-surface-container-highest text-on-surface text-label-sm px-1 rounded shadow-sm opacity-0 group-hover:opacity-100 transition-opacity">00:00:55</div>
              </div>
              {/* Highlight Region (Anomaly) */}
              <div className="absolute top-0 bottom-0 left-[40%] w-[15%] bg-error/10 border-x border-error/50 z-0" />
            </div>
          </div>
          {/* Mel-Spectrogram */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-padding-default flex flex-col h-[280px]">
            <h3 className="text-title-lg font-title-lg text-on-surface mb-2">Mel-Spectrogram</h3>
            <div className="flex-1 rounded border border-outline-variant relative overflow-hidden bg-surface-container-high" style={{background: 'linear-gradient(90deg, #121b2e 0%, #1a0063 50%, #2f1191 100%)'}}>
              {/* Simulated Heatmap Texture (Using CSS pattern instead of image) */}
              <div className="absolute inset-0 opacity-40 mix-blend-overlay" style={{backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.1) 2px, rgba(255,255,255,0.1) 4px)', backgroundSize: '100% 4px'}} />
              {/* Specific Frequency Anomaly Highlight */}
              <div className="absolute top-[30%] left-[40%] w-[15%] h-[20%] border border-error bg-error/20 rounded-sm pointer-events-none z-10">
                <span className="absolute -top-5 right-0 text-error text-label-sm bg-surface-container-lowest px-1 rounded border border-error">Phase discontinuity</span>
              </div>
            </div>
          </div>
        </div>
        {/* Right Rail (Col 9-12) */}
        <div className="col-span-4 flex flex-col gap-gutter">
          {/* Probability Gauge */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-padding-default flex flex-col items-center justify-center">
            <h3 className="text-title-lg font-title-lg text-on-surface self-start mb-4">Synthetic Speech Probability</h3>
            <div className="relative w-40 h-40 flex items-center justify-center mb-2">
              {/* Circular Progress SVG */}
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle className="stroke-surface-container-highest" cx={50} cy={50} fill="none" r={45} strokeWidth={8} />
                <circle className="stroke-error" cx={50} cy={50} fill="none" r={45} strokeDasharray={283} strokeDashoffset={22} strokeLinecap="round" strokeWidth={8} />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-display-lg font-display-lg text-error">92%</span>
                <span className="text-label-sm text-error">HIGH CONFIDENCE</span>
              </div>
            </div>
            <p className="text-body-sm font-body-sm text-on-surface-variant text-center mt-2">Deepfake generation signatures detected in high-frequency spectral bands.</p>
          </div>
          {/* Speaker Consistency */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-padding-default">
            <h3 className="text-title-lg font-title-lg text-on-surface mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-[20px] text-primary">record_voice_over</span>
              Speaker Consistency
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-body-sm font-body-sm">
                <span className="text-on-surface-variant">Primary Speaker Profile</span>
                <span className="text-on-surface font-medium">Match: 45%</span>
              </div>
              <div className="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                <div className="bg-error h-full" style={{width: '45%'}} />
              </div>
              <div className="mt-4 p-3 bg-error-container/30 border border-error/20 rounded text-body-sm font-body-sm text-on-surface">
                <span className="font-semibold text-error block mb-1">Anomaly Detected</span>
                Vocal tract resonance mismatch detected between [00:00:55] and [00:01:20].
              </div>
            </div>
          </div>
          {/* Prosody Flags */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-padding-default flex-1">
            <h3 className="text-title-lg font-title-lg text-on-surface mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-[20px] text-secondary">trending_up</span>
              Prosody Analysis
            </h3>
            <ul className="space-y-2">
              <li className="flex gap-2 items-start text-body-sm font-body-sm p-2 bg-surface rounded border border-outline-variant">
                <span className="material-symbols-outlined text-[16px] text-error mt-0.5">warning</span>
                <div>
                  <span className="font-medium text-on-surface block">Unnatural Pitch Contours</span>
                  <span className="text-on-surface-variant text-label-sm">Absence of typical micro-tremors in sustained vowels.</span>
                </div>
              </li>
              <li className="flex gap-2 items-start text-body-sm font-body-sm p-2 bg-surface rounded border border-outline-variant">
                <span className="material-symbols-outlined text-[16px] text-primary mt-0.5">info</span>
                <div>
                  <span className="font-medium text-on-surface block">Rhythm Regularity</span>
                  <span className="text-on-surface-variant text-label-sm">Slightly more rhythmic than baseline human speech.</span>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
      {/* Segment Analysis Table */}
      <div className="mt-gutter bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden">
        <div className="p-padding-default border-b border-outline-variant flex justify-between items-center bg-surface">
          <h3 className="text-title-lg font-title-lg text-on-surface">Segment Analysis</h3>
          <button className="text-label-md text-primary flex items-center gap-1 hover:underline">
            View Full Details <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
          </button>
        </div>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-low text-label-sm text-on-surface-variant border-b border-outline-variant">
              <th className="py-2 px-4 font-medium w-24">Time Range</th>
              <th className="py-2 px-4 font-medium w-32">Segment Type</th>
              <th className="py-2 px-4 font-medium">Artifact Description</th>
              <th className="py-2 px-4 font-medium w-48">Manipulation Probability</th>
              <th className="py-2 px-4 font-medium w-24 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="text-body-sm font-body-sm text-on-surface">
            <tr className="border-b border-outline-variant hover:bg-primary/5 transition-colors">
              <td className="py-3 px-4 font-mono text-on-surface-variant">00:00:10 - 00:00:45</td>
              <td className="py-3 px-4">Baseline Speech</td>
              <td className="py-3 px-4 text-on-surface-variant">Natural breath sounds, consistent room tone.</td>
              <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                    <div className="bg-primary h-full" style={{width: '12%'}} />
                  </div>
                  <span className="text-label-sm">12%</span>
                </div>
              </td>
              <td className="py-3 px-4 text-center">
                <button className="text-on-surface-variant hover:text-primary"><span className="material-symbols-outlined text-[18px]">play_arrow</span></button>
              </td>
            </tr>
            <tr className="border-b border-outline-variant bg-error/5 hover:bg-error/10 transition-colors">
              <td className="py-3 px-4 font-mono text-error font-medium">00:00:55 - 00:01:20</td>
              <td className="py-3 px-4 font-medium">Suspect Inject</td>
              <td className="py-3 px-4">Phase discontinuity at splice point; synthetic high-frequency artifacts.</td>
              <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                    <div className="bg-error h-full" style={{width: '96%'}} />
                  </div>
                  <span className="text-label-sm text-error font-bold">96%</span>
                </div>
              </td>
              <td className="py-3 px-4 text-center">
                <button className="text-primary hover:text-primary-container"><span className="material-symbols-outlined text-[18px]">play_circle</span></button>
              </td>
            </tr>
            <tr className="hover:bg-primary/5 transition-colors">
              <td className="py-3 px-4 font-mono text-on-surface-variant">00:01:25 - 00:02:45</td>
              <td className="py-3 px-4">Baseline Speech</td>
              <td className="py-3 px-4 text-on-surface-variant">Return to baseline profile characteristics.</td>
              <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                    <div className="bg-primary h-full" style={{width: '15%'}} />
                  </div>
                  <span className="text-label-sm">15%</span>
                </div>
              </td>
              <td className="py-3 px-4 text-center">
                <button className="text-on-surface-variant hover:text-primary"><span className="material-symbols-outlined text-[18px]">play_arrow</span></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  );
}

