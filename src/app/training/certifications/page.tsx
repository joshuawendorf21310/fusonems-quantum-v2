"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Award,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  Filter,
  RefreshCw,
  Search,
  Upload,
} from "lucide-react";

interface Certification {
  id: number;
  personnel_id: number;
  personnel_name: string;
  certification_type: string;
  certification_number: string;
  issuing_authority: string;
  issue_date: string;
  expiration_date: string;
  status: string;
  days_until_expiry: number;
}

export default function CertificationsPage() {
  const [certifications, setCertifications] = useState<Certification[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [stats, setStats] = useState({
    total: 0,
    current: 0,
    expiring_30: 0,
    expiring_60: 0,
    expired: 0,
  });

  useEffect(() => {
    fetchCertifications();
  }, [statusFilter]);

  const fetchCertifications = async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (search) params.set("search", search);

      const [certsRes, statsRes] = await Promise.all([
        fetch(`/api/training/certifications?${params}`, { credentials: "include" }),
        fetch("/api/training/certifications/stats", { credentials: "include" }),
      ]);

      if (certsRes.ok) setCertifications(await certsRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
    } catch (error) {
      console.error("Error fetching certifications:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (days: number) => {
    if (days < 0) return "bg-red-500/20 text-red-400 border-red-500";
    if (days < 30) return "bg-orange-500/20 text-orange-400 border-orange-500";
    if (days < 60) return "bg-yellow-500/20 text-yellow-400 border-yellow-500";
    return "bg-emerald-500/20 text-emerald-400 border-emerald-500";
  };

  const getStatusIcon = (days: number) => {
    if (days < 0) return <AlertTriangle size={16} />;
    if (days < 30) return <Clock size={16} />;
    return <CheckCircle size={16} />;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
        >
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
              Certifications Tracking
            </h1>
            <p className="text-zinc-400 mt-2">Monitor personnel certifications and compliance</p>
          </div>
          <div className="flex gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={fetchCertifications}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700 flex items-center gap-2"
            >
              <RefreshCw size={20} />
              Refresh
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700 flex items-center gap-2"
            >
              <Upload size={20} />
              Upload
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-lg flex items-center gap-2"
            >
              <Download size={20} />
              Export
            </motion.button>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {[
            { label: "Total Certifications", value: stats.total, color: "blue", icon: Award },
            { label: "Current", value: stats.current, color: "emerald", icon: CheckCircle },
            { label: "Expiring in 30 Days", value: stats.expiring_30, color: "orange", icon: AlertTriangle },
            { label: "Expiring in 60 Days", value: stats.expiring_60, color: "yellow", icon: Clock },
            { label: "Expired", value: stats.expired, color: "red", icon: AlertTriangle },
          ].map((stat, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              whileHover={{ y: -2 }}
              className={`bg-zinc-900 border border-zinc-800 rounded-xl p-4 cursor-pointer hover:border-${stat.color}-500/50`}
            >
              <div className="flex items-center justify-between mb-2">
                <stat.icon className={`text-${stat.color}-400`} size={24} />
                <div className={`text-2xl font-bold text-${stat.color}-400`}>{stat.value}</div>
              </div>
              <div className="text-sm text-zinc-400">{stat.label}</div>
            </motion.div>
          ))}
        </div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"
        >
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400" size={20} />
              <input
                type="text"
                placeholder="Search by name, certification type, or number..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchCertifications()}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="current">Current</option>
              <option value="expiring">Expiring Soon</option>
              <option value="expired">Expired</option>
            </select>
          </div>
        </motion.div>

        {/* Certifications Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden"
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-zinc-800 border-b border-zinc-700">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Personnel</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Certification</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Number</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Issuing Authority</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Issue Date</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Expiration</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {certifications.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-zinc-500">
                      No certifications found
                    </td>
                  </tr>
                ) : (
                  certifications.map((cert) => (
                    <motion.tr
                      key={cert.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="hover:bg-zinc-800/50 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <Link
                          href={`/hr/personnel/${cert.personnel_id}`}
                          className="text-blue-400 hover:text-blue-300"
                        >
                          {cert.personnel_name}
                        </Link>
                      </td>
                      <td className="px-6 py-4 font-medium">{cert.certification_type}</td>
                      <td className="px-6 py-4 font-mono text-sm text-zinc-400">
                        {cert.certification_number}
                      </td>
                      <td className="px-6 py-4 text-sm text-zinc-400">{cert.issuing_authority}</td>
                      <td className="px-6 py-4 text-sm">
                        {new Date(cert.issue_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {new Date(cert.expiration_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        <div
                          className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg border text-xs font-medium ${getStatusColor(
                            cert.days_until_expiry
                          )}`}
                        >
                          {getStatusIcon(cert.days_until_expiry)}
                          {cert.days_until_expiry < 0
                            ? "Expired"
                            : `${cert.days_until_expiry} days`}
                        </div>
                      </td>
                    </motion.tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
