import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const searchablePages = [
  { label: 'Dashboard', path: '/' },
  { label: 'Cases', path: '/cases' },
  { label: 'Evidence', path: '/evidence' },
  { label: 'Image Forensics', path: '/image-forensics' },
  { label: 'Video Forensics', path: '/video-forensics' },
  { label: 'Audio Forensics', path: '/audio-forensics' },
  { label: 'Metadata & Provenance', path: '/metadata-provenance' },
  { label: 'Cross-Modal Analysis', path: '/cross-modal-analysis' },
  { label: 'Investigation Timeline', path: '/timeline' },
  { label: 'Reports', path: '/reports' },
  { label: 'Audit Logs', path: '/audit-logs' },
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

  const results = searchablePages.filter((page) => page.label.toLowerCase().includes(query.toLowerCase()));

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
          <button aria-label="Search" aria-expanded={searchOpen} onClick={openSearch} className="p-1.5 hover:bg-surface-container-highest rounded-full transition-colors">
            <span className="material-symbols-outlined text-[20px]">search</span>
          </button>
          <button aria-label="Notifications" aria-expanded={notificationsOpen} onClick={openNotifications} className="p-1.5 hover:bg-surface-container-highest rounded-full transition-colors relative">
            <span className="material-symbols-outlined text-[20px]">notifications</span>
            <span className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full"></span>
          </button>
          <div className="h-6 w-px bg-outline-variant mx-1"></div>
          <button aria-label="Open investigator profile" aria-expanded={profileOpen} onClick={openProfile} className="flex items-center gap-2 p-1 hover:bg-surface-container-highest rounded-full transition-colors pl-2 pr-1">
            <span className="text-label-sm hidden sm:block">Investigator</span>
            <span className="material-symbols-outlined text-[24px]">account_circle</span>
          </button>
        </div>
      </div>
      {searchOpen && (
        <div data-topbar-menu className="absolute right-44 top-12 w-72 bg-surface border border-outline-variant rounded-lg shadow-lg p-3 z-30">
          <label className="sr-only" htmlFor="global-search">Search ADIS</label>
          <div className="flex items-center gap-2 border border-outline-variant rounded px-2 py-1.5">
            <span className="material-symbols-outlined text-[18px] text-on-surface-variant">search</span>
            <input ref={searchRef} id="global-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search pages" className="w-full bg-transparent outline-none text-body-md text-on-surface" />
          </div>
          <div className="mt-2 max-h-64 overflow-y-auto">
            {results.length ? results.map((page) => (
              <button key={page.path} onClick={() => { navigate(page.path); setSearchOpen(false); setQuery(''); }} className={`w-full text-left px-2 py-2 rounded hover:bg-surface-container-highest text-body-md ${pathname === page.path ? 'text-primary font-semibold' : 'text-on-surface'}`}>
                {page.label}
              </button>
            )) : <p className="px-2 py-2 text-body-sm text-on-surface-variant">No pages found.</p>}
          </div>
        </div>
      )}
      {notificationsOpen && (
        <div data-topbar-menu className="absolute right-28 top-12 w-80 bg-surface border border-outline-variant rounded-lg shadow-lg p-4 z-30">
          <div className="flex items-center justify-between mb-3"><h3 className="text-title-md font-semibold text-on-surface">Notifications</h3><span className="text-label-sm text-error">3 new</span></div>
          <div className="space-y-3 text-body-sm">
            <p className="border-l-2 border-error pl-3 text-on-surface"><strong>High-risk detection</strong><br /><span className="text-on-surface-variant">Evidence IMG_092 needs review.</span></p>
            <p className="border-l-2 border-primary pl-3 text-on-surface"><strong>Analysis complete</strong><br /><span className="text-on-surface-variant">Case #4492 is ready.</span></p>
            <p className="border-l-2 border-outline pl-3 text-on-surface"><strong>Evidence uploaded</strong><br /><span className="text-on-surface-variant">Batch #4492-B was added.</span></p>
          </div>
        </div>
      )}
      {profileOpen && (
        <div data-topbar-menu className="absolute right-4 top-12 w-52 bg-surface border border-outline-variant rounded-lg shadow-lg p-2 z-30">
          <div className="px-3 py-2 border-b border-outline-variant mb-1"><p className="text-body-md font-semibold text-on-surface">Investigator</p><p className="text-label-sm text-on-surface-variant">Forensic Analyst</p></div>
          <button onClick={() => setProfileOpen(false)} className="w-full text-left px-3 py-2 rounded hover:bg-surface-container-highest text-body-md text-on-surface">Account settings</button>
          <button onClick={() => navigate('/login')} className="w-full text-left px-3 py-2 rounded hover:bg-surface-container-highest text-body-md text-error">Sign out</button>
        </div>
      )}
    </header>
  );
}

