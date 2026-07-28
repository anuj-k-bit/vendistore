import React, { useState } from 'react';
import { X, Server, RefreshCw, Thermometer, DollarSign, Signal, CheckCircle, AlertTriangle, ShieldCheck, Wrench } from 'lucide-react';

export default function MachineDetailModal({ machine, onClose, onRestockMachine }) {
  const [isRestocking, setIsRestocking] = useState(false);

  if (!machine) return null;

  const totalCapacity = machine.slots.reduce((sum, s) => sum + s.maxCapacity, 0);
  const currentTotalStock = machine.slots.reduce((sum, s) => sum + s.stock, 0);

  const handleRestock = () => {
    setIsRestocking(true);
    setTimeout(() => {
      onRestockMachine(machine.id);
      setIsRestocking(false);
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="relative w-full max-w-3xl ops-panel rounded-2xl border border-slate-700 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-900">
          <div className="flex items-center space-x-3">
            <span className="font-mono text-sm font-black text-cyan-300 px-2.5 py-1 rounded bg-cyan-950 border border-cyan-800">
              {machine.id}
            </span>
            <div>
              <h2 className="text-lg font-bold text-white font-mono">{machine.name}</h2>
              <p className="text-xs text-slate-400">{machine.address} • Zone: {machine.zone}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Telemetry Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Machine Status</span>
              <span className={`text-sm font-bold font-mono ${
                machine.status === 'Operational' ? 'text-emerald-400' : 'text-amber-400'
              }`}>
                {machine.status}
              </span>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Chiller Temp</span>
              <span className="text-sm font-bold font-mono text-cyan-300">{machine.temperature}°C</span>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Cash Canister</span>
              <span className="text-sm font-bold font-mono text-slate-200">{machine.cashBoxPercent}% Full</span>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">24h Sales</span>
              <span className="text-sm font-bold font-mono text-emerald-400">${machine.todaySales.toFixed(2)}</span>
            </div>
          </div>

          {/* Slot Inventory Breakdown */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase font-mono tracking-wider">
                Slot Level Inventory Matrix ({currentTotalStock}/{totalCapacity} Items)
              </h3>

              <button
                onClick={handleRestock}
                disabled={isRestocking}
                className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow active:scale-95 transition-all"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRestocking ? 'animate-spin' : ''}`} />
                <span>{isRestocking ? 'Restocking Machine...' : 'Refill All Slots (Restock)'}</span>
              </button>
            </div>

            <div className="space-y-2">
              {machine.slots.map((slot) => {
                const fillPct = Math.round((slot.stock / slot.maxCapacity) * 100);
                return (
                  <div
                    key={slot.slotId}
                    className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between gap-4"
                  >
                    <div className="flex items-center space-x-3 min-w-[180px]">
                      <span className="w-8 h-8 rounded bg-slate-900 border border-slate-700 flex items-center justify-center font-mono text-xs font-black text-cyan-300">
                        {slot.slotId}
                      </span>
                      <div>
                        <h4 className="text-xs font-bold text-white">{slot.productName}</h4>
                        <span className="text-[11px] text-slate-400 font-mono">${slot.price.toFixed(2)} / unit</span>
                      </div>
                    </div>

                    {/* Progress Fill Bar */}
                    <div className="flex-1 max-w-xs">
                      <div className="flex justify-between text-[10px] font-mono text-slate-400 mb-1">
                        <span>Fill Density</span>
                        <span className="font-bold text-white">{slot.stock} / {slot.maxCapacity} ({fillPct}%)</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            fillPct < 20 ? 'bg-rose-500' : fillPct < 60 ? 'bg-amber-500' : 'bg-emerald-500'
                          }`}
                          style={{ width: `${fillPct}%` }}
                        ></div>
                      </div>
                    </div>

                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      fillPct === 0
                        ? 'bg-slate-800 text-slate-500'
                        : fillPct < 20
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}>
                      {fillPct === 0 ? 'EMPTY' : fillPct < 20 ? 'LOW STOCK' : 'OPTIMAL'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-mono text-xs font-bold"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
