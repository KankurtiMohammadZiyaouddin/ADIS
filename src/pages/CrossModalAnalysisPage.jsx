export default function CrossModalAnalysisPage() {
  return (
    <main className="flex-1 p-gutter lg:p-container-margin overflow-y-auto bg-background">
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h2 className="text-display-lg font-display-lg text-on-surface">Cross-Modal Correlation</h2>
          <p className="text-body-lg font-body-lg text-on-surface-variant mt-2">Combined evidence assessment for Exhibit C-88 (Deepfake Suspected)</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 border border-outline-variant bg-surface text-on-surface rounded text-label-md hover:bg-surface-container transition-colors">
            Export Full Report
          </button>
          <button className="px-4 py-2 bg-secondary text-on-secondary rounded text-label-md hover:opacity-90 transition-opacity flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px]" data-icon="auto_awesome">auto_awesome</span>
            Re-run Analysis
          </button>
        </div>
      </div>
      {/* Bento Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter lg:gap-6">
        {/* Overall Confidence Score (Hero Card) */}
        <div className="col-span-1 md:col-span-4 lg:col-span-3 bg-surface border border-outline-variant rounded-xl p-6 flex flex-col justify-between shadow-[0px_4px_12px_rgba(23,32,51,0.08)]">
          <div>
            <h3 className="text-headline-sm font-headline-sm text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-error" data-icon="warning">warning</span>
              Assessment
            </h3>
            <p className="text-body-sm font-body-sm text-on-surface-variant mt-1">AI Manipulation Probability</p>
          </div>
          <div className="mt-8 mb-4">
            <div className="flex items-end gap-2 mb-2">
              <span className="text-[48px] font-bold leading-none text-error tracking-tight">94<span className="text-[24px]">%</span></span>
            </div>
            <div className="w-full bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
              <div className="bg-error h-full rounded-full w-[94%]" />
            </div>
            <p className="text-label-sm text-error mt-2 font-bold uppercase tracking-wider">High Confidence: Synthetic</p>
          </div>
          <div className="pt-4 border-t border-outline-variant mt-auto space-y-2 text-body-sm font-body-sm">
            <div className="flex justify-between">
              <span className="text-on-surface-variant">Visual Traces</span>
              <span className="text-on-surface font-mono">0.89</span>
            </div>
            <div className="flex justify-between">
              <span className="text-on-surface-variant">Audio Spectral</span>
              <span className="text-on-surface font-mono">0.96</span>
            </div>
          </div>
        </div>
        {/* Correlation Matrix */}
        <div className="col-span-1 md:col-span-8 lg:col-span-9 bg-surface border border-outline-variant rounded-xl p-6 shadow-[0px_4px_12px_rgba(23,32,51,0.08)]">
          <h3 className="text-headline-sm font-headline-sm text-on-surface mb-6">Cross-Modal Matrix</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr>
                  <th className="p-3 text-label-sm text-on-surface-variant bg-surface-container-low border-b border-outline-variant font-medium">Modality Pairing</th>
                  <th className="p-3 text-label-sm text-on-surface-variant bg-surface-container-low border-b border-outline-variant font-medium">Correlation Coefficient</th>
                  <th className="p-3 text-label-sm text-on-surface-variant bg-surface-container-low border-b border-outline-variant font-medium">Deviation Vector</th>
                  <th className="p-3 text-label-sm text-on-surface-variant bg-surface-container-low border-b border-outline-variant font-medium">Forensic Status</th>
                </tr>
              </thead>
              <tbody className="text-body-md font-body-md text-on-surface">
                <tr className="hover:bg-primary/5 border-b border-outline-variant/50 transition-colors group">
                  <td className="p-3 py-4 flex items-center gap-3">
                    <div className="flex -space-x-2">
                      <div className="w-8 h-8 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center z-10"><span className="material-symbols-outlined text-[16px]" data-icon="videocam">videocam</span></div>
                      <div className="w-8 h-8 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center"><span className="material-symbols-outlined text-[16px]" data-icon="mic">mic</span></div>
                    </div>
                    <span className="font-medium">Face / Voice Pairing</span>
                  </td>
                  <td className="p-3 font-mono">r = 0.24 (Expected: &gt;0.85)</td>
                  <td className="p-3">
                    <div className="w-24 bg-surface-container-highest h-1 rounded-full"><div className="bg-error h-full rounded-full w-[80%]" /></div>
                  </td>
                  <td className="p-3"><span className="inline-flex items-center gap-1 text-error text-label-sm px-2 py-1 bg-error-container/30 rounded"><span className="material-symbols-outlined text-[14px]" data-icon="cancel">cancel</span> Anomalous</span></td>
                </tr>
                <tr className="hover:bg-primary/5 border-b border-outline-variant/50 transition-colors">
                  <td className="p-3 py-4 flex items-center gap-3">
                    <div className="flex -space-x-2">
                      <div className="w-8 h-8 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center z-10"><span className="material-symbols-outlined text-[16px]" data-icon="face">face</span></div>
                      <div className="w-8 h-8 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center"><span className="material-symbols-outlined text-[16px]" data-icon="graphic_eq">graphic_eq</span></div>
                    </div>
                    <span className="font-medium">Lip-Sync Correlation</span>
                  </td>
                  <td className="p-3 font-mono">Δt = 142ms delay</td>
                  <td className="p-3">
                    <div className="w-24 bg-surface-container-highest h-1 rounded-full"><div className="bg-tertiary h-full rounded-full w-[65%]" /></div>
                  </td>
                  <td className="p-3"><span className="inline-flex items-center gap-1 text-tertiary text-label-sm px-2 py-1 bg-tertiary-container/30 rounded"><span className="material-symbols-outlined text-[14px]" data-icon="warning">warning</span> De-synced</span></td>
                </tr>
                <tr className="hover:bg-primary/5 transition-colors">
                  <td className="p-3 py-4 flex items-center gap-3">
                    <div className="flex -space-x-2">
                      <div className="w-8 h-8 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center z-10"><span className="material-symbols-outlined text-[16px]" data-icon="timer">timer</span></div>
                      <div className="w-8 h-8 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center"><span className="material-symbols-outlined text-[16px]" data-icon="code">code</span></div>
                    </div>
                    <span className="font-medium">Temporal / Metadata Alignment</span>
                  </td>
                  <td className="p-3 font-mono">Valid PTS/DTS</td>
                  <td className="p-3">
                    <div className="w-24 bg-surface-container-highest h-1 rounded-full"><div className="bg-primary h-full rounded-full w-[10%]" /></div>
                  </td>
                  <td className="p-3"><span className="inline-flex items-center gap-1 text-primary text-label-sm px-2 py-1 bg-primary-container/30 rounded"><span className="material-symbols-outlined text-[14px]" data-icon="check_circle">check_circle</span> Consistent</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        {/* Deep Dive: Spectral vs Visual */}
        <div className="col-span-1 md:col-span-12 bg-surface border border-outline-variant rounded-xl p-6 flex flex-col lg:flex-row gap-6 shadow-[0px_4px_12px_rgba(23,32,51,0.08)]">
          <div className="w-full lg:w-1/3 flex flex-col justify-center">
            <h4 className="text-title-lg font-title-lg text-on-surface mb-2">Spectrogram vs. Frame Analysis</h4>
            <p className="text-body-sm font-body-sm text-on-surface-variant mb-4">
              High-frequency artifacts detected in audio channel (12-16kHz range) do not correspond with ambient visual noise signatures in the background environment. This suggests the audio track was synthesized or heavily processed separately from the video capture.
            </p>
            <div className="bg-surface-container p-4 rounded border border-outline-variant border-dashed">
              <div className="flex justify-between mb-1">
                <span className="text-label-sm text-on-surface-variant">Audio Artifact Severity</span>
                <span className="text-label-sm text-error font-mono">High</span>
              </div>
              <div className="w-full bg-surface h-1 rounded-full"><div className="bg-error h-full rounded-full w-[88%]" /></div>
            </div>
          </div>
          <div className="w-full lg:w-2/3 h-64 bg-surface-container-lowest border border-outline-variant rounded overflow-hidden relative">
            {/* Simulated Shader / Data Viz Area */}
            <div className="absolute inset-0 opacity-40 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/20 via-surface to-surface" />
            <div className="absolute bottom-4 left-4 right-4 h-32 border-b border-l border-outline-variant flex items-end gap-1 pb-1 pl-1">
              {/* Fake Bar Chart representing spectral data */}
              <div className="w-full h-[30%] bg-outline-variant/30 rounded-t" />
              <div className="w-full h-[45%] bg-outline-variant/30 rounded-t" />
              <div className="w-full h-[85%] bg-error/50 rounded-t" />
              <div className="w-full h-[95%] bg-error/70 rounded-t" />
              <div className="w-full h-[60%] bg-error/50 rounded-t" />
              <div className="w-full h-[20%] bg-outline-variant/30 rounded-t" />
              <div className="w-full h-[15%] bg-outline-variant/30 rounded-t" />
              <div className="w-full h-[40%] bg-outline-variant/30 rounded-t" />
            </div>
            <span className="absolute top-4 right-4 text-[10px] text-on-surface-variant font-mono">FREQ: 14.2kHz SPIKE DETECTED</span>
          </div>
        </div>
      </div>
    </main>
  );
}

