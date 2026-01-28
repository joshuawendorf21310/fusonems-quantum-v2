"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Vehicle {
  id: number;
  vehicle_id: string;
  call_sign: string;
  vehicle_type: string;
  make: string;
  model: string;
  year: string;
  status: string;
  mileage?: number;
}

interface FleetStats {
  total_vehicles: number;
  in_service: number;
  out_of_service: number;
  maintenance: number;
  inspections_today: number;
  inspections_this_week: number;
  defects_pending_correction: number;
  maintenance_due_soon: number;
}

export default function FleetPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [stats, setStats] = useState<FleetStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/fleet/vehicles", { credentials: "include" }).then((r) => r.json()),
      fetch("/api/fleet/statistics", { credentials: "include" }).then((r) => r.json()),
    ])
      .then(([vehicleData, statsData]) => {
        setVehicles(vehicleData);
        setStats(statsData);
      })
      .catch((err) => {
        console.error("Failed to load fleet data:", err);
      })
      .finally(() => setLoading(false));
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "in_service":
        return "bg-green-600/20 text-green-400 border-green-600/30";
      case "out_of_service":
        return "bg-red-600/20 text-red-400 border-red-600/30";
      case "maintenance":
        return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      case "reserve":
        return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      default:
        return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  const getTypeIcon = (type: string) => {
    if (type.toLowerCase().includes("ambulance")) return "🚑";
    if (type.toLowerCase().includes("engine") || type.toLowerCase() === "als" || type.toLowerCase() === "bls") return "🚒";
    if (type.toLowerCase().includes("ladder")) return "🪜";
    if (type.toLowerCase().includes("rescue")) return "🛻";
    if (type.toLowerCase().includes("chief")) return "🚗";
    if (type.toLowerCase().includes("helicopter")) return "🚁";
    return "🚐";
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Fleet Management</h1>
            <p className="text-zinc-400 mt-1">Vehicle tracking, DVIR, and maintenance</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/fleet/dvir"
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
            >
              DVIR Inspection
            </Link>
            <Link
              href="/fleet/vehicles"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium"
            >
              View All Vehicles
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-blue-400">{stats?.total_vehicles || vehicles.length}</div>
            <div className="text-sm text-zinc-400 mt-1">Total Vehicles</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-green-400">{stats?.in_service || 0}</div>
            <div className="text-sm text-zinc-400 mt-1">In Service</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-yellow-400">{stats?.maintenance || 0}</div>
            <div className="text-sm text-zinc-400 mt-1">In Maintenance</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-orange-400">{stats?.defects_pending_correction || 0}</div>
            <div className="text-sm text-zinc-400 mt-1">Pending Defects</div>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Link href="/fleet/dvir" className="bg-zinc-900 rounded-lg border border-zinc-800 p-6 hover:border-zinc-700 transition-colors">
            <div className="flex items-center gap-4">
              <div className="text-4xl">📋</div>
              <div>
                <h3 className="font-semibold text-lg">DVIR Inspections</h3>
                <p className="text-zinc-400 text-sm">Pre-trip and post-trip vehicle inspections</p>
                <div className="mt-2 text-sm">
                  <span className="text-blue-400 font-medium">{stats?.inspections_today || 0}</span> today
                  <span className="mx-2">|</span>
                  <span className="text-blue-400 font-medium">{stats?.inspections_this_week || 0}</span> this week
                </div>
              </div>
            </div>
          </Link>
          <Link href="/fleet/maintenance" className="bg-zinc-900 rounded-lg border border-zinc-800 p-6 hover:border-zinc-700 transition-colors">
            <div className="flex items-center gap-4">
              <div className="text-4xl">🔧</div>
              <div>
                <h3 className="font-semibold text-lg">Maintenance</h3>
                <p className="text-zinc-400 text-sm">Scheduled and preventive maintenance</p>
                <div className="mt-2 text-sm">
                  <span className="text-yellow-400 font-medium">{stats?.maintenance || 0}</span> in shop
                  <span className="mx-2">|</span>
                  <span className="text-orange-400 font-medium">{stats?.maintenance_due_soon || 0}</span> due soon
                </div>
              </div>
            </div>
          </Link>
          <Link href="/fleet/inspections" className="bg-zinc-900 rounded-lg border border-zinc-800 p-6 hover:border-zinc-700 transition-colors">
            <div className="flex items-center gap-4">
              <div className="text-4xl">✅</div>
              <div>
                <h3 className="font-semibold text-lg">Inspections</h3>
                <p className="text-zinc-400 text-sm">View inspection history and reports</p>
                <div className="mt-2 text-sm">
                  <span className="text-green-400 font-medium">{stats?.inspections_this_week || 0}</span> this week
                </div>
              </div>
            </div>
          </Link>
        </div>

        <div className="bg-zinc-900 rounded-lg border border-zinc-800">
          <div className="p-6 border-b border-zinc-800 flex justify-between items-center">
            <h2 className="font-semibold text-lg">Fleet Overview</h2>
            <Link
              href="/fleet/vehicles"
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              View All →
            </Link>
          </div>
          {loading ? (
            <div className="p-8 text-center text-zinc-400">Loading...</div>
          ) : vehicles.length === 0 ? (
            <div className="p-8 text-center text-zinc-400">No vehicles found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-zinc-800/50 text-left text-sm text-zinc-400">
                  <tr>
                    <th className="px-6 py-3">Unit</th>
                    <th className="px-6 py-3">Type</th>
                    <th className="px-6 py-3">Vehicle</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Mileage</th>
                    <th className="px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {vehicles.slice(0, 10).map((vehicle) => (
                    <tr key={vehicle.id} className="hover:bg-zinc-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className="text-xl">{getTypeIcon(vehicle.vehicle_type)}</span>
                          <div>
                            <div className="font-medium">{vehicle.call_sign || vehicle.vehicle_id}</div>
                            <div className="text-xs text-zinc-500">{vehicle.vehicle_id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm">{vehicle.vehicle_type}</td>
                      <td className="px-6 py-4 text-sm">
                        {vehicle.year} {vehicle.make} {vehicle.model}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(vehicle.status)}`}>
                          {vehicle.status.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-zinc-400">
                        {vehicle.mileage ? `${vehicle.mileage.toLocaleString()} mi` : "N/A"}
                      </td>
                      <td className="px-6 py-4">
                        <Link
                          href={`/fleet/vehicles/${vehicle.id}`}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
