'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Calendar,
  Clock,
  Users,
  Plus,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Filter,
  Download,
  Settings,
  Bell,
  RefreshCw,
  Zap,
  TrendingUp,
  UserCheck,
  CalendarDays,
  GripVertical,
} from 'lucide-react';
import { PageShell } from "@/components/PageShell";

interface DashboardStats {
  total_shifts_this_week: number;
  open_shifts: number;
  pending_requests: number;
  coverage_rate: number;
  overtime_hours: number;
  alerts_count: number;
}

interface CalendarDay {
  date: string;
  day_of_week: string;
  shifts: CalendarShift[];
  coverage: { required: number; assigned: number; rate: number };
  alerts: { id: number; severity: string; title: string }[];
  has_gaps: boolean;
}

interface CalendarShift {
  id: number;
  start: string;
  end: string;
  station: string | null;
  unit: string | null;
  status: string;
  required: number;
  assigned: number;
  is_open: boolean;
  is_critical: boolean;
}

const shiftColors: Record<string, string> = {
  draft: 'bg-zinc-700 border-zinc-600',
  scheduled: 'bg-orange-900/40 border-orange-600/50',
  published: 'bg-green-900/40 border-green-600/50',
  in_progress: 'bg-blue-900/40 border-blue-600/50',
  completed: 'bg-zinc-800 border-zinc-600',
  cancelled: 'bg-red-900/20 border-red-600/30',
};

const statusBadgeColors: Record<string, string> = {
  draft: 'bg-zinc-600 text-zinc-200',
  scheduled: 'bg-orange-600 text-white',
  published: 'bg-green-600 text-white',
  in_progress: 'bg-blue-600 text-white',
  completed: 'bg-zinc-500 text-white',
  cancelled: 'bg-red-600 text-white',
};

