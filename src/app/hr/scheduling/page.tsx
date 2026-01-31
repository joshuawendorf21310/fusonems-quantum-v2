'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Calendar as CalendarIcon,
  Clock,
  Users,
  Plus,
  Download,
  Filter,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  XCircle,
  Moon,
  Sun,
  Sunrise,
  Sunset,
} from 'lucide-react';

// Mock schedule data
const shifts = {
  'A-Shift': { icon: Sun, color: 'blue', time: '06:00-18:00' },
  'B-Shift': { icon: Moon, color: 'purple', time: '18:00-06:00' },
  'C-Shift': { icon: Sunrise, color: 'orange', time: '06:00-18:00' },
  'Day': { icon: Sunrise, color: 'yellow', time: '08:00-17:00' },
};

const scheduleData = [
  {
    date: '2024-02-01',
    day: 'Mon',
    shifts: [
      { shift: 'A-Shift', personnel: ['John Doe', 'Sarah Johnson'], station: 'Station 1' },
      { shift: 'B-Shift', personnel: ['Michael Chen'], station: 'Station 2' },
    ],
  },
  {
    date: '2024-02-02',
    day: 'Tue',
    shifts: [
      { shift: 'A-Shift', personnel: ['Emily Rodriguez'], station: 'Station 1' },
      { shift: 'C-Shift', personnel: ['David Thompson', 'John Doe'], station: 'Station 3' },
    ],
  },
  // Add more days...
];

const timeOffRequests = [
  {
    id: 1,
    employeeName: 'John Doe',
    requestType: 'Vacation',
    startDate: '2024-02-15',
    endDate: '2024-02-20',
    days: 5,
    status: 'pending',
    reason: 'Family vacation',
  },
  {
    id: 2,
    employeeName: 'Sarah Johnson',
    requestType: 'Sick Leave',
    startDate: '2024-02-10',
    endDate: '2024-02-11',
    days: 2,
    status: 'approved',
    reason: 'Medical appointment',
  },
  {
    id: 3,
    employeeName: 'Michael Chen',
    requestType: 'Personal',
    startDate: '2024-02-25',
    endDate: '2024-02-25',
    days: 1,
    status: 'rejected',
    reason: 'Personal matters',
  },
];

const coverageStats = [
  { station: 'Station 1', required: 6, scheduled: 6, coverage: 100 },
  { station: 'Station 2', required: 4, scheduled: 3, coverage: 75 },
  { station: 'Station 3', required: 5, scheduled: 5, coverage: 100 },
  { station: 'HQ', required: 3, scheduled: 3, coverage: 100 },
];

