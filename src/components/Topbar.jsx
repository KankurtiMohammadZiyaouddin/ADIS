import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { INITIAL_VIDEO_DATABASE } from '../services/deepfakeService';

const searchablePages = [
  { label: 'Dashboard', path: '/', category: 'Page' },
  { label: 'Cases', path: '/cases', category: 'Page' },
  { label: 'Evidence Management', path: '/evidence', category: 'Page' },
  { label: 'Deepfake Video Forensics', path: '/video-forensics', category: 'Forensic Studio' },
  { label: 'Image Forensics', path: '/image-forensics', category: 'Forensic Studio' },
  { label: 'Audio Forensics', path: '/audio-forensics', category: 'Forensic Studio' },
  { label: 'Metadata & Provenance', path: '/metadata-provenance', category: 'Page' },
  { label: 'Cross-Modal Analysis', path: '/cross-modal-analysis', category: 'Page' },
  { label: 'Investigation Timeline', path: '/timeline', category: 'Page' },
  { label: 'Reports', path: '/reports', category: 'System' },
  { label: 'Audit Logs', path: '/audit-logs', category: 'System' },
];

export default function Topbar({ title, caseTag = '#4492' }) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [searchOpen, setSearchOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [query, setQuery] = useState('');
  const searchRef = useRef(null);

  useEffect(() => {
    function closeMenus(event) {
      if (!event.target.closest('[data-topbar-menu]')) {
        setSearchOpen(false);
        setNotificationsOpen(false);
        setProfileOpen(false);
      }
    }

    document.addEventListener('click', closeMenus);
    return () => document.removeEventListener('click', closeMenus);
  }, []);

  useEffect(() => {
    if (searchOpen) searchRef.current?.focus();
  }, [searchOpen]);

  // Search across pages and video evidence items
  const cleanQ = query.trim().toLowerCase();
  const pageResults = searchablePages.filter((page) =>
    page.label.toLowerCase().includes(cleanQ)
  );

  const videoResults = cleanQ
    ? INITIAL_VIDEO_DATABASE.filter(
        (v) =>
          v.title.toLowerCase().includes(cleanQ) ||
          v.caseId.toLowerCase().includes(cleanQ) ||
          v.verdict.toLowerCase().includes(cleanQ) ||
          v.sha256.toLowerCase().includes(cleanQ)
      ).map((v) => ({
        label: `${v.title} (${v.verdict} - ${v.confidence}%)`,
        path: `/video-forensics?videoId=${v.id}`,
        category: `Video Evidence (${v.caseId})`,
        isVideo: true
      }))
    : [];

  const combinedResults = [...pageResults, ...videoResults];

  function openSearch(event) {
    event.stopPropagation();
    setNotificationsOpen(false);
    setProfileOpen(false);
    setSearchOpen((open) => !open);
  }

  function openNotifications(event) {
    event.stopPropagation();
    setSearchOpen(false);
    setProfileOpen(false);
    setNotificationsOpen((open) => !open);
  }

  function openProfile(event) {
    event.stopPropagation();
    setSearchOpen(false);
    setNotificationsOpen(false);
    setProfileOpen((open) => !open);
  }

  return (
    <header className="flex justify-between items-center h-14 px-gutter w-full bg-surface border-b border-outline-variant shrink-0 z-10">
      <div className="flex items-center gap-6">
        <h2 className="text-title-lg font-title-lg text-on-surface">{title}</h2>
      </div>
      <div className="flex items-center gap-4">
        <div className="hidden lg:flex items-center bg-surface-container rounded-full px-3 py-1.5 border border-outline-variant">
          <span className="text-label-sm text-on-surface-variant">Current Case: {caseTag}</span>
        </div>
        <div className="flex items-center gap-2 text-on-surface-variant">
          <button
            aria-label="Search"
            aria-expanded={searchOpen}
            onClick={openSearch}
            className="p-1.5 hover:bg-surface-container-highest rounded-full transition-colors relative"
            title="Global Forensic Search"
          >
            <span className="material-symbols-outlined text-[20px]">search</span>
          </button>
          <button
            aria-label="Notifications"
            aria-expanded={notificationsOpen}
            onClick={openNotifications}
            className="p-1.5 hover:bg-surface-container-highest rounded-full transition-colors relative"
          >
            <span className="material-symbols-outlined text-[20px]">notifications</span>
            <span className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full" />
          </button>
          <div className="h-6 w-px bg-outline-variant mx-1" />
          <button
            aria-label="Open investigator profile"
            aria-expanded={profileOpen}
            onClick={openProfile}
            className="flex items-center gap-2 p-1 hover:bg-surface-container-highest rounded-full transition-colors pl-2 pr-1"
          >
            <span className="text-label-sm hidden sm:block">Investigator</span>
            <span className="material-symbols-outlined text-[24px]">account_circle</span>
          </button>
        </div>
      </div>

      {searchOpen && (
        <div
          data-topbar-menu
          className="absolute right-44 top-12 w-80 bg-surface border border-outline-variant rounded-xl shadow-2xl p-3 z-50 animate-scaleUp"
        >
          <label className="sr-only" htmlFor="global-search">
            Search ADIS Forensic Suite
          </label>
          <div className="flex items-center gap-2 border border-outline-variant rounded-lg px-2.5 py-1.5 bg-surface-container-low">
            <span className="material-symbols-outlined text-[18px] text-on-surface-variant">
              search
            </span>
            <input
              ref={searchRef}
              id="global-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search pages, deepfake videos, hash..."
              className="w-full bg-transparent outline-none text-body-sm text-on-surface placeholder:text-on-surface-variant"
            />
          </div>
          <div className="mt-2 max-h-72 overflow-y-auto space-y-1">
            {combinedResults.length ? (
              combinedResults.map((item) => (
                <button
                  key={item.path}
                  onClick={() => {
                    navigate(item.path);
                    setSearchOpen(false);
                    setQuery('');
                  }}
                  className={`w-full text-left px-2.5 py-2 rounded-lg hover:bg-surface-container-highest flex flex-col ${
                    pathname === item.path ? 'bg-primary/10' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-body-sm font-medium ${
                        pathname === item.path ? 'text-primary' : 'text-on-surface'
                      }`}
                    >
                      {item.label}
                    </span>
                    <span className="text-[10px] text-on-surface-variant bg-surface-container px-1.5 py-0.5 rounded">
                      {item.category}
                    </span>
                  </div>
                </button>
              ))
            ) : (
              <p className="px-2 py-3 text-body-sm text-on-surface-variant text-center">
                No matching results found.
              </p>
            )}
          </div>
        </div>
      )}

      {notificationsOpen && (
        <div
          data-topbar-menu
          className="absolute right-28 top-12 w-80 bg-surface border border-outline-variant rounded-xl shadow-2xl p-4 z-50 animate-scaleUp"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-title-md font-semibold text-on-surface">Notifications</h3>
            <span className="text-label-sm text-error font-bold">3 new</span>
          </div>
          <div className="space-y-2.5 text-body-sm">
            <p className="border-l-2 border-error pl-3 text-on-surface bg-error/5 p-1.5 rounded-r">
              <strong>Deepfake Detected (98.4%)</strong>
              <br />
              <span className="text-on-surface-variant text-[12px]">
                EVID_4492_INTERVIEW_CAM2 has jawline blend artifacts.
              </span>
            </p>
            <p className="border-l-2 border-primary pl-3 text-on-surface bg-primary/5 p-1.5 rounded-r">
              <strong>Analysis Completed</strong>
              <br />
              <span className="text-on-surface-variant text-[12px]">
                PyTorch ResNeXt50+LSTM processed 60 frames.
              </span>
            </p>
            <p className="border-l-2 border-outline pl-3 text-on-surface bg-surface-container-low p-1.5 rounded-r">
              <strong>Evidence Ingested</strong>
              <br />
              <span className="text-on-surface-variant text-[12px]">
                SHA-256 Checksum verified for Case #4492.
              </span>
            </p>
          </div>
        </div>
      )}

      {profileOpen && (
        <div
          data-topbar-menu
          className="absolute right-4 top-12 w-56 bg-surface border border-outline-variant rounded-xl shadow-2xl p-2 z-50 animate-scaleUp"
        >
          <div className="px-3 py-2 border-b border-outline-variant mb-1">
            <p className="text-body-md font-semibold text-on-surface">Forensic Analyst</p>
            <p className="text-label-sm text-on-surface-variant">ADIS Deepfake Specialist</p>
          </div>
          <button
            onClick={() => setProfileOpen(false)}
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-surface-container-highest text-body-md text-on-surface"
          >
            Account Settings
          </button>
          <button
            onClick={() => navigate('/login')}
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-surface-container-highest text-body-md text-error font-medium"
          >
            Sign out
          </button>
        </div>
      )}
    </header>
  );
}
