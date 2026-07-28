import React, { useState, useEffect } from 'react';
import { CheckCircle2, PackageCheck, QrCode, ArrowRight, Sparkles, Receipt, RefreshCw, ShoppingBag } from 'lucide-react';
import confetti from 'canvas-confetti';
import { kioskAudio } from '../utils/audio';

export default function SuccessScreen({ order, onReset }) {
  const [countdown, setCountdown] = useState(10);
  const [dispenseProgress, setDispenseProgress] = useState(0);
  const [dispensed, setDispensed] = useState(false);

  useEffect(() => {
    // Fire confetti on mount
    try {
      confetti({
        particleCount: 60,
        spread: 70,
        origin: { y: 0.6 }
      });
    } catch (e) {
      console.warn("Confetti error", e);
    }

    // Play dispense audio
    kioskAudio.playDispenseSound();

    // Dispense progress animation
    const progressInterval = setInterval(() => {
      setDispenseProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          setDispensed(true);
          return 100;
        }
        return prev + 20;
      });
    }, 400);

    // Countdown reset
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          onReset();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      clearInterval(progressInterval);
      clearInterval(timer);
    };
  }, [onReset]);

  if (!order) return null;

  const { product, quantity, total, transactionId } = order;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-lg animate-fadeIn">
      <div className="relative w-full max-w-xl glass-panel rounded-3xl overflow-hidden border border-emerald-500/40 p-8 shadow-2xl text-center">
        
        {/* Animated Checkmark Icon */}
        <div className="relative w-24 h-24 mx-auto mb-5 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping"></div>
          <div className="relative w-20 h-20 rounded-full bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-xl shadow-emerald-500/30">
            <CheckCircle2 className="w-12 h-12 text-slate-950 stroke-[2.5]" />
          </div>
        </div>

        {/* Success Title */}
        <h2 className="text-3xl font-black text-white mb-1">Payment Successful!</h2>
        <p className="text-sm text-emerald-300 font-semibold mb-6 flex items-center justify-center gap-1">
          <Sparkles className="w-4 h-4" /> Transaction Approved • {transactionId}
        </p>

        {/* Dispensing Conveyor Animation Status */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 mb-6 text-left">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <PackageCheck className="w-5 h-5 text-cyan-400" />
              <span className="text-sm font-bold text-white">
                {dispensed ? 'Item Dispensed!' : `Dispensing Slot ${product.slot}...`}
              </span>
            </div>
            <span className="text-xs font-mono font-bold text-cyan-300">{dispenseProgress}%</span>
          </div>

          {/* Progress bar with mechanical conveyor styling */}
          <div className="w-full h-4 rounded-full bg-slate-950 overflow-hidden p-0.5 border border-slate-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-400 animate-conveyor transition-all duration-300"
              style={{ width: `${dispenseProgress}%` }}
            ></div>
          </div>

          <p className="text-xs text-slate-400 mt-2 font-medium">
            {dispensed ? (
              <span className="text-emerald-400 font-bold">Please grab your item from the tray below ↓</span>
            ) : (
              `Dispensing ${quantity}x ${product.name}... Please wait.`
            )}
          </p>
        </div>

        {/* Purchased Item & Receipt */}
        <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-900/50 border border-slate-800 mb-6">
          <div className="flex items-center space-x-3 text-left">
            <img src={product.image} alt={product.name} className="w-12 h-12 rounded-xl object-cover border border-slate-700" />
            <div>
              <h4 className="text-sm font-bold text-white">{product.name}</h4>
              <span className="text-xs text-slate-400">Qty: {quantity} • Total: ${total.toFixed(2)}</span>
            </div>
          </div>

          {/* QR Receipt Download */}
          <div className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-xs text-slate-300">
            <QrCode className="w-6 h-6 text-cyan-400 shrink-0" />
            <div className="text-left leading-tight">
              <span className="font-bold text-white block">E-Receipt</span>
              <span className="text-[10px] text-slate-400">Scan for phone copy</span>
            </div>
          </div>
        </div>

        {/* Action Button & Auto-reset countdown */}
        <div className="flex flex-col items-center gap-3">
          <button
            onClick={() => {
              kioskAudio.playTap();
              onReset();
            }}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-black text-base flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 active:scale-95 transition-all"
          >
            <span>Done / Collect & Return</span>
            <ArrowRight className="w-5 h-5" />
          </button>
          
          <p className="text-xs text-slate-400 flex items-center gap-1 font-mono">
            <RefreshCw className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
            Screen auto-resets in <strong className="text-cyan-300 font-bold">{countdown}s</strong>
          </p>
        </div>

      </div>
    </div>
  );
}
