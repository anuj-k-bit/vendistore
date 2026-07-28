import React from 'react';
import { Sparkles, ArrowRight, Zap, Star } from 'lucide-react';
import { kioskAudio } from '../utils/audio';

export default function RecommendationStrip({ products, onSelectProduct }) {
  const recommendedItems = products.filter((p) => p.recommended || p.stockStatus === 'low');

  return (
    <div className="w-full mb-6">
      {/* Strip Header */}
      <div className="flex items-center justify-between px-2 mb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-400">
            <Sparkles className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              Recommended For You
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800 font-semibold">
                Smart Picks
              </span>
            </h2>
            <p className="text-xs text-slate-400">Curated based on current weather (Warm) & popular items</p>
          </div>
        </div>
        <div className="text-xs font-semibold text-slate-400 flex items-center gap-1">
          <Zap className="w-3.5 h-3.5 text-amber-400" /> Instant Dispense Ready
        </div>
      </div>

      {/* Recommended Items horizontal strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {recommendedItems.map((item) => {
          const isOutOfStock = item.stockStatus === 'empty';

          return (
            <div
              key={`rec-${item.id}`}
              onClick={() => {
                if (!isOutOfStock) {
                  kioskAudio.playSelect();
                  onSelectProduct(item);
                }
              }}
              className={`relative group rounded-2xl p-4 transition-all duration-200 border cursor-pointer flex items-center gap-4 ${
                isOutOfStock
                  ? 'bg-slate-900/40 border-slate-800 opacity-60 pointer-events-none'
                  : 'glass-card border-amber-500/30 hover:border-amber-400/60 shadow-lg hover:shadow-amber-500/10'
              }`}
            >
              {/* Badge */}
              <div className="absolute -top-2.5 right-4 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 shadow-md">
                {item.recommendationBadge || 'Top Choice'}
              </div>

              {/* Thumbnail */}
              <div className="relative w-20 h-20 rounded-xl overflow-hidden bg-slate-900 shrink-0 border border-slate-700/80">
                <img
                  src={item.image}
                  alt={item.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
                <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-slate-950/80 text-[10px] font-mono font-bold text-amber-400">
                  {item.slot}
                </span>
              </div>

              {/* Details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1 text-[11px] font-semibold text-amber-400 mb-0.5">
                  <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                  <span>{item.rating}</span>
                  <span className="text-slate-500">•</span>
                  <span className="text-slate-400">{item.calories || item.volume}</span>
                </div>
                <h3 className="text-base font-bold text-slate-100 truncate group-hover:text-amber-300 transition-colors">
                  {item.name}
                </h3>
                <p className="text-xs text-slate-400 truncate mb-2">{item.subtitle}</p>

                <div className="flex items-center justify-between">
                  <span className="text-lg font-black text-cyan-300 font-mono">
                    ${item.price.toFixed(2)}
                  </span>
                  <button
                    disabled={isOutOfStock}
                    className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1 shadow-md active:scale-95 transition-all"
                  >
                    Select <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
