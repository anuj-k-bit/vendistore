import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX, Thermometer, Cpu, Sparkles, HelpCircle, ShieldCheck } from 'lucide-react';
import { kioskAudio } from '../utils/audio';

export default function Header({ soundEnabled, setSoundEnabled, onOpenHelp }) {
  const [timeStr, setTimeStr] = useState('');
  const [dateStr, setDateStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
      setDateStr(now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleAudio = () => {
    const nextState = kioskAudio.toggleSound();
    setSoundEnabled(nextState);
    if (nextState) kioskAudio.playTap();
  };

  return (
    <header className="w-full glass-panel px-6 py-4 flex items-center justify-between border-b border-slate-800 sticky top-0 z-30 shadow-2xl">
      {/* Brand Logo & Status */}
      <div className="flex items-center space-x-4">
        <div className="relative flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-600 to-emerald-500 shadow-lg shadow-cyan-500/20">
          <Cpu className="w-7 h-7 text-white animate-pulse" />
          <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-emerald-400 border-2 border-slate-900 rounded-full animate-ping"></span>
          <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-emerald-400 border-2 border-slate-900 rounded-full"></span>
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black tracking-wider bg-gradient-to-r from-white via-cyan-100 to-cyan-400 bg-clip-text text-transparent">
              INTELLIVEND
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 rounded-full">
              Kiosk OS 3.2
            </span>
          </div>
          <p className="text-xs text-slate-400 font-medium flex items-center gap-2">
            <span>Terminal ID: <strong className="text-slate-200">#KV-802</strong></span>
            <span className="w-1 h-1 rounded-full bg-slate-600"></span>
            <span className="flex items-center text-emerald-400 gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> Online
            </span>
          </p>
        </div>
      </div>

      {/* Center Ambient Info */}
      <div className="hidden md:flex items-center space-x-6 px-4 py-2 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex items-center space-x-2">
          <Thermometer className="w-4 h-4 text-cyan-400" />
          <div>
            <span className="text-[10px] uppercase text-slate-400 block tracking-wider font-semibold">Chiller Temp</span>
            <span className="text-xs font-bold text-slate-200">3.8°C (Optimal)</span>
          </div>
        </div>
        <div className="h-6 w-px bg-slate-800"></div>
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <div>
            <span className="text-[10px] uppercase text-slate-400 block tracking-wider font-semibold">Smart Sensor</span>
            <span className="text-xs font-bold text-emerald-400">UV-C Sterilized</span>
          </div>
        </div>
      </div>

      {/* Right Time & Controls */}
      <div className="flex items-center space-x-4">
        {/* Clock */}
        <div className="text-right">
          <div className="text-xl font-bold font-mono text-cyan-300 tracking-tight">{timeStr}</div>
          <div className="text-[11px] text-slate-400 font-medium">{dateStr}</div>
        </div>

        {/* Audio Toggle */}
        <button
          onClick={handleToggleAudio}
          className={`p-3 rounded-xl border transition-all active:scale-95 flex items-center justify-center ${
            soundEnabled
              ? 'bg-cyan-950/40 text-cyan-400 border-cyan-800/60 hover:bg-cyan-900/50'
              : 'bg-slate-800/50 text-slate-500 border-slate-700 hover:bg-slate-800'
          }`}
          title={soundEnabled ? 'Mute Touch Sounds' : 'Enable Touch Sounds'}
        >
          {soundEnabled ? <Volume2 className="w-6 h-6" /> : <VolumeX className="w-6 h-6" />}
        </button>

        {/* Help Button */}
        <button
          onClick={() => {
            kioskAudio.playTap();
            onOpenHelp();
          }}
          className="p-3 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all active:scale-95 flex items-center justify-center"
          title="Assistance / Help"
        >
          <HelpCircle className="w-6 h-6" />
        </button>
      </div>
    </header>
  );
}
