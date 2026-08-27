import { useNavigate } from 'react-router-dom';

export default function CasesPage() {
  const navigate = useNavigate();
  return (
    <main className="flex-1 p-spacious bg-background">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header & Actions */}
        <div className="flex justify-between items-end">
          <div>
            <h2 className="text-headline-md font-headline-md text-on-surface mb-1">Cases Management</h2>
            <p className="text-body-md font-body-md text-on-surface-variant">Manage and track all forensic investigations.</p>
          </div>
          <div className="flex gap-3">
            <button className="bg-surface border border-outline-variant text-on-surface px-4 py-2 rounded flex items-center gap-2 text-label-md hover:bg-surface-container-low transition-colors">
              <span className="material-symbols-outlined text-[18px]">download</span>
              Export
            </button>
            <button className="bg-primary text-on-primary px-4 py-2 rounded flex items-center gap-2 text-label-md hover:opacity-90 transition-opacity">
              <span className="material-symbols-outlined text-[18px]">add</span>
              New Case
            </button>
          </div>
        </div>
        {/* Filters & Search Bar */}
        <div className="bg-surface border border-outline-variant rounded-lg p-4 flex flex-col md:flex-row gap-4 items-center">
          <div className="relative flex-1 w-full">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">search</span>
            <input className="w-full pl-10 pr-4 py-2 bg-background border border-outline-variant rounded text-body-sm font-body-sm focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all outline-none" placeholder="Search cases by ID, name, or investigator..." type="text" />
          </div>
          <div className="flex gap-3 w-full md:w-auto">
            <select className="bg-background border border-outline-variant rounded px-3 py-2 text-body-sm font-body-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none">
              <option value>All Priorities</option>
              <option value="high">High Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="low">Low Priority</option>
            </select>
            <select className="bg-background border border-outline-variant rounded px-3 py-2 text-body-sm font-body-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none">
              <option value>All Statuses</option>
              <option value="active">Active</option>
              <option value="pending">Pending Review</option>
              <option value="closed">Closed</option>
            </select>
            <input className="bg-background border border-outline-variant rounded px-3 py-2 text-body-sm font-body-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none" type="date" />
          </div>
        </div>
        {/* Data Table */}
        <div className="bg-surface border border-outline-variant rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-low border-b border-outline-variant text-label-sm text-on-surface-variant">
                  <th className="px-6 py-3 font-semibold">Case ID</th>
                  <th className="px-6 py-3 font-semibold">Case Name</th>
                  <th className="px-6 py-3 font-semibold">Primary Investigator</th>
                  <th className="px-6 py-3 font-semibold">Date Created</th>
                  <th className="px-6 py-3 font-semibold">Priority</th>
                  <th className="px-6 py-3 font-semibold">Status</th>
                  <th className="px-6 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="text-body-md font-body-md text-on-surface divide-y divide-outline-variant">
                <tr className="hover:bg-primary/5 transition-colors group cursor-pointer" onClick={() => navigate('/cases/4492')}>
                  <td className="px-6 py-4 font-mono text-primary">#4492</td>
                  <td className="px-6 py-4 font-medium">Operation Silk Road Data Extraction</td>
                  <td className="px-6 py-4">J. Doe</td>
                  <td className="px-6 py-4 text-on-surface-variant text-body-sm">Oct 24, 2023</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1 text-error text-label-sm px-2 py-1 bg-error-container rounded-sm">
                      <span className="material-symbols-outlined text-[14px]">priority_high</span> High
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-surface-tint" />
                      <span className="text-body-sm">Active</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-primary hover:text-primary-fixed-variant text-label-sm opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => { e.stopPropagation(); navigate('/cases/4492'); }}>Open Case</button>
                  </td>
                </tr>
                <tr className="hover:bg-primary/5 transition-colors group cursor-pointer" onClick={() => navigate('/cases/4491')}>
                  <td className="px-6 py-4 font-mono text-primary">#4491</td>
                  <td className="px-6 py-4 font-medium">Financial Fraud - Enron Archives</td>
                  <td className="px-6 py-4">A. Smith</td>
                  <td className="px-6 py-4 text-on-surface-variant text-body-sm">Oct 22, 2023</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1 text-on-surface-variant text-label-sm px-2 py-1 bg-surface-container-high rounded-sm">
                      <span className="material-symbols-outlined text-[14px]">remove</span> Medium
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-outline" />
                      <span className="text-body-sm">Pending Review</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-primary hover:text-primary-fixed-variant text-label-sm opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => { e.stopPropagation(); navigate('/cases/4491'); }}>Open Case</button>
                  </td>
                </tr>
                <tr className="hover:bg-primary/5 transition-colors group cursor-pointer" onClick={() => navigate('/cases/4488')}>
                  <td className="px-6 py-4 font-mono text-primary">#4488</td>
                  <td className="px-6 py-4 font-medium">Cyber Intrusion - Nexus Corp</td>
                  <td className="px-6 py-4">M. Johnson</td>
                  <td className="px-6 py-4 text-on-surface-variant text-body-sm">Oct 15, 2023</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1 text-error text-label-sm px-2 py-1 bg-error-container rounded-sm">
                      <span className="material-symbols-outlined text-[14px]">priority_high</span> High
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-surface-tint" />
                      <span className="text-body-sm">Active</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-primary hover:text-primary-fixed-variant text-label-sm opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => { e.stopPropagation(); navigate('/cases/4488'); }}>Open Case</button>
                  </td>
                </tr>
                <tr className="hover:bg-primary/5 transition-colors group cursor-pointer" onClick={() => navigate('/cases/4475')}>
                  <td className="px-6 py-4 font-mono text-primary">#4475</td>
                  <td className="px-6 py-4 font-medium">Dark Web Narcotics Tracing</td>
                  <td className="px-6 py-4">R. Garcia</td>
                  <td className="px-6 py-4 text-on-surface-variant text-body-sm">Sep 28, 2023</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1 text-tertiary text-label-sm px-2 py-1 bg-tertiary-container/20 rounded-sm">
                      <span className="material-symbols-outlined text-[14px]">arrow_downward</span> Low
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-on-surface-variant" />
                      <span className="text-body-sm text-on-surface-variant">Closed</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-primary hover:text-primary-fixed-variant text-label-sm opacity-0 group-hover:opacity-100 transition-opacity">View Details</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          <div className="bg-surface-container-low border-t border-outline-variant px-6 py-3 flex items-center justify-between">
            <span className="text-label-sm text-on-surface-variant">Showing 1 to 4 of 128 Cases</span>
            <div className="flex gap-2">
              <button className="p-1 rounded text-on-surface-variant hover:bg-surface-variant transition-colors disabled:opacity-50" disabled>
                <span className="material-symbols-outlined text-[20px]">chevron_left</span>
              </button>
              <button className="p-1 rounded text-on-surface-variant hover:bg-surface-variant transition-colors">
                <span className="material-symbols-outlined text-[20px]">chevron_right</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

