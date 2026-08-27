export default function EvidencePage() {
  return (
    <main className="ml-[260px] flex-1 flex flex-col h-screen relative w-[calc(100%-260px)]">
      {/* TopNavBar (Shared Component) */}
      <header className="bg-surface flex justify-between items-center h-14 px-gutter border-b border-outline-variant shrink-0 z-10 w-full">
        <div className="flex items-center gap-6">
          {/* Navigation Links / Breadcrumbs */}
          <nav className="flex items-center gap-4 text-label-sm">
            <a className="text-on-surface-variant font-medium hover:text-primary transition-colors" href="#">Cases</a>
            <span className="material-symbols-outlined text-outline-variant text-[16px]">chevron_right</span>
            <a className="text-primary font-bold border-b-2 border-primary pb-1 scale-95 transition-transform" href="#">Evidence</a>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-label-sm text-on-surface-variant px-3 py-1 bg-surface-container-highest rounded border border-outline-variant/50">
            Current Case: #4492
          </div>
          <div className="h-4 w-px bg-outline-variant" />
          <div className="flex items-center gap-3 text-on-surface-variant">
            <button className="hover:text-primary transition-colors"><span className="material-symbols-outlined text-[20px]">notifications</span></button>
            <button className="hover:text-primary transition-colors"><span className="material-symbols-outlined text-[20px]">search</span></button>
            <button className="hover:text-primary transition-colors flex items-center gap-2">
              <span className="material-symbols-outlined text-[24px]">account_circle</span>
              <span className="text-label-sm">Investigator</span>
            </button>
          </div>
        </div>
      </header>
      {/* Page Content */}
      <div className="flex-1 overflow-hidden flex relative">
        {/* Main Canvas */}
        <div className="flex-1 flex flex-col h-full overflow-y-auto p-container-margin transition-all duration-300" id="main-canvas">
          <div className="flex justify-between items-end mb-6">
            <div>
              <h2 className="text-headline-md font-headline-md text-on-surface mb-1">Evidence Management</h2>
              <p className="text-body-sm font-body-sm text-on-surface-variant">Upload, categorize, and analyze digital artifacts for Case #4492.</p>
            </div>
            <div className="flex gap-2">
              <button className="px-4 py-2 border border-outline-variant rounded bg-surface-container-lowest text-on-surface text-label-md hover:bg-surface-container-low transition-colors flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">filter_list</span>
                Filter
              </button>
              <button className="px-4 py-2 border border-outline-variant rounded bg-surface-container-lowest text-on-surface text-label-md hover:bg-surface-container-low transition-colors flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">download</span>
                Export Log
              </button>
            </div>
          </div>
          {/* Drag & Drop Area */}
          <div className="border-2 border-dashed border-outline-variant rounded-xl p-8 mb-8 bg-surface-container-lowest flex flex-col items-center justify-center text-center cursor-pointer" id="drop-zone">
            <span className="material-symbols-outlined text-[48px] text-outline mb-4">cloud_upload</span>
            <h3 className="text-title-lg font-title-lg text-on-surface mb-2">Drag &amp; Drop Evidence Files Here</h3>
            <p className="text-body-sm font-body-sm text-on-surface-variant max-w-md mx-auto mb-4">Supported formats: JPG, PNG, MP4, WAV, PDF. Maximum file size: 5GB per artifact. All uploads are automatically hashed (SHA-256) upon ingestion.</p>
            <button className="bg-primary text-on-primary py-2 px-6 rounded text-label-md hover:bg-surface-tint transition-colors">
              Browse Files
            </button>
          </div>
          {/* Evidence Inventory */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-[0px_4px_12px_rgba(23,32,51,0.08)] flex-1 flex flex-col overflow-hidden">
            <div className="px-4 py-3 border-b border-outline-variant flex justify-between items-center bg-[#F6F8FB]">
              <h3 className="text-title-lg font-title-lg text-on-surface">Evidence Inventory (24 Items)</h3>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline-variant text-[18px]">search</span>
                <input className="pl-9 pr-4 py-1.5 text-body-sm font-body-sm border border-outline-variant rounded bg-surface-container-lowest focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all w-64" placeholder="Search ID, Filename, Hash..." type="text" />
              </div>
            </div>
            <div className="flex-1 overflow-auto">
              <table className="w-full text-left border-collapse min-w-[900px]">
                <thead className="sticky top-0 bg-[#F6F8FB] z-10 border-b border-outline-variant shadow-sm">
                  <tr>
                    <th className="py-3 px-4 text-label-sm text-on-surface-variant font-semibold">Evidence ID</th>
                    <th className="py-3 px-4 text-label-sm text-on-surface-variant font-semibold">Filename</th>
                    <th className="py-3 px-4 text-label-sm text-on-surface-variant font-semibold">Type</th>
                    <th className="py-3 px-4 text-label-sm text-on-surface-variant font-semibold">SHA-256</th>
                    <th className="py-3 px-4 text-label-sm text-on-surface-variant font-semibold">Timestamp</th>
                    <th className="py-3 px-4 text-label-sm text-on-surface-variant font-semibold">Status</th>
                    <th className="py-3 px-4 text-label-sm text-on-surface-variant font-semibold">Assessment</th>
                  </tr>
                </thead>
                <tbody className="text-body-md font-body-md divide-y divide-outline-variant/50">
                  {/* Row 1 (Selected) */}
                  <tr className="evidence-row selected transition-colors" onclick="toggleSidebar(true)">
                    <td className="py-3 px-4 font-mono text-primary">EV-2023-089A</td>
                    <td className="py-3 px-4 text-on-surface font-medium flex items-center gap-2">
                      <span className="material-symbols-outlined text-[18px] text-outline">image</span>
                      suspect_vehicle_cam2.jpg
                    </td>
                    <td className="py-3 px-4 text-on-surface-variant">JPEG Image</td>
                    <td className="py-3 px-4 font-mono text-on-surface-variant text-xs">8f4e2...a1b9</td>
                    <td className="py-3 px-4 text-on-surface-variant text-xs">2023-10-24 14:32:11Z</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#E0F2FE] text-[#0369A1] text-[10px] font-bold uppercase tracking-wider">
                        <span className="material-symbols-outlined text-[12px]">done</span> Analyzed
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-col gap-1 w-32">
                        <span className="text-[11px] font-semibold text-[#EF4444]">Likely Manipulated</span>
                        <div className="w-full bg-outline-variant/30 rounded-full h-1 overflow-hidden">
                          <div className="confidence-bar confidence-manipulated" />
                        </div>
                      </div>
                    </td>
                  </tr>
                  {/* Row 2 */}
                  <tr className="evidence-row transition-colors" onclick="toggleSidebar(true)">
                    <td className="py-3 px-4 font-mono text-primary">EV-2023-089B</td>
                    <td className="py-3 px-4 text-on-surface font-medium flex items-center gap-2">
                      <span className="material-symbols-outlined text-[18px] text-outline">videocam</span>
                      alley_security_feed.mp4
                    </td>
                    <td className="py-3 px-4 text-on-surface-variant">H.264 Video</td>
                    <td className="py-3 px-4 font-mono text-on-surface-variant text-xs">c3d4e...f5a6</td>
                    <td className="py-3 px-4 text-on-surface-variant text-xs">2023-10-24 15:01:44Z</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#FEF3C7] text-[#B45309] text-[10px] font-bold uppercase tracking-wider animate-pulse">
                        <span className="material-symbols-outlined text-[12px] animate-spin">sync</span> Processing
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-col gap-1 w-32">
                        <span className="text-[11px] font-semibold text-[#F59E0B]">Analyzing...</span>
                        <div className="w-full bg-outline-variant/30 rounded-full h-1 overflow-hidden">
                          <div className="confidence-bar confidence-processing" />
                        </div>
                      </div>
                    </td>
                  </tr>
                  {/* Row 3 */}
                  <tr className="evidence-row transition-colors" onclick="toggleSidebar(true)">
                    <td className="py-3 px-4 font-mono text-primary">EV-2023-089C</td>
                    <td className="py-3 px-4 text-on-surface font-medium flex items-center gap-2">
                      <span className="material-symbols-outlined text-[18px] text-outline">description</span>
                      ransom_note_scanned.pdf
                    </td>
                    <td className="py-3 px-4 text-on-surface-variant">PDF Document</td>
                    <td className="py-3 px-4 font-mono text-on-surface-variant text-xs">7a8b9...c0d1</td>
                    <td className="py-3 px-4 text-on-surface-variant text-xs">2023-10-24 16:15:02Z</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#E0F2FE] text-[#0369A1] text-[10px] font-bold uppercase tracking-wider">
                        <span className="material-symbols-outlined text-[12px]">done</span> Analyzed
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-col gap-1 w-32">
                        <span className="text-[11px] font-semibold text-[#10B981]">Likely Authentic</span>
                        <div className="w-full bg-outline-variant/30 rounded-full h-1 overflow-hidden">
                          <div className="confidence-bar confidence-authentic" />
                        </div>
                      </div>
                    </td>
                  </tr>
                  {/* Row 4 */}
                  <tr className="evidence-row transition-colors" onclick="toggleSidebar(true)">
                    <td className="py-3 px-4 font-mono text-primary">EV-2023-090A</td>
                    <td className="py-3 px-4 text-on-surface font-medium flex items-center gap-2">
                      <span className="material-symbols-outlined text-[18px] text-outline">audio_file</span>
                      voicemail_intercept.wav
                    </td>
                    <td className="py-3 px-4 text-on-surface-variant">WAV Audio</td>
                    <td className="py-3 px-4 font-mono text-on-surface-variant text-xs">e5f6g...h7i8</td>
                    <td className="py-3 px-4 text-on-surface-variant text-xs">2023-10-25 09:12:33Z</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-surface-container-highest text-on-surface-variant text-[10px] font-bold uppercase tracking-wider">
                        <span className="material-symbols-outlined text-[12px]">cloud_done</span> Uploaded
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[11px] font-semibold text-on-surface-variant">Pending Analysis</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        {/* Detailed Sidebar (Hidden by default, shown for demo) */}
        <div className="w-[400px] border-l border-outline-variant bg-surface-container-lowest h-full flex flex-col shrink-0 absolute right-0 top-0 z-20 shadow-[-4px_0_24px_rgba(23,32,51,0.05)]" id="details-sidebar">
          {/* Sidebar Header */}
          <div className="px-6 py-4 border-b border-outline-variant flex justify-between items-center bg-[#F6F8FB]">
            <div>
              <h3 className="text-title-lg font-title-lg text-on-surface">Artifact Details</h3>
              <span className="font-mono text-primary text-xs">EV-2023-089A</span>
            </div>
            <button className="p-1 text-on-surface-variant hover:bg-surface-container rounded transition-colors" onclick="toggleSidebar(false)">
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Preview */}
            <div className="rounded border border-outline-variant overflow-hidden bg-surface-container-low aspect-video relative flex items-center justify-center">
              <img className="object-cover w-full h-full opacity-80 mix-blend-multiply" data-alt="A clinical, high-resolution forensic analysis view of a suspect vehicle image. The image is overlaid with a subtle grid and bounding boxes highlighting potential manipulated areas around the license plate. The overall aesthetic is serious, technical, and light-mode compatible, emphasizing data clarity." src="https://lh3.googleusercontent.com/aida-public/AB6AXuCdN6e3Yw61njZAgPJnFDd8e4ISl3JBiedkz6IoZIbsENvxgsUSQAoCFYG6cmhnat3wrNi_fIga9p9ZuuQNQ7EekonlVJnbQVQmeKZWuvv56zhKKpZEBGZHk-IJqcfO_rpKVzOX3qkuyxQxlaHmMuCuXf_8Sx5U6dpKRZdORSkHpvOdNkwUH8uwke1N3u1CGzXaZaJQBJPg3W9c6x6xi1bLJ7tGCe-jie5ain0dH6tZ3Oawka_c6lw" />
              <div className="absolute inset-0 border-4 border-error/20 pointer-events-none" />
              <span className="absolute top-2 left-2 bg-error text-on-error text-[10px] font-bold px-2 py-1 rounded uppercase tracking-wide shadow-sm">Manipulation Detected</span>
            </div>
            {/* Actions */}
            <div className="flex gap-2">
              <button className="flex-1 bg-secondary text-on-secondary py-2 px-3 rounded text-label-md hover:bg-secondary/90 transition-colors flex items-center justify-center gap-2">
                <span className="material-symbols-outlined text-[16px]">psychology</span>
                Deep Analysis
              </button>
              <button className="flex-1 border border-outline-variant bg-surface-container-lowest text-on-surface py-2 px-3 rounded text-label-md hover:bg-surface-container-low transition-colors flex items-center justify-center gap-2">
                <span className="material-symbols-outlined text-[16px]">visibility</span>
                View Full
              </button>
            </div>
            {/* Metadata List */}
            <div>
              <h4 className="text-label-sm text-on-surface-variant uppercase tracking-wider mb-3 pb-1 border-b border-outline-variant/50">Technical Metadata</h4>
              <dl className="space-y-2 text-body-sm font-body-sm">
                <div className="flex justify-between">
                  <dt className="text-on-surface-variant">Filename</dt>
                  <dd className="text-on-surface font-medium text-right break-all ml-4">suspect_vehicle_cam2.jpg</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-on-surface-variant">Size</dt>
                  <dd className="text-on-surface font-medium">4.2 MB</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-on-surface-variant">Resolution</dt>
                  <dd className="text-on-surface font-medium">3840 x 2160</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-on-surface-variant">Camera Model</dt>
                  <dd className="text-on-surface font-medium">Sony A7S III (EXIF)</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-on-surface-variant">Color Space</dt>
                  <dd className="text-on-surface font-medium">sRGB</dd>
                </div>
                <div className="flex justify-between pt-2">
                  <dt className="text-on-surface-variant">MD5 Hash</dt>
                  <dd className="font-mono text-[11px] text-on-surface">d41d8cd98f00b204e9800998ecf8427e</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-on-surface-variant">SHA-256</dt>
                  <dd className="font-mono text-[11px] text-on-surface w-40 text-right truncate" title="8f4e2...a1b9">8f4e27f6a9c8d3b2e1f4a7c8d9e0b1f2</dd>
                </div>
              </dl>
            </div>
            {/* Chain of Custody */}
            <div>
              <h4 className="text-label-sm text-on-surface-variant uppercase tracking-wider mb-3 pb-1 border-b border-outline-variant/50">Chain of Custody</h4>
              <div className="relative border-l-2 border-outline-variant/50 ml-2 space-y-4 py-2">
                <div className="relative pl-6">
                  <span className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-primary ring-4 ring-surface-container-lowest" />
                  <div className="text-label-md text-on-surface">Automated Analysis Completed</div>
                  <div className="text-body-sm font-body-sm text-on-surface-variant">System (Model v2.4.1)</div>
                  <div className="text-xs text-on-surface-variant/70 mt-1">2023-10-24 14:35:12Z</div>
                </div>
                <div className="relative pl-6">
                  <span className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-surface-variant border-2 border-outline-variant ring-4 ring-surface-container-lowest" />
                  <div className="text-label-md text-on-surface">Analysis Triggered</div>
                  <div className="text-body-sm font-body-sm text-on-surface-variant">Investigator (ID: J.Doe)</div>
                  <div className="text-xs text-on-surface-variant/70 mt-1">2023-10-24 14:32:15Z</div>
                </div>
                <div className="relative pl-6">
                  <span className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-surface-variant border-2 border-outline-variant ring-4 ring-surface-container-lowest" />
                  <div className="text-label-md text-on-surface">Evidence Uploaded</div>
                  <div className="text-body-sm font-body-sm text-on-surface-variant">Investigator (ID: J.Doe)</div>
                  <div className="text-xs text-on-surface-variant/70 mt-1">2023-10-24 14:32:11Z</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

