import React, { useState } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { TrendingUp, DollarSign, Calendar, Clock, BarChart2 } from 'lucide-react';

export default function RevenueChart({ timelineData }) {
  const [timeframe, setTimeframe] = useState('24h');
  const [viewMetric, setViewMetric] = useState('revenue'); // 'revenue' or 'units'

  return (
    <div className="ops-panel rounded-xl p-5 mb-6 border border-slate-800">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-400">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-mono uppercase tracking-tight flex items-center gap-2">
              Fleet Revenue Over Time
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/90 text-emerald-400 font-sans border border-emerald-700 font-bold flex items-center gap-1">
                ⚡ LinUCB Bandit +18.4% Dynamic Pricing Uplift
              </span>
            </h2>
            <p className="text-xs text-slate-400">Hourly sales volume & revenue velocity across 10 vending nodes</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-2">
          {/* Metric Toggle */}
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setViewMetric('revenue')}
              className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
                viewMetric === 'revenue'
                  ? 'bg-emerald-500 text-slate-950 font-black'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Revenue ($)
            </button>
            <button
              onClick={() => setViewMetric('units')}
              className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
                viewMetric === 'units'
                  ? 'bg-cyan-500 text-slate-950 font-black'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Units Sold
            </button>
          </div>

          {/* Timeframe */}
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800">
            {['24h', '7d', '30d'].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-2.5 py-1 text-xs font-mono font-bold rounded-md transition-colors uppercase ${
                  timeframe === tf
                    ? 'bg-slate-800 text-cyan-300 border border-slate-700'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart Visual Container */}
      <div className="h-64 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={timelineData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                color: '#f8fafc',
                fontSize: '12px',
                fontFamily: 'monospace'
              }}
              formatter={(value) => [viewMetric === 'revenue' ? `$${value}` : `${value} units`, viewMetric.toUpperCase()]}
            />
            <Line
              type="monotone"
              dataKey={viewMetric}
              stroke={viewMetric === 'revenue' ? '#10b981' : '#06b6d4'}
              strokeWidth={3}
              dot={{ fill: viewMetric === 'revenue' ? '#10b981' : '#06b6d4', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Chart Footer Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4 pt-3 border-t border-slate-800/80 text-xs">
        <div className="flex items-center space-x-2 text-slate-400">
          <Clock className="w-4 h-4 text-emerald-400" />
          <span>Peak Demand Hour: <strong className="text-white font-mono">12:00 - 13:00 ($1,240.00)</strong></span>
        </div>
        <div className="flex items-center space-x-2 text-slate-400">
          <BarChart2 className="w-4 h-4 text-cyan-400" />
          <span>Avg Transaction Size: <strong className="text-white font-mono">$3.92 / vend</strong></span>
        </div>
        <div className="flex items-center space-x-2 text-slate-400">
          <TrendingUp className="w-4 h-4 text-amber-400" />
          <span>Velocity: <strong className="text-emerald-400 font-mono">+18.4% vs yesterday</strong></span>
        </div>
      </div>
    </div>
  );
}
