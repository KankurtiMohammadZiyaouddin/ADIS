export default function CaseInvestigationPage() {
  return (
    <main className="flex-1 overflow-y-auto p-gutter lg:p-container-margin relative">
      {/* Decorative background element for modern feel */}
      <div className="absolute top-0 right-0 w-1/3 h-64 bg-gradient-to-bl from-primary-container/10 to-transparent -z-10 blur-3xl pointer-events-none" />
      {/* Page Header Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="bg-error/10 text-error border border-error/20 px-2 py-0.5 rounded text-[10px] font-bold tracking-wider">ACTIVE</span>
            <span className="text-[11px] text-on-surface-variant uppercase tracking-wider">CASE-2024-0892</span>
          </div>
          <h2 className="text-display-lg font-display-lg text-on-surface">Target Entity Verification</h2>
        </div>
        <div className="flex gap-2">
          <button className="bg-surface text-on-surface border border-outline-variant px-4 py-2 rounded text-label-md hover:bg-surface-container-low transition-colors shadow-sm flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">download</span> Export Report
          </button>
          <button className="bg-secondary text-white px-4 py-2 rounded text-label-md hover:bg-secondary-container hover:text-on-secondary-container transition-colors shadow-sm flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">auto_awesome</span> Run AI Pipeline
          </button>
        </div>
      </div>
      {/* Bento Grid Layout */}
      <div className="grid grid-cols-12 gap-gutter">
        {/* Assessment Card (Bento Left - Top) */}
        <div className="col-span-12 lg:col-span-4 bg-surface border border-outline-variant rounded-xl p-6 shadow-sm flex flex-col justify-between relative overflow-hidden">
          <div className="absolute -right-10 -top-10 text-error/5 material-symbols-outlined text-[150px] pointer-events-none">warning</div>
          <div>
            <h3 className="text-label-sm text-on-surface-variant uppercase tracking-wider mb-2">Overall Assessment</h3>
            <div className="text-[48px] font-bold text-error leading-none mb-1">78%</div>
            <div className="text-headline-sm font-headline-sm text-on-surface mb-4">HIGHLY SUSPICIOUS</div>
            <div className="flex items-center gap-2 mb-6">
              <span className="material-symbols-outlined text-primary text-[18px]">verified_user</span>
              <span className="text-body-sm font-body-sm text-on-surface-variant">Confidence Level: <strong>92%</strong></span>
            </div>
          </div>
          <div className="space-y-3 pt-4 border-t border-outline-variant">
            <h4 className="text-label-md text-on-surface">Key Indicators:</h4>
            <div className="flex flex-wrap gap-2">
              <span className="px-2 py-1 bg-surface-container-highest text-on-surface text-[11px] font-mono rounded border border-outline-variant">GAN Artifacts Detected</span>
              <span className="px-2 py-1 bg-surface-container-highest text-on-surface text-[11px] font-mono rounded border border-outline-variant">Moiré Pattern (Audio)</span>
              <span className="px-2 py-1 bg-surface-container-highest text-on-surface text-[11px] font-mono rounded border border-outline-variant">Metadata Missing</span>
            </div>
          </div>
        </div>
        {/* Analysis Pipeline / Evidence Preview (Bento Middle/Right - Top) */}
        <div className="col-span-12 lg:col-span-8 bg-surface border border-outline-variant rounded-xl flex flex-col overflow-hidden shadow-sm">
          {/* Tabs */}
          <div className="flex border-b border-outline-variant bg-surface-container-low px-2 pt-2">
            <button className="px-4 py-2 text-label-md text-primary border-b-2 border-primary font-bold">Overview</button>
            <button className="px-4 py-2 text-label-md text-on-surface-variant hover:text-on-surface">Evidence Gallery</button>
            <button className="px-4 py-2 text-label-md text-on-surface-variant hover:text-on-surface">Analysis Pipeline</button>
            <button className="px-4 py-2 text-label-md text-on-surface-variant hover:text-on-surface">Timeline</button>
          </div>
          <div className="p-6 flex-1 flex flex-col md:flex-row gap-6">
            {/* Evidence Preview */}
            <div className="w-full md:w-1/2 flex flex-col">
              <h3 className="text-label-sm text-on-surface-variant uppercase tracking-wider mb-3">Primary Subject Evidence</h3>
              <div className="relative rounded-lg overflow-hidden border border-outline-variant bg-black flex-1 min-h-[200px] flex items-center justify-center group cursor-pointer">
                <img alt="Primary Evidence Subject" className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" data-alt="A stark, high-contrast black and white surveillance-style still image of a male suspect in an urban setting. A subtle green digital targeting reticle is overlaid on his face. The overall aesthetic is gritty, technical, and analytical, fitting a modern digital forensics platform." src="https://lh3.googleusercontent.com/aida-public/AB6AXuD0H4TiUNBINKkxSJMmKcnu6nEh7AVwSr7Ke4cMoMYP1ujP50pItE_PKTdpmB9tuUb2z-lFciX1Vjyl9TtmAi6yrEzSGQY-B3BKYslsfwq2CJtdBZwuxsnOPajbRbwZRG_OMSLR6livxGILzwvkbip54fQBK3xoyoC4ad8KdJa3B2vdQ1VZwzroygAJBxfaWWgr1Or8IsGdOw5ksJ6klfq6RRXotMSJvSt0yrVn3tk2uMbaRGoOC_M" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="bg-surface/80 backdrop-blur rounded-full p-3 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                    <span className="material-symbols-outlined fill-icon text-3xl">play_arrow</span>
                  </div>
                </div>
                <div className="absolute bottom-2 left-2 bg-surface/90 px-2 py-1 rounded text-[10px] font-mono text-on-surface border border-outline-variant shadow-sm backdrop-blur">
                  SRC: VID_492_A.mp4
                </div>
              </div>
            </div>
            {/* Forensic Indicators */}
            <div className="w-full md:w-1/2 flex flex-col">
              <h3 className="text-label-sm text-on-surface-variant uppercase tracking-wider mb-3">Forensic Vectors</h3>
              <div className="space-y-4">
                {/* Indicator 1 */}
                <div>
                  <div className="flex justify-between text-body-sm font-body-sm mb-1">
                    <span className="text-on-surface flex items-center gap-1"><span className="material-symbols-outlined text-[16px] text-outline">face</span> Face Morphing</span>
                    <span className="text-error font-bold">84%</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-error rounded-full" style={{width: '84%'}} />
                  </div>
                </div>
                {/* Indicator 2 */}
                <div>
                  <div className="flex justify-between text-body-sm font-body-sm mb-1">
                    <span className="text-on-surface flex items-center gap-1"><span className="material-symbols-outlined text-[16px] text-outline">graphic_eq</span> Audio Deepfake</span>
                    <span className="text-error font-bold">71%</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-error rounded-full" style={{width: '71%'}} />
                  </div>
                </div>
                {/* Indicator 3 */}
                <div>
                  <div className="flex justify-between text-body-sm font-body-sm mb-1">
                    <span className="text-on-surface flex items-center gap-1"><span className="material-symbols-outlined text-[16px] text-outline">code</span> Metadata Integrity</span>
                    <span className="text-primary font-bold">12% Anomalies</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{width: '12%'}} />
                  </div>
                </div>
                {/* Indicator 4 */}
                <div>
                  <div className="flex justify-between text-body-sm font-body-sm mb-1">
                    <span className="text-on-surface flex items-center gap-1"><span className="material-symbols-outlined text-[16px] text-outline">location_on</span> Geolocation Drift</span>
                    <span className="text-outline-variant">N/A</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-outline-variant rounded-full" style={{width: '0%'}} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        {/* Bottom Row: Notes & Actions */}
        <div className="col-span-12 lg:col-span-12 grid grid-cols-1 lg:grid-cols-3 gap-gutter">
          {/* Investigator Notes */}
          <div className="col-span-1 lg:col-span-2 bg-surface border border-outline-variant rounded-xl p-6 shadow-sm flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-label-sm text-on-surface-variant uppercase tracking-wider">Investigator Notes</h3>
              <button className="text-primary text-label-sm flex items-center gap-1 hover:underline">
                <span className="material-symbols-outlined text-[16px]">edit</span> Edit
              </button>
            </div>
            <div className="bg-surface-container-lowest border border-outline-variant rounded flex-1 p-4 text-body-md font-body-md text-on-surface min-h-[120px]">
              Initial review of VID_492_A.mp4 shows significant blurring around the jawline during frames 240-310. Audio track appears desynchronized with lip movement in the secondary channel. Proceeding with cross-modal analysis to verify...
            </div>
          </div>
          {/* Human-in-the-Loop Actions */}
          <div className="col-span-1 bg-surface border border-outline-variant rounded-xl p-6 shadow-sm flex flex-col justify-center">
            <h3 className="text-label-sm text-on-surface-variant uppercase tracking-wider mb-4 text-center">Analyst Adjudication</h3>
            <p className="text-body-sm font-body-sm text-on-surface-variant text-center mb-6">Review AI findings and determine final evidentiary status.</p>
            <div className="flex flex-col gap-3">
              <button className="w-full bg-primary text-on-primary py-2.5 rounded text-label-md hover:bg-primary-container transition-colors shadow flex justify-center items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">thumb_up</span> Accept AI Findings
              </button>
              <button className="w-full bg-surface text-error border border-error/50 py-2.5 rounded text-label-md hover:bg-error/10 transition-colors flex justify-center items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">thumb_down</span> Reject / Flag for Review
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

