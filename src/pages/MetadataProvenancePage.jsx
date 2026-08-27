export default function MetadataProvenancePage() {
  return (
    <main className="flex-1 p-gutter overflow-y-auto">
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h2 className="font-headline-md text-headline-md text-on-surface mb-1">EVD-2024-0892_source.mp4</h2>
          <p className="font-body-sm text-body-sm text-on-surface-variant">Detailed Metadata &amp; C2PA Provenance Analysis</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 border border-outline-variant bg-surface-container-lowest text-on-surface text-label-md rounded flex items-center gap-2 hover:bg-surface-container-low">
            <span className="material-symbols-outlined text-[18px]">download</span> Export Report
          </button>
          <button className="px-4 py-2 bg-secondary text-on-secondary text-label-md rounded flex items-center gap-2 hover:opacity-90">
            <span className="material-symbols-outlined text-[18px]">psychology</span> AI Deep Scan
          </button>
        </div>
      </div>
      {/* Bento Grid Layout */}
      <div className="grid grid-cols-12 gap-gutter">
        {/* Left Column: Metadata & Codec */}
        <div className="col-span-12 xl:col-span-8 space-y-gutter">
          {/* Quick Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-surface-container-lowest border border-outline-variant p-4 rounded shadow-sm">
              <div className="text-label-sm text-on-surface-variant mb-1 uppercase tracking-wider">Format</div>
              <div className="font-title-lg text-title-lg text-on-surface">MPEG-4</div>
            </div>
            <div className="bg-surface-container-lowest border border-outline-variant p-4 rounded shadow-sm">
              <div className="text-label-sm text-on-surface-variant mb-1 uppercase tracking-wider">Resolution</div>
              <div className="font-title-lg text-title-lg text-on-surface">1920x1080</div>
            </div>
            <div className="bg-surface-container-lowest border border-outline-variant p-4 rounded shadow-sm">
              <div className="text-label-sm text-on-surface-variant mb-1 uppercase tracking-wider">Duration</div>
              <div className="font-title-lg text-title-lg text-on-surface">00:02:14.08</div>
            </div>
            <div className="bg-surface-container-lowest border border-outline-variant p-4 rounded shadow-sm">
              <div className="text-label-sm text-on-surface-variant mb-1 uppercase tracking-wider">Hash (SHA-256)</div>
              <div className="font-mono text-on-surface truncate" title="a8f9c7...3b21">a8f9c7...3b21</div>
            </div>
          </div>
          {/* EXIF / Structure Table */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded shadow-sm overflow-hidden">
            <div className="bg-surface-container-low px-4 py-3 border-b border-outline-variant flex justify-between items-center">
              <h3 className="font-title-lg text-title-lg text-on-surface">EXIF &amp; Codec Structure</h3>
              <button className="text-primary text-label-md hover:underline">View Raw Dump</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead className="bg-surface text-label-sm text-on-surface-variant">
                  <tr>
                    <th className="px-4 py-2 border-b border-outline-variant">Tag</th>
                    <th className="px-4 py-2 border-b border-outline-variant">Property</th>
                    <th className="px-4 py-2 border-b border-outline-variant">Value</th>
                    <th className="px-4 py-2 border-b border-outline-variant w-16">Status</th>
                  </tr>
                </thead>
                <tbody className="font-body-sm text-body-sm text-on-surface divide-y divide-outline-variant">
                  <tr className="hover:bg-primary/5 transition-colors">
                    <td className="px-4 py-2 font-mono">0x010E</td>
                    <td className="px-4 py-2">ImageDescription</td>
                    <td className="px-4 py-2">Sony A7S III Capture</td>
                    <td className="px-4 py-2 text-center"><span className="material-symbols-outlined text-[16px] text-primary">check_circle</span></td>
                  </tr>
                  <tr className="hover:bg-primary/5 transition-colors">
                    <td className="px-4 py-2 font-mono">0x0132</td>
                    <td className="px-4 py-2">ModifyDate</td>
                    <td className="px-4 py-2">2024:08:15 14:32:01</td>
                    <td className="px-4 py-2 text-center"><span className="material-symbols-outlined text-[16px] text-error">warning</span></td>
                  </tr>
                  <tr className="hover:bg-primary/5 transition-colors">
                    <td className="px-4 py-2 font-mono">0x8769</td>
                    <td className="px-4 py-2">ExifOffset</td>
                    <td className="px-4 py-2">2148</td>
                    <td className="px-4 py-2 text-center"><span className="material-symbols-outlined text-[16px] text-primary">check_circle</span></td>
                  </tr>
                  <tr className="hover:bg-primary/5 transition-colors">
                    <td className="px-4 py-2 font-mono">Codec</td>
                    <td className="px-4 py-2">Video Codec ID</td>
                    <td className="px-4 py-2">avc1 (H.264)</td>
                    <td className="px-4 py-2 text-center"><span className="material-symbols-outlined text-[16px] text-primary">check_circle</span></td>
                  </tr>
                  <tr className="hover:bg-primary/5 transition-colors bg-error-container/20">
                    <td className="px-4 py-2 font-mono">GPS</td>
                    <td className="px-4 py-2">GPSInfo</td>
                    <td className="px-4 py-2 italic text-on-surface-variant">Null / Stripped</td>
                    <td className="px-4 py-2 text-center"><span className="material-symbols-outlined text-[16px] text-error">error</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        {/* Right Column: Provenance & Anomalies */}
        <div className="col-span-12 xl:col-span-4 space-y-gutter">
          {/* Anomalies Panel */}
          <div className="bg-surface-container-lowest border border-error-container rounded shadow-sm overflow-hidden">
            <div className="bg-error-container/30 px-4 py-3 border-b border-error-container flex items-center gap-2">
              <span className="material-symbols-outlined text-error">gavel</span>
              <h3 className="font-title-lg text-title-lg text-on-surface">Forensic Anomalies</h3>
            </div>
            <div className="p-4 space-y-3">
              <div className="flex gap-3 items-start">
                <span className="material-symbols-outlined text-error mt-0.5 text-[20px]">warning</span>
                <div>
                  <h4 className="text-label-md text-on-surface">Timestamp Mismatch</h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">File creation date (2024:08:15) precedes internal metadata edit timestamp (2024:08:14).</p>
                </div>
              </div>
              <div className="flex gap-3 items-start">
                <span className="material-symbols-outlined text-tertiary-container mt-0.5 text-[20px]">content_cut</span>
                <div>
                  <h4 className="text-label-md text-on-surface">Metadata Stripping Detected</h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">GPS and MakerNote blocks show signs of deliberate nullification post-capture.</p>
                </div>
              </div>
            </div>
          </div>
          {/* C2PA Provenance Chain */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded shadow-sm overflow-hidden flex-1">
            <div className="bg-surface-container-low px-4 py-3 border-b border-outline-variant">
              <h3 className="font-title-lg text-title-lg text-on-surface">C2PA Provenance Chain</h3>
            </div>
            <div className="p-4 relative">
              {/* Timeline Line */}
              <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-outline-variant" />
              <ul className="space-y-6 relative z-10">
                <li className="flex gap-4">
                  <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center shrink-0 mt-1 border-2 border-surface-container-lowest">
                    <span className="material-symbols-outlined text-[12px] text-on-primary">verified</span>
                  </div>
                  <div>
                    <h4 className="text-label-md text-on-surface">Verified Source</h4>
                    <p className="font-mono text-on-surface-variant text-[11px] mt-1">Sony A7S III • XAVC S-I</p>
                    <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">Initial capture. Cryptographic signature valid.</p>
                  </div>
                </li>
                <li className="flex gap-4">
                  <div className="w-5 h-5 rounded-full bg-surface-container-highest border-2 border-outline-variant flex items-center justify-center shrink-0 mt-1">
                    <span className="material-symbols-outlined text-[12px] text-on-surface-variant">edit</span>
                  </div>
                  <div>
                    <h4 className="text-label-md text-on-surface">Software Edit</h4>
                    <p className="font-mono text-on-surface-variant text-[11px] mt-1">Adobe Premiere Pro 2024</p>
                    <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">Color grading and trim applied. Signature unbroken.</p>
                  </div>
                </li>
                <li className="flex gap-4">
                  <div className="w-5 h-5 rounded-full bg-error flex items-center justify-center shrink-0 mt-1 border-2 border-surface-container-lowest">
                    <span className="material-symbols-outlined text-[12px] text-on-error">link_off</span>
                  </div>
                  <div>
                    <h4 className="text-label-md text-error">Orphaned Edit</h4>
                    <p className="font-mono text-on-surface-variant text-[11px] mt-1">Unknown Application</p>
                    <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">Chain broken. Metadata stripped. Hash mismatch detected.</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

