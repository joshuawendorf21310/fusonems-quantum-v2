"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Calendar, Clock, Check, X, AlertCircle } from "lucide-react";

export default function LeavePage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/hr/leave/requests", { credentials: "include" })
      .then((r) => r.ok && r.json())
      .then((data) => setRequests(data || []))
      .finally(() => setLoading(false));
  }, []);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "approved": return "bg-emerald-500/20 text-emerald-400 border-emerald-500";
      case "pending": return "bg-yellow-500/20 text-yellow-400 border-yellow-500";
      case "denied": return "bg-red-500/20 text-red-400 border-red-500";
      default: return "bg-zinc-500/20 text-zinc-400 border-zinc-500";
    }
  };

  if (loading) return <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center"><div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">Leave Management</h1>
          <button className="px-6 py-2 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-lg">Request Leave</button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[{label: "Total Requests", value: requests.length}, {label: "Pending", value: requests.filter(r => r.status === "pending").length}, {label: "Approved", value: requests.filter(r => r.status === "approved").length}, {label: "Denied", value: requests.filter(r => r.status === "denied").length}].map((stat, idx) => (
            <div key={idx} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6"><div className="text-3xl font-bold text-blue-400">{stat.value}</div><div className="text-sm text-zinc-400 mt-1">{stat.label}</div></div>
          ))}
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-zinc-800 border-b border-zinc-700"><tr><th className="px-6 py-4 text-left text-sm font-semibold">Employee</th><th className="px-6 py-4 text-left text-sm font-semibold">Leave Type</th><th className="px-6 py-4 text-left text-sm font-semibold">Start Date</th><th className="px-6 py-4 text-left text-sm font-semibold">End Date</th><th className="px-6 py-4 text-left text-sm font-semibold">Status</th></tr></thead>
            <tbody className="divide-y divide-zinc-800">{requests.length === 0 ? <tr><td colSpan={5} className="px-6 py-12 text-center text-zinc-500">No leave requests</td></tr> : requests.map((req) => (<tr key={req.id} className="hover:bg-zinc-800/50"><td className="px-6 py-4">{req.personnel_name}</td><td className="px-6 py-4">{req.leave_type}</td><td className="px-6 py-4">{new Date(req.start_date).toLocaleDateString()}</td><td className="px-6 py-4">{new Date(req.end_date).toLocaleDateString()}</td><td className="px-6 py-4"><span className={`px-3 py-1 rounded-lg border text-xs font-medium ${getStatusColor(req.status)}`}>{req.status}</span></td></tr>))}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
