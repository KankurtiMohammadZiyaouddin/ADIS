import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const INITIAL_EVIDENCE = [
  {
    id: 'EV-2023-089A',
    filename: 'suspect_vehicle_cam2.jpg',
    type: 'Image',
    format: 'JPEG Image',
    sha256: '8f4e27f6a9c8d3b2e1f4a7c8d9e0b1f2',
    timestamp: '2023-10-24 14:32:11Z',
    status: 'ANALYZED',
    verdict: 'Likely Manipulated',
    confidence: 88.5,
    size: '4.2 MB',
    resolution: '3840 x 2160',
    device: 'Sony A7S III (EXIF)',
    preview: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=600&auto=format&fit=crop&q=80',
    isVideo: false,
    route: '/image-forensics'
  },
  {
    id: 'VID-4492-01',
    filename: 'EVID_4492_INTERVIEW_CAM2.mp4',
    type: 'Video',
    format: 'H.264 Video (1080p60)',
    sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    timestamp: '2026-08-27 14:15:22Z',
    status: 'ANALYZED',
    verdict: 'Deepfake Manipulated (98.4%)',
    confidence: 98.4,
    size: '48.2 MB',
    resolution: '1920 x 1080',
    device: 'Forensic Video Capture',
    preview: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80',
    isVideo: true,
    route: '/video-forensics?videoId=VID-4492-01'
  },
  {
    id: 'VID-4492-02',
    filename: 'EVID_4492_SECURITY_HALLWAY.mp4',
    type: 'Video',
    format: 'H.264 Video (720p30)',
    sha256: '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
    timestamp: '2026-08-27 15:40:10Z',
    status: 'ANALYZED',
    verdict: 'Likely Authentic (96.2%)',
    confidence: 96.2,
    size: '24.7 MB',
    resolution: '1280 x 720',
    device: 'CCTV Camera Node #04',
    preview: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&auto=format&fit=crop&q=80',
    isVideo: true,
    route: '/video-forensics?videoId=VID-4492-02'
  },
  {
    id: 'VID-4493-01',
    filename: 'EVID_4493_PRESS_BRIEFING_DEEPFAKE.mp4',
    type: 'Video',
    format: 'HEVC / H.265 (1080p)',
    sha256: '9f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9044',
    timestamp: '2026-08-26 11:20:00Z',
    status: 'ANALYZED',
    verdict: 'Deepfake Manipulated (99.2%)',
    confidence: 99.2,
    size: '36.5 MB',
    resolution: '1920 x 1080',
    device: 'Digital Stream Intercept',
    preview: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=600&auto=format&fit=crop&q=80',
    isVideo: true,
    route: '/video-forensics?videoId=VID-4493-01'
  },
  {
    id: 'EV-2023-089C',
    filename: 'ransom_note_scanned.pdf',
    type: 'Document',
    format: 'PDF Document',
    sha256: '7a8b9e0f1a2b3c4d5e6f7a8b9c0d1e2f',
    timestamp: '2023-10-24 16:15:02Z',
    status: 'ANALYZED',
    verdict: 'Likely Authentic',
    confidence: 94.0,
    size: '1.8 MB',
    resolution: '300 DPI Scan',
    device: 'Flatbed Scanner',
    preview: 'https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=600&auto=format&fit=crop&q=80',
    isVideo: false,
    route: '/metadata-provenance'
  },
  {
    id: 'EV-2023-090A',
    filename: 'voicemail_intercept.wav',
    type: 'Audio',
    format: 'WAV Audio (44.1kHz)',
    sha256: 'e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0',
    timestamp: '2023-10-25 09:12:33Z',
    status: 'ANALYZED',
    verdict: 'Synthetic Voice Clone',
    confidence: 91.0,
    size: '8.4 MB',
    resolution: '16-bit PCM',
    device: 'VoIP Telephony Log',
    preview: 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop&q=80',
    isVideo: false,
    route: '/audio-forensics'
  }
];

