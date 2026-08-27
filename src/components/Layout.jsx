import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function Layout() {
  const { pathname } = useLocation();
  const titles = {
    '/': 'Dashboard',
    '/cases': 'Cases',
    '/evidence': 'Evidence',
    '/image-forensics': 'Image Forensics',
    '/video-forensics': 'Video Forensics',
    '/audio-forensics': 'Audio Forensics',
    '/metadata-provenance': 'Metadata & Provenance',
    '/cross-modal-analysis': 'Cross-Modal Analysis',
    '/timeline': 'Investigation Timeline',
    '/reports': 'Reports',
    '/audit-logs': 'Audit Logs',
  };
  const title = pathname.startsWith('/cases/') ? 'Case Investigation' : (titles[pathname] ?? 'ADIS');

  return (
    <div className="bg-background text-on-background flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col ml-0 md:ml-[260px] h-screen bg-background">
        <Topbar title={title} />
        <div className="flex-1 flex overflow-hidden">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

