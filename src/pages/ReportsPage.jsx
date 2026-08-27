export default function ReportsPage() {
  return (
    <main className="ml-[260px] pt-14 p-spacious min-h-screen">
      <div className="max-w-[1600px] mx-auto grid grid-cols-1 xl:grid-cols-12 gap-6 p-6">
        {/* Left Column: Reports List (Table) */}
        <div className="xl:col-span-5 flex flex-col gap-6">
          <div className="flex justify-between items-end mb-2">
            <div>
              <h2 className="text-headline-md font-headline-md text-on-surface">Generated Reports</h2>
              <p className="text-body-sm font-body-sm text-on-surface-variant mt-1">Manage and export forensic documentation.</p>
            </div>
            <div className="flex gap-2">
              <button aria-label="Filter" className="p-2 border border-outline-variant rounded bg-surface hover:bg-surface-container transition-colors text-on-surface-variant">
                <span className="material-symbols-outlined text-[18px]">filter_list</span>
              </button>
            </div>
          </div>
          <div className="bg-surface rounded-lg border border-outline-variant shadow-sm overflow-hidden flex-1">
            <table className="w-full text-left border-collapse">
              <thead className="bg-surface-container-low border-b border-outline-variant">
                <tr>
                  <th className="py-3 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider">Report ID</th>
                  <th className="py-3 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider">Type</th>
                  <th className="py-3 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider">Date</th>
                  <th className="py-3 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant">
                {/* Active Row */}
                <tr className="bg-primary/5 cursor-pointer hover:bg-primary/10 transition-colors">
                  <td className="py-3 px-4 text-body-sm font-body-sm font-medium text-primary">FR-4492-A</td>
                  <td className="py-3 px-4 text-body-sm font-body-sm text-on-surface">Deepfake Analysis</td>
                  <td className="py-3 px-4 text-body-sm font-body-sm text-on-surface-variant">Oct 24, 2023</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-secondary-container text-on-secondary-container">FINAL</span>
                  </td>
                </tr>
                <tr className="cursor-pointer hover:bg-surface-container-low transition-colors">
                  <td className="py-3 px-4 text-body-sm font-body-sm font-medium text-on-surface">FR-4492-B</td>
                  <td className="py-3 px-4 text-body-sm font-body-sm text-on-surface">Metadata Ext.</td>
                  <td className="py-3 px-4 text-body-sm font-body-sm text-on-surface-variant">Oct 23, 2023</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-surface-variant text-on-surface-variant">DRAFT</span>
                  </td>
                </tr>
                <tr className="cursor-pointer hover:bg-surface-container-low transition-colors">
                  <td className="py-3 px-4 text-body-sm font-body-sm font-medium text-on-surface">FR-4491-C</td>
                  <td className="py-3 px-4 text-body-sm font-body-sm text-on-surface">Audio Spectra</td>
                  <td className="py-3 px-4 text-body-sm font-body-sm text-on-surface-variant">Oct 20, 2023</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-secondary-container text-on-secondary-container">FINAL</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        {/* Right Column: Document Preview (Bento/Paper style) */}
        <div className="xl:col-span-7 flex flex-col gap-4">
          {/* Action Bar */}
          <div className="flex justify-between items-center bg-surface p-3 rounded-lg border border-outline-variant shadow-sm">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-on-surface-variant">picture_as_pdf</span>
              <span className="text-label-md text-on-surface font-medium">FR-4492-A_Final.pdf</span>
            </div>
            <div className="flex gap-2">
              <button className="px-4 py-1.5 border border-outline-variant bg-surface rounded text-body-sm font-body-sm text-on-surface hover:bg-surface-container transition-colors flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px]">share</span> Secure Share
              </button>
              <button className="px-4 py-1.5 bg-primary rounded text-body-sm font-body-sm text-on-primary hover:bg-primary-container transition-colors flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px]">download</span> Export PDF
              </button>
            </div>
          </div>
          {/* Document Paper */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-sm shadow-[0px_4px_12px_rgba(23,32,51,0.08)] p-8 md:p-12 min-h-[800px] flex flex-col gap-8 relative overflow-hidden">
            {/* Govt/Official Header */}
            <div className="border-b-2 border-on-surface pb-6 flex justify-between items-start">
              <div>
                <h1 className="text-display-lg font-display-lg text-on-surface uppercase tracking-tight">Forensic Analysis Report</h1>
                <p className="text-label-md text-on-surface-variant mt-2 font-mono">CASE REF: #4492 | DOC ID: FR-4492-A</p>
              </div>
              <div className="text-right">
                <div className="text-title-lg font-title-lg font-black text-on-surface tracking-tight">ADIS</div>
                <p className="text-label-sm text-on-surface-variant uppercase">Dept. of Digital Forensics</p>
                <p className="text-label-sm text-on-surface-variant mt-1">DATE: 2023-10-24</p>
              </div>
            </div>
            {/* Executive Summary */}
            <section>
              <h3 className="text-title-lg font-title-lg text-on-surface border-b border-outline-variant pb-2 mb-4">1.0 Executive Summary</h3>
              <p className="text-body-md font-body-md text-on-surface-variant leading-relaxed">
                Analysis of Exhibit A (vid_evidence_04.mp4) indicates high probability of synthetic manipulation. Cross-modal analysis reveals inconsistencies between facial rendering artifacts and audio lip-sync alignment. The primary subject's facial features exhibit temporal flickering characteristic of GAN-based synthesis.
              </p>
            </section>
            {/* Artifacts & Confidence (Bento layout within doc) */}
            <section>
              <h3 className="text-title-lg font-title-lg text-on-surface border-b border-outline-variant pb-2 mb-4">2.0 Detection Methodologies &amp; Confidence</h3>
              <div className="grid grid-cols-2 gap-4">
                {/* Card 1 */}
                <div className="border border-outline-variant p-4 rounded bg-surface">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-label-md text-on-surface uppercase">Spatial Frequency Analysis</span>
                    <span className="material-symbols-outlined text-error text-[18px]">warning</span>
                  </div>
                  <p className="text-body-sm font-body-sm text-on-surface-variant mb-3">Detected anomalous high-frequency noise patterns consistent with upscaling models.</p>
                  <div className="w-full bg-surface-container-high h-1 rounded-full overflow-hidden">
                    <div className="bg-error h-full" style={{width: '92%'}} />
                  </div>
                  <div className="text-right mt-1 text-label-sm text-error">92% Confidence (Anomaly)</div>
                </div>
                {/* Card 2 */}
                <div className="border border-outline-variant p-4 rounded bg-surface">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-label-md text-on-surface uppercase">Audio-Visual Sync</span>
                    <span className="material-symbols-outlined text-error text-[18px]">warning</span>
                  </div>
                  <p className="text-body-sm font-body-sm text-on-surface-variant mb-3">Viseme-phoneme mismatch detected in frames 450-520.</p>
                  <div className="w-full bg-surface-container-high h-1 rounded-full overflow-hidden">
                    <div className="bg-error h-full" style={{width: '88%'}} />
                  </div>
                  <div className="text-right mt-1 text-label-sm text-error">88% Confidence (Anomaly)</div>
                </div>
              </div>
            </section>
            {/* Verdict */}
            <section className="mt-auto pt-8 border-t border-outline-variant">
              <h3 className="text-title-lg font-title-lg text-on-surface mb-4">3.0 Investigator Verdict</h3>
              <div className="bg-error-container text-on-error-container p-4 rounded-sm border-l-4 border-error">
                <p className="text-body-md font-body-md font-medium uppercase tracking-wide mb-1">Conclusion: SYNTHETIC / MANIPULATED</p>
                <p className="text-body-sm font-body-sm">The digital evidence submitted has been confirmed as artificially generated or substantially manipulated with intent to deceive.</p>
              </div>
              <div className="mt-8 flex justify-between items-end">
                <div>
                  <p className="text-label-sm text-on-surface-variant uppercase mb-1">Authorized By</p>
                  <div className="font-mono text-body-md border-b border-outline-variant pb-1 px-4 inline-block">J. Doe, Sr. Analyst</div>
                </div>
                <div className="w-24 h-24 border border-outline-variant rounded-full flex items-center justify-center opacity-50 relative">
                  <span className="absolute text-[10px] text-on-surface-variant uppercase font-bold tracking-widest rotate-[-30deg]">Official Seal</span>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}

