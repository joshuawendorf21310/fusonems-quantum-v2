"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Search,
  Filter,
  UserPlus,
  Download,
  Mail,
  Phone,
  MapPin,
  Award,
  Calendar,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";

interface Personnel {
  id: number;
  employee_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  job_title: string;
  department: string | null;
  station_assignment: string | null;
  employment_status: string;
  hire_date: string;
  certifications_count: number;
  certifications_expiring: number;
}

export default function PersonnelDirectoryPage() {
  const [personnel, setPersonnel] = useState<Personnel[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("all");

  useEffect(() => {
    fetchPersonnel();
  }, [departmentFilter]);

  const fetchPersonnel = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (departmentFilter !== "all") params.set("department", departmentFilter);

      const res = await fetch(`/api/hr/personnel?${params}`, { credentials: "include" });
      if (res.ok) setPersonnel(await res.json());
    } catch (error) {
      console.error("Error fetching personnel:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "active":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500";
      case "on_leave":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500";
      case "inactive":
        return "bg-red-500/20 text-red-400 border-red-500";
      default:
        return "bg-zinc-500/20 text-zinc-400 border-zinc-500";
    }
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
          className="flex justify-between items-center"
        >
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
              Personnel Directory
            </h1>
            <p className="text-zinc-400 mt-2">{personnel.length} total personnel</p>
          </div>
          <div className="flex gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700 flex items-center gap-2"
            >
              <Download size={20} />
              Export
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-lg flex items-center gap-2"
            >
              <UserPlus size={20} />
              Add Personnel
            </motion.button>
          </div>
        </motion.div>

        {/* Search and Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"
        >
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400" size={20} />
              <input
                type="text"
                placeholder="Search by name, employee ID, or email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchPersonnel()}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Departments</option>
              <option value="Operations">Operations</option>
              <option value="Medical">Medical</option>
              <option value="Admin">Admin</option>
              <option value="Fire">Fire</option>
            </select>
          </div>
        </motion.div>

        {/* Personnel Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {personnel.map((person, idx) => (
            <motion.div
              key={person.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + idx * 0.02 }}
              whileHover={{ y: -4 }}
            >
              <Link href={`/hr/personnel/${person.id}`}>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-all cursor-pointer h-full">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center text-lg font-bold">
                        {person.first_name[0]}{person.last_name[0]}
                      </div>
                      <div>
                        <h3 className="font-bold text-lg">
                          {person.first_name} {person.last_name}
                        </h3>
                        <p className="text-sm text-zinc-400">{person.employee_id}</p>
                      </div>
                    </div>
                  </div>

                  <div
                    className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg border text-xs font-medium mb-4 ${getStatusColor(
                      person.employment_status
                    )}`}
                  >
                    {person.employment_status.replace("_", " ")}
                  </div>

                  <div className="space-y-2 mb-4">
                    <div className="text-sm">
                      <span className="text-zinc-400">Position:</span>{" "}
                      <span className="font-medium">{person.job_title}</span>
                    </div>
                    {person.department && (
                      <div className="text-sm">
                        <span className="text-zinc-400">Department:</span>{" "}
                        <span className="font-medium">{person.department}</span>
                      </div>
                    )}
                    {person.station_assignment && (
                      <div className="text-sm">
                        <span className="text-zinc-400">Station:</span>{" "}
                        <span className="font-medium">{person.station_assignment}</span>
                      </div>
                    )}
                  </div>

                  <div className="space-y-2 pt-4 border-t border-zinc-800">
                    {person.email && (
                      <div className="flex items-center gap-2 text-sm text-zinc-400">
                        <Mail size={14} />
                        <span className="truncate">{person.email}</span>
                      </div>
                    )}
                    {person.phone && (
                      <div className="flex items-center gap-2 text-sm text-zinc-400">
                        <Phone size={14} />
                        {person.phone}
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-sm text-zinc-400">
                      <Calendar size={14} />
                      Hired: {new Date(person.hire_date).toLocaleDateString()}
                    </div>
                  </div>

                  {person.certifications_expiring > 0 && (
                    <div className="mt-4 pt-4 border-t border-zinc-800">
                      <div className="flex items-center gap-2 text-sm text-orange-400">
                        <AlertTriangle size={14} />
                        {person.certifications_expiring} certification(s) expiring soon
                      </div>
                    </div>
                  )}
                </div>
              </Link>
            </motion.div>
          ))}
        </motion.div>

        {personnel.length === 0 && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-12 text-center">
            <p className="text-zinc-500">No personnel found</p>
          </div>
        )}
      </div>
    </div>
  );
}
