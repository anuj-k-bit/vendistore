import React from 'react';
import { X, PhoneCall, HelpCircle, Shield, Accessibility, Globe, Volume2 } from 'lucide-react';
import { kioskAudio } from '../utils/audio';

export default function HelpModal({ onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-lg glass-panel rounded-3xl overflow-hidden border border-slate-700 p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
          <div className="flex items-center space-x-2 text-cyan-400">
            <HelpCircle className="w-6 h-6" />
            <h3 className="text-xl font-bold text-white">Kiosk Assistance & Support</h3>
          </div>
          <button
            onClick={() => {
              kioskAudio.playTap();
              onClose();
            }}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4 mb-6">
          <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <PhoneCall className="w-6 h-6 text-emerald-400" />
              <div>
                <h4 className="text-sm font-bold text-white">24/7 Kiosk Helpline</h4>
                <p className="text-xs text-slate-400">Call 1-800-INTELLI for refund or item issues</p>
              </div>
            </div>
            <span className="px-3 py-1 rounded-lg bg-emerald-950 text-emerald-300 text-xs font-mono font-bold border border-emerald-800">
              Active
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Accessibility className="w-6 h-6 text-cyan-400" />
              <div>
                <h4 className="text-sm font-bold text-white">Accessibility Mode</h4>
                <p className="text-xs text-slate-400">High Contrast & Audio Voiceover Support</p>
              </div>
            </div>
            <span className="px-3 py-1 rounded-lg bg-cyan-950 text-cyan-300 text-xs font-bold border border-cyan-800">
              Enabled
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Globe className="w-6 h-6 text-amber-400" />
              <div>
                <h4 className="text-sm font-bold text-white">Interface Language</h4>
                <p className="text-xs text-slate-400">Currently set to English (US)</p>
              </div>
            </div>
            <div className="flex gap-1">
              <span className="px-2 py-1 rounded bg-cyan-500 text-slate-950 text-xs font-bold">EN</span>
              <span className="px-2 py-1 rounded bg-slate-800 text-slate-400 text-xs font-bold">ES</span>
            </div>
          </div>
        </div>

        <button
          onClick={() => {
            kioskAudio.playTap();
            onClose();
          }}
          className="w-full py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm border border-slate-700"
        >
          Close Assistance
        </button>
      </div>
    </div>
  );
}
