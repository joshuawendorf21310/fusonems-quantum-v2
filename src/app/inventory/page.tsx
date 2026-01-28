"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface DashboardStats {
  total_items: number;
  low_stock_items: number;
  out_of_stock_items: number;
  controlled_items: number;
  expired_lots: number;
  expiring_30_days: number;
  expiring_90_days: number;
  controlled_transactions_today: number;
  total_inventory_value: number;
}

interface InventoryItem {
  id: number;
  name: string;
  category: string;
  sku: string;
  quantity_on_hand: number;
  par_level: number;
  reorder_point: number;
  is_controlled: boolean;
  dea_schedule: string | null;
  unit_cost: number;
  is_critical: boolean;
}

interface ExpiringLot {
  id: number;
  item_id: number;
  lot_number: string;
  expiration_date: string;
  quantity: number;
  item_name: string;
  days_until_expiration: number;
  is_expired: boolean;
  value_at_risk: number;
}

const CATEGORIES = [
  { value: "medication", label: "Medications", icon: "💊" },
  { value: "supply", label: "Supplies", icon: "🩹" },
  { value: "equipment", label: "Equipment", icon: "🔧" },
  { value: "airway", label: "Airway", icon: "🫁" },
  { value: "cardiac", label: "Cardiac", icon: "❤️" },
  { value: "trauma", label: "Trauma", icon: "🩸" },
  { value: "iv", label: "IV/Fluids", icon: "💉" },
  { value: "ppe", label: "PPE", icon: "🧤" },
];

