'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  UserPlus,
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle,
  FileText,
  Award,
  BookOpen,
  Clipboard,
  Users,
  Download,
  Plus,
  MoreVertical,
  Eye,
  Edit,
  TrendingUp,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

// Mock onboarding data
const onboardingColumns = [
  {
    id: 'pending',
    title: 'Pending Start',
    icon: Clock,
    color: 'slate',
    items: [
      {
        id: 1,
        name: 'Alex Martinez',
        position: 'Paramedic',
        startDate: '2024-02-15',
        avatar: null,
        progress: 0,
        tasks: 12,
        completed: 0,
      },
      {
        id: 2,
        name: 'Jessica Lee',
        position: 'EMT-B',
        startDate: '2024-02-20',
        avatar: null,
        progress: 0,
        tasks: 10,
        completed: 0,
      },
    ],
  },
  {
    id: 'documentation',
    title: 'Documentation',
    icon: FileText,
    color: 'blue',
    items: [
      {
        id: 3,
        name: 'Robert Kim',
        position: 'EMT-A',
        startDate: '2024-02-01',
        avatar: null,
        progress: 45,
        tasks: 15,
        completed: 7,
      },
      {
        id: 4,
        name: 'Maria Garcia',
        position: 'Paramedic',
        startDate: '2024-02-05',
        avatar: null,
        progress: 60,
        tasks: 15,
        completed: 9,
      },
    ],
  },
  {
    id: 'training',
    title: 'Training',
    icon: BookOpen,
    color: 'purple',
    items: [
      {
        id: 5,
        name: 'David Wilson',
        position: 'Critical Care Paramedic',
        startDate: '2024-01-20',
        avatar: null,
        progress: 75,
        tasks: 20,
        completed: 15,
      },
    ],
  },
  {
    id: 'field_training',
    title: 'Field Training',
    icon: Users,
    color: 'orange',
    items: [
      {
        id: 6,
        name: 'Lisa Anderson',
        position: 'Paramedic',
        startDate: '2024-01-15',
        avatar: null,
        progress: 85,
        tasks: 18,
        completed: 16,
      },
    ],
  },
  {
    id: 'completed',
    title: 'Completed',
    icon: CheckCircle,
    color: 'green',
    items: [
      {
        id: 7,
        name: 'James Taylor',
        position: 'EMT-B',
        startDate: '2024-01-05',
        avatar: null,
        progress: 100,
        tasks: 12,
        completed: 12,
      },
      {
        id: 8,
        name: 'Emily White',
        position: 'Paramedic',
        startDate: '2023-12-20',
        avatar: null,
        progress: 100,
        tasks: 15,
        completed: 15,
      },
    ],
  },
];

const onboardingMetrics = [
  { month: 'Aug', started: 8, completed: 6, avgDays: 45 },
  { month: 'Sep', started: 10, completed: 8, avgDays: 42 },
  { month: 'Oct', started: 12, completed: 10, avgDays: 40 },
  { month: 'Nov', started: 9, completed: 9, avgDays: 38 },
  { month: 'Dec', started: 7, completed: 6, avgDays: 35 },
  { month: 'Jan', started: 11, completed: 9, avgDays: 37 },
];

const completionRates = [
  { status: 'On Track', value: 65, color: '#10b981' },
  { status: 'At Risk', value: 25, color: '#f59e0b' },
  { status: 'Delayed', value: 10, color: '#ef4444' },
];

