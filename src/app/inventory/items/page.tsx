"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { Search, Filter, Package } from "lucide-react";

export default function InventoryItemsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    fetch(`/api/inventory/items?${params}`, { credentials: "include" })
      .then((r) => r.ok && r.json())
      .then((data) => setItems(data || []))
      .finally(() => setLoading(false));
  }, [search]);

  const getStockStatus = (item: any) => {
    if (item.quantity_on_hand === 0) return { label: "Out", color: "bg-red-500/20 text-red-400" };
    if (item.quantity_on_hand <= item.reorder_point) return { label: "Low", color: "bg-yellow-500/20 text-yellow-400" };
    return { label: "OK", color: "bg-emerald-500/20 text-emerald-400" };
  };

  if (loading) return <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center"><div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">Inventory Items</h1>
          <button className="px-6 py-2 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-lg">Add Item</button>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400" size={20} />
            <input type="text" placeholder="Search items..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full bg-zinc-800 border border-zinc-700 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-blue-500" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {items.map((item) => {
            const status = getStockStatus(item);
            return (
              <Link key={item.id} href={`/inventory/items/${item.id}`}>
                <motion.div whileHover={{ y: -4 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 cursor-pointer">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-zinc-800 rounded-lg flex items-center justify-center"><Package size={24} className="text-blue-400" /></div>
                    <div className="flex-1 min-w-0"><h3 className="font-bold truncate">{item.name}</h3><p className="text-xs text-zinc-500">{item.sku}</p></div>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-zinc-400">On Hand:</span><span className="font-bold">{item.quantity_on_hand}</span></div>
                    <div className="flex justify-between"><span className="text-zinc-400">Par Level:</span><span>{item.par_level}</span></div>
                    <div className="flex justify-between"><span className="text-zinc-400">Status:</span><span className={`px-2 py-1 rounded text-xs ${status.color}`}>{status.label}</span></div>
                  </div>
                </motion.div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
