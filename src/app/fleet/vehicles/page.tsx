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
  vin?: string;
  license_plate?: string;
}

export default function VehiclesListPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    loadVehicles();
  }, [statusFilter, typeFilter]);

  const loadVehicles = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.append("status", statusFilter);
      if (typeFilter !== "all") params.append("type", typeFilter);

      const response = await fetch(`/api/fleet/vehicles?${params.toString()}`, {
        credentials: "include"
      });
      const data = await response.json();
      setVehicles(data);
      setError(null);
    } catch (err) {
      setError("Failed to load vehicles.");
    } finally {
      setLoading(false);
    }
  };

  const filteredVehicles = vehicles.filter(v =>
    searchTerm === "" ||
    v.vehicle_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.call_sign?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    `${v.year} ${v.make} ${v.model}`.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case "in_service": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "out_of_service": return "bg-red-600/20 text-red-400 border-red-600/30";
      case "maintenance": return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      case "reserve": return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  const getTypeIcon = (type: string) => {
    if (type.toLowerCase().includes("ambulance")) return "🚑";
    if (type.toLowerCase().includes("engine")) return "🚒";
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
            <h1 className="text-3xl font-bold">Fleet Vehicles</h1>
            <p className="text-zinc-400 mt-1">Manage all vehicles in your fleet</p>
          </div>
          <Link
            href="/fleet"
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
          >
            ← Back to Fleet Dashboard
          </Link>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4 mb-6">
          <div className="flex gap-4">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by unit, vehicle ID, or vehicle..."
              className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="in_service">In Service</option>
              <option value="out_of_service">Out of Service</option>
              <option value="maintenance">Maintenance</option>
              <option value="reserve">Reserve</option>
            </select>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Types</option>
              <option value="ambulance">Ambulance</option>
              <option value="engine">Engine</option>
              <option value="rescue">Rescue</option>
              <option value="chief">Chief</option>
            </select>
          </div>
        </div>

        {/* Vehicles Table */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800">
          {loading ? (
            <div className="px-6 py-12 text-center text-zinc-400">Loading vehicles...</div>
          ) : filteredVehicles.length === 0 ? (
            <div className="px-6 py-12 text-center text-zinc-400">
              No vehicles found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-zinc-800/50 text-left text-sm text-zinc-400">
                  <tr>
                    <th className="px-6 py-3">Unit</th>
                    <th className="px-6 py-3">Type</th>
                    <th className="px-6 py-3">Vehicle</th>
                    <th className="px-6 py-3">VIN</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Mileage</th>
                    <th className="px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {filteredVehicles.map((vehicle) => (
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
                        <div>{vehicle.year} {vehicle.make} {vehicle.model}</div>
                        {vehicle.license_plate && (
                          <div className="text-xs text-zinc-500">{vehicle.license_plate}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-xs font-mono text-zinc-400">
                        {vehicle.vin || "N/A"}
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
