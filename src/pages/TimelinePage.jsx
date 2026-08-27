export default function TimelinePage() {
  return (
    <main className="flex-1 overflow-y-auto p-padding-spacious bg-background">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 flex justify-between items-end">
          <div>
            <h2 className="text-display-lg font-display-lg text-on-surface mb-2">Investigation Timeline</h2>
            <p className="text-body-md font-body-md text-on-surface-variant">Chronological log for Case #4492. All timestamps in UTC.</p>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 bg-surface-container-lowest border border-outline-variant text-on-surface px-3 py-1.5 rounded text-label-md hover:bg-surface-container transition-colors">
              <span className="material-symbols-outlined text-[16px]" data-icon="filter_list">filter_list</span>
              Filter
            </button>
            <button className="flex items-center gap-2 bg-surface-container-lowest border border-outline-variant text-on-surface px-3 py-1.5 rounded text-label-md hover:bg-surface-container transition-colors">
              <span className="material-symbols-outlined text-[16px]" data-icon="download">download</span>
              Export
            </button>
          </div>
        </div>
        {/* Timeline Container */}
        <div className="relative bg-surface-container-lowest border border-outline-variant rounded-xl p-padding-spacious shadow-[0px_4px_12px_rgba(23,32,51,0.08)]">
          <div className="space-y-6">
            {/* Event 1: Evidence Uploaded */}
            <div className="relative flex gap-4 timeline-item timeline-line">
              <div className="flex flex-col items-center z-10 w-12 shrink-0">
                <div className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center border-2 border-surface-container-lowest shadow-sm">
                  <span className="material-symbols-outlined text-on-surface-variant text-[20px]" data-icon="cloud_upload">cloud_upload</span>
                </div>
              </div>
              <div className="flex-1 bg-surface-container-lowest border border-outline-variant rounded-lg p-4 hover:border-primary transition-colors group">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-primary" />
                    <h3 className="text-headline-sm font-headline-sm text-on-surface">Evidence Uploaded</h3>
                  </div>
                  <span className="font-mono text-on-surface-variant">2023-10-24 09:15:22</span>
                </div>
                <p className="text-body-md font-body-md text-on-surface-variant mb-3">Source video file 'IMG_8921.mp4' successfully ingested into evidence locker.</p>
                <div className="flex items-center gap-4 text-label-sm text-on-surface-variant bg-surface-container-low p-2 rounded">
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]" data-icon="badge">badge</span>
                    INV-842
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]" data-icon="check_circle">check_circle</span>
                    <span className="text-primary font-bold">Success</span>
                  </div>
                </div>
              </div>
            </div>
            {/* Event 2: SHA-256 Generated */}
            <div className="relative flex gap-4 timeline-item timeline-line">
              <div className="flex flex-col items-center z-10 w-12 shrink-0">
                <div className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center border-2 border-surface-container-lowest shadow-sm">
                  <span className="material-symbols-outlined text-on-surface-variant text-[20px]" data-icon="fingerprint">fingerprint</span>
                </div>
              </div>
              <div className="flex-1 bg-surface-container-lowest border border-outline-variant rounded-lg p-4 hover:border-primary transition-colors group">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-primary" />
                    <h3 className="text-headline-sm font-headline-sm text-on-surface">Hash Generated</h3>
                  </div>
                  <span className="font-mono text-on-surface-variant">2023-10-24 09:15:45</span>
                </div>
                <p className="text-body-md font-body-md text-on-surface-variant mb-3">Cryptographic hash calculated for chain of custody verification.</p>
                <div className="bg-surface-container-low p-2 rounded flex items-center justify-between mb-3 border border-outline-variant">
                  <span className="font-mono text-on-surface truncate pr-4">8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4</span>
                  <button className="text-primary hover:bg-surface-variant p-1 rounded transition-colors" title="Copy Hash">
                    <span className="material-symbols-outlined text-[16px]" data-icon="content_copy">content_copy</span>
                  </button>
                </div>
                <div className="flex items-center gap-4 text-label-sm text-on-surface-variant">
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]" data-icon="memory">memory</span>
                    System (Automated)
                  </div>
                </div>
              </div>
            </div>
            {/* Event 3: Metadata Anomaly */}
            <div className="relative flex gap-4 timeline-item timeline-line">
              <div className="flex flex-col items-center z-10 w-12 shrink-0">
                <div className="w-10 h-10 rounded-full bg-error-container flex items-center justify-center border-2 border-surface-container-lowest shadow-sm">
                  <span className="material-symbols-outlined text-on-error-container text-[20px]" data-icon="warning">warning</span>
                </div>
              </div>
              <div className="flex-1 bg-surface-container-lowest border border-outline-variant rounded-lg p-4 hover:border-error transition-colors group">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-error" />
                    <h3 className="text-headline-sm font-headline-sm text-on-surface">Metadata Anomaly Detected</h3>
                  </div>
                  <span className="font-mono text-on-surface-variant">2023-10-24 09:16:12</span>
                </div>
                <p className="text-body-md font-body-md text-on-surface-variant mb-3">Creation date mismatch detected between EXIF data and file system properties.</p>
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="bg-surface-container-low p-2 rounded border border-outline-variant">
                    <span className="text-label-sm text-on-surface-variant block">EXIF Date/Time Original</span>
                    <span className="font-mono text-error">2023-09-12 14:30:00</span>
                  </div>
                  <div className="bg-surface-container-low p-2 rounded border border-outline-variant">
                    <span className="text-label-sm text-on-surface-variant block">File System Creation Date</span>
                    <span className="font-mono text-on-surface">2023-10-24 08:05:11</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-label-sm text-on-surface-variant">
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]" data-icon="memory">memory</span>
                    System (ExifTool parser)
                  </div>
                </div>
              </div>
            </div>
            {/* Event 4: AI Analysis Started */}
            <div className="relative flex gap-4 timeline-item timeline-line">
              <div className="flex flex-col items-center z-10 w-12 shrink-0">
                <div className="w-10 h-10 rounded-full bg-secondary-fixed flex items-center justify-center border-2 border-surface-container-lowest shadow-sm">
                  <span className="material-symbols-outlined text-on-secondary-fixed text-[20px]" data-icon="smart_toy">smart_toy</span>
                </div>
              </div>
              <div className="flex-1 bg-surface-container-lowest border border-outline-variant rounded-lg p-4 hover:border-secondary transition-colors group">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-secondary" />
                    <h3 className="text-headline-sm font-headline-sm text-on-surface">AI Deepfake Analysis Initiated</h3>
                  </div>
                  <span className="font-mono text-on-surface-variant">2023-10-24 09:20:05</span>
                </div>
                <p className="text-body-md font-body-md text-on-surface-variant mb-3">Model 'VidForensics-v4.2' queued for spatial-temporal artifact detection.</p>
                <div className="flex items-center gap-4 text-label-sm text-on-surface-variant bg-surface-container-low p-2 rounded">
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]" data-icon="badge">badge</span>
                    INV-842
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-1 bg-surface-variant rounded-full overflow-hidden">
                      <div className="w-full h-full bg-secondary rounded-full" />
                    </div>
                    <span>Completed</span>
                  </div>
                </div>
              </div>
            </div>
            {/* Event 5: Suspicious Segment Flagged */}
            <div className="relative flex gap-4 timeline-item timeline-line">
              <div className="flex flex-col items-center z-10 w-12 shrink-0">
                <div className="w-10 h-10 rounded-full bg-tertiary-fixed flex items-center justify-center border-2 border-surface-container-lowest shadow-sm">
                  <span className="material-symbols-outlined text-on-tertiary-fixed text-[20px]" data-icon="movie_filter">movie_filter</span>
                </div>
              </div>
              <div className="flex-1 bg-surface-container-lowest border border-outline-variant rounded-lg p-4 hover:border-tertiary transition-colors group">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-tertiary" />
                    <h3 className="text-headline-sm font-headline-sm text-on-surface">Suspicious Segment Flagged</h3>
                  </div>
                  <span className="font-mono text-on-surface-variant">2023-10-24 09:25:33</span>
                </div>
                <p className="text-body-md font-body-md text-on-surface-variant mb-3">AI analysis detected high probability of facial manipulation (Deepfake).</p>
                <div className="flex gap-3 mb-3">
                  <div className="w-32 h-20 bg-surface-container rounded overflow-hidden relative border border-outline-variant">
                    <img className="object-cover w-full h-full opacity-80 mix-blend-luminosity" data-alt="A highly detailed, clinically objective forensic analysis frame showing a human face with a heat map overlay indicating digital manipulation in a stark, technical UI context. Modern, high-resolution, cold corporate aesthetic." src="https://lh3.googleusercontent.com/aida-public/AB6AXuBX4yX45pOwPadwp7NKVuv0TbnQjVlFdYVYPK0gqiWEMVOklAVEoF-wECqXlDMDpnxQKRbl8K1iQSIK2z388bE7pWl8d-uZRO1E-m_cu7CB4_Z9vduU1EvEGIh-vIiYSAeeww1oHoElNYqyx1aR9R1grShf8HiI_vX8hf8GJ9dax1OOh-JVMwy-WgIKc_SMbzoyfNmIUHFZf1hhn-akKXe2S1z2kTUAMDjj4NYfTCi4dzCW8NGABRk" />
                    <div className="absolute inset-0 bg-gradient-to-t from-surface/80 to-transparent flex items-end p-1">
                      <span className="text-[10px] font-mono text-on-surface">00:01:42:15</span>
                    </div>
                  </div>
                  <div className="flex-1 flex flex-col justify-center gap-2">
                    <div className="flex justify-between items-center text-label-sm">
                      <span className="text-on-surface-variant">Manipulation Confidence</span>
                      <span className="text-tertiary font-bold">94.2%</span>
                    </div>
                    <div className="w-full h-1.5 bg-surface-variant rounded-full overflow-hidden">
                      <div className="w-[94%] h-full bg-tertiary rounded-full" />
                    </div>
                    <span className="text-[11px] text-on-surface-variant">Artifact type: Temporal flickering, Blending boundary</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-label-sm text-on-surface-variant">
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]" data-icon="memory">memory</span>
                    Model: VidForensics-v4.2
                  </div>
                </div>
              </div>
            </div>
            {/* Event 6: Investigator Review */}
            <div className="relative flex gap-4 timeline-item timeline-line">
              <div className="flex flex-col items-center z-10 w-12 shrink-0">
                <div className="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center border-2 border-surface-container-lowest shadow-sm">
                  <span className="material-symbols-outlined text-on-primary-container text-[20px]" data-icon="rate_review">rate_review</span>
                </div>
              </div>
              <div className="flex-1 bg-surface-container-lowest border border-outline-variant rounded-lg p-4 hover:border-primary transition-colors group">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-primary" />
                    <h3 className="text-headline-sm font-headline-sm text-on-surface">Investigator Review Logged</h3>
                  </div>
                  <span className="font-mono text-on-surface-variant">2023-10-24 10:05:11</span>
                </div>
                <div className="bg-surface-container p-3 rounded mb-3 border-l-2 border-primary">
                  <p className="text-body-md font-body-md text-on-surface italic">"Reviewed AI flags at 01:42. Confirmed unnatural blending around jawline and inconsistent lighting on the subject's face compared to the background environment. Flagging as verified manipulation for the final report."</p>
                </div>
                <div className="flex items-center gap-4 text-label-sm text-on-surface-variant bg-surface-container-low p-2 rounded w-fit">
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]" data-icon="badge">badge</span>
                    INV-842
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]" data-icon="verified">verified</span>
                    <span className="text-primary font-bold">Verified Findings</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        {/* Footer spacing */}
        <div className="h-12" />
      </div>
    </main>
  );
}

