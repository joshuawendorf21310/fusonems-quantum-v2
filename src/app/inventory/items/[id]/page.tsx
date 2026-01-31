"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Package, TrendingUp, TrendingDown, Calendar } from "lucide-react";

export default function ItemDetailPage() {
  const params = useParams();
  const [item, setItem] = useState<any>(null);
  const [movements, setMovements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`/api/inventory/items/${params.id}`, { credentials: "include" }),
      fetch(`/api/inventory/movements?item_id=${params.id}`, { credentials: "include" })
    ]).then(([itemRes, movementsRes]) => {
      if (itemRes.ok) itemRes.json().then(setItem);
      if (movementsRes.ok) movementsRes.json().then(setMovements);
    }).finally(() => setLoading(false));
  }, [params.id]);

  if (loading) return <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center"><div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div></div>;
  if (!item) return <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6"><div className="text-center">Item not found</div></div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <Link href="/inventory/items" className="inline-flex items-center gap-2 text-zinc-400 hover:text-zinc-100"><ArrowLeft size={20} />Back to Items</Link>
        
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8">
          <div className="flex gap-6">
            <div className="w-24 h-24 bg-zinc-800 rounded-xl flex items-center justify-center"><Package size={48} className="text-blue-400" /></div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold">{item.name}</h1>
              <p className="text-zinc-400">{item.description}</p>
              <div className="grid grid-cols-4 gap-4 mt-6">
                <div><div className="text-sm text-zinc-400">SKU</div><div className="font-mono text-lg">{item.sku}</div></div>
                <div><div className="text-sm text-zinc-400">On Hand</div><div className="text-2xl font-bold text-blue-400">{item.quantity_on_hand}</div></div>
                <div><div className="text-sm text-zinc-400">Par Level</div><div className="text-lg">{item.par_level}</div></div>
                <div><div className="text-sm text-zinc-400">Unit Cost</div><div className="text-lg">${item.unit_cost}</div></div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-2xl font-bold mb-6">Movement History</h2>
          <div className="space-y-3">
            {movements.length === 0 ? <p className="text-zinc-500 text-center py-8">No movements recorded</p> : movements.map((mov) => (
              <div key={mov.id} className="flex items-center gap-4 p-4 bg-zinc-800 rounded-lg">
                <div className={`p-3 rounded-lg ${mov.movement_type === 'in' ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
                  {mov.movement_type === 'in' ? <TrendingUp className="text-emerald-400" size={20} /> : <TrendingDown className="text-red-400" size={20} />}
                </div>
                <div className="flex-1">
                  <div className="font-semibold">{mov.movement_type === 'in' ? 'Received' : 'Dispensed'}: {mov.quantity} units</div>
                  <div className="text-sm text-zinc-400">{mov.notes || 'No notes'}</div>
                </div>
                <div className="text-sm text-zinc-400 flex items-center gap-2"><Calendar size={14} />{new Date(mov.movement_date).toLocaleDateString()}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
