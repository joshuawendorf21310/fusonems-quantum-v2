"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { DollarSign, Calendar, Download, CheckCircle, Clock } from "lucide-react";

export default function PayrollPage() {
  const [payrollPeriods, setPayrollPeriods] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/hr/payroll/periods", { credentials: "include" })
      .then((r) => r.ok && r.json())
      .then((data) => setPayrollPeriods(data || []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center"><div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">Payroll Management</h1>
          <div className="flex gap-3">
            <button className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700 flex items-center gap-2"><Download size={20} />Export</button>
            <button className="px-6 py-2 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-lg">Process Payroll</button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[{label: "Current Period", value: "$156,200", icon: DollarSign}, {label: "Total Hours", value: "3,124", icon: Clock}, {label: "Employees Paid", value: "162", icon: CheckCircle}, {label: "Average Pay", value: "$965", icon: DollarSign}].map((stat, idx) => (
            <div key={idx} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6"><div className="flex items-center justify-between mb-2"><stat.icon className="text-blue-400" size={24} /><div className="text-2xl font-bold text-blue-400">{stat.value}</div></div><div className="text-sm text-zinc-400">{stat.label}</div></div>
          ))}
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-2xl font-bold mb-6">Payroll Periods</h2>
          <div className="space-y-4">
            {payrollPeriods.length === 0 ? <p className="text-zinc-500 text-center py-8">No payroll periods found</p> : payrollPeriods.map((period) => (
              <motion.div key={period.id} whileHover={{ x: 4 }} className="flex items-center justify-between p-4 bg-zinc-800 rounded-lg border border-zinc-700 hover:border-zinc-600">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-zinc-700 rounded-lg flex items-center justify-center"><Calendar size={24} className="text-blue-400" /></div>
                  <div><div className="font-semibold">{period.period_name}</div><div className="text-sm text-zinc-400">{new Date(period.start_date).toLocaleDateString()} - {new Date(period.end_date).toLocaleDateString()}</div></div>
                </div>
                <div className="text-right">
                  <div className="text-xl font-bold text-emerald-400">${period.total_amount?.toLocaleString()}</div>
                  <div className={`text-sm px-3 py-1 rounded-lg ${period.status === 'processed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-yellow-500/20 text-yellow-400'}`}>{period.status}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