export default function SchedulingDashboard() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<'week' | 'month'>('week');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [calendarData, setCalendarData] = useState<Record<string, CalendarDay>>({});
  const [loading, setLoading] = useState(true);
  const [selectedShift, setSelectedShift] = useState<CalendarShift | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [draggedShift, setDraggedShift] = useState<CalendarShift | null>(null);
  const [dragOverDate, setDragOverDate] = useState<string | null>(null);
  const [isMovingShift, setIsMovingShift] = useState(false);

  const getWeekDates = useCallback(() => {
    const dates: Date[] = [];
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
    
    for (let i = 0; i < 7; i++) {
      const d = new Date(startOfWeek);
      d.setDate(startOfWeek.getDate() + i);
      dates.push(d);
    }
    return dates;
  }, [currentDate]);

  const formatDateKey = (date: Date) => {
    return date.toISOString().split('T')[0];
  };

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/v1/scheduling/dashboard/stats', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const fetchCalendarData = async () => {
    const weekDates = getWeekDates();
    const startDate = formatDateKey(weekDates[0]);
    const endDate = formatDateKey(weekDates[6]);
    
    try {
      const res = await fetch(
        `/api/v1/scheduling/calendar?start_date=${startDate}&end_date=${endDate}`,
        { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setCalendarData(data.calendar || {});
      }
    } catch (err) {
      console.error('Failed to fetch calendar:', err);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchStats(), fetchCalendarData()]);
      setLoading(false);
    };
    loadData();
  }, [currentDate]);

  const navigateWeek = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() + (direction === 'next' ? 7 : -7));
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const handleDragStart = (e: React.DragEvent, shift: CalendarShift, sourceDate: string) => {
    if (shift.status === 'published' || shift.status === 'completed' || shift.status === 'cancelled') {
      e.preventDefault();
      return;
    }
    setDraggedShift(shift);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('application/json', JSON.stringify({ shiftId: shift.id, sourceDate }));
    const dragImage = document.createElement('div');
    dragImage.className = 'bg-orange-600 text-white px-3 py-1 rounded text-sm';
    dragImage.textContent = shift.station || 'Shift';
    dragImage.style.position = 'absolute';
    dragImage.style.top = '-1000px';
    document.body.appendChild(dragImage);
    e.dataTransfer.setDragImage(dragImage, 0, 0);
    setTimeout(() => document.body.removeChild(dragImage), 0);
  };

  const handleDragOver = (e: React.DragEvent, targetDate: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverDate(targetDate);
  };

  const handleDragLeave = () => {
    setDragOverDate(null);
  };

  const handleDrop = async (e: React.DragEvent, targetDate: string) => {
    e.preventDefault();
    setDragOverDate(null);
    
    if (!draggedShift) return;
    
    try {
      const data = JSON.parse(e.dataTransfer.getData('application/json'));
      const { shiftId, sourceDate } = data;
      
      if (sourceDate === targetDate) {
        setDraggedShift(null);
        return;
      }
      
      setIsMovingShift(true);
      
      const shiftStart = new Date(draggedShift.start);
      const shiftEnd = new Date(draggedShift.end);
      const daysDiff = Math.round((new Date(targetDate).getTime() - new Date(sourceDate).getTime()) / (1000 * 60 * 60 * 24));
      
      shiftStart.setDate(shiftStart.getDate() + daysDiff);
      shiftEnd.setDate(shiftEnd.getDate() + daysDiff);
      
      const res = await fetch(`/api/v1/scheduling/shifts/${shiftId}/move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          new_date: targetDate,
          new_start_datetime: shiftStart.toISOString(),
          new_end_datetime: shiftEnd.toISOString(),
        }),
      });
      
      if (res.ok) {
        setCalendarData(prev => {
          const updated = { ...prev };
          if (updated[sourceDate]) {
            updated[sourceDate] = {
              ...updated[sourceDate],
              shifts: updated[sourceDate].shifts.filter(s => s.id !== shiftId),
            };
          }
          const movedShift = {
            ...draggedShift,
            start: shiftStart.toISOString(),
            end: shiftEnd.toISOString(),
          };
          if (updated[targetDate]) {
            updated[targetDate] = {
              ...updated[targetDate],
              shifts: [...updated[targetDate].shifts, movedShift],
            };
          } else {
            updated[targetDate] = {
              date: targetDate,
              day_of_week: new Date(targetDate).toLocaleDateString('en-US', { weekday: 'short' }),
              shifts: [movedShift],
              coverage: { required: 0, assigned: 0, rate: 0 },
              alerts: [],
              has_gaps: false,
            };
          }
          return updated;
        });
      } else {
        const error = await res.json();
        alert(error.detail || 'Failed to move shift');
      }
    } catch (err) {
      console.error('Failed to move shift:', err);
    } finally {
      setDraggedShift(null);
      setIsMovingShift(false);
    }
  };

  const handleDragEnd = () => {
    setDraggedShift(null);
    setDragOverDate(null);
  };

  const weekDates = getWeekDates();
  const today = new Date().toISOString().split('T')[0];

  const StatCard = ({ 
    icon: Icon, 
    label, 
    value, 
    trend, 
    color 
  }: { 
    icon: React.ElementType; 
    label: string; 
    value: string | number; 
    trend?: string; 
    color: string;
  }) => (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 hover:border-orange-600/30 transition-colors">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-zinc-400 text-sm font-medium">{label}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {trend && <p className="text-xs text-green-500 mt-1">{trend}</p>}
        </div>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
    </div>
  );

  return (
    <PageShell title="Scheduling" requireAuth={true}>
      <div className="max-w-[1800px] mx-auto p-6 space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">
              <span className="text-orange-500">Scheduling</span> Module
            </h1>
            <p className="text-zinc-400 mt-1">Enterprise workforce scheduling and management</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg hover:border-orange-600/50 transition-colors flex items-center gap-2"
            >
              <Filter className="w-4 h-4" />
              Filters
            </button>
            <button className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg hover:border-orange-600/50 transition-colors flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export
            </button>
            <button className="px-5 py-2 bg-orange-600 hover:bg-orange-500 rounded-lg font-medium flex items-center gap-2 transition-colors">
              <Plus className="w-4 h-4" />
              New Shift
            </button>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          <StatCard
            icon={CalendarDays}
            label="Shifts This Week"
            value={stats?.total_shifts_this_week || 0}
            color="bg-orange-600/20"
          />
          <StatCard
            icon={AlertTriangle}
            label="Open Shifts"
            value={stats?.open_shifts || 0}
            color="bg-red-600/20"
          />
          <StatCard
            icon={UserCheck}
            label="Coverage Rate"
            value={`${stats?.coverage_rate || 0}%`}
            color="bg-green-600/20"
          />
          <StatCard
            icon={Clock}
            label="Overtime Hours"
            value={stats?.overtime_hours || 0}
            color="bg-yellow-600/20"
          />
          <StatCard
            icon={Bell}
            label="Pending Requests"
            value={stats?.pending_requests || 0}
            color="bg-blue-600/20"
          />
          <StatCard
            icon={Zap}
            label="Active Alerts"
            value={stats?.alerts_count || 0}
            color="bg-purple-600/20"
          />
        </div>

        <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigateWeek('prev')}
                className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <h2 className="text-lg font-semibold">
                {weekDates[0].toLocaleDateString('en-US', { month: 'long', day: 'numeric' })} - {weekDates[6].toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
              </h2>
              <button
                onClick={() => navigateWeek('next')}
                className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
              <button
                onClick={goToToday}
                className="px-3 py-1 text-sm bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
              >
                Today
              </button>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode('week')}
                className={`px-3 py-1 text-sm rounded-lg transition-colors ${viewMode === 'week' ? 'bg-orange-600 text-white' : 'bg-zinc-800 hover:bg-zinc-700'}`}
              >
                Week
              </button>
              <button
                onClick={() => setViewMode('month')}
                className={`px-3 py-1 text-sm rounded-lg transition-colors ${viewMode === 'month' ? 'bg-orange-600 text-white' : 'bg-zinc-800 hover:bg-zinc-700'}`}
              >
                Month
              </button>
              <button
                onClick={() => { fetchStats(); fetchCalendarData(); }}
                className="p-2 hover:bg-zinc-800 rounded-lg transition-colors ml-2"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {loading ? (
            <div className="p-8 text-center">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-orange-500" />
              <p className="mt-2 text-zinc-400">Loading schedule...</p>
            </div>
          ) : (
            <div className="grid grid-cols-7 divide-x divide-zinc-800">
              {weekDates.map((date, idx) => {
                const dateKey = formatDateKey(date);
                const dayData = calendarData[dateKey];
                const isToday = dateKey === today;
                const hasGaps = dayData?.has_gaps;
                const isDragOver = dragOverDate === dateKey;

                return (
                  <div
                    key={idx}
                    className={`min-h-[400px] transition-colors ${isToday ? 'bg-orange-900/10' : ''} ${isDragOver ? 'bg-orange-600/20 ring-2 ring-orange-500 ring-inset' : ''}`}
                    onDragOver={(e) => handleDragOver(e, dateKey)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, dateKey)}
                  >
                    <div className={`p-3 border-b border-zinc-800 ${isToday ? 'bg-orange-600/20' : 'bg-zinc-900/50'}`}>
                      <p className="text-xs text-zinc-400 uppercase">
                        {date.toLocaleDateString('en-US', { weekday: 'short' })}
                      </p>
                      <p className={`text-lg font-bold ${isToday ? 'text-orange-500' : 'text-white'}`}>
                        {date.getDate()}
                      </p>
                      {dayData && (
                        <div className="mt-1 flex items-center gap-2">
                          <span className={`text-xs px-1.5 py-0.5 rounded ${dayData.coverage.rate >= 100 ? 'bg-green-600/20 text-green-400' : dayData.coverage.rate >= 80 ? 'bg-yellow-600/20 text-yellow-400' : 'bg-red-600/20 text-red-400'}`}>
                            {dayData.coverage.rate}%
                          </span>
                          {hasGaps && (
                            <AlertTriangle className="w-3 h-3 text-red-500" />
                          )}
                        </div>
                      )}
                    </div>

                    <div className="p-2 space-y-2">
                      {dayData?.shifts?.map((shift) => {
                        const isDraggable = !['published', 'completed', 'cancelled'].includes(shift.status);
                        const isBeingDragged = draggedShift?.id === shift.id;
                        
                        return (
                          <div
                            key={shift.id}
                            draggable={isDraggable}
                            onDragStart={(e) => handleDragStart(e, shift, dateKey)}
                            onDragEnd={handleDragEnd}
                            onClick={() => !isBeingDragged && setSelectedShift(shift)}
                            className={`p-2 rounded-lg border transition-all ${shiftColors[shift.status] || 'bg-zinc-800 border-zinc-700'} ${isDraggable ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer'} ${isBeingDragged ? 'opacity-50 ring-2 ring-orange-500' : 'hover:border-orange-500/50'}`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex items-start gap-1.5 flex-1 min-w-0">
                                {isDraggable && (
                                  <GripVertical className="w-3 h-3 text-zinc-500 mt-0.5 flex-shrink-0" />
                                )}
                                <div className="min-w-0 flex-1">
                                  <p className="text-xs text-zinc-400">
                                    {new Date(shift.start).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })} - {new Date(shift.end).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                                  </p>
                                  <p className="text-sm font-medium truncate mt-0.5">
                                    {shift.station || 'No Station'}
                                  </p>
                                </div>
                              </div>
                              {shift.is_critical && (
                                <span className="px-1.5 py-0.5 text-[10px] bg-red-600 text-white rounded flex-shrink-0">
                                  CRITICAL
                                </span>
                              )}
                            </div>
                            <div className="flex items-center justify-between mt-2">
                              <div className="flex items-center gap-1">
                                <Users className="w-3 h-3 text-zinc-500" />
                                <span className={`text-xs ${shift.assigned < shift.required ? 'text-red-400' : 'text-green-400'}`}>
                                  {shift.assigned}/{shift.required}
                                </span>
                              </div>
                              <span className={`text-[10px] px-1.5 py-0.5 rounded ${statusBadgeColors[shift.status]}`}>
                                {shift.status.toUpperCase()}
                              </span>
                            </div>
                          </div>
                        );
                      })}

                      {(!dayData?.shifts || dayData.shifts.length === 0) && (
                        <div className="text-center py-8 text-zinc-600">
                          <Calendar className="w-6 h-6 mx-auto mb-2 opacity-50" />
                          <p className="text-xs">No shifts</p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-zinc-900/80 border border-zinc-800 rounded-xl p-4">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
              Active Alerts
            </h3>
            <div className="space-y-3">
              {Object.values(calendarData).flatMap(day => day.alerts || []).slice(0, 5).map((alert, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border ${alert.severity === 'critical' ? 'bg-red-900/20 border-red-600/30' : alert.severity === 'warning' ? 'bg-yellow-900/20 border-yellow-600/30' : 'bg-blue-900/20 border-blue-600/30'}`}
                >
                  <div className="flex items-start gap-3">
                    <AlertTriangle className={`w-4 h-4 mt-0.5 ${alert.severity === 'critical' ? 'text-red-500' : alert.severity === 'warning' ? 'text-yellow-500' : 'text-blue-500'}`} />
                    <div>
                      <p className="text-sm font-medium">{alert.title}</p>
                    </div>
                  </div>
                </div>
              )) || (
                <div className="text-center py-6 text-zinc-500">
                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
                  <p>No active alerts</p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-orange-500" />
              Quick Actions
            </h3>
            <div className="space-y-2">
              <button className="w-full p-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-left transition-colors flex items-center gap-3">
                <Plus className="w-4 h-4 text-orange-500" />
                <span>Create New Shift</span>
              </button>
              <button className="w-full p-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-left transition-colors flex items-center gap-3">
                <Users className="w-4 h-4 text-orange-500" />
                <span>Manage Assignments</span>
              </button>
              <button className="w-full p-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-left transition-colors flex items-center gap-3">
                <Bell className="w-4 h-4 text-orange-500" />
                <span>Review Requests</span>
              </button>
              <button className="w-full p-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-left transition-colors flex items-center gap-3">
                <Settings className="w-4 h-4 text-orange-500" />
                <span>Schedule Settings</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {selectedShift && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" onClick={() => setSelectedShift(null)}>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 max-w-lg w-full mx-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-bold">Shift Details</h3>
                <p className="text-zinc-400 text-sm">{selectedShift.station || 'No Station'}</p>
              </div>
              <button onClick={() => setSelectedShift(null)} className="p-2 hover:bg-zinc-800 rounded-lg">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Start Time</p>
                  <p className="text-white font-medium">{new Date(selectedShift.start).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase">End Time</p>
                  <p className="text-white font-medium">{new Date(selectedShift.end).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Status</p>
                  <span className={`inline-block mt-1 text-xs px-2 py-1 rounded ${statusBadgeColors[selectedShift.status]}`}>
                    {selectedShift.status.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase">Staffing</p>
                  <p className={`font-medium ${selectedShift.assigned < selectedShift.required ? 'text-red-400' : 'text-green-400'}`}>
                    {selectedShift.assigned} / {selectedShift.required} assigned
                  </p>
                </div>
              </div>
              <div className="flex gap-2 pt-4 border-t border-zinc-800">
                <button className="flex-1 py-2 bg-orange-600 hover:bg-orange-500 rounded-lg font-medium transition-colors">
                  Edit Shift
                </button>
                <button className="flex-1 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg font-medium transition-colors">
                  Manage Crew
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </PageShell>
  );
}
