import React from 'react';
import { ShoppingBag, AlertTriangle, CheckCircle2, XCircle, ChevronRight, Tag } from 'lucide-react';
import { kioskAudio } from '../utils/audio';

export default function ProductGrid({ products, activeCategory, setActiveCategory, onSelectProduct }) {
  const categories = ['All Products', 'Coffee & Tea', 'Hydration', 'Snacks', 'Fresh Juices'];

  const filteredProducts = activeCategory === 'All Products'
    ? products
    : products.filter(p => p.category === activeCategory);

  return (
    <div className="w-full">
      {/* Category Filter Pills (Large Touch Targets) */}
      <div className="flex items-center space-x-3 mb-5 overflow-x-auto pb-2 no-scrollbar">
        {categories.map((cat) => {
          const isActive = activeCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => {
                kioskAudio.playTap();
                setActiveCategory(cat);
              }}
              className={`px-5 py-3 rounded-xl font-bold text-sm whitespace-nowrap transition-all duration-200 border active:scale-95 flex items-center gap-2 ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-600 to-cyan-500 text-slate-950 border-cyan-400 shadow-lg shadow-cyan-500/25 font-extrabold'
                  : 'bg-slate-900/80 text-slate-300 border-slate-800 hover:bg-slate-800 hover:text-white'
              }`}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Grid Container (8 Slots Layout) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-5">
        {filteredProducts.map((product) => {
          const isOutOfStock = product.stockStatus === 'empty';
          const isLowStock = product.stockStatus === 'low';

          return (
            <div
              key={product.id}
              onClick={() => {
                if (!isOutOfStock) {
                  kioskAudio.playSelect();
                  onSelectProduct(product);
                }
              }}
              className={`relative rounded-2xl p-4 flex flex-col justify-between border transition-all duration-200 ${
                isOutOfStock
                  ? 'bg-slate-950/60 border-slate-900 opacity-50 cursor-not-allowed'
                  : 'glass-card hover:border-cyan-500/50 cursor-pointer group shadow-xl'
              }`}
            >
              {/* Top Header Row in Card: Slot Tag & Stock Badge */}
              <div className="flex items-center justify-between mb-3">
                {/* Slot Tag */}
                <div className="px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-700/80 font-mono text-xs font-bold text-cyan-300 flex items-center gap-1 shadow-inner">
                  <Tag className="w-3 h-3 text-cyan-400" />
                  <span>SLOT {product.slot}</span>
                </div>

                {/* Stock Status Badge */}
                {isOutOfStock ? (
                  <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-950/90 text-rose-400 border border-rose-800/80 flex items-center gap-1">
                    <XCircle className="w-3.5 h-3.5" /> Empty
                  </span>
                ) : isLowStock ? (
                  <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-950/90 text-amber-300 border border-amber-700/80 flex items-center gap-1 animate-pulse">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Only {product.stockCount} Left
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800/80 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> In Stock
                  </span>
                )}
              </div>

              {/* Product Visual Container */}
              <div className="relative w-full aspect-square rounded-xl overflow-hidden bg-slate-950 mb-3 border border-slate-800/80 group-hover:border-slate-700 transition-colors">
                <img
                  src={product.image}
                  alt={product.name}
                  className={`w-full h-full object-cover transition-transform duration-500 ${
                    isOutOfStock ? 'grayscale opacity-40' : 'group-hover:scale-105'
                  }`}
                />
                
                {/* Overlay details on hover or touch */}
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-80"></div>
                
                {/* Calories or weight tag */}
                <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-slate-900/90 backdrop-blur-sm text-[11px] font-medium text-slate-300 border border-slate-800">
                  {product.calories || product.volume || product.weight}
                </div>
              </div>

              {/* Product Title & Category */}
              <div className="mb-3">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-cyan-400 block mb-0.5">
                  {product.category}
                </span>
                <h3 className="text-base font-extrabold text-slate-100 line-clamp-1 group-hover:text-cyan-300 transition-colors">
                  {product.name}
                </h3>
                <p className="text-xs text-slate-400 line-clamp-1">{product.subtitle}</p>
              </div>

              {/* Footer: Price & Touch Target Button */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                <div>
                  <span className="text-[10px] uppercase text-slate-500 font-semibold block">Price</span>
                  <span className="text-xl font-black text-white font-mono tracking-tight">
                    ${product.price.toFixed(2)}
                  </span>
                </div>

                <button
                  disabled={isOutOfStock}
                  className={`px-4 py-2.5 rounded-xl font-bold text-xs flex items-center gap-1.5 transition-all shadow-md active:scale-95 ${
                    isOutOfStock
                      ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                      : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-cyan-500/20 group-hover:shadow-cyan-500/40 font-extrabold'
                  }`}
                >
                  {isOutOfStock ? (
                    'Sold Out'
                  ) : (
                    <>
                      <span>Tap to Buy</span>
                      <ChevronRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
