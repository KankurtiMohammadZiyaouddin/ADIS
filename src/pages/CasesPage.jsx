import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCases, createCase } from '../services/analysisStore';

export default function CasesPage() {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [modalOpen, setModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [investigator, setInvestigator] = useState('Senior Investigator');

  const loadData = async () => {
    const list = await getCases();
    setCases(list);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateCase = async (e) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    await createCase({ title: newTitle, description: newDesc, investigator });
    setModalOpen(false);
    setNewTitle('');
    setNewDesc('');
    await loadData();
  };

  const filteredCases = cases.filter((c) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch = !q || c.id?.toLowerCase().includes(q) || c.title?.toLowerCase().includes(q) || c.investigator?.toLowerCase().includes(q);
    const matchesStatus = statusFilter === 'ALL' || c.status?.toLowerCase() === statusFilter.toLowerCase();
    return matchesSearch && matchesStatus;
  });

  return (
    <main className="flex-1 p-spacious bg-background">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header & Actions */}
        <div className="flex justify-between items-end">
          <div>
            <h2 className="text-headline-md font-headline-md text-on-surface mb-1">Investigations Management</h2>
            <p className="text-body-md font-body-md text-on-surface-variant">
              Centralized SQLite Chain-of-Custody cases across Desktop & Mobile.
            </p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={() => setModalOpen(true)}
              className="bg-primary text-on-primary px-4 py-2 rounded flex items-center gap-2 text-label-md hover:opacity-90 transition-opacity"
            >
              <span className="material-symbols-outlined text-[18px]">add</span>
              New Case
            </button>
          </div>
        </div>

        {/* Filters & Search Bar */}
        <div className="bg-surface border border-outline-variant rounded-lg p-4 flex flex-col md:flex-row gap-4 items-center">
          <div className="relative flex-1 w-full">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">search</span>
            <input 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-background border border-outline-variant rounded text-body-sm font-body-sm focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all outline-none" 
              placeholder="Search cases by ID, name, or investigator..." 
              type="text" 
            />
          </div>
          <div className="flex gap-3 w-full md:w-auto">
            <select 
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-background border border-outline-variant rounded px-3 py-2 text-body-sm font-body-sm text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="active">Active</option>
              <option value="pending">Pending</option>
              <option value="closed">Closed</option>
            </select>
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
                  <th className="px-6 py-3 font-semibold">Status</th>
                  <th className="px-6 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="text-body-md font-body-md text-on-surface divide-y divide-outline-variant">
                {filteredCases.map((item) => (
                  <tr 
                    key={item.id}
                    className="hover:bg-primary/5 transition-colors group cursor-pointer" 
                    onClick={() => navigate(`/cases/${item.id.replace('CAS-', '')}`)}
                  >
                    <td className="px-6 py-4 font-mono text-primary font-bold">{item.id}</td>
                    <td className="px-6 py-4 font-medium">{item.title}</td>
                    <td className="px-6 py-4 text-on-surface-variant">{item.investigator || 'ADIS Analyst'}</td>
                    <td className="px-6 py-4 text-on-surface-variant text-body-sm">
                      {item.created_at ? item.created_at.slice(0, 10) : '2026-09-28'}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${item.status === 'active' ? 'bg-surface-tint' : 'bg-outline'}`} />
                        <span className="text-body-sm capitalize">{item.status || 'Active'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        className="text-primary hover:text-primary-fixed-variant text-label-sm font-semibold"
                        onClick={(e) => { e.stopPropagation(); navigate(`/cases/${item.id.replace('CAS-', '')}`); }}
                      >
                        Open Case →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          <div className="bg-surface-container-low border-t border-outline-variant px-6 py-3 flex items-center justify-between">
            <span className="text-label-sm text-on-surface-variant">Showing {filteredCases.length} Cases</span>
          </div>
        </div>

        {/* Modal for creating case */}
        {modalOpen && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-surface border border-outline-variant rounded-xl p-6 max-w-md w-full shadow-2xl">
              <h3 className="text-headline-sm font-headline-sm text-on-surface mb-4">Open New Investigation Case</h3>
              <form onSubmit={handleCreateCase} className="space-y-4">
                <div>
                  <label className="block text-label-sm text-on-surface-variant mb-1">Case Title</label>
                  <input 
                    type="text" 
                    value={newTitle} 
                    onChange={(e) => setNewTitle(e.target.value)} 
                    placeholder="e.g. Synthetic Voice Impersonation Probe"
                    className="w-full bg-background border border-outline-variant rounded p-2 text-body-sm text-on-surface outline-none focus:border-primary"
                    required
                  />
                </div>
                <div>
                  <label className="block text-label-sm text-on-surface-variant mb-1">Description</label>
                  <textarea 
                    value={newDesc} 
                    onChange={(e) => setNewDesc(e.target.value)} 
                    placeholder="Investigation scope and notes..."
                    className="w-full bg-background border border-outline-variant rounded p-2 text-body-sm text-on-surface outline-none focus:border-primary h-20"
                  />
                </div>
                <div>
                  <label className="block text-label-sm text-on-surface-variant mb-1">Lead Investigator</label>
                  <input 
                    type="text" 
                    value={investigator} 
                    onChange={(e) => setInvestigator(e.target.value)} 
                    className="w-full bg-background border border-outline-variant rounded p-2 text-body-sm text-on-surface outline-none focus:border-primary"
                  />
                </div>
                <div className="flex gap-3 justify-end pt-2">
                  <button 
                    type="button" 
                    onClick={() => setModalOpen(false)}
                    className="px-4 py-2 border border-outline-variant rounded text-label-md text-on-surface hover:bg-surface-container"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    className="px-4 py-2 bg-primary text-on-primary rounded text-label-md font-medium hover:opacity-90"
                  >
                    Create Case
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}


