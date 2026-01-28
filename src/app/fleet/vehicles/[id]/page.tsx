"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface VehicleDetail {
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
  registration_expires?: string;
  inspection_due?: string;
  oil_change_due?: number;
  last_inspection_date?: string;
}

interface MaintenanceRecord {
  id: number;
  maintenance_type: string;
  description: string;
  date: string;
  mileage?: number;
  cost?: number;
  vendor?: string;
  status: string;
}

interface InspectionRecord {
  id: number;
  inspection_type: string;
  date: string;
  inspector: string;
  result: string;
  defects_found?: number;
}

export default function VehicleDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const [vehicle, setVehicle] = useState<VehicleDetail | null>(null);
  const [maintenance, setMaintenance] = useState<MaintenanceRecord[]>([]);
  const [inspections, setInspections] = useState<InspectionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "maintenance" | "inspections">("overview");

  useEffect(() => {
    if (!id) return;
    loadVehicleData();
  }, [id]);

  const loadVehicleData = async () => {
    setLoading(true);
    try {
      const [vehicleData, maintenanceData, inspectionsData] = await Promise.all([
        fetch(`/api/fleet/vehicles/${id}`, { credentials: "include" }).then(r => r.json()),
        fetch(`/api/fleet/vehicles/${id}/maintenance`, { credentials: "include" }).then(r => r.json()).catch(() => []),
        fetch(`/api/fleet/vehicles/${id}/inspections`, { credentials: "include" }).then(r => r.json()).catch(() => [])
      ]);
      setVehicle(vehicleData);
      setMaintenance(maintenanceData);
      setInspections(inspectionsData);
      setError(null);
    } catch (err) {
      setError("Failed to load vehicle details.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "in_service": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "out_of_service": return "bg-red-600/20 text-red-400 border-red-600/30";
      case "maintenance": return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      case "reserve": return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  const getMaintenanceStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "scheduled": return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      case "in_progress": return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  const getInspectionResultColor = (result: string) => {
    switch (result.toLowerCase()) {
      case "pass": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "fail": return "bg-red-600/20 text-red-400 border-red-600/30";
      case "conditional": return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
        <div className="text-center py-12 text-zinc-400">Loading vehicle...</div>
      </div>
    );
  }

  if (error || !vehicle) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
        <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg">
          {error || "Vehicle not found"}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Link href="/fleet/vehicles" className="text-zinc-400 hover:text-zinc-300">
                ← Back to Vehicles
              </Link>
            </div>
            <h1 className="text-3xl font-bold">{vehicle.call_sign || vehicle.vehicle_id}</h1>
            <p className="text-zinc-400 mt-1">
              {vehicle.year} {vehicle.make} {vehicle.model}
            </p>
          </div>
          <div className="flex gap-3">
            <Link
              href={`/fleet/dvir?vehicle=${vehicle.id}`}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
            >
              Start DVIR
            </Link>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
              Schedule Maintenance
            </button>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
            <div className="text-sm text-zinc-400 mb-1">Status</div>
            <span className={`inline-block px-2 py-1 rounded text-xs font-medium border ${getStatusColor(vehicle.status)}`}>
              {vehicle.status.replace("_", " ")}
            </span>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
            <div className="text-sm text-zinc-400 mb-1">Mileage</div>
            <div className="font-semibold">{vehicle.mileage ? `${vehicle.mileage.toLocaleString()} mi` : "N/A"}</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
            <div className="text-sm text-zinc-400 mb-1">Last Inspection</div>
            <div className="font-semibold">
              {vehicle.last_inspection_date ? new Date(vehicle.last_inspection_date).toLocaleDateString() : "N/A"}
            </div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
            <div className="text-sm text-zinc-400 mb-1">Registration Expires</div>
            <div className="font-semibold">
              {vehicle.registration_expires ? new Date(vehicle.registration_expires).toLocaleDateString() : "N/A"}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 mb-6">
          <div className="flex border-b border-zinc-800">
            <button
              onClick={() => setActiveTab("overview")}
              className={`px-6 py-3 font-medium ${
                activeTab === "overview"
                  ? "border-b-2 border-blue-500 text-blue-400"
                  : "text-zinc-400 hover:text-zinc-300"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab("maintenance")}
              className={`px-6 py-3 font-medium ${
                activeTab === "maintenance"
                  ? "border-b-2 border-blue-500 text-blue-400"
                  : "text-zinc-400 hover:text-zinc-300"
              }`}
            >
              Maintenance History
            </button>
            <button
              onClick={() => setActiveTab("inspections")}
              className={`px-6 py-3 font-medium ${
                activeTab === "inspections"
                  ? "border-b-2 border-blue-500 text-blue-400"
                  : "text-zinc-400 hover:text-zinc-300"
              }`}
            >
              Inspections
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === "overview" && (
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold text-lg mb-4">Vehicle Information</h3>
                  <div className="space-y-3">
                    <div>
                      <div className="text-sm text-zinc-400 mb-1">Vehicle ID</div>
                      <div className="font-medium">{vehicle.vehicle_id}</div>
                    </div>
                    <div>
                      <div className="text-sm text-zinc-400 mb-1">VIN</div>
                      <div className="font-mono text-sm">{vehicle.vin || "N/A"}</div>
                    </div>
                    <div>
                      <div className="text-sm text-zinc-400 mb-1">License Plate</div>
                      <div className="font-medium">{vehicle.license_plate || "N/A"}</div>
                    </div>
                    <div>
                      <div className="text-sm text-zinc-400 mb-1">Type</div>
                      <div className="font-medium">{vehicle.vehicle_type}</div>
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-4">Maintenance Schedule</h3>
                  <div className="space-y-3">
                    <div>
                      <div className="text-sm text-zinc-400 mb-1">Oil Change Due</div>
                      <div className="font-medium">
                        {vehicle.oil_change_due ? `${vehicle.oil_change_due.toLocaleString()} mi` : "N/A"}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-zinc-400 mb-1">Inspection Due</div>
                      <div className="font-medium">
                        {vehicle.inspection_due ? new Date(vehicle.inspection_due).toLocaleDateString() : "N/A"}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "maintenance" && (
              <div>
                {maintenance.length === 0 ? (
                  <div className="text-center py-8 text-zinc-400">
                    No maintenance records found
                  </div>
                ) : (
                  <div className="space-y-3">
                    {maintenance.map((record) => (
                      <div key={record.id} className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div className="font-semibold">{record.maintenance_type}</div>
                            <div className="text-sm text-zinc-400">{record.description}</div>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs font-medium border ${getMaintenanceStatusColor(record.status)}`}>
                            {record.status}
                          </span>
                        </div>
                        <div className="flex gap-4 text-sm text-zinc-400">
                          <div>Date: {new Date(record.date).toLocaleDateString()}</div>
                          {record.mileage && <div>Mileage: {record.mileage.toLocaleString()} mi</div>}
                          {record.cost && <div>Cost: ${record.cost.toFixed(2)}</div>}
                          {record.vendor && <div>Vendor: {record.vendor}</div>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "inspections" && (
              <div>
                {inspections.length === 0 ? (
                  <div className="text-center py-8 text-zinc-400">
                    No inspection records found
                  </div>
                ) : (
                  <div className="space-y-3">
                    {inspections.map((record) => (
                      <div key={record.id} className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div className="font-semibold">{record.inspection_type}</div>
                            <div className="text-sm text-zinc-400">Inspector: {record.inspector}</div>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs font-medium border ${getInspectionResultColor(record.result)}`}>
                            {record.result}
                          </span>
                        </div>
                        <div className="flex gap-4 text-sm text-zinc-400">
                          <div>Date: {new Date(record.date).toLocaleDateString()}</div>
                          {record.defects_found !== undefined && (
                            <div>Defects: {record.defects_found}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
