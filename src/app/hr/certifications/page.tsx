'use client';

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Award,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Search,
  Filter,
  Download,
  Upload,
  Plus,
  Bell,
  Calendar,
  FileText,
  TrendingUp,
  Users,
  Shield,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// Mock certification data
const mockCertifications = [
  {
    id: 1,
    personnelId: 1,
    personnelName: 'John Doe',
    certificationType: 'Paramedic',
    certificationNumber: 'P-12345',
    issuingAuthority: 'State EMS Board',
    issueDate: '2020-01-15',
    expirationDate: '2025-01-15',
    daysUntilExpiry: 365,
    status: 'active',
    documentPath: '/docs/cert-001.pdf',
  },
  {
    id: 2,
    personnelId: 1,
    personnelName: 'John Doe',
    certificationType: 'ACLS',
    certificationNumber: 'ACLS-54321',
    issuingAuthority: 'American Heart Association',
    issueDate: '2023-06-20',
    expirationDate: '2025-06-20',
    daysUntilExpiry: 509,
    status: 'active',
    documentPath: '/docs/cert-002.pdf',
  },
  {
    id: 3,
    personnelId: 2,
    personnelName: 'Sarah Johnson',
    certificationType: 'EMT-B',
    certificationNumber: 'EMT-67890',
    issuingAuthority: 'State EMS Board',
    issueDate: '2021-03-10',
    expirationDate: '2024-03-10',
    daysUntilExpiry: -293,
    status: 'expired',
    documentPath: '/docs/cert-003.pdf',
  },
  {
    id: 4,
    personnelId: 3,
    personnelName: 'Michael Chen',
    certificationType: 'PHTLS',
    certificationNumber: 'PHTLS-11111',
    issuingAuthority: 'NAEMT',
    issueDate: '2022-09-15',
    expirationDate: '2024-09-15',
    daysUntilExpiry: -104,
    status: 'expired',
    documentPath: '/docs/cert-004.pdf',
  },
  {
    id: 5,
    personnelId: 4,
    personnelName: 'Emily Rodriguez',
    certificationType: 'FP-C',
    certificationNumber: 'FPC-22222',
    issuingAuthority: 'BCCTPC',
    issueDate: '2023-01-20',
    expirationDate: '2024-01-20',
    daysUntilExpiry: 15,
    status: 'expiring_soon',
    documentPath: '/docs/cert-005.pdf',
  },
  {
    id: 6,
    personnelId: 5,
    personnelName: 'David Thompson',
    certificationType: 'PALS',
    certificationNumber: 'PALS-33333',
    issuingAuthority: 'American Heart Association',
    issueDate: '2023-04-10',
    expirationDate: '2024-04-10',
    daysUntilExpiry: 28,
    status: 'expiring_soon',
    documentPath: '/docs/cert-006.pdf',
  },
];

const complianceData = [
  { month: 'Jul', compliance: 95, expiring: 8, expired: 2 },
  { month: 'Aug', compliance: 94, expiring: 10, expired: 3 },
  { month: 'Sep', compliance: 96, expiring: 6, expired: 2 },
  { month: 'Oct', compliance: 93, expiring: 12, expired: 4 },
  { month: 'Nov', compliance: 97, expiring: 5, expired: 1 },
  { month: 'Dec', compliance: 98, expiring: 3, expired: 1 },
];

const certTypeDistribution = [
  { name: 'Paramedic', value: 45, color: '#3b82f6' },
  { name: 'EMT', value: 62, color: '#10b981' },
  { name: 'ACLS/PALS', value: 85, color: '#f59e0b' },
  { name: 'Specialty', value: 28, color: '#8b5cf6' },
];

