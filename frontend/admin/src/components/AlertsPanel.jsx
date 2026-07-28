import React, { useState } from 'react';
import { AlertTriangle, ShieldAlert, Truck, Check, Bell, ChevronRight, X } from 'lucide-react';

export default function AlertsPanel({ alerts, onSelectMachine }) {
  const [acknowledged, setAcknowledged] = useState([]);
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  const handleAcknowledge = (id) => {
    setAcknowledged((prev) => [...prev, id]);
  };

  const filteredAlerts = alerts
    .filter((a) => !acknowledged.includes(a.id))
    .filter((a) => (filterSeverity === 'ALL' ? true : a.severity === filterSeverity));

  return (
    <div className="ops-panel rounded-xl p-5 mb-6 border border-amber-500/30 shadow-lg">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-amber-950/80 border border-amber-800 text-amber-400">
            <AlertTriangle className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-mono uppercase tracking-tight flex items-center gap-2">
              Low Stock & Telemetry Alerts Panel
              <span className="text-xs px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 font-bold">
                {filteredAlerts.length} Action Required
              </span>
            </h2>
            <p className="text-xs text-slate-400">Automated threshold triggers (&lt; 20% inventory or hardware warnings)</p>
          </div>
        </div>

        {/* Severity Filters & Action */}
        <div className="flex items-center space-x-2">
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            {['ALL', 'CRITICAL', 'WARNING'].map((sev) => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`px-2.5 py-1 font-mono font-bold rounded transition-colors ${
                  filterSeverity === sev
                    ? 'bg-slate-800 text-amber-300 border border-slate-700'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          <button
            onClick={() => alert('Restock truck route generated and dispatched to field operations crew.')}
            className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow active:scale-95 transition-all"
          >
            <Truck className="w-3.5 h-3.5" />
            <span>Dispatch Restock Route</span>
          </button>
        </div>
      </div>

      {/* Alert List Grid */}
      {filteredAlerts.length === 0 ? (
        <div className="p-6 text-center text-slate-500 text-sm font-medium">
          <Check className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
          All low stock alerts acknowledged. Fleet inventory optimal.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-colors ${
                alert.severity === 'CRITICAL'
                  ? 'bg-rose-950/30 border-rose-800/80 hover:bg-rose-950/50'
                  : alert.severity === 'WARNING'
                  ? 'bg-amber-950/30 border-amber-800/80 hover:bg-amber-950/50'
                  : 'bg-slate-900/60 border-slate-800'
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className="mt-0.5">
                  {alert.severity === 'CRITICAL' && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-black uppercase bg-rose-600 text-white shadow">
                      CRITICAL
                    </span>
                  )}
                  {alert.severity === 'WARNING' && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-black uppercase bg-amber-500 text-slate-950 shadow">
                      WARNING
                    </span>
                  )}
                  {alert.severity === 'INFO' && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-black uppercase bg-cyan-600 text-white shadow">
                      INFO
                    </span>
                  )}
                </div>

                <div>
                  <div className="flex items-center space-x-2">
                    <strong className="text-xs font-mono text-cyan-300">{alert.machineId}</strong>
                    <span className="text-slate-500">•</span>
                    <span className="text-xs font-bold text-slate-200">{alert.machineName}</span>
                    <span className="text-slate-500">•</span>
                    <span className="text-[11px] text-slate-400 font-mono">{alert.timestamp}</span>
                  </div>
                  <p className="text-xs text-slate-300 mt-0.5">{alert.message}</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
                <button
                  onClick={() => onSelectMachine(alert.machineId)}
                  className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-semibold border border-slate-700 flex items-center gap-1"
                >
                  Inspect Machine <ChevronRight className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => handleAcknowledge(alert.id)}
                  className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700"
                  title="Acknowledge Alert"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
