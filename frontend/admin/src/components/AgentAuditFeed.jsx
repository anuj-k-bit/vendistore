import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertOctagon, CheckCircle2, ShieldAlert, Terminal, RefreshCw } from 'lucide-react';

export default function AgentAuditFeed() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  async function fetchAuditLogs() {
    try {
      const res = await fetch('http://localhost:8086/agent/audit-log?limit=10');
      if (res.ok) {
        const data = await res.json();
        if (data.audit_logs) {
          setLogs(data.audit_logs);
        }
      }
    } catch (err) {
      console.warn('Using fallback audit log entries:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchAuditLogs();
    const interval = setInterval(fetchAuditLogs, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-950 border border-indigo-800 text-indigo-400">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white font-mono uppercase tracking-tight text-sm flex items-center gap-2">
              Agent Audit Log Feed
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
            </h3>
            <p className="text-xs text-slate-400">Live append-only guardrail policy decisions & ReAct traces</p>
          </div>
        </div>
        <button
          onClick={fetchAuditLogs}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
        {logs.length === 0 ? (
          <div className="text-center py-6 text-slate-500 text-xs font-mono">No agent audit logs recorded yet.</div>
        ) : (
          logs.map((log) => (
            <div
              key={log.id}
              className="bg-slate-950 p-3 rounded-xl border border-slate-800 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-slate-500 font-bold">#{log.id}</span>
                  <span className="font-mono font-bold text-xs text-cyan-400">{log.tool_name}</span>
                  <span className="text-[10px] text-slate-400 font-mono">({log.target_resource})</span>
                </div>

                <span className={`inline-flex items-center gap-1 font-mono text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase ${
                  log.status === 'EXECUTED' || log.status === 'ALLOWED'
                    ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                    : log.status === 'REJECTED'
                    ? 'bg-rose-950 text-rose-400 border-rose-800'
                    : 'bg-amber-950 text-amber-400 border-amber-800'
                }`}>
                  {log.status === 'REJECTED' ? <AlertOctagon className="w-3 h-3" /> : <ShieldCheck className="w-3 h-3" />}
                  {log.status}
                </span>
              </div>

              <div className="text-xs text-slate-300 font-sans mb-1">
                <strong className="text-slate-400 font-mono text-[11px] mr-1">[{log.policy_name}]:</strong>
                {log.policy_reason}
              </div>

              {log.arguments && (
                <div className="text-[10px] font-mono text-slate-500 bg-slate-900/60 p-1.5 rounded border border-slate-800/80 truncate">
                  Args: {JSON.stringify(log.arguments)}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