const OnboardingTracker = () => {
  const [draggedItem, setDraggedItem] = useState<any>(null);
  const [columns, setColumns] = useState(onboardingColumns);
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('');
  };

  const totalActive = columns.reduce(
    (sum, col) => sum + (col.id !== 'completed' ? col.items.length : 0),
    0
  );
  const totalCompleted = columns.find((c) => c.id === 'completed')?.items.length || 0;
  const avgProgress =
    columns.reduce(
      (sum, col) => sum + col.items.reduce((s, item) => s + item.progress, 0),
      0
    ) / columns.reduce((sum, col) => sum + col.items.length, 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-violet-50 to-fuchsia-50 p-8">
      <div className="max-w-[1800px] mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
              Onboarding Tracker
            </h1>
            <p className="text-slate-600 mt-1">
              New hire onboarding progress and milestones
            </p>
          </div>
          <div className="flex gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-4 py-2 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-violet-400 transition-colors flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              <span>Export Report</span>
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-6 py-2 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl shadow-lg hover:shadow-xl transition-shadow flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              <span>Add New Hire</span>
            </motion.button>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            {
              label: 'Active Onboarding',
              value: totalActive.toString(),
              icon: UserPlus,
              color: 'violet',
              change: '+3',
            },
            {
              label: 'Completed This Month',
              value: totalCompleted.toString(),
              icon: CheckCircle,
              color: 'green',
              change: '+2',
            },
            {
              label: 'Avg Progress',
              value: `${avgProgress.toFixed(0)}%`,
              icon: TrendingUp,
              color: 'blue',
              change: '+8%',
            },
            {
              label: 'Avg Time to Complete',
              value: '37 days',
              icon: Clock,
              color: 'orange',
              change: '-3 days',
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
                  <p className="text-sm text-green-600 font-medium mt-1">{stat.change}</p>
                </div>
                <div
                  className={`p-3 rounded-xl ${
                    stat.color === 'violet'
                      ? 'bg-violet-100 text-violet-600'
                      : stat.color === 'green'
                      ? 'bg-green-100 text-green-600'
                      : stat.color === 'blue'
                      ? 'bg-blue-100 text-blue-600'
                      : 'bg-orange-100 text-orange-600'
                  }`}
                >
                  <stat.icon className="w-6 h-6" />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Onboarding Metrics */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-2xl shadow-lg p-6 border border-slate-100"
            style={{ minWidth: 320, minHeight: 160 }}
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Onboarding Metrics</h3>
                <p className="text-sm text-slate-600">6-month trends</p>
              </div>
              <TrendingUp className="w-5 h-5 text-violet-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={onboardingMetrics}>
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
                  dataKey="started"
                  stroke="#8b5cf6"
                  strokeWidth={3}
                  name="Started"
                />
                <Line
                  type="monotone"
                  dataKey="completed"
                  stroke="#10b981"
                  strokeWidth={3}
                  name="Completed"
                />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Completion Rates */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-2xl shadow-lg p-6 border border-slate-100"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Completion Status</h3>
                <p className="text-sm text-slate-600">Current cohort</p>
              </div>
              <Clipboard className="w-5 h-5 text-fuchsia-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={completionRates}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(props) => {
                    const p = props as unknown as { payload?: { status?: string }; value?: number }
                    return `${p.payload?.status ?? "Status"}: ${p.value ?? 0}%`
                  }}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {completionRates.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Kanban Board */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg p-6 border border-slate-100"
        >
          <h3 className="text-lg font-bold text-slate-900 mb-6">Onboarding Pipeline</h3>

          <div className="flex gap-4 overflow-x-auto pb-4">
            {columns.map((column) => {
              const ColumnIcon = column.icon;
              return (
                <motion.div
                  key={column.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex-shrink-0 w-80"
                >
                  {/* Column Header */}
                  <div
                    className={`p-4 rounded-t-xl bg-${column.color}-50 border-2 border-${column.color}-200`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <ColumnIcon
                          className={`w-5 h-5 text-${column.color}-600`}
                        />
                        <h4 className={`font-bold text-${column.color}-900`}>
                          {column.title}
                        </h4>
                      </div>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-bold bg-${column.color}-200 text-${column.color}-700`}
                      >
                        {column.items.length}
                      </span>
                    </div>
                  </div>

                  {/* Column Items */}
                  <div className="space-y-3 p-4 bg-slate-50 rounded-b-xl border-x-2 border-b-2 border-slate-200 min-h-[400px]">
                    {column.items.map((item, idx) => (
                      <motion.div
                        key={item.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.05 }}
                        whileHover={{ y: -2, boxShadow: "0 8px 20px rgba(0,0,0,0.15)" }}
                        className="bg-white rounded-xl shadow-md p-4 cursor-pointer border border-slate-200 hover:border-violet-300 transition-all"
                        onClick={() => setSelectedEmployee(item)}
                      >
                        {/* Employee Info */}
                        <div className="flex items-start gap-3 mb-3">
                          <div
                            className={`w-12 h-12 rounded-full bg-gradient-to-br from-${column.color}-400 to-${column.color}-600 flex items-center justify-center text-white font-bold`}
                          >
                            {getInitials(item.name)}
                          </div>
                          <div className="flex-1">
                            <h5 className="font-bold text-slate-900">{item.name}</h5>
                            <p className="text-xs text-slate-600">{item.position}</p>
                          </div>
                        </div>

                        {/* Progress */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-600">Progress</span>
                            <span className="font-bold text-slate-900">
                              {item.progress}%
                            </span>
                          </div>
                          <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${item.progress}%` }}
                              transition={{ duration: 1, delay: idx * 0.1 }}
                              className={`h-full bg-gradient-to-r from-${column.color}-500 to-${column.color}-600 rounded-full`}
                            />
                          </div>
                          <p className="text-xs text-slate-600">
                            {item.completed}/{item.tasks} tasks completed
                          </p>
                        </div>

                        {/* Meta */}
                        <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
                          <div className="flex items-center gap-1 text-xs text-slate-600">
                            <Clock className="w-3 h-3" />
                            <span>Start: {item.startDate}</span>
                          </div>
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={(e) => {
                              e.stopPropagation();
                            }}
                            className="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded"
                          >
                            <MoreVertical className="w-4 h-4" />
                          </motion.button>
                        </div>
                      </motion.div>
                    ))}

                    {/* Add Button */}
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="w-full p-4 border-2 border-dashed border-slate-300 rounded-xl text-slate-400 hover:border-violet-400 hover:text-violet-600 transition-colors flex items-center justify-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      <span className="text-sm font-medium">Add Employee</span>
                    </motion.button>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Employee Detail Modal */}
        {selectedEmployee && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedEmployee(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-8"
            >
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-violet-400 to-fuchsia-400 flex items-center justify-center text-white font-bold text-2xl">
                    {getInitials(selectedEmployee.name)}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900">
                      {selectedEmployee.name}
                    </h2>
                    <p className="text-slate-600">{selectedEmployee.position}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedEmployee(null)}
                  className="text-slate-400 hover:text-slate-600 text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="text-sm font-medium text-slate-600">Start Date</label>
                  <p className="text-slate-900 mt-1">{selectedEmployee.startDate}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-600 mb-2 block">
                    Overall Progress
                  </label>
                  <div className="w-full bg-slate-200 rounded-full h-4 overflow-hidden">
                    <div
                      style={{ width: `${selectedEmployee.progress}%` }}
                      className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-full flex items-center justify-end px-2"
                    >
                      <span className="text-xs font-bold text-white">
                        {selectedEmployee.progress}%
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-slate-600 mt-2">
                    {selectedEmployee.completed} of {selectedEmployee.tasks} tasks completed
                  </p>
                </div>

                <div className="flex gap-3">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex-1 px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl shadow-lg hover:shadow-xl transition-shadow font-medium"
                  >
                    View Full Details
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-6 py-3 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-colors font-medium"
                  >
                    Edit
                  </motion.button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default OnboardingTracker;
