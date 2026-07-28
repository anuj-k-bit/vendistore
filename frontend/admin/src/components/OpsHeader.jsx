import React from 'react';
import { Activity, Server, DollarSign, AlertTriangle, Thermometer, ShieldCheck, Search, Filter, RefreshCw } from 'lucide-react';

export default function OpsHeader({ summary, searchTerm, setSearchTerm, statusFilter, setStatusFilter, onRefresh }) {
  return (
    <header className="w-full bg-slate-900 border-b border-slate-800 px-6 py-3 sticky top-0 z-30 shadow-md">
      {/* Top row: Brand & Status pill */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-3">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-cyan-950 border border-cyan-800 text-cyan-400">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-black tracking-tight text-white uppercase font-mono">
                INTELLIVEND <span className="text-cyan-400 font-sans text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-semibold ml-2">OPS COMMAND</span>
              </h1>
              <span className="flex items-center text-[10px] font-bold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1 animate-pulse"></span>
                SYSTEM NORMAL
              </span>
            </div>
            <p className="text-xs text-slate-400">Fleet telemetry & automated inventory monitoring console</p>
          </div>
        </div>

        {/* Global Action & Search */}
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search machine ID or location..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-56 font-mono"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-cyan-500 font-semibold"
          >
            <option value="ALL">All Statuses (10)</option>
            <option value="Operational">Operational</option>
            <option value="Low Stock">Low Stock Alert</option>
            <option value="Critical">Critical</option>
          </select>

          <button
            onClick={onRefresh}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
            title="Refresh Telemetry"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPI Metrics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3 pt-2 border-t border-slate-800/80">
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500 block tracking-wider">Fleet Online</span>
            <span className="text-base font-black text-white font-mono">{summary.operationalCount} / {summary.totalMachines} Active</span>
          </div>
          <Activity className="w-5 h-5 text-emerald-400" />
        </div>

        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500 block tracking-wider">24h Fleet Sales</span>
            <span className="text-base font-black text-emerald-400 font-mono">${summary.totalDailyRevenue.toFixed(2)}</span>
          </div>
          <DollarSign className="w-5 h-5 text-emerald-400" />
        </div>

        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500 block tracking-wider">Total Units Dispatched</span>
            <span className="text-base font-black text-cyan-300 font-mono">{summary.totalUnitsSold} Units</span>
          </div>
          <Server className="w-5 h-5 text-cyan-400" />
        </div>

        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500 block tracking-wider">Low Stock Threshold Alerts</span>
            <span className="text-base font-black text-amber-400 font-mono">{summary.activeAlertsCount} Alerts</span>
          </div>
          <AlertTriangle className="w-5 h-5 text-amber-400" />
        </div>

        <div className="hidden lg:flex bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500 block tracking-wider">Avg Chiller Temp</span>
            <span className="text-base font-black text-cyan-300 font-mono">{summary.avgChillerTemp}°C</span>
          </div>
          <Thermometer className="w-5 h-5 text-cyan-400" />
        </div>
      </div>
    </header>
  );
}
