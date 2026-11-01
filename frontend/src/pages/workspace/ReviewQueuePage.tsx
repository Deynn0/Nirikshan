import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  AlertTriangle,
  ShieldAlert,
  Clock,
  ArrowUpDown,
  Search,
  Filter,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
import { mockApplications, ApplicationItem } from '../../data/mockScrutinyData';
import { PillBadge } from '../../components/common/PillBadge';
import { LinkedApplicationsGraph } from '../../components/workspace/LinkedApplicationsGraph';

export const ReviewQueuePage: React.FC = () => {
  const navigate = useNavigate();
  const [filterTab, setFilterTab] = useState<'NEEDS_ATTENTION' | 'ALL'>('NEEDS_ATTENTION');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAppId, setSelectedAppId] = useState<string>('APP-2026-AICTE-4891');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');

  // Filter applications
  const filteredApps = mockApplications.filter((app) => {
    if (filterTab === 'NEEDS_ATTENTION' && app.statusType === 'verified') return false;
    if (categoryFilter !== 'ALL' && app.category !== categoryFilter) return false;
    if (
      searchQuery &&
      !app.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !app.id.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  const handleSelect = (app: ApplicationItem) => {
    setSelectedAppId(app.id);
  };

  const handleOpenDetail = (appId: string) => {
    navigate(`/workspace/application/${appId}`);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400 dark:text-stone-500">
          Scrutiny Directorate · Western Regional Office
        </span>
        <h2 className="text-2xl font-bold text-stone-900 dark:text-white tracking-tight mt-0.5">
          Review Queue
        </h2>
        <p className="text-xs text-stone-500 mt-1">
          Monitor incoming institutional compliance dossiers, cross-institution anomaly flags, and forensic discrepancies.
        </p>
      </div>

      {/* 1. Four KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Applications */}
        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft hover:shadow transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-slate-400">
              Applications
            </span>
            <div className="w-7 h-7 rounded-lg bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 flex items-center justify-center">
              <FileText className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-stone-900 dark:text-white">142</span>
            <span className="text-[11px] font-medium text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 px-1.5 py-0.5 rounded-full">
              +12% vs 2025
            </span>
          </div>
          <p className="text-[11px] text-stone-400 mt-1">Active regulatory cycle dossiers</p>
        </div>

        {/* KPI 2: Open Findings */}
        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft hover:shadow transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-slate-400">
              Open Findings
            </span>
            <div className="w-7 h-7 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 flex items-center justify-center">
              <AlertTriangle className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-stone-900 dark:text-white">38</span>
            <span className="text-[11px] font-medium text-amber-600 bg-amber-50 dark:bg-amber-950/40 px-1.5 py-0.5 rounded-full">
              29 actionable
            </span>
          </div>
          <p className="text-[11px] text-stone-400 mt-1">Deficiencies pending rectification</p>
        </div>

        {/* KPI 3: High or Critical */}
        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft hover:shadow transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-slate-400">
              High or Critical
            </span>
            <div className="w-7 h-7 rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 flex items-center justify-center">
              <ShieldAlert className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-rose-600 dark:text-rose-400">9</span>
            <span className="text-[11px] font-medium text-rose-700 bg-rose-50 dark:bg-rose-950/40 px-1.5 py-0.5 rounded-full">
              Requires Hearing
            </span>
          </div>
          <p className="text-[11px] text-stone-400 mt-1">Tampered PDFs & ghost faculty</p>
        </div>

        {/* KPI 4: Awaiting Manual Confirmation */}
        <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-5 shadow-soft hover:shadow transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-stone-500 dark:text-slate-400">
              Awaiting Confirmation
            </span>
            <div className="w-7 h-7 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 flex items-center justify-center">
              <Clock className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-stone-900 dark:text-white">14</span>
            <span className="text-[11px] font-medium text-indigo-600 bg-indigo-50 dark:bg-indigo-950/40 px-1.5 py-0.5 rounded-full">
              Field Photos
            </span>
          </div>
          <p className="text-[11px] text-stone-400 mt-1">CAD & GIS survey inspections</p>
        </div>
      </div>

      {/* Main Layout: Table on Left (8 cols), Graph & Needs Attention on Right (4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Table & Filters */}
        <div className="lg:col-span-8 space-y-4">
          {/* Table Toolbar */}
          <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-4 shadow-soft flex flex-wrap items-center justify-between gap-3">
            {/* Filter Tabs: Needs Attention / All */}
            <div className="flex items-center p-1 bg-stone-100 dark:bg-slate-800 rounded-lg">
              <button
                onClick={() => setFilterTab('NEEDS_ATTENTION')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  filterTab === 'NEEDS_ATTENTION'
                    ? 'bg-white dark:bg-slate-900 text-purple-700 dark:text-purple-300 shadow-xs'
                    : 'text-stone-500 hover:text-stone-900 dark:hover:text-slate-200'
                }`}
              >
                Needs attention ({mockApplications.filter((a) => a.statusType !== 'verified').length})
              </button>
              <button
                onClick={() => setFilterTab('ALL')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  filterTab === 'ALL'
                    ? 'bg-white dark:bg-slate-900 text-purple-700 dark:text-purple-300 shadow-xs'
                    : 'text-stone-500 hover:text-stone-900 dark:hover:text-slate-200'
                }`}
              >
                All Applications ({mockApplications.length})
              </button>
            </div>

            {/* Search and Category filter */}
            <div className="flex items-center gap-2 flex-1 sm:flex-initial">
              <div className="relative flex-1 sm:w-56">
                <Search className="w-3.5 h-3.5 text-stone-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter table..."
                  className="w-full bg-stone-50 dark:bg-slate-800/60 border border-stone-200 dark:border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-stone-900 dark:text-slate-100 placeholder:text-stone-400 outline-none focus:border-purple-500"
                />
              </div>

              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="bg-stone-50 dark:bg-slate-800/60 border border-stone-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-stone-700 dark:text-slate-300 outline-none"
              >
                <option value="ALL">All Categories</option>
                <option value="Engineering">Engineering</option>
                <option value="Management">Management</option>
                <option value="Pharmacy">Pharmacy</option>
                <option value="Polytechnic">Polytechnic</option>
              </select>
            </div>
          </div>

          {/* Sortable Table */}
          <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl shadow-soft overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-stone-50/80 dark:bg-slate-900/80 border-b border-stone-200 dark:border-slate-800 text-stone-400 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-4 py-3">Institution & ID</th>
                    <th className="px-3 py-3">Category</th>
                    <th className="px-3 py-3">Status</th>
                    <th className="px-3 py-3">Open Findings</th>
                    <th className="px-3 py-3">Risk Score</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100 dark:divide-slate-800">
                  {filteredApps.map((app) => {
                    const isSelected = selectedAppId === app.id;
                    return (
                      <tr
                        key={app.id}
                        onClick={() => handleSelect(app)}
                        className={`cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-purple-50/60 dark:bg-purple-950/30 item-selected-orange'
                            : 'hover:bg-stone-50/70 dark:hover:bg-slate-800/50'
                        }`}
                      >
                        {/* Institution */}
                        <td className="px-4 py-3.5">
                          <div className="font-semibold text-stone-900 dark:text-slate-100">
                            {app.name}
                          </div>
                          <div className="text-[11px] font-mono text-stone-400 mt-0.5">
                            {app.id} · {app.location}
                          </div>
                        </td>

                        {/* Category */}
                        <td className="px-3 py-3.5">
                          <span className="font-medium text-stone-600 dark:text-slate-300">
                            {app.category}
                          </span>
                        </td>

                        {/* Status */}
                        <td className="px-3 py-3.5">
                          <PillBadge
                            variant={
                              app.statusType === 'critical'
                                ? 'critical'
                                : app.statusType === 'warning'
                                ? 'warning'
                                : app.statusType === 'verified'
                                ? 'verified'
                                : 'neutral'
                            }
                            size="sm"
                          >
                            {app.status}
                          </PillBadge>
                        </td>

                        {/* Open Findings */}
                        <td className="px-3 py-3.5">
                          {app.openFindings > 0 ? (
                            <span className="inline-flex items-center gap-1 font-semibold text-rose-600 dark:text-rose-400">
                              <AlertTriangle className="w-3.5 h-3.5" />
                              {app.openFindings} findings
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 font-semibold text-emerald-600">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              Clean
                            </span>
                          )}
                        </td>

                        {/* Risk score */}
                        <td className="px-3 py-3.5">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-stone-100 dark:bg-slate-800 rounded-full overflow-hidden">
                              <div
                                style={{ width: `${app.riskScore}%` }}
                                className={`h-full rounded-full ${
                                  app.riskScore > 70
                                    ? 'bg-rose-500'
                                    : app.riskScore > 40
                                    ? 'bg-amber-500'
                                    : 'bg-emerald-500'
                                }`}
                              />
                            </div>
                            <span className="font-mono font-bold text-stone-700 dark:text-slate-300">
                              {app.riskScore}
                            </span>
                          </div>
                        </td>

                        {/* Action */}
                        <td className="px-4 py-3.5 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenDetail(app.id);
                            }}
                            className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-[#6D28D9] hover:bg-[#5B21B6] text-white text-[11px] font-semibold transition-all shadow-xs"
                          >
                            Review
                            <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Table Footer */}
            <div className="px-4 py-3 bg-stone-50/70 dark:bg-slate-900/80 border-t border-stone-200 dark:border-slate-800 flex items-center justify-between text-[11px] text-stone-500">
              <span>Showing {filteredApps.length} applications</span>
              <span className="font-mono">Western Regional Directorate Ledger</span>
            </div>
          </div>
        </div>

        {/* Right Column: Linked Applications Mini Graph & Needs Attention List */}
        <div className="lg:col-span-4 space-y-6">
          {/* Linked Applications Network Graph */}
          <LinkedApplicationsGraph />

          {/* Needs Attention Priority List */}
          <div className="surface-card bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl p-4 shadow-soft">
            <div className="flex items-center justify-between pb-3 border-b border-stone-200 dark:border-slate-800 mb-3">
              <span className="text-xs font-bold text-stone-900 dark:text-slate-100 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                Needs Attention
              </span>
              <span className="text-[10px] font-mono text-stone-400">Top Priority</span>
            </div>

            <div className="space-y-3">
              {mockApplications
                .filter((a) => a.riskScore > 70)
                .map((app) => (
                  <div
                    key={app.id}
                    onClick={() => handleOpenDetail(app.id)}
                    className="p-3 rounded-xl border border-stone-200 dark:border-slate-800 bg-stone-50/50 dark:bg-slate-800/40 hover:bg-purple-50/40 dark:hover:bg-purple-950/20 hover:border-purple-200 cursor-pointer transition-all group"
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="font-semibold text-xs text-stone-900 dark:text-slate-100 line-clamp-1 group-hover:text-purple-700">
                        {app.name}
                      </span>
                      <PillBadge variant="critical" size="sm">
                        Score {app.riskScore}
                      </PillBadge>
                    </div>
                    <p className="text-[11px] text-stone-500">
                      {app.openFindings} critical findings · {app.location}
                    </p>
                    <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-purple-700 dark:text-purple-400 font-semibold">
                      <span>Jump to Scrutiny</span>
                      <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
