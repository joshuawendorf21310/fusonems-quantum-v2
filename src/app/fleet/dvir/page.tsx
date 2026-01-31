"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

interface Vehicle {
  id: number;
  vehicle_id: string;
  call_sign: string;
  vehicle_type: string;
}

interface CheckItem {
  key: string;
  label: string;
  category: "dot" | "ems" | "fire";
}

const DOT_CHECKS: CheckItem[] = [
  { key: "brakes_ok", label: "Service brakes, parking brake", category: "dot" },
  { key: "steering_ok", label: "Steering mechanism", category: "dot" },
  { key: "lights_headlights_ok", label: "Headlights (high/low beam)", category: "dot" },
  { key: "lights_taillights_ok", label: "Tail lights", category: "dot" },
  { key: "lights_brake_ok", label: "Brake lights", category: "dot" },
  { key: "lights_turn_signals_ok", label: "Turn signals (front/rear)", category: "dot" },
  { key: "lights_emergency_ok", label: "Emergency warning lights", category: "dot" },
  { key: "horn_ok", label: "Horn", category: "dot" },
  { key: "windshield_ok", label: "Windshield (no cracks/visibility)", category: "dot" },
  { key: "wipers_ok", label: "Windshield wipers and washer", category: "dot" },
  { key: "mirrors_ok", label: "Mirrors (both sides)", category: "dot" },
  { key: "tires_front_ok", label: "Front tires (tread/pressure/damage)", category: "dot" },
  { key: "tires_rear_ok", label: "Rear tires (tread/pressure/damage)", category: "dot" },
  { key: "wheels_lugs_ok", label: "Wheels and lug nuts", category: "dot" },
  { key: "fluid_levels_ok", label: "Fluid levels (oil, coolant, brake)", category: "dot" },
  { key: "exhaust_ok", label: "Exhaust system", category: "dot" },
  { key: "battery_ok", label: "Battery and connections", category: "dot" },
  { key: "fire_extinguisher_ok", label: "Fire extinguisher (charged/accessible)", category: "dot" },
  { key: "reflective_triangles_ok", label: "Reflective triangles/flares", category: "dot" },
  { key: "first_aid_kit_ok", label: "First aid kit", category: "dot" },
  { key: "seatbelts_ok", label: "Seat belts (all positions)", category: "dot" },
];

const EMS_CHECKS: CheckItem[] = [
  { key: "stretcher_ok", label: "Primary stretcher operation", category: "ems" },
  { key: "stretcher_straps_ok", label: "Stretcher straps and restraints", category: "ems" },
  { key: "suction_ok", label: "Suction unit (portable and fixed)", category: "ems" },
  { key: "oxygen_main_ok", label: "Main O2 tank (level and regulator)", category: "ems" },
  { key: "oxygen_portable_ok", label: "Portable O2 (D-tank/level)", category: "ems" },
  { key: "monitor_defibrillator_ok", label: "Cardiac monitor/defibrillator", category: "ems" },
  { key: "drug_box_sealed_ok", label: "Drug box sealed/intact", category: "ems" },
  { key: "airway_bag_ok", label: "Airway bag (BVM, airways, intubation)", category: "ems" },
  { key: "trauma_bag_ok", label: "Trauma bag (dressings, splints)", category: "ems" },
  { key: "iv_supplies_ok", label: "IV supplies and fluids", category: "ems" },
  { key: "splinting_ok", label: "Splinting equipment", category: "ems" },
  { key: "stair_chair_ok", label: "Stair chair", category: "ems" },
  { key: "backboard_ok", label: "Backboard and head blocks", category: "ems" },
  { key: "c_collar_ok", label: "Cervical collars (all sizes)", category: "ems" },
];

const FIRE_CHECKS: CheckItem[] = [
  { key: "pump_ok", label: "Pump operation", category: "fire" },
  { key: "pump_gauges_ok", label: "Pump panel gauges", category: "fire" },
  { key: "aerial_ok", label: "Aerial device operation", category: "fire" },
  { key: "ground_ladders_ok", label: "Ground ladders secured", category: "fire" },
  { key: "hose_loads_ok", label: "Hose loads (all beds)", category: "fire" },
  { key: "scba_ok", label: "SCBA units (4500 PSI/masks)", category: "fire" },
  { key: "nozzles_ok", label: "Nozzles and appliances", category: "fire" },
  { key: "hand_tools_ok", label: "Hand tools (axes, Halligan, pike)", category: "fire" },
  { key: "forcible_entry_ok", label: "Forcible entry equipment", category: "fire" },
  { key: "vent_equipment_ok", label: "Ventilation equipment (fans, saws)", category: "fire" },
  { key: "rope_rescue_ok", label: "Rope and rescue equipment", category: "fire" },
  { key: "thermal_camera_ok", label: "Thermal imaging camera", category: "fire" },
];

function DVIRClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedVehicle = searchParams.get("vehicle");

  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<string>(preselectedVehicle || "");
  const [inspectionType, setInspectionType] = useState<"pre_trip" | "post_trip">("pre_trip");
  const [odometer, setOdometer] = useState("");
  const [checks, setChecks] = useState<Record<string, boolean | null>>({});
  const [defectNotes, setDefectNotes] = useState("");
  const [safeToOperate, setSafeToOperate] = useState(true);
  const [signature, setSignature] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [vehicleType, setVehicleType] = useState<"ambulance" | "fire" | "other">("ambulance");
  const [recentDVIRs, setRecentDVIRs] = useState<any[]>([]);

  useEffect(() => {
    fetch("/api/fleet/vehicles")
      .then((r) => r.json())
      .then(setVehicles);
    fetch("/api/fleet/dvir?limit=10")
      .then((r) => r.json())
      .then(setRecentDVIRs);
  }, []);

  useEffect(() => {
    const vehicle = vehicles.find((v) => String(v.id) === selectedVehicle);
    if (vehicle) {
      const type = vehicle.vehicle_type.toLowerCase();
      if (type.includes("ambulance") || type === "als" || type === "bls" || type.includes("medic")) {
        setVehicleType("ambulance");
      } else if (type.includes("engine") || type.includes("ladder") || type.includes("rescue") || type.includes("tanker")) {
        setVehicleType("fire");
      } else {
        setVehicleType("other");
      }
    }
  }, [selectedVehicle, vehicles]);

  useEffect(() => {
    const initial: Record<string, boolean | null> = {};
    DOT_CHECKS.forEach((c) => (initial[c.key] = true));
    if (vehicleType === "ambulance") {
      EMS_CHECKS.forEach((c) => (initial[c.key] = true));
    } else if (vehicleType === "fire") {
      FIRE_CHECKS.forEach((c) => (initial[c.key] = true));
    }
    setChecks(initial);
  }, [vehicleType]);

  const toggleCheck = (key: string) => {
    setChecks((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const hasDefects = Object.values(checks).some((v) => v === false);

  const handleSubmit = async () => {
    if (!selectedVehicle || !signature) {
      alert("Please select a vehicle and provide your signature");
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        vehicle_id: parseInt(selectedVehicle),
        inspection_type: inspectionType,
        odometer: parseInt(odometer) || 0,
        ...checks,
        defects_found: hasDefects,
        defect_description: hasDefects ? defectNotes : "",
        vehicle_safe_to_operate: safeToOperate,
        driver_signature: signature,
      };
      const res = await fetch("/api/fleet/dvir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        router.push("/fleet");
      } else {
        alert("Failed to submit DVIR");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const renderCheckSection = (title: string, items: CheckItem[], icon: string) => (
    <div className="bg-white rounded-lg shadow mb-4">
      <div className="p-4 border-b bg-gray-50 flex items-center gap-2">
        <span className="text-xl">{icon}</span>
        <h3 className="font-semibold">{title}</h3>
        <span className="ml-auto text-sm text-gray-500">{items.length} items</span>
      </div>
      <div className="p-4 grid md:grid-cols-2 gap-2">
        {items.map((item) => (
          <button
            key={item.key}
            onClick={() => toggleCheck(item.key)}
            className={`flex items-center gap-3 p-3 rounded-lg border text-left transition-all ${
              checks[item.key] === true
                ? "border-green-300 bg-green-50"
                : checks[item.key] === false
                ? "border-red-300 bg-red-50"
                : "border-gray-200 bg-gray-50"
            }`}
          >
            <div
              className={`w-6 h-6 rounded flex items-center justify-center text-sm font-bold ${
                checks[item.key] === true
                  ? "bg-green-500 text-white"
                  : checks[item.key] === false
                  ? "bg-red-500 text-white"
                  : "bg-gray-300 text-gray-600"
              }`}
            >
              {checks[item.key] === true ? "✓" : checks[item.key] === false ? "✗" : "?"}
            </div>
            <span className={`text-sm ${checks[item.key] === false ? "text-red-700 font-medium" : ""}`}>
              {item.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100 p-4 md:p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <Link href="/fleet" className="text-blue-600 hover:underline text-sm mb-1 block">
              ← Back to Fleet
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">Driver Vehicle Inspection Report</h1>
            <p className="text-gray-600 text-sm">DOT-Compliant Pre/Post Trip Inspection</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow mb-4 p-4">
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Vehicle</label>
              <select
                value={selectedVehicle}
                onChange={(e) => setSelectedVehicle(e.target.value)}
                className="w-full border rounded-lg px-3 py-2"
              >
                <option value="">Select Vehicle...</option>
                {vehicles.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.call_sign || v.vehicle_id} - {v.vehicle_type}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Inspection Type</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setInspectionType("pre_trip")}
                  className={`flex-1 py-2 px-4 rounded-lg border font-medium ${
                    inspectionType === "pre_trip"
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-gray-700 border-gray-300"
                  }`}
                >
                  Pre-Trip
                </button>
                <button
                  onClick={() => setInspectionType("post_trip")}
                  className={`flex-1 py-2 px-4 rounded-lg border font-medium ${
                    inspectionType === "post_trip"
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-gray-700 border-gray-300"
                  }`}
                >
                  Post-Trip
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Odometer Reading</label>
              <input
                type="number"
                value={odometer}
                onChange={(e) => setOdometer(e.target.value)}
                placeholder="Current mileage"
                className="w-full border rounded-lg px-3 py-2"
              />
            </div>
          </div>
        </div>

        {selectedVehicle && (
          <>
            {renderCheckSection("DOT Required Checks (49 CFR 396.11)", DOT_CHECKS, "📋")}

            {vehicleType === "ambulance" && renderCheckSection("EMS Equipment Checks", EMS_CHECKS, "🚑")}

            {vehicleType === "fire" && renderCheckSection("Fire Apparatus Checks", FIRE_CHECKS, "🚒")}

            {hasDefects && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xl">⚠️</span>
                  <h3 className="font-semibold text-red-800">Defects Noted</h3>
                </div>
                <p className="text-sm text-red-700 mb-3">
                  {Object.entries(checks)
                    .filter(([, v]) => v === false)
                    .map(([k]) => {
                      const item = [...DOT_CHECKS, ...EMS_CHECKS, ...FIRE_CHECKS].find((c) => c.key === k);
                      return item?.label;
                    })
                    .join(", ")}
                </p>
                <div className="mb-3">
                  <label className="block text-sm font-medium text-red-800 mb-1">Describe Defects</label>
                  <textarea
                    value={defectNotes}
                    onChange={(e) => setDefectNotes(e.target.value)}
                    rows={3}
                    placeholder="Describe each defect in detail..."
                    className="w-full border border-red-300 rounded-lg px-3 py-2"
                  />
                </div>
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={safeToOperate}
                      onChange={(e) => setSafeToOperate(e.target.checked)}
                      className="w-5 h-5"
                    />
                    <span className="text-sm font-medium text-red-800">Vehicle is safe to operate with noted defects</span>
                  </label>
                </div>
              </div>
            )}

            <div className="bg-white rounded-lg shadow p-4 mb-4">
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Driver Signature</label>
                  <input
                    type="text"
                    value={signature}
                    onChange={(e) => setSignature(e.target.value)}
                    placeholder="Type your full name as signature"
                    className="w-full border rounded-lg px-3 py-2"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    By signing, I certify this vehicle has been inspected in accordance with DOT regulations 49 CFR 396.11
                  </p>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Link
                href="/fleet"
                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
              >
                Cancel
              </Link>
              <button
                onClick={handleSubmit}
                disabled={submitting || !signature}
                className={`flex-1 py-3 rounded-lg font-medium ${
                  hasDefects && !safeToOperate
                    ? "bg-red-600 hover:bg-red-700 text-white"
                    : "bg-green-600 hover:bg-green-700 text-white"
                } disabled:opacity-50`}
              >
                {submitting
                  ? "Submitting..."
                  : hasDefects && !safeToOperate
                  ? "Submit - OUT OF SERVICE"
                  : "Submit DVIR - Vehicle Approved"}
              </button>
            </div>
          </>
        )}

        {recentDVIRs.length > 0 && (
          <div className="mt-8 bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h3 className="font-semibold">Recent DVIR Inspections</h3>
            </div>
            <div className="divide-y">
              {recentDVIRs.slice(0, 5).map((dvir) => (
                <div key={dvir.id} className="p-4 flex items-center justify-between">
                  <div>
                    <div className="font-medium">Vehicle #{dvir.vehicle_id}</div>
                    <div className="text-sm text-gray-500">
                      {dvir.inspection_type.replace("_", "-")} | {dvir.driver_name} |{" "}
                      {new Date(dvir.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {dvir.defects_found ? (
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        dvir.defects_corrected
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}>
                        {dvir.defects_corrected ? "Corrected" : "Defects Pending"}
                      </span>
                    ) : (
                      <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                        Pass
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function DVIRPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-zinc-950" />}>
      <DVIRClient />
    </Suspense>
  );
}