export default function InventoryPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [expiring, setExpiring] = useState<ExpiringLot[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [showLowStock, setShowLowStock] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch("/api/inventory/dashboard").then((r) => r.json()),
      fetch("/api/inventory/items?limit=50").then((r) => r.json()),
      fetch("/api/inventory/lots/expiring?days=30").then((r) => r.json()),
    ])
      .then(([statsData, itemsData, expiringData]) => {
        setStats(statsData);
        setItems(itemsData);
        setExpiring(expiringData);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (category) params.set("category", category);
    if (showLowStock) params.set("low_stock", "true");
    fetch(`/api/inventory/items?${params.toString()}&limit=100`)
      .then((r) => r.json())
      .then(setItems);
  }, [search, category, showLowStock]);

  const getStockStatus = (item: InventoryItem) => {
    if (item.quantity_on_hand === 0) return { label: "Out", color: "bg-red-100 text-red-800" };
    if (item.quantity_on_hand <= item.reorder_point) return { label: "Low", color: "bg-yellow-100 text-yellow-800" };
    return { label: "OK", color: "bg-green-100 text-green-800" };
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-zinc-100">Inventory Management</h1>
            <p className="text-zinc-400">Par levels, expiration tracking, and controlled substances</p>
          </div>
          <div className="flex gap-2">
            <Link
              href="/inventory/controlled"
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium"
            >
              Controlled Substances
            </Link>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
              + Add Item
            </button>
          </div>
        </div>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
              <div className="text-3xl font-bold text-zinc-100">{stats.total_items}</div>
              <div className="text-sm text-zinc-400">Total Items</div>
            </div>
            <Link href="/inventory?low_stock=true" className="bg-white rounded-lg shadow p-4 hover:shadow-md">
              <div className="text-3xl font-bold text-yellow-600">{stats.low_stock_items}</div>
              <div className="text-sm text-gray-600">Low Stock</div>
            </Link>
            <Link href="/inventory?low_stock=true" className="bg-white rounded-lg shadow p-4 hover:shadow-md">
              <div className="text-3xl font-bold text-red-600">{stats.out_of_stock_items}</div>
              <div className="text-sm text-gray-600">Out of Stock</div>
            </Link>
            <Link href="/inventory/expiring" className="bg-white rounded-lg shadow p-4 hover:shadow-md">
              <div className="text-3xl font-bold text-orange-600">{stats.expiring_30_days}</div>
              <div className="text-sm text-gray-600">Expiring 30d</div>
            </Link>
            <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
              <div className="text-3xl font-bold text-green-600">${stats.total_inventory_value.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Total Value</div>
            </div>
          </div>
        )}

        <div className="grid md:grid-cols-4 gap-4 mb-6">
          <Link href="/inventory/controlled" className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-3">
              <div className="text-3xl">🔒</div>
              <div>
                <h3 className="font-semibold">Controlled Substances</h3>
                <p className="text-sm text-gray-600">{stats?.controlled_items || 0} items tracked</p>
                <p className="text-xs text-purple-600 mt-1">{stats?.controlled_transactions_today || 0} transactions today</p>
              </div>
            </div>
          </Link>
          <Link href="/inventory/expiring" className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-3">
              <div className="text-3xl">⏰</div>
              <div>
                <h3 className="font-semibold">Expiration Tracking</h3>
                <p className="text-sm text-gray-600">{stats?.expired_lots || 0} expired lots</p>
                <p className="text-xs text-orange-600 mt-1">{stats?.expiring_90_days || 0} expiring in 90 days</p>
              </div>
            </div>
          </Link>
          <Link href="/inventory/reorder" className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-3">
              <div className="text-3xl">📦</div>
              <div>
                <h3 className="font-semibold">Reorder Management</h3>
                <p className="text-sm text-gray-600">Smart suggestions</p>
                <p className="text-xs text-blue-600 mt-1">Based on usage patterns</p>
              </div>
            </div>
          </Link>
          <Link href="/inventory/kits" className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-3">
              <div className="text-3xl">🎒</div>
              <div>
                <h3 className="font-semibold">Supply Kits</h3>
                <p className="text-sm text-gray-600">Kit management</p>
                <p className="text-xs text-gray-500 mt-1">Trauma, airway, cardiac</p>
              </div>
            </div>
          </Link>
        </div>

        {expiring.length > 0 && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">⚠️</span>
              <h3 className="font-semibold text-orange-800">Expiring Soon</h3>
              <Link href="/inventory/expiring" className="ml-auto text-sm text-orange-600 hover:underline">
                View All
              </Link>
            </div>
            <div className="grid md:grid-cols-3 gap-3">
              {expiring.slice(0, 6).map((lot) => (
                <div
                  key={lot.id}
                  className={`p-3 rounded-lg ${lot.is_expired ? "bg-red-100" : "bg-orange-100"}`}
                >
                  <div className="font-medium text-sm">{lot.item_name}</div>
                  <div className="text-xs text-gray-600">Lot: {lot.lot_number}</div>
                  <div className={`text-xs font-medium mt-1 ${lot.is_expired ? "text-red-700" : "text-orange-700"}`}>
                    {lot.is_expired ? "EXPIRED" : `${lot.days_until_expiration} days left`}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex-1 min-w-[200px]">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by name, SKU, or barcode..."
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="border rounded-lg px-3 py-2"
              >
                <option value="">All Categories</option>
                {CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.icon} {cat.label}
                  </option>
                ))}
              </select>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showLowStock}
                  onChange={(e) => setShowLowStock(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Low Stock Only</span>
              </label>
            </div>
          </div>

          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 text-left text-sm text-gray-600">
                  <tr>
                    <th className="px-4 py-3">Item</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">SKU</th>
                    <th className="px-4 py-3 text-center">On Hand</th>
                    <th className="px-4 py-3 text-center">Par</th>
                    <th className="px-4 py-3 text-center">Status</th>
                    <th className="px-4 py-3 text-right">Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {items.map((item) => {
                    const status = getStockStatus(item);
                    return (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {item.is_controlled && <span title="Controlled">🔒</span>}
                            {item.is_critical && <span title="Critical">⚡</span>}
                            <div>
                              <div className="font-medium">{item.name}</div>
                              {item.dea_schedule && (
                                <span className="text-xs bg-purple-100 text-purple-800 px-1 rounded">
                                  Schedule {item.dea_schedule}
                                </span>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm capitalize">{item.category}</td>
                        <td className="px-4 py-3 text-sm font-mono text-gray-500">{item.sku}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`font-bold ${item.quantity_on_hand === 0 ? "text-red-600" : ""}`}>
                            {item.quantity_on_hand}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center text-gray-500">{item.par_level}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${status.color}`}>
                            {status.label}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-sm">
                          ${(item.quantity_on_hand * item.unit_cost).toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
