"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ClipboardCheck, CheckCircle, XCircle, Clock } from "lucide-react";

export default function RigChecksPage() {
  const [checks, setChecks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/inventory/rig-checks", { credentials: "include" })
      .then((r) => r.ok && r.json())
      .then((data) => setChecks(data || []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center"><div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">Rig Checks</h1>
          <button className="px-6 py-2 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-lg flex items-center gap-2"><ClipboardCheck size={20} />New Check</button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {checks.length === 0 ? <div className="col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl p-12 text-center"><ClipboardCheck size={64} className="mx-auto mb-4 text-zinc-600" /><p className="text-zinc-500">No rig checks recorded</p></div> : checks.map((check) => (
            <motion.div key={check.id} whileHover={{ y: -2 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <div className="flex items-start justify-between mb-4">
                <div><h3 className="text-xl font-bold">{check.unit_name}</h3><p className="text-sm text-zinc-400">By {check.checked_by_name}</p></div>
                <div className={`p-3 rounded-xl ${check.passed ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>{check.passed ? <CheckCircle className="text-emerald-400" size={24} /> : <XCircle className="text-red-400" size={24} />}</div>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-zinc-400">Date:</span><span>{new Date(check.check_date).toLocaleDateString()}</span></div>
                <div className="flex justify-between"><span className="text-zinc-400">Items Checked:</span><span>{check.items_checked || 0}</span></div>
                {check.notes && <div className="pt-3 border-t border-zinc-800 text-zinc-400">{check.notes}</div>}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