const CertificationsTracker = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState<'expiry' | 'name' | 'type'>('expiry');

  const filteredCertifications = useMemo(() => {
    let filtered = mockCertifications.filter((cert) => {
      const matchesSearch =
        cert.personnelName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        cert.certificationType.toLowerCase().includes(searchTerm.toLowerCase()) ||
        cert.certificationNumber.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus = filterStatus === 'all' || cert.status === filterStatus;
      const matchesType =
        filterType === 'all' || cert.certificationType === filterType;

      return matchesSearch && matchesStatus && matchesType;
    });

    // Sort
    if (sortBy === 'expiry') {
      filtered.sort((a, b) => a.daysUntilExpiry - b.daysUntilExpiry);
    } else if (sortBy === 'name') {
      filtered.sort((a, b) => a.personnelName.localeCompare(b.personnelName));
    } else if (sortBy === 'type') {
      filtered.sort((a, b) => a.certificationType.localeCompare(b.certificationType));
    }

    return filtered;
  }, [searchTerm, filterStatus, filterType, sortBy]);

  const certTypes = Array.from(
    new Set(mockCertifications.map((c) => c.certificationType))
  );

  const getStatusConfig = (status: string, daysUntilExpiry: number) => {
    if (status === 'expired' || daysUntilExpiry < 0) {
      return {
        color: 'bg-red-100 text-red-700 border-red-200',
        icon: XCircle,
        label: 'Expired',
      };
    } else if (status === 'expiring_soon' || daysUntilExpiry <= 30) {
      return {
        color: 'bg-orange-100 text-orange-700 border-orange-200',
        icon: AlertTriangle,
        label: 'Expiring Soon',
      };
    } else if (daysUntilExpiry <= 60) {
      return {
        color: 'bg-yellow-100 text-yellow-700 border-yellow-200',
        icon: Clock,
        label: 'Expiring 60d',
      };
    } else {
      return {
        color: 'bg-green-100 text-green-700 border-green-200',
        icon: CheckCircle,
        label: 'Active',
      };
    }
  };

  const stats = {
    total: mockCertifications.length,
    active: mockCertifications.filter((c) => c.daysUntilExpiry > 60).length,
    expiringSoon: mockCertifications.filter(
      (c) => c.daysUntilExpiry > 0 && c.daysUntilExpiry <= 60
    ).length,
    expired: mockCertifications.filter((c) => c.daysUntilExpiry < 0).length,
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-orange-50 to-amber-50 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent">
              Certification Tracker
            </h1>
            <p className="text-slate-600 mt-1">Compliance monitoring and management</p>
          </div>
          <div className="flex gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-4 py-2 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-orange-400 transition-colors flex items-center gap-2"
            >
              <Bell className="w-5 h-5" />
              <span>Send Reminders</span>
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-4 py-2 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-orange-400 transition-colors flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              <span>Export</span>
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-6 py-2 bg-gradient-to-r from-orange-600 to-amber-600 text-white rounded-xl shadow-lg hover:shadow-xl transition-shadow flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              <span>Add Certification</span>
            </motion.button>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            {
              label: 'Total Certifications',
              value: stats.total,
              icon: Award,
              color: 'blue',
              trend: '+8',
            },
            {
              label: 'Active & Current',
              value: stats.active,
              icon: CheckCircle,
              color: 'green',
              trend: '+5',
            },
            {
              label: 'Expiring Soon',
              value: stats.expiringSoon,
              icon: AlertTriangle,
              color: 'orange',
              trend: '-3',
            },
            {
              label: 'Expired',
              value: stats.expired,
              icon: XCircle,
              color: 'red',
              trend: '-2',
            },
          ].map((stat, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              whileHover={{ y: -4 }}
              className="bg-white rounded-2xl shadow-lg p-6 border border-slate-100"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-600 font-medium">{stat.label}</p>
                  <p className="text-3xl font-bold text-slate-900 mt-2">{stat.value}</p>
                  <p className="text-sm text-slate-500 mt-1">
                    <span className="text-green-600 font-medium">{stat.trend}</span> this
                    month
                  </p>
                </div>
                <div
                  className={`p-3 rounded-xl ${
                    stat.color === 'blue'
                      ? 'bg-blue-100 text-blue-600'
                      : stat.color === 'green'
                      ? 'bg-green-100 text-green-600'
                      : stat.color === 'orange'
                      ? 'bg-orange-100 text-orange-600'
                      : 'bg-red-100 text-red-600'
                  }`}
                >
                  <stat.icon className="w-6 h-6" />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Compliance Trend */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-2xl shadow-lg p-6 border border-slate-100"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Compliance Trend</h3>
                <p className="text-sm text-slate-600">6-month overview</p>
              </div>
              <TrendingUp className="w-5 h-5 text-green-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={complianceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="compliance"
                  stroke="#10b981"
                  strokeWidth={3}
                  name="Compliance %"
                />
                <Line
                  type="monotone"
                  dataKey="expiring"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  name="Expiring"
                />
                <Line
                  type="monotone"
                  dataKey="expired"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Expired"
                />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Certification Type Distribution */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-2xl shadow-lg p-6 border border-slate-100"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  Certification Distribution
                </h3>
                <p className="text-sm text-slate-600">By type</p>
              </div>
              <Shield className="w-5 h-5 text-blue-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={certTypeDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {certTypeDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Search and Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg p-6 border border-slate-100"
        >
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-[300px] relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search certifications..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-12 pr-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-orange-400 transition-colors"
              />
            </div>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:border-orange-400"
            >
              <option value="expiry">Sort by Expiry</option>
              <option value="name">Sort by Name</option>
              <option value="type">Sort by Type</option>
            </select>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowFilters(!showFilters)}
              className={`px-6 py-3 rounded-xl border transition-colors flex items-center gap-2 ${
                showFilters
                  ? 'bg-orange-100 border-orange-400 text-orange-700'
                  : 'bg-white border-slate-200 text-slate-700 hover:border-orange-400'
              }`}
            >
              <Filter className="w-5 h-5" />
              <span>Filters</span>
            </motion.button>
          </div>

          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate-200"
              >
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Status
                  </label>
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:border-orange-400"
                  >
                    <option value="all">All Statuses</option>
                    <option value="active">Active</option>
                    <option value="expiring_soon">Expiring Soon</option>
                    <option value="expired">Expired</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Type
                  </label>
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:outline-none focus:border-orange-400"
                  >
                    <option value="all">All Types</option>
                    {certTypes.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Certification Timeline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden"
        >
          <div className="p-6 border-b border-slate-100">
            <h3 className="text-lg font-bold text-slate-900">Certification Timeline</h3>
            <p className="text-sm text-slate-600 mt-1">
              {filteredCertifications.length} certifications found
            </p>
          </div>

          <div className="divide-y divide-slate-100">
            {filteredCertifications.map((cert, idx) => {
              const statusConfig = getStatusConfig(cert.status, cert.daysUntilExpiry);
              const StatusIcon = statusConfig.icon;

              return (
                <motion.div
                  key={cert.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  whileHover={{ backgroundColor: '#fffbeb' }}
                  className="p-6 cursor-pointer transition-colors"
                >
                  <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-xl ${statusConfig.color}`}>
                      <StatusIcon className="w-6 h-6" />
                    </div>

                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-bold text-slate-900">
                            {cert.certificationType}
                          </h4>
                          <p className="text-sm text-slate-600 mt-1">
                            {cert.personnelName} • {cert.certificationNumber}
                          </p>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium border ${statusConfig.color}`}
                        >
                          {statusConfig.label}
                        </span>
                      </div>

                      <div className="grid grid-cols-3 gap-4 mt-4">
                        <div>
                          <p className="text-xs text-slate-500">Issuing Authority</p>
                          <p className="text-sm font-medium text-slate-900 mt-1">
                            {cert.issuingAuthority}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500">Issue Date</p>
                          <p className="text-sm font-medium text-slate-900 mt-1">
                            {cert.issueDate}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500">Expiration Date</p>
                          <p className="text-sm font-medium text-slate-900 mt-1">
                            {cert.expirationDate}
                          </p>
                        </div>
                      </div>

                      <div className="mt-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-slate-400" />
                          <span className="text-sm text-slate-600">
                            {cert.daysUntilExpiry < 0
                              ? `Expired ${Math.abs(cert.daysUntilExpiry)} days ago`
                              : `${cert.daysUntilExpiry} days until expiry`}
                          </span>
                        </div>
                        <div className="flex gap-2">
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="px-4 py-2 bg-orange-100 text-orange-700 rounded-lg text-sm font-medium hover:bg-orange-200 transition-colors"
                          >
                            <FileText className="w-4 h-4 inline mr-1" />
                            View Document
                          </motion.button>
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-200 transition-colors"
                          >
                            Send Reminder
                          </motion.button>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default CertificationsTracker;
