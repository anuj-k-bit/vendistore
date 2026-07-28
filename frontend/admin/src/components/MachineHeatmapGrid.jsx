import React from 'react';
import { Server, Thermometer, DollarSign, Signal, Lock, Eye, AlertCircle, RefreshCw } from 'lucide-react';

export default function MachineHeatmapGrid({ machines, onSelectMachine }) {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center space-x-2">
          <Server className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-slate-200 font-mono uppercase tracking-wider">
            Fleet Heatmap Matrix ({machines.length} Machines)
          </h2>
        </div>
        <div className="flex items-center space-x-3 text-[11px] font-mono">
          <span className="text-slate-400 flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-emerald-500/80 inline-block border border-emerald-400"></span> 60-100% Full
          </span>
          <span className="text-slate-400 flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-amber-500/80 inline-block border border-amber-400"></span> 20-59% Medium
          </span>
          <span className="text-slate-400 flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-rose-500/80 inline-block border border-rose-400"></span> 1-19% Critical
          </span>
          <span className="text-slate-400 flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-slate-800 inline-block border border-slate-600"></span> 0% Empty
          </span>
        </div>
      </div>

      {/* 10 Machine Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {machines.map((machine) => {
          const totalCapacity = machine.slots.reduce((sum, s) => sum + s.maxCapacity, 0);
          const currentTotalStock = machine.slots.reduce((sum, s) => sum + s.stock, 0);
          const overallStockPercent = Math.round((currentTotalStock / totalCapacity) * 100);

          return (
            <div
              key={machine.id}
              onClick={() => onSelectMachine(machine.id)}
              className={`ops-card rounded-xl p-4 flex flex-col justify-between cursor-pointer border transition-all hover:scale-[1.01] ${
                machine.status === 'Critical'
                  ? 'border-rose-900/80 shadow-rose-950/20 shadow-lg'
                  : machine.status === 'Low Stock'
                  ? 'border-amber-900/80'
                  : 'border-slate-800'
              }`}
            >
              {/* Top Row: ID & Status Badge */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-1.5">
                    <span className="font-mono text-xs font-black text-cyan-300 px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800">
                      {machine.id}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">{machine.lastPing}</span>
                  </div>

                  {machine.status === 'Operational' && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                      Operational
                    </span>
                  )}
                  {machine.status === 'Low Stock' && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-800 animate-pulse">
                      Low Stock
                    </span>
                  )}
                  {machine.status === 'Critical' && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800 animate-pulse">
                      CRITICAL
                    </span>
                  )}
                </div>

                <h3 className="text-xs font-bold text-white truncate mb-0.5" title={machine.name}>
                  {machine.name}
                </h3>
                <p className="text-[10px] text-slate-400 truncate mb-3">{machine.zone} • {machine.address}</p>

                {/* Telemetry Bar */}
                <div className="grid grid-cols-3 gap-1 bg-slate-950/80 p-2 rounded-lg border border-slate-800 text-[10px] font-mono mb-3">
                  <div>
                    <span className="text-slate-500 block">TEMP</span>
                    <span className="text-slate-200 font-bold">{machine.temperature}°C</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">CASH</span>
                    <span className={`font-bold ${machine.cashBoxPercent > 85 ? 'text-rose-400' : 'text-slate-200'}`}>
                      {machine.cashBoxPercent}%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">SALES</span>
                    <span className="text-emerald-400 font-bold">${machine.todaySales.toFixed(0)}</span>
                  </div>
                </div>

                {/* Slot Stock Level Heatmap Grid */}
                <div className="mb-3">
                  <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 mb-1">
                    <span>SLOT INVENTORY HEATMAP</span>
                    <span className="font-bold text-slate-200">{currentTotalStock}/{totalCapacity} ({overallStockPercent}%)</span>
                  </div>

                  <div className="grid grid-cols-4 gap-1.5">
                    {machine.slots.map((slot) => {
                      const fillPct = Math.round((slot.stock / slot.maxCapacity) * 100);
                      let heatClass = 'heatmap-optimal';
                      if (fillPct === 0) heatClass = 'heatmap-empty';
                      else if (fillPct < 20) heatClass = 'heatmap-low';
                      else if (fillPct < 60) heatClass = 'heatmap-medium';

                      return (
                        <div
                          key={slot.slotId}
                          className={`relative p-1.5 rounded text-center transition-transform hover:scale-105 cursor-pointer ${heatClass}`}
                          title={`${slot.slotId}: ${slot.productName} (${slot.stock}/${slot.maxCapacity} items - ${fillPct}%)`}
                        >
                          <span className="block text-[9px] font-mono font-bold leading-tight">{slot.slotId}</span>
                          <span className="block text-[10px] font-mono font-black">{slot.stock}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Card Footer Action */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectMachine(machine.id);
                }}
                className="w-full py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 font-mono text-xs font-bold border border-slate-700 flex items-center justify-center gap-1 transition-colors"
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Inspect Machine</span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