const ScheduleManager = () => {
  const [currentWeek, setCurrentWeek] = useState(0);
  const [viewMode, setViewMode] = useState<'calendar' | 'timeoff' | 'coverage'>('calendar');
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const getDaysInWeek = () => {
    const days = [];
    const today = new Date();
    const startOfWeek = new Date(today.setDate(today.getDate() - today.getDay() + currentWeek * 7));

    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      days.push({
        date: date.toISOString().split('T')[0],
        dayName: date.toLocaleDateString('en-US', { weekday: 'short' }),
        dayNumber: date.getDate(),
        isToday: date.toDateString() === new Date().toDateString(),
      });
    }
    return days;
  };

  const weekDays = getDaysInWeek();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
              Schedule Manager
            </h1>
            <p className="text-slate-600 mt-1">Shift scheduling and time-off management</p>
          </div>
          <div className="flex gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-4 py-2 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-cyan-400 transition-colors flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              <span>Export</span>
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-6 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-xl shadow-lg hover:shadow-xl transition-shadow flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              <span>Add Shift</span>
            </motion.button>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            {
              label: 'Shifts This Week',
              value: '45',
              icon: CalendarIcon,
              color: 'cyan',
              change: '+3',
            },
            {
              label: 'Time-Off Requests',
              value: '8',
              icon: AlertCircle,
              color: 'orange',
              change: '+2',
            },
            {
              label: 'Coverage Rate',
              value: '94%',
              icon: CheckCircle,
              color: 'green',
              change: '+2%',
            },
            {
              label: 'Open Shifts',
              value: '3',
              icon: XCircle,
              color: 'red',
              change: '-1',
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
                    stat.color === 'cyan'
                      ? 'bg-cyan-100 text-cyan-600'
                      : stat.color === 'orange'
                      ? 'bg-orange-100 text-orange-600'
                      : stat.color === 'green'
                      ? 'bg-green-100 text-green-600'
                      : 'bg-red-100 text-red-600'
                  }`}
                >
                  <stat.icon className="w-6 h-6" />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* View Toggle */}
        <div className="flex gap-2 bg-white p-2 rounded-xl shadow-lg border border-slate-100 w-fit">
          {[
            { value: 'calendar', label: 'Calendar', icon: CalendarIcon },
            { value: 'timeoff', label: 'Time Off', icon: Clock },
            { value: 'coverage', label: 'Coverage', icon: Users },
          ].map((view) => (
            <button
              key={view.value}
              onClick={() => setViewMode(view.value as any)}
              className={`px-6 py-3 rounded-lg transition-all flex items-center gap-2 ${
                viewMode === view.value
                  ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              <view.icon className="w-5 h-5" />
              <span className="font-medium">{view.label}</span>
            </button>
          ))}
        </div>

        {/* Calendar View */}
        {viewMode === 'calendar' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden"
          >
            {/* Week Navigation */}
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900">Weekly Schedule</h3>
              <div className="flex items-center gap-4">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setCurrentWeek(currentWeek - 1)}
                  className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  <ChevronLeft className="w-5 h-5" />
                </motion.button>
                <span className="font-medium text-slate-900">
                  Week of {weekDays[0]?.date}
                </span>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => setCurrentWeek(currentWeek + 1)}
                  className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  <ChevronRight className="w-5 h-5" />
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setCurrentWeek(0)}
                  className="px-4 py-2 bg-cyan-100 text-cyan-700 rounded-lg text-sm font-medium"
                >
                  Today
                </motion.button>
              </div>
            </div>

            {/* Calendar Grid */}
            <div className="grid grid-cols-7 divide-x divide-slate-100">
              {weekDays.map((day, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className={`p-4 min-h-[200px] ${
                    day.isToday ? 'bg-cyan-50' : 'bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="text-sm font-medium text-slate-600">{day.dayName}</p>
                      <p
                        className={`text-2xl font-bold ${
                          day.isToday ? 'text-cyan-600' : 'text-slate-900'
                        }`}
                      >
                        {day.dayNumber}
                      </p>
                    </div>
                    {day.isToday && (
                      <span className="px-2 py-1 bg-cyan-600 text-white text-xs font-medium rounded-full">
                        Today
                      </span>
                    )}
                  </div>

                  <div className="space-y-2">
                    {/* Sample shifts */}
                    {Object.entries(shifts)
                      .slice(0, 2)
                      .map(([shiftName, shiftConfig], shiftIdx) => {
                        const ShiftIcon = shiftConfig.icon;
                        return (
                          <motion.div
                            key={shiftIdx}
                            whileHover={{ scale: 1.02 }}
                            className={`p-3 rounded-lg bg-${shiftConfig.color}-50 border border-${shiftConfig.color}-200 cursor-pointer`}
                          >
                            <div className="flex items-center gap-2 mb-1">
                              <ShiftIcon className={`w-4 h-4 text-${shiftConfig.color}-600`} />
                              <span
                                className={`text-xs font-bold text-${shiftConfig.color}-700`}
                              >
                                {shiftName}
                              </span>
                            </div>
                            <p className={`text-xs text-${shiftConfig.color}-600`}>
                              {shiftConfig.time}
                            </p>
                            <p className="text-xs text-slate-600 mt-1">
                              {2 + shiftIdx} assigned
                            </p>
                          </motion.div>
                        );
                      })}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Time Off View */}
        {viewMode === 'timeoff' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden"
          >
            <div className="p-6 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-900">Time-Off Requests</h3>
              <p className="text-sm text-slate-600 mt-1">
                {timeOffRequests.length} requests pending review
              </p>
            </div>

            <div className="divide-y divide-slate-100">
              {timeOffRequests.map((request, idx) => (
                <motion.div
                  key={request.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  whileHover={{ backgroundColor: '#ecfeff' }}
                  className="p-6 cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-bold text-slate-900">{request.employeeName}</h4>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            request.status === 'approved'
                              ? 'bg-green-100 text-green-700'
                              : request.status === 'rejected'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-orange-100 text-orange-700'
                          }`}
                        >
                          {request.status}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600">{request.requestType}</p>
                      <div className="grid grid-cols-3 gap-4 mt-3">
                        <div>
                          <p className="text-xs text-slate-500">Start Date</p>
                          <p className="text-sm font-medium text-slate-900">
                            {request.startDate}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500">End Date</p>
                          <p className="text-sm font-medium text-slate-900">
                            {request.endDate}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500">Duration</p>
                          <p className="text-sm font-medium text-slate-900">
                            {request.days} days
                          </p>
                        </div>
                      </div>
                      <p className="text-sm text-slate-600 mt-3">
                        <span className="font-medium">Reason:</span> {request.reason}
                      </p>
                    </div>
                    {request.status === 'pending' && (
                      <div className="flex gap-2">
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          className="px-4 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-medium hover:bg-green-200"
                        >
                          Approve
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200"
                        >
                          Reject
                        </motion.button>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Coverage View */}
        {viewMode === 'coverage' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl shadow-lg border border-slate-100"
          >
            <div className="p-6 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-900">Station Coverage</h3>
              <p className="text-sm text-slate-600 mt-1">Current staffing levels</p>
            </div>

            <div className="p-6 space-y-6">
              {coverageStats.map((station, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-slate-900">{station.station}</h4>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-slate-600">
                        {station.scheduled}/{station.required} scheduled
                      </span>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          station.coverage === 100
                            ? 'bg-green-100 text-green-700'
                            : station.coverage >= 75
                            ? 'bg-orange-100 text-orange-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {station.coverage}%
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${station.coverage}%` }}
                      transition={{ duration: 1, delay: idx * 0.1 }}
                      className={`h-full rounded-full ${
                        station.coverage === 100
                          ? 'bg-gradient-to-r from-green-500 to-green-600'
                          : station.coverage >= 75
                          ? 'bg-gradient-to-r from-orange-500 to-orange-600'
                          : 'bg-gradient-to-r from-red-500 to-red-600'
                      }`}
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default ScheduleManager;
