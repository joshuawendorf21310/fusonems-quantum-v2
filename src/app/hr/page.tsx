'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  TrendingUp,
  TrendingDown,
  Award,
  Calendar,
  DollarSign,
  AlertTriangle,
  Clock,
  UserPlus,
  FileText,
  BarChart3,
  Activity,
  Download,
  RefreshCw,
  Filter,
  ChevronRight,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// Mock data for dashboard
const headcountData = [
  { month: 'Jan', total: 145, active: 140, onLeave: 5 },
  { month: 'Feb', total: 148, active: 142, onLeave: 6 },
  { month: 'Mar', total: 152, active: 148, onLeave: 4 },
  { month: 'Apr', total: 155, active: 150, onLeave: 5 },
  { month: 'May', total: 158, active: 153, onLeave: 5 },
  { month: 'Jun', total: 162, active: 157, onLeave: 5 },
];

const departmentData = [
  { name: 'Operations', value: 85, color: '#3b82f6' },
  { name: 'Medical', value: 45, color: '#10b981' },
  { name: 'Admin', value: 15, color: '#f59e0b' },
  { name: 'Fire', value: 17, color: '#ef4444' },
];

const certificationExpiry = [
  { status: 'Current', count: 142, color: '#10b981' },
  { status: 'Expiring 30d', count: 12, color: '#f59e0b' },
  { status: 'Expiring 60d', count: 18, color: '#fbbf24' },
  { status: 'Expired', count: 3, color: '#ef4444' },
];

const payrollTrend = [
  { period: 'Jan 1-15', amount: 142500, hours: 2850 },
  { period: 'Jan 16-31', amount: 145800, hours: 2916 },
  { period: 'Feb 1-15', amount: 148200, hours: 2964 },
  { period: 'Feb 16-28', amount: 151000, hours: 3020 },
  { period: 'Mar 1-15', amount: 153600, hours: 3072 },
  { period: 'Mar 16-31', amount: 156200, hours: 3124 },
];

const HRDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [timeRange, setTimeRange] = useState('6m');

  useEffect(() => {
    setTimeout(() => setLoading(false), 800);
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1000);
  };

  const handleExport = () => {
    console.log('Exporting dashboard data...');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-zinc-900 rounded-2xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
              HR Dashboard
            </h1>
            <p className="text-zinc-400 mt-1">Personnel management and analytics</p>
          </div>
          <div className="flex gap-3">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl hover:border-blue-400 transition-colors"
            >
              <option value="1m">Last Month</option>
              <option value="3m">Last 3 Months</option>
              <option value="6m">Last 6 Months</option>
              <option value="1y">Last Year</option>
            </select>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleRefresh}
              className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl hover:border-blue-400 transition-colors"
            >
              <RefreshCw className={`w-5 h-5 text-slate-600 ${refreshing ? 'animate-spin' : ''}`} />
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleExport}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl shadow-lg hover:shadow-xl transition-shadow"
            >
              <Download className="w-5 h-5" />
            </motion.button>
          </div>
        </motion.div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              title: 'Total Personnel',
              value: '162',
              change: '+3.8%',
              trend: 'up',
              icon: Users,
              color: 'blue',
            },
            {
              title: 'Active Certifications',
              value: '142',
              change: '+5.2%',
              trend: 'up',
              icon: Award,
              color: 'green',
            },
            {
              title: 'Expiring Soon',
              value: '30',
              change: '-12%',
              trend: 'down',
              icon: AlertTriangle,
              color: 'orange',
            },
            {
              title: 'Payroll This Period',
              value: '$156.2K',
              change: '+2.1%',
              trend: 'up',
              icon: DollarSign,
              color: 'purple',
            },
          ].map((kpi, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              whileHover={{ y: -4, shadow: '0 20px 40px rgba(0,0,0,0.1)' }}
              className="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 hover:border-zinc-700 transition-all"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-zinc-400 font-medium">{kpi.title}</p>
                  <p className="text-3xl font-bold text-zinc-100 mt-2">{kpi.value}</p>
                  <div className="flex items-center gap-1 mt-2">
                    {kpi.trend === 'up' ? (
                      <TrendingUp className="w-4 h-4 text-green-500" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-red-500" />
                    )}
                    <span
                      className={`text-sm font-medium ${
                        kpi.trend === 'up' ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {kpi.change}
                    </span>
                    <span className="text-xs text-slate-500 ml-1">vs last period</span>
                  </div>
                </div>
                <div
                  className={`p-3 rounded-xl bg-gradient-to-br ${
                    kpi.color === 'blue'
                      ? 'from-blue-500 to-blue-600'
                      : kpi.color === 'green'
                      ? 'from-green-500 to-green-600'
                      : kpi.color === 'orange'
                      ? 'from-orange-500 to-orange-600'
                      : 'from-purple-500 to-purple-600'
                  }`}
                >
                  <kpi.icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Main Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Headcount Trend */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-zinc-900 rounded-2xl border border-zinc-800 p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-zinc-100">Headcount Trend</h3>
                <p className="text-sm text-zinc-400 mt-1">Active personnel over time</p>
              </div>
              <Activity className="w-5 h-5 text-blue-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={headcountData}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                <XAxis dataKey="month" stroke="#a1a1aa" />
                <YAxis stroke="#a1a1aa" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#18181b',
                    border: '1px solid #3f3f46',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="total"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  fill="url(#colorTotal)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Department Distribution */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-zinc-900 rounded-2xl border border-zinc-800 p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Department Distribution</h3>
                <p className="text-sm text-slate-600 mt-1">Personnel by department</p>
              </div>
              <BarChart3 className="w-5 h-5 text-green-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={departmentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {departmentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Certification Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-zinc-900 rounded-2xl border border-zinc-800 p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Certification Status</h3>
                <p className="text-sm text-slate-600 mt-1">Compliance tracking</p>
              </div>
              <Award className="w-5 h-5 text-orange-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={certificationExpiry} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" stroke="#64748b" />
                <YAxis dataKey="status" type="category" stroke="#64748b" width={100} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#18181b',
                    border: '1px solid #3f3f46',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                  }}
                />
                <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                  {certificationExpiry.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Payroll Trend */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-zinc-900 rounded-2xl border border-zinc-800 p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Payroll Trend</h3>
                <p className="text-sm text-slate-600 mt-1">Cost analysis by period</p>
              </div>
              <DollarSign className="w-5 h-5 text-purple-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={payrollTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="period" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#18181b',
                    border: '1px solid #3f3f46',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="amount"
                  stroke="#8b5cf6"
                  strokeWidth={3}
                  dot={{ fill: '#8b5cf6', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-xl p-8 text-white"
        >
          <h3 className="text-2xl font-bold mb-6">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Add Personnel', icon: UserPlus, href: '/hr/personnel' },
              { label: 'View Certifications', icon: Award, href: '/hr/certifications' },
              { label: 'Manage Schedule', icon: Calendar, href: '/hr/scheduling' },
              { label: 'Process Payroll', icon: DollarSign, href: '/hr/payroll' },
            ].map((action, idx) => (
              <motion.a
                key={idx}
                href={action.href}
                whileHover={{ scale: 1.05, backgroundColor: 'rgba(255,255,255,0.2)' }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-3 p-4 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 hover:border-white/40 transition-all"
              >
                <action.icon className="w-6 h-6" />
                <span className="font-medium">{action.label}</span>
                <ChevronRight className="w-4 h-4 ml-auto" />
              </motion.a>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default HRDashboard;
