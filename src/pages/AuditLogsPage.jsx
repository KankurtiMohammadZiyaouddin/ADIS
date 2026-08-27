export default function AuditLogsPage() {
  return (
    <main className="flex-1 p-container-margin overflow-auto">
      <div className="flex justify-between items-end mb-6">
        <div>
          <h2 className="text-display-lg font-display-lg text-on-surface mb-1">Audit Logs</h2>
          <p className="text-body-md font-body-md text-on-surface-variant">Cryptographically secure record of system access.</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 bg-surface-container-lowest border border-outline-variant text-on-surface px-4 py-2 rounded text-label-md hover:bg-surface-container transition-colors">
            <span className="material-symbols-outlined text-[18px]">filter_list</span> Filter
          </button>
          <button className="flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded text-label-md hover:bg-primary-container transition-colors">
            <span className="material-symbols-outlined text-[18px]">download</span> Export CSV
          </button>
        </div>
      </div>
      {/* Data Table Container */}
      <div className="bg-surface-container-lowest border border-outline-variant rounded-lg overflow-hidden shadow-sm">
        {/* Filters / Search bar intra-table */}
        <div className="p-4 border-b border-outline-variant bg-surface flex gap-4 items-center">
          <div className="relative flex-1 max-w-md">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">search</span>
            <input className="w-full pl-10 pr-3 py-2 bg-surface-container-lowest border border-outline-variant rounded text-body-md font-body-md focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all outline-none" placeholder="Search by ID or Hash..." type="text" />
          </div>
          <select className="border border-outline-variant bg-surface-container-lowest rounded py-2 px-3 text-body-md font-body-md text-on-surface focus:border-primary outline-none">
            <option>All Events</option>
            <option>Read</option>
            <option>Verify</option>
            <option>Export</option>
            <option>Analysis</option>
          </select>
          <select className="border border-outline-variant bg-surface-container-lowest rounded py-2 px-3 text-body-md font-body-md text-on-surface focus:border-primary outline-none">
            <option>Last 24 Hours</option>
            <option>Last 7 Days</option>
            <option>Last 30 Days</option>
          </select>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-low border-b border-outline-variant text-label-sm text-on-surface-variant uppercase tracking-wider">
                <th className="py-3 px-4 font-medium w-48">Timestamp (UTC)</th>
                <th className="py-3 px-4 font-medium w-32">Investigator ID</th>
                <th className="py-3 px-4 font-medium w-32">Event Type</th>
                <th className="py-3 px-4 font-medium">Action Details</th>
                <th className="py-3 px-4 font-medium w-64">Integrity Hash (SHA-256)</th>
              </tr>
            </thead>
            <tbody className="text-body-sm font-body-sm">
              <tr className="border-b border-outline-variant hover:bg-primary/5 transition-colors">
                <td className="py-3 px-4 font-mono text-on-surface">2023-10-27 14:32:01</td>
                <td className="py-3 px-4 text-on-surface">INV-8892</td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-container-highest text-on-surface-variant text-label-sm">Analysis</span>
                </td>
                <td className="py-3 px-4 text-on-surface-variant">Initiated deepface model execution on Ev-4492-A</td>
                <td className="py-3 px-4 font-mono text-xs text-outline truncate max-w-[200px]" title="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855">e3b0c442...b855</td>
              </tr>
              <tr className="border-b border-outline-variant hover:bg-primary/5 transition-colors">
                <td className="py-3 px-4 font-mono text-on-surface">2023-10-27 14:28:15</td>
                <td className="py-3 px-4 text-on-surface">INV-8892</td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-container-highest text-on-surface-variant text-label-sm">Read</span>
                </td>
                <td className="py-3 px-4 text-on-surface-variant">Accessed Case #4492 Metadata Record</td>
                <td className="py-3 px-4 font-mono text-xs text-outline truncate max-w-[200px]" title="8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92">8d969eef...6c92</td>
              </tr>
              <tr className="border-b border-outline-variant hover:bg-primary/5 transition-colors">
                <td className="py-3 px-4 font-mono text-on-surface">2023-10-27 14:15:22</td>
                <td className="py-3 px-4 text-on-surface">SYS-AUTO</td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-container-highest text-on-surface-variant text-label-sm">Verify</span>
                </td>
                <td className="py-3 px-4 text-on-surface-variant">Automated integrity check passed for Case #4492</td>
                <td className="py-3 px-4 font-mono text-xs text-outline truncate max-w-[200px]" title="c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2">c3ab8ff1...c4f2</td>
              </tr>
              <tr className="border-b border-outline-variant hover:bg-primary/5 transition-colors">
                <td className="py-3 px-4 font-mono text-on-surface">2023-10-27 13:50:05</td>
                <td className="py-3 px-4 text-on-surface">INV-2104</td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-container-highest text-on-surface-variant text-label-sm">Export</span>
                </td>
                <td className="py-3 px-4 text-on-surface-variant">Exported Evidence Ev-4480-C as PDF Report</td>
                <td className="py-3 px-4 font-mono text-xs text-outline truncate max-w-[200px]" title="f8e916298516104bc1a43a0d9228eb19875e5332f91040ea4611488c5ef33420">f8e91629...3420</td>
              </tr>
              <tr className="hover:bg-primary/5 transition-colors">
                <td className="py-3 px-4 font-mono text-on-surface">2023-10-27 13:45:12</td>
                <td className="py-3 px-4 text-on-surface">INV-2104</td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-container-highest text-on-surface-variant text-label-sm">Read</span>
                </td>
                <td className="py-3 px-4 text-on-surface-variant">Accessed Case #4480 Dashboard</td>
                <td className="py-3 px-4 font-mono text-xs text-outline truncate max-w-[200px]" title="4a44dc15364204a80fe80e9039455cc1608281820fe2b24f1e5233ade6af1dd5">4a44dc15...1dd5</td>
              </tr>
            </tbody>
          </table>
        </div>
        {/* Pagination Footer */}
        <div className="p-4 border-t border-outline-variant bg-surface flex items-center justify-between">
          <span className="text-label-sm text-on-surface-variant">Showing 1 to 5 of 124 entries</span>
          <div className="flex gap-1">
            <button className="p-1 rounded text-on-surface-variant hover:bg-surface-container transition-colors disabled:opacity-50"><span className="material-symbols-outlined text-[20px]">chevron_left</span></button>
            <button className="p-1 rounded text-on-surface-variant hover:bg-surface-container transition-colors"><span className="material-symbols-outlined text-[20px]">chevron_right</span></button>
          </div>
        </div>
      </div>
    </main>
  );
}

