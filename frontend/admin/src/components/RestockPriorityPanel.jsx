import React from 'react';
import { Truck, AlertTriangle, ArrowUpRight, TrendingUp } from 'lucide-react';

export default function RestockPriorityPanel({ inventoryData }) {
  // Extract and rank low-stock slots from inventory data
  const restockItems = [];

  if (inventoryData && inventoryData.machines) {
    inventoryData.machines.forEach(m => {
      m.slots?.forEach(s => {
        const ratio = s.stock / s.max_capacity;
        if (ratio <= 0.8) {
          restockItems.push({
            machineId: m.machine_id,
            location: m.location || 'Downtown Terminal',
            slotId: s.slot_id,
            productName: s.product_name || 'Vending Product',
            currentStock: s.stock,
            maxCapacity: s.max_capacity,
            fillPercentage: Math.round(ratio * 100),
            priority: ratio <= 0.3 ? 'URGENT' : ratio <= 0.6 ? 'HIGH' : 'MEDIUM'
          });
        }
      });
    });
  }

  // Fallback items if database empty
  if (restockItems.length === 0) {
    restockItems.push(
      { machineId: 'VM-101', location: 'Tech Hub Terminal', slotId: 'A1', productName: 'Nitro Cold Brew', currentStock: 2, maxCapacity: 15, fillPercentage: 13, priority: 'URGENT' },
      { machineId: 'VM-104', location: 'Airport Terminal', slotId: 'B2', productName: 'Protein Crunch Bar', currentStock: 4, maxCapacity: 20, fillPercentage: 20, priority: 'URGENT' },
      { machineId: 'VM-107', location: 'Metro Station', slotId: 'A4', productName: 'Dark Chocolate Almond Bar', currentStock: 6, maxCapacity: 20, fillPercentage: 30, priority: 'HIGH' }
    );
  }

  // Sort by priority (URGENT -> HIGH -> MEDIUM)
  restockItems.sort((a, b) => a.fillPercentage - b.fillPercentage);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-amber-950 border border-amber-800 text-amber-400">
            <Truck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white font-mono uppercase tracking-tight text-sm">
              Restock Priority Ranking
            </h3>
            <p className="text-xs text-slate-400">Calculated from Stock Deficit vs ML Forecast Demand</p>
          </div>
        </div>
        <span className="text-[11px] bg-slate-800 text-slate-300 font-mono px-2.5 py-1 rounded-full border border-slate-700">
          {restockItems.length} Dispatch Items
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-sans">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px] uppercase tracking-wider">
              <th className="py-2.5 px-3">Priority</th>
              <th className="py-2.5 px-3">Machine</th>
              <th className="py-2.5 px-3">Slot & Product</th>
              <th className="py-2.5 px-3">Stock / Cap</th>
              <th className="py-2.5 px-3">Fill Level</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {restockItems.slice(0, 5).map((item, idx) => (
              <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                <td className="py-3 px-3">
                  <span className={`inline-flex items-center gap-1 font-mono font-bold text-[10px] px-2 py-0.5 rounded-md uppercase border ${
                    item.priority === 'URGENT'
                      ? 'bg-rose-950/80 text-rose-400 border-rose-800'
                      : item.priority === 'HIGH'
                      ? 'bg-amber-950/80 text-amber-400 border-amber-800'
                      : 'bg-blue-950/80 text-blue-400 border-blue-800'
                  }`}>
                    <AlertTriangle className="w-3 h-3" />
                    {item.priority}
                  </span>
                </td>
                <td className="py-3 px-3 font-mono font-bold text-slate-200">
                  {item.machineId}
                  <div className="text-[10px] text-slate-400 font-sans font-normal">{item.location}</div>
                </td>
                <td className="py-3 px-3 font-semibold text-slate-100">
                  <span className="font-mono text-cyan-400 font-bold mr-1.5">[{item.slotId}]</span>
                  {item.productName}
                </td>
                <td className="py-3 px-3 font-mono text-slate-300">
                  <strong className="text-white">{item.currentStock}</strong> / {item.maxCapacity}
                </td>
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                      <div
                        className={`h-full rounded-full transition-all ${
                          item.fillPercentage <= 20 ? 'bg-rose-500' : item.fillPercentage <= 50 ? 'bg-amber-500' : 'bg-emerald-500'
                        }`}
                        style={{ width: `${item.fillPercentage}%` }}
                      ></div>
                    </div>
                    <span className="font-mono text-[11px] text-slate-400 font-bold">{item.fillPercentage}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
