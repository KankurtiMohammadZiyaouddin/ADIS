import { useNavigate } from 'react-router-dom';
import RiskChart from '../components/RiskChart';

export default function DashboardPage() {
  const navigate = useNavigate();
  return (
    <main className="flex-1 overflow-y-auto p-gutter space-y-gutter">
      <div className="flex justify-between items-end mb-6">
        <div>
          <h2 className="text-display-lg font-display-lg text-on-surface mb-1">Overview</h2>
          <p className="text-body-md font-body-md text-on-surface-variant">Real-time systemic forensic health and active case monitoring.</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 bg-surface border border-outline-variant px-3 py-1.5 rounded text-label-md text-on-surface hover:bg-surface-container transition-colors">
            <span className="material-symbols-outlined text-[18px]">calendar_today</span>
            Last 7 Days
          </button>
        </div>
      </div>
      {/* Bento Grid - KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter">
        {/* KPI 1 */}
        <div className="glass-card rounded-xl p-4 flex flex-col justify-between h-[120px]">
          <div className="flex justify-between items-start">
            <span className="text-label-md text-on-surface-variant">Total Cases</span>
            <span className="material-symbols-outlined text-outline text-[20px]">folder</span>
          </div>
          <div>
            <div className="text-headline-md font-headline-md text-on-surface">1,248</div>
            <div className="flex items-center gap-1 mt-1 text-label-sm text-primary">
              <span className="material-symbols-outlined text-[14px]">arrow_upward</span>
              12% from last week
            </div>
          </div>
        </div>
        {/* KPI 2 */}
        <div className="glass-card rounded-xl p-4 flex flex-col justify-between h-[120px]">
          <div className="flex justify-between items-start">
            <span className="text-label-md text-on-surface-variant">Active Evidence</span>
            <span className="material-symbols-outlined text-outline text-[20px]">inventory</span>
          </div>
          <div>
            <div className="text-headline-md font-headline-md text-on-surface">8,402</div>
            <div className="flex items-center gap-1 mt-1 text-label-sm text-primary">
              <span className="material-symbols-outlined text-[14px]">arrow_upward</span>
              4% from last week
            </div>
          </div>
        </div>
        {/* KPI 3 */}
        <div className="glass-card rounded-xl p-4 flex flex-col justify-between h-[120px]">
          <div className="flex justify-between items-start">
            <span className="text-label-md text-on-surface-variant">In-Progress Analytics</span>
            <span className="material-symbols-outlined text-outline text-[20px]">sync</span>
          </div>
          <div>
            <div className="text-headline-md font-headline-md text-on-surface">34</div>
            <div className="w-full bg-surface-container-highest h-1 mt-2 rounded-full overflow-hidden">
              <div className="bg-primary h-full w-[65%]" />
            </div>
          </div>
        </div>
        {/* KPI 4 */}
        <div className="glass-card rounded-xl p-4 flex flex-col justify-between h-[120px] border-error-container bg-error-container/10">
          <div className="flex justify-between items-start">
            <span className="text-label-md text-error">Suspicious Detections</span>
            <span className="material-symbols-outlined text-error text-[20px]">warning</span>
          </div>
          <div>
            <div className="text-headline-md font-headline-md text-error">12</div>
            <div className="flex items-center gap-1 mt-1 text-label-sm text-error">
              Requires immediate review
            </div>
          </div>
        </div>
      </div>
      {/* Complex Data Layer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter mt-gutter">
        {/* Main Table Area */}
        <div className="lg:col-span-2 glass-card rounded-xl flex flex-col overflow-hidden">
          <div className="p-4 border-b border-outline-variant flex justify-between items-center bg-surface-container-lowest">
            <h3 className="text-title-lg font-title-lg text-on-surface">Recent Cases</h3>
            <button onClick={() => navigate('/cases')} className="text-label-md text-primary flex items-center gap-1">View All <span className="material-symbols-outlined text-[16px]">arrow_forward</span></button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-low border-b border-outline-variant">
                  <th className="py-2 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">Case ID</th>
                  <th className="py-2 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">Description</th>
                  <th className="py-2 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">Status</th>
                  <th className="py-2 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">Priority</th>
                  <th className="py-2 px-4 text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">Last Update</th>
                </tr>
              </thead>
              <tbody className="text-body-md font-body-md divide-y divide-outline-variant bg-surface-container-lowest">
                <tr className="hover:bg-primary/5 transition-colors group cursor-pointer" onClick={() => navigate('/cases/4492')}>
                  <td className="py-3 px-4 font-mono text-primary">#4492</td>
                  <td className="py-3 px-4 text-on-surface font-medium truncate max-w-[200px]">Operation Silent Echo</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-label-sm bg-primary-container text-on-primary-container">
                      <span className="w-1.5 h-1.5 rounded-full bg-on-primary-container" /> Processing
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-error font-medium text-label-sm">High</span>
                  </td>
                  <td className="py-3 px-4 text-on-surface-variant">10 mins ago</td>
                </tr>
                <tr className="hover:bg-primary/5 transition-colors group cursor-pointer" onClick={() => navigate('/cases/4491')}>
                  <td className="py-3 px-4 font-mono text-primary">#4491</td>
                  <td className="py-3 px-4 text-on-surface font-medium truncate max-w-[200px]">Project Vanguard Data Leak</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-label-sm bg-surface-container-high text-on-surface">
                      <span className="w-1.5 h-1.5 rounded-full bg-outline" /> Pending Review
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-on-surface font-medium text-label-sm">Medium</span>
                  </td>
                  <td className="py-3 px-4 text-on-surface-variant">2 hours ago</td>
                </tr>
                <tr className="hover:bg-primary/5 transition-colors group cursor-pointer" onClick={() => navigate('/cases/4488')}>
                  <td className="py-3 px-4 font-mono text-primary">#4488</td>
                  <td className="py-3 px-4 text-on-surface font-medium truncate max-w-[200px]">Financial Irregularity Q3</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-label-sm bg-secondary-container text-on-secondary-container">
                      <span className="w-1.5 h-1.5 rounded-full bg-on-secondary-container" /> Cross-Modal Active
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-error font-medium text-label-sm">High</span>
                  </td>
                  <td className="py-3 px-4 text-on-surface-variant">Yesterday</td>
                </tr>
                <tr className="hover:bg-primary/5 transition-colors group cursor-pointer" onClick={() => navigate('/cases/4470')}>
                  <td className="py-3 px-4 font-mono text-primary">#4470</td>
                  <td className="py-3 px-4 text-on-surface font-medium truncate max-w-[200px]">Unauthorized Access Log A</td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-label-sm bg-surface-container-high text-on-surface">
                      <span className="w-1.5 h-1.5 rounded-full bg-outline" /> Closed
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-outline font-medium text-label-sm">Low</span>
                  </td>
                  <td className="py-3 px-4 text-on-surface-variant">Oct 12, 2023</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        {/* Side Panel (Charts & Activity) */}
        <div className="flex flex-col gap-gutter">
          {/* Donut Chart Card */}
          <div className="glass-card rounded-xl p-4 flex flex-col h-[280px]">
            <h3 className="text-title-lg font-title-lg text-on-surface mb-2">Risk Distribution</h3>
            <div className="flex-1 relative flex items-center justify-center">
              <RiskChart />
            </div>
          </div>
          {/* Activity Timeline */}
          <div className="glass-card rounded-xl p-4 flex-1 overflow-hidden flex flex-col">
            <h3 className="text-title-lg font-title-lg text-on-surface mb-4">Activity Timeline</h3>
            <div className="flex-1 overflow-y-auto pr-2 space-y-4">
              <div className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className="w-6 h-6 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center">
                    <span className="material-symbols-outlined text-[14px]">psychology</span>
                  </div>
                  <div className="w-px h-full bg-outline-variant my-1" />
                </div>
                <div className="pb-2">
                  <div className="text-label-sm text-on-surface-variant">10:42 AM</div>
                  <div className="text-body-sm font-body-sm text-on-surface font-medium mt-0.5">AI Analysis Complete</div>
                  <div className="text-body-sm font-body-sm text-on-surface-variant mt-1 bg-surface-container-low p-2 rounded border border-outline-variant">Deepfake detection confirmed 98% confidence on Evidence IMG_092.</div>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className="w-6 h-6 rounded-full bg-surface-container-high text-on-surface flex items-center justify-center border border-outline-variant">
                    <span className="material-symbols-outlined text-[14px]">upload_file</span>
                  </div>
                  <div className="w-px h-full bg-outline-variant my-1" />
                </div>
                <div className="pb-2">
                  <div className="text-label-sm text-on-surface-variant">09:15 AM</div>
                  <div className="text-body-sm font-body-sm text-on-surface font-medium mt-0.5">New Evidence Uploaded</div>
                  <div className="text-body-sm font-body-sm text-on-surface-variant mt-1">Batch #4492-B uploaded by Agent Smith.</div>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className="w-6 h-6 rounded-full bg-error-container text-on-error-container flex items-center justify-center">
                    <span className="material-symbols-outlined text-[14px]">gavel</span>
                  </div>
                </div>
                <div>
                  <div className="text-label-sm text-on-surface-variant">Yesterday, 16:30 PM</div>
                  <div className="text-body-sm font-body-sm text-on-surface font-medium mt-0.5">Warrant Issued</div>
                  <div className="text-body-sm font-body-sm text-on-surface-variant mt-1">Linked to Case #4488.</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="h-8" />
    </main>
  );
}

