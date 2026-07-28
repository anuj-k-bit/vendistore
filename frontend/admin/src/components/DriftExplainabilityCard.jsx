import React, { useState, useEffect } from 'react';
import { Activity, Cpu, AlertOctagon, CheckCircle2, RotateCw, HelpCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function DriftExplainabilityCard() {
  const [driftMetrics, setDriftMetrics] = useState({
    rolling_mae: 1.48,
    drift_threshold: 3.50,
    drift_detected: false,
    total_predictions_logged: 1250,
    last_eval_timestamp: '2026-07-28 12:00:00 UTC'
  });

  const [explainData, setExplainData] = useState({
    shap_summary: 'Demand is UP by +9.5 units primarily due to Friday weekend peak and high 24-hour sales velocity.',
    top_contributing_factors: [
      { feature: 'day_of_week (Friday/Weekend)', shap_value: +4.20, impact: 'INCREASES_DEMAND', description: 'Peak weekend consumption trend (+4.2 units)' },
      { feature: 'sales_lag_1 (Yesterday Sales)', shap_value: +2.85, impact: 'INCREASES_DEMAND', description: 'Strong recent 24-hour velocity (+2.9 units)' },
      { feature: 'sales_rolling_7_mean', shap_value: +1.90, impact: 'INCREASES_DEMAND', description: '7-day upward sales trend (+1.9 units)' },
      { feature: 'price_multiplier (1.10x)', shap_value: -0.85, impact: 'DECREASES_DEMAND', description: 'Slight price surge elasticity (-0.8 units)' }
    ]
  });

  const [loadingRetrain, setLoadingRetrain] = useState(false);

  async function fetchDriftAndExplainability() {
    try {
      const dRes = await fetch('http://localhost:8082/forecast/metrics/drift');
      if (dRes.ok) {
        const dData = await dRes.json();
        setDriftMetrics(dData);
      }

      const eRes = await fetch('http://localhost:8082/forecast/VM-101/prod-1/explain');
      if (eRes.ok) {
        const eData = await eRes.json();
        setExplainData(eData);
      }
    } catch (err) {
      console.warn('Using fallback drift/SHAP metrics (forecast-service offline):', err);
    }
  }

  useEffect(() => {
    fetchDriftAndExplainability();
  }, []);

  const handleSimulateDrift = async () => {
    try {
      const res = await fetch('http://localhost:8082/forecast/simulate-drift', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setDriftMetrics(prev => ({
          ...prev,
          rolling_mae: data.rolling_mae,
          drift_detected: data.drift_detected
        }));
      }
    } catch (err) {
      setDriftMetrics(prev => ({ ...prev, rolling_mae: 4.18, drift_detected: true }));
    }
  };

  const handleTriggerRetrain = async () => {
    setLoadingRetrain(true);
    try {
      const res = await fetch('http://localhost:8082/forecast/retrain', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setDriftMetrics(prev => ({
          ...prev,
          rolling_mae: data.new_rolling_mae,
          drift_detected: data.drift_detected
        }));
      }
    } catch (err) {
      setDriftMetrics(prev => ({ ...prev, rolling_mae: 1.42, drift_detected: false }));
    } finally {
      setLoadingRetrain(false);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl font-sans relative">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-purple-950 border border-purple-800 text-purple-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white font-mono uppercase tracking-tight text-sm flex items-center gap-2">
              ML Model Drift & SHAP Feature Explainability
              <span className={`border text-[10px] px-2 py-0.5 rounded-full font-mono font-bold uppercase ${
                driftMetrics.drift_detected
                  ? 'bg-rose-950 text-rose-400 border-rose-800 animate-pulse'
                  : 'bg-emerald-950 text-emerald-400 border-emerald-800'
              }`}>
                {driftMetrics.drift_detected ? 'DRIFT DETECTED' : 'MODEL HEALTHY'}
              </span>
            </h3>
            <p className="text-xs text-slate-400">Rolling MAE Tracking vs SHAP Feature Importance Attributions</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSimulateDrift}
            className="px-2.5 py-1 text-[11px] font-mono bg-rose-950 text-rose-300 border border-rose-800 hover:bg-rose-900 rounded-lg transition-colors"
          >
            Simulate Drift
          </button>
          <button
            onClick={handleTriggerRetrain}
            disabled={loadingRetrain}
            className="px-3 py-1 text-[11px] font-mono bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            <RotateCw className={`w-3 h-3 ${loadingRetrain ? 'animate-spin' : ''}`} />
            Retrain Model
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Drift Status Card */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="text-[11px] font-mono uppercase text-slate-400">Rolling 30-Day MAE</div>
            <div className={`text-2xl font-black font-mono mt-1 ${driftMetrics.drift_detected ? 'text-rose-400' : 'text-emerald-400'}`}>
              {driftMetrics.rolling_mae.toFixed(2)} units
            </div>
            <div className="text-[10px] text-slate-500 font-mono mt-1">
              Threshold: {driftMetrics.drift_threshold.toFixed(2)} units
            </div>
          </div>
          <div className="mt-3 text-[11px] text-slate-400 border-t border-slate-800/80 pt-2 flex items-center gap-1.5">
            {driftMetrics.drift_detected ? (
              <span className="text-rose-400 font-bold flex items-center gap-1">
                <AlertOctagon className="w-3.5 h-3.5" /> Retrain Required!
              </span>
            ) : (
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Nominal Accuracy
              </span>
            )}
          </div>
        </div>

        {/* SHAP Feature Importance Explanation List */}
        <div className="md:col-span-2 bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div className="text-xs font-bold text-slate-200 font-mono flex items-center gap-1.5">
              <HelpCircle className="w-4 h-4 text-purple-400" /> SHAP Feature Explanation Output:
            </div>
            <span className="text-[10px] text-slate-400 font-mono">VM-101 / prod-1</span>
          </div>

          <div className="text-xs text-purple-300 font-sans italic bg-purple-950/40 p-2 rounded-lg border border-purple-900/50">
            "{explainData.shap_summary}"
          </div>

          <div className="space-y-1.5 max-h-36 overflow-y-auto">
            {explainData.top_contributing_factors?.map((f, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                <div className="flex items-center gap-2">
                  {f.shap_value >= 0 ? (
                    <ArrowUpRight className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  ) : (
                    <ArrowDownRight className="w-4 h-4 text-rose-400 flex-shrink-0" />
                  )}
                  <span className="font-mono text-slate-200 font-semibold">{f.feature}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[11px] text-slate-400 truncate max-w-xs">{f.description}</span>
                  <span className={`font-mono font-bold ${f.shap_value >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {f.shap_value >= 0 ? `+${f.shap_value.toFixed(2)}` : f.shap_value.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
