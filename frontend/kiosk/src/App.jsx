import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import RecommendationStrip from './components/RecommendationStrip';
import ProductGrid from './components/ProductGrid';
import CheckoutModal from './components/CheckoutModal';
import SuccessScreen from './components/SuccessScreen';
import HelpModal from './components/HelpModal';
import SupportAgentChat from './components/SupportAgentChat';

import initialProducts from './data/products.json';
import { CreditCard, Smartphone, ShieldCheck, Heart, Sparkles, AlertCircle } from 'lucide-react';

export default function App() {
  const [products, setProducts] = useState(initialProducts);
  const [activeCategory, setActiveCategory] = useState('All Products');
  const [soundEnabled, setSoundEnabled] = useState(true);
  
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [completedOrder, setCompletedOrder] = useState(null);
  const [showHelp, setShowHelp] = useState(false);

  // Fetch live inventory from inventory-service & recommendations from recommendation-service
  useEffect(() => {
    async function loadLiveBackendData() {
      try {
        const invRes = await fetch('http://localhost:8080/machines/VM-101/inventory');
        if (invRes.ok) {
          const invData = await invRes.json();
          // Map PostgreSQL / inventory-service slot data to product state
          if (invData.slots) {
            setProducts(prev => prev.map(p => {
              const matchedSlot = invData.slots.find(s => s.slot_id === p.slotNumber);
              if (matchedSlot) {
                return {
                  ...p,
                  stockCount: matchedSlot.stock,
                  stockStatus: matchedSlot.stock === 0 ? 'empty' : matchedSlot.stock <= 2 ? 'low' : 'full'
                };
              }
              return p;
            }));
          }
        }
      } catch (err) {
        console.warn('Using fallback inventory data (inventory-service offline):', err);
      }
    }

    loadLiveBackendData();
  }, []);

  // Handle successful purchase & update local stock
  const handlePaymentSuccess = (orderData) => {
    const { product, quantity } = orderData;

    setProducts((prevProducts) =>
      prevProducts.map((p) => {
        if (p.id === product.id) {
          const newCount = Math.max(0, p.stockCount - quantity);
          let newStatus = p.stockStatus;
          if (newCount === 0) newStatus = 'empty';
          else if (newCount <= 2) newStatus = 'low';
          return {
            ...p,
            stockCount: newCount,
            stockStatus: newStatus
          };
        }
        return p;
      })
    );

    setSelectedProduct(null);
    setCompletedOrder(orderData);
  };

  const handleResetOrder = () => {
    setCompletedOrder(null);
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col justify-between select-none font-sans relative overflow-hidden">
      
      {/* Background ambient lighting glows */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-cyan-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute top-1/2 -right-40 w-96 h-96 bg-emerald-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute -bottom-40 left-1/3 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>

      {/* Top Navigation Header */}
      <Header
        soundEnabled={soundEnabled}
        setSoundEnabled={setSoundEnabled}
        onOpenHelp={() => setShowHelp(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 md:px-6 py-6 z-10 flex flex-col justify-start">
        
        {/* Recommended For You Strip (Above the Grid) */}
        <RecommendationStrip
          products={products}
          onSelectProduct={setSelectedProduct}
        />

        {/* Product Grid (8 Slots) */}
        <div className="flex-1">
          <ProductGrid
            products={products}
            activeCategory={activeCategory}
            setActiveCategory={setActiveCategory}
            onSelectProduct={setSelectedProduct}
          />
        </div>
      </main>

      {/* Bottom Kiosk Footer Banner */}
      <footer className="w-full glass-panel border-t border-slate-800 py-3 px-6 z-20 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
        <div className="flex items-center space-x-4">
          <span className="flex items-center gap-1.5 text-cyan-400 font-bold">
            <Smartphone className="w-4 h-4" /> Tap to Pay Supported
          </span>
          <span className="h-3 w-px bg-slate-800"></span>
          <span className="flex items-center gap-1.5 text-slate-300">
            <CreditCard className="w-4 h-4 text-emerald-400" /> All Major Cards Accepted
          </span>
        </div>

        <div className="flex items-center space-x-2 text-[11px] font-semibold text-slate-500">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          <span>IntelliVend Automated Touch System • Clean & Sterilized</span>
        </div>
      </footer>

      {/* Modals & Overlays */}
      {selectedProduct && (
        <CheckoutModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onPaymentSuccess={handlePaymentSuccess}
        />
      )}

      {completedOrder && (
        <SuccessScreen
          order={completedOrder}
          onReset={handleResetOrder}
        />
      )}

      {showHelp && (
        <HelpModal onClose={() => setShowHelp(false)} />
      )}

      {/* AI Customer Support Agent Chat Widget */}
      <SupportAgentChat />
    </div>
  );
}
