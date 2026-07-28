import React, { useState, useEffect } from 'react';
import OpsHeader from './components/OpsHeader';
import RevenueChart from './components/RevenueChart';
import AlertsPanel from './components/AlertsPanel';
import MachineHeatmapGrid from './components/MachineHeatmapGrid';
import MachineDetailModal from './components/MachineDetailModal';
import RestockPriorityPanel from './components/RestockPriorityPanel';
import RevenueComparisonCard from './components/RevenueComparisonCard';
import AgentAuditFeed from './components/AgentAuditFeed';
import RestockMapView from './components/RestockMapView';
import DriftExplainabilityCard from './components/DriftExplainabilityCard';

import initialAdminData from './data/mockAdminData.json';

export default function App() {
  const [data, setData] = useState(initialAdminData);
  const [liveInventory, setLiveInventory] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedMachineId, setSelectedMachineId] = useState(null);

  // Poll live inventory from inventory-service (port 8080)
  useEffect(() => {
    async function fetchLiveInventory() {
      try {
        const res = await fetch('http://localhost:8080/fleet/inventory');
        if (res.ok) {
          const invData = await res.json();
          setLiveInventory(invData);
        }
      } catch (err) {
        console.warn('Using fallback inventory data (inventory-service offline):', err);
      }
    }
    fetchLiveInventory();
    const interval = setInterval(fetchLiveInventory, 5000);
    return () => clearInterval(interval);
  }, []);

  // Filter 10 machines based on search query and status dropdown
  const filteredMachines = data.machines.filter((m) => {
    const matchesSearch =
      m.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.zone.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'ALL' || m.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  // Restock action simulator
  const handleRestockMachine = (machineId) => {
    setData((prevData) => {
      const updatedMachines = prevData.machines.map((m) => {
        if (m.id === machineId) {
          const restockedSlots = m.slots.map((s) => ({
            ...s,
            stock: s.maxCapacity
          }));
          return {
            ...m,
            status: 'Operational',
            slots: restockedSlots
          };
        }
        return m;
      });

      // Recalculate summary metrics
      const operationalCount = updatedMachines.filter((m) => m.status === 'Operational').length;
      const lowStockCount = updatedMachines.filter((m) => m.status === 'Low Stock').length;
      const criticalCount = updatedMachines.filter((m) => m.status === 'Critical').length;

      return {
        ...prevData,
        fleetSummary: {
          ...prevData.fleetSummary,
          operationalCount,
          lowStockCount,
          criticalCount
        },
        machines: updatedMachines
      };
    });
  };

  const selectedMachine = data.machines.find((m) => m.id === selectedMachineId);

  return (
    <div className="min-h-screen bg-[#080b11] text-slate-100 flex flex-col justify-between font-sans relative">
      {/* Top Operations Header */}
      <OpsHeader
        summary={data.fleetSummary}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        onRefresh={() => alert('Refreshing live telemetry feeds from 10 vending nodes...')}
      />

      {/* Main Dashboard Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 md:px-6 py-6 space-y-6">
        
        {/* Top Split Layout: Revenue Chart & Alerts Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Revenue Chart (2 cols on large screen) */}
          <div className="lg:col-span-2">
            <RevenueChart timelineData={data.revenueTimeline} />
          </div>

          {/* Low Stock Alerts Panel (1 col on large screen) */}
          <div className="lg:col-span-1">
            <AlertsPanel
              alerts={data.alerts}
              onSelectMachine={(id) => setSelectedMachineId(id)}
            />
          </div>
        </div>

        {/* ML Model Drift Detection & SHAP Feature Explainability */}
        <DriftExplainabilityCard />

        {/* LinUCB Dynamic Pricing Revenue Uplift Card */}
        <RevenueComparisonCard />

        {/* GIS Leaflet Restock Route Map View */}
        <RestockMapView inventoryData={liveInventory} />

        {/* Restock Priority Ranking & Agent Audit Feed Split Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RestockPriorityPanel inventoryData={liveInventory} />
          <AgentAuditFeed />
        </div>

        {/* 10 Machine Stock-Level Heatmap Grid */}
        <MachineHeatmapGrid
          machines={filteredMachines}
          onSelectMachine={(id) => setSelectedMachineId(id)}
        />
      </main>

      {/* Footer */}
      <footer className="w-full bg-slate-900 border-t border-slate-800 py-3 px-6 text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2 font-mono">
        <div>INTELLIVEND FLEET OPS v4.1 • REALTIME TELEMETRY SYSTEM</div>
        <div>10 Active Nodes Connected • Next Sensor Sync in 45s</div>
      </footer>

      {/* Inspector Modal */}
      {selectedMachine && (
        <MachineDetailModal
          machine={selectedMachine}
          onClose={() => setSelectedMachineId(null)}
          onRestockMachine={handleRestockMachine}
        />
      )}
    </div>
  );
}
