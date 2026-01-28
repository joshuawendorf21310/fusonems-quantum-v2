"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Filter, Download } from "lucide-react";

export default function MovementsPage() {
  const [movements, setMovements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    const params = new URLSearchParams();
    if (filter !== "all") params.set("type", filter);
    fetch(`/api/inventory/movements?${params}`, { credentials: "include" })
      .then((r) => r.ok && r.json())
      .then((data) => setMovements(data || []))
      .finally(() => setLoading(false));
  }, [filter]);

  if (loading) return <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center"><div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">Stock Movements</h1>
          <button className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700 flex items-center gap-2"><Download size={20} />Export</button>
        </div>

        <div className="flex gap-2">{["all", "in", "out", "adjustment"].map((type) => (<button key={type} onClick={() => setFilter(type)} className={`px-6 py-3 rounded-lg font-medium capitalize ${filter === type ? 'bg-gradient-to-r from-blue-600 to-emerald-600' : 'bg-zinc-800 hover:bg-zinc-700'}`}>{type}</button>))}</div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-zinc-800 border-b border-zinc-700"><tr><th className="px-6 py-4 text-left text-sm font-semibold">Date</th><th className="px-6 py-4 text-left text-sm font-semibold">Item</th><th className="px-6 py-4 text-left text-sm font-semibold">Type</th><th className="px-6 py-4 text-left text-sm font-semibold">Quantity</th><th className="px-6 py-4 text-left text-sm font-semibold">Location</th><th className="px-6 py-4 text-left text-sm font-semibold">By</th></tr></thead>
            <tbody className="divide-y divide-zinc-800">{movements.length === 0 ? <tr><td colSpan={6} className="px-6 py-12 text-center text-zinc-500">No movements found</td></tr> : movements.map((mov) => (<tr key={mov.id} className="hover:bg-zinc-800/50"><td className="px-6 py-4 text-sm">{new Date(mov.movement_date).toLocaleDateString()}</td><td className="px-6 py-4 font-medium">{mov.item_name}</td><td className="px-6 py-4"><span className={`px-3 py-1 rounded-lg text-xs ${mov.movement_type === 'in' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>{mov.movement_type}</span></td><td className="px-6 py-4 font-bold">{mov.quantity}</td><td className="px-6 py-4 text-sm text-zinc-400">{mov.location_name || 'N/A'}</td><td className="px-6 py-4 text-sm text-zinc-400">{mov.performed_by_name}</td></tr>))}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