export default function EvidencePage() {
  const navigate = useNavigate();
  const [evidenceList] = useState(INITIAL_EVIDENCE);
  const [selectedItem, setSelectedItem] = useState(INITIAL_EVIDENCE[1]); // Default select video
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');

  const filteredItems = evidenceList.filter((item) => {
    const matchesSearch =
      !searchQuery ||
      item.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.sha256.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.verdict.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesType = typeFilter === 'ALL' || item.type === typeFilter;

    return matchesSearch && matchesType;
  });

  return (
    <main className="flex-1 flex flex-col h-screen overflow-hidden bg-background">
      {/* Page Workspace */}
      <div className="flex-1 overflow-hidden flex relative">
        {/* Main Canvas */}
        <div className="flex-1 flex flex-col h-full overflow-y-auto p-5 transition-all duration-300">
          <div className="flex justify-between items-end mb-5">
            <div>
              <h2 className="text-display-lg font-display-lg text-on-surface mb-1">
                Evidence Management
              </h2>
              <p className="text-body-md font-body-md text-on-surface-variant">
                Upload, search, categorize, and launch AI deepfake forensic analysis for Case #4492.
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => navigate('/video-forensics')}
                className="px-3.5 py-2 bg-primary text-on-primary rounded-lg text-label-md hover:bg-primary/90 transition-colors flex items-center gap-2 shadow-sm font-medium"
              >
                <span className="material-symbols-outlined text-[18px]">videocam</span>
                Video Forensics Studio
              </button>
            </div>
          </div>

          {/* Quick Search & Filters Bar */}
          <div className="flex items-center justify-between gap-3 mb-4 bg-surface p-3 rounded-xl border border-outline-variant">
            <div className="relative flex-1 max-w-md">
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-on-surface-variant text-[18px]">
                search
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by ID, Filename, Hash, or Verdict..."
                className="w-full pl-9 pr-4 py-1.5 text-body-sm rounded-lg bg-surface-container-low border border-outline-variant text-on-surface focus:outline-none focus:border-primary"
              />
            </div>

            {/* Type Filters */}
            <div className="flex gap-1.5">
              {['ALL', 'Video', 'Image', 'Audio', 'Document'].map((t) => (
                <button
                  key={t}
                  onClick={() => setTypeFilter(t)}
                  className={`px-3 py-1 rounded-lg text-label-sm font-medium transition-colors ${
                    typeFilter === t
                      ? 'bg-primary text-on-primary shadow-sm'
                      : 'bg-surface-container text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  {t === 'ALL' ? 'All Types' : t}
                </button>
              ))}
            </div>
          </div>

          {/* Evidence Inventory Table */}
          <div className="bg-surface border border-outline-variant rounded-xl shadow-sm flex-1 flex flex-col overflow-hidden">
            <div className="px-4 py-3 border-b border-outline-variant flex justify-between items-center bg-surface-container-low">
              <h3 className="text-label-md font-semibold text-on-surface">
                Evidence Inventory ({filteredItems.length} Items)
              </h3>
              <span className="text-[11px] text-on-surface-variant">
                Click any row to inspect or launch deep analysis
              </span>
            </div>

            <div className="flex-1 overflow-auto">
              <table className="w-full text-left border-collapse min-w-[850px]">
                <thead className="sticky top-0 bg-surface-container z-10 border-b border-outline-variant">
                  <tr>
                    <th className="py-2.5 px-4 text-label-sm text-on-surface-variant font-semibold">
                      Evidence ID
                    </th>
                    <th className="py-2.5 px-4 text-label-sm text-on-surface-variant font-semibold">
                      Filename
                    </th>
                    <th className="py-2.5 px-4 text-label-sm text-on-surface-variant font-semibold">
                      Type
                    </th>
                    <th className="py-2.5 px-4 text-label-sm text-on-surface-variant font-semibold">
                      SHA-256 Hash
                    </th>
                    <th className="py-2.5 px-4 text-label-sm text-on-surface-variant font-semibold">
                      Status
                    </th>
                    <th className="py-2.5 px-4 text-label-sm text-on-surface-variant font-semibold">
                      Assessment & Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/40">
                  {filteredItems.map((item) => {
                    const isSelected = selectedItem?.id === item.id;
                    const isFake = item.verdict.toLowerCase().includes('manipulated') || item.verdict.toLowerCase().includes('deepfake');

                    return (
                      <tr
                        key={item.id}
                        onClick={() => {
                          setSelectedItem(item);
                          setSidebarOpen(true);
                        }}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-primary/10 font-medium'
                            : 'hover:bg-surface-container-low'
                        }`}
                      >
                        <td className="py-3 px-4 font-mono text-primary text-body-sm">
                          {item.id}
                        </td>
                        <td className="py-3 px-4 text-on-surface text-body-sm font-medium flex items-center gap-2">
                          <span
                            className={`material-symbols-outlined text-[18px] ${
                              item.isVideo ? 'text-primary' : 'text-on-surface-variant'
                            }`}
                          >
                            {item.isVideo
                              ? 'videocam'
                              : item.type === 'Image'
                              ? 'image'
                              : item.type === 'Audio'
                              ? 'audiotrack'
                              : 'description'}
                          </span>
                          {item.filename}
                        </td>
                        <td className="py-3 px-4 text-on-surface-variant text-body-sm">
                          {item.format}
                        </td>
                        <td className="py-3 px-4 font-mono text-on-surface-variant text-xs">
                          {item.sha256.substring(0, 12)}...
                        </td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-bold uppercase tracking-wider">
                            <span className="material-symbols-outlined text-[12px]">done</span>{' '}
                            {item.status}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center justify-between gap-3">
                            <span
                              className={`text-[11px] font-bold ${
                                isFake ? 'text-error' : 'text-emerald-400'
                              }`}
                            >
                              {item.verdict}
                            </span>

                            {item.isVideo && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate(`/video-forensics?videoId=${item.id}`);
                                }}
                                className="px-2.5 py-1 bg-primary/20 hover:bg-primary text-primary hover:text-on-primary rounded text-label-sm font-medium transition-colors flex items-center gap-1 shrink-0"
                              >
                                <span className="material-symbols-outlined text-[14px]">
                                  analytics
                                </span>
                                Analyze
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Detailed Artifact Sidebar */}
        {sidebarOpen && selectedItem && (
          <aside className="w-[380px] border-l border-outline-variant bg-surface h-full flex flex-col shrink-0 z-20 shadow-xl animate-fadeIn">
            {/* Sidebar Header */}
            <div className="px-4 py-3.5 border-b border-outline-variant flex justify-between items-center bg-surface-container-low">
              <div>
                <h3 className="text-label-md font-semibold text-on-surface">Artifact Details</h3>
                <span className="font-mono text-primary text-xs">{selectedItem.id}</span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-1 text-on-surface-variant hover:bg-surface-container rounded-lg transition-colors"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Preview Thumbnail */}
              <div className="rounded-xl border border-outline-variant overflow-hidden bg-black aspect-video relative flex items-center justify-center shadow-inner">
                <img
                  src={selectedItem.preview}
                  alt={selectedItem.filename}
                  className="object-cover w-full h-full opacity-85"
                />
                <span
                  className={`absolute top-2 left-2 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wide shadow ${
                    selectedItem.verdict.toLowerCase().includes('manipulated') ||
                    selectedItem.verdict.toLowerCase().includes('deepfake')
                      ? 'bg-error text-white'
                      : 'bg-emerald-600 text-white'
                  }`}
                >
                  {selectedItem.verdict}
                </span>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={() => navigate(selectedItem.route)}
                  className="flex-1 bg-primary text-on-primary py-2 px-3 rounded-lg text-label-md hover:bg-primary/90 transition-colors flex items-center justify-center gap-1.5 shadow font-medium"
                >
                  <span className="material-symbols-outlined text-[18px]">psychology</span>
                  Launch Forensic Studio
                </button>
              </div>

              {/* Technical Metadata */}
              <div className="bg-surface-container-low p-3.5 rounded-xl border border-outline-variant">
                <h4 className="text-label-sm text-on-surface-variant uppercase tracking-wider mb-2 font-semibold">
                  Technical Metadata
                </h4>
                <dl className="space-y-1.5 text-body-sm font-mono text-[12px]">
                  <div className="flex justify-between">
                    <dt className="text-on-surface-variant font-sans">Filename</dt>
                    <dd className="text-on-surface truncate ml-2 max-w-[200px]" title={selectedItem.filename}>
                      {selectedItem.filename}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-on-surface-variant font-sans">Size</dt>
                    <dd className="text-on-surface">{selectedItem.size}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-on-surface-variant font-sans">Resolution</dt>
                    <dd className="text-on-surface">{selectedItem.resolution}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-on-surface-variant font-sans">Device / Source</dt>
                    <dd className="text-on-surface">{selectedItem.device}</dd>
                  </div>
                  <div className="flex justify-between pt-1 border-t border-outline-variant/40">
                    <dt className="text-on-surface-variant font-sans">SHA-256</dt>
                    <dd className="text-primary truncate ml-2 max-w-[180px]" title={selectedItem.sha256}>
                      {selectedItem.sha256}
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Chain of Custody */}
              <div className="bg-surface-container-low p-3.5 rounded-xl border border-outline-variant">
                <h4 className="text-label-sm text-on-surface-variant uppercase tracking-wider mb-2.5 font-semibold">
                  Chain of Custody
                </h4>
                <div className="relative border-l-2 border-primary/40 ml-2 space-y-3.5 py-1">
                  <div className="relative pl-4">
                    <span className="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full bg-primary" />
                    <div className="text-label-sm font-semibold text-on-surface">
                      Deepfake Neural Inspection Completed
                    </div>
                    <div className="text-[11px] text-on-surface-variant">
                      ResNeXt-50 + LSTM Sequence Engine
                    </div>
                    <div className="text-[10px] text-on-surface-variant/70 mt-0.5">
                      {selectedItem.timestamp}
                    </div>
                  </div>
                  <div className="relative pl-4">
                    <span className="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full bg-outline" />
                    <div className="text-label-sm font-semibold text-on-surface">
                      Cryptographic Evidence Ingestion
                    </div>
                    <div className="text-[11px] text-on-surface-variant">
                      SHA-256 Checksum Computed
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </aside>
        )}
      </div>
    </main>
  );
}
