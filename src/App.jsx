import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import CasesPage from './pages/CasesPage';
import CaseInvestigationPage from './pages/CaseInvestigationPage';
import EvidencePage from './pages/EvidencePage';
import ImageForensicsPage from './pages/ImageForensicsPage';
import VideoForensicsPage from './pages/VideoForensicsPage';
import AudioForensicsPage from './pages/AudioForensicsPage';
import MetadataProvenancePage from './pages/MetadataProvenancePage';
import CrossModalAnalysisPage from './pages/CrossModalAnalysisPage';
import TimelinePage from './pages/TimelinePage';
import ReportsPage from './pages/ReportsPage';
import AuditLogsPage from './pages/AuditLogsPage';
import LoginPage from './pages/LoginPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} handle={{ title: 'Dashboard' }} />
          <Route path="/cases" element={<CasesPage />} handle={{ title: 'Cases' }} />
          <Route path="/cases/:caseId" element={<CaseInvestigationPage />} handle={{ title: 'Case Investigation' }} />
          <Route path="/evidence" element={<EvidencePage />} handle={{ title: 'Evidence' }} />
          <Route path="/image-forensics" element={<ImageForensicsPage />} handle={{ title: 'Image Forensics' }} />
          <Route path="/video-forensics" element={<VideoForensicsPage />} handle={{ title: 'Video Forensics' }} />
          <Route path="/audio-forensics" element={<AudioForensicsPage />} handle={{ title: 'Audio Forensics' }} />
          <Route path="/metadata-provenance" element={<MetadataProvenancePage />} handle={{ title: 'Metadata & Provenance' }} />
          <Route path="/cross-modal-analysis" element={<CrossModalAnalysisPage />} handle={{ title: 'Cross-Modal Analysis' }} />
          <Route path="/timeline" element={<TimelinePage />} handle={{ title: 'Investigation Timeline' }} />
          <Route path="/reports" element={<ReportsPage />} handle={{ title: 'Reports' }} />
          <Route path="/audit-logs" element={<AuditLogsPage />} handle={{ title: 'Audit Logs' }} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

