'use client'
import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Wand2, Calendar, Users, Clock, AlertTriangle, CheckCircle, Zap, RefreshCw, Settings, ChevronLeft, ChevronRight, Sun, Moon, Sunset } from 'lucide-react'
import { format, startOfWeek, addDays, addWeeks, subWeeks } from 'date-fns'

interface ScheduleSlot {
  id: string
  day: number
  shift: 'day' | 'night' | 'swing'
  employee?: { name: string; role: string; fatigueScore: number }
  aiRecommended?: { name: string; role: string; score: number; reason: string }
  conflicts?: string[]
}

const shiftConfig = {
  day: { label: 'Day (06-18)', icon: Sun, color: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  night: { label: 'Night (18-06)', icon: Moon, color: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' },
  swing: { label: 'Swing (14-02)', icon: Sunset, color: 'bg-orange-500/20 text-orange-400 border-orange-500/30' },
}

const employees = [
  { name: 'John Smith', role: 'Paramedic', fatigueScore: 25 },
  { name: 'Sarah Johnson', role: 'Paramedic', fatigueScore: 78 },
  { name: 'Mike Chen', role: 'EMT-B', fatigueScore: 45 },
  { name: 'Lisa Park', role: 'EMT-A', fatigueScore: 32 },
  { name: 'Emily Davis', role: 'Paramedic', fatigueScore: 62 },
  { name: 'Chris Wilson', role: 'EMT-B', fatigueScore: 18 },
]

const generateMockSchedule = (): ScheduleSlot[] => {
  const slots: ScheduleSlot[] = []
  for (let day = 0; day < 7; day++) {
    for (const shift of ['day', 'night', 'swing'] as const) {
      const hasEmployee = Math.random() > 0.3
      const emp = hasEmployee ? employees[Math.floor(Math.random() * employees.length)] : undefined
      slots.push({
        id: `${day}-${shift}`,
        day,
        shift,
        employee: emp,
        aiRecommended: !emp ? {
          name: employees[Math.floor(Math.random() * employees.length)].name,
          role: 'Paramedic',
          score: Math.floor(80 + Math.random() * 15),
          reason: 'Low fatigue, skill match, availability confirmed'
        } : undefined,
        conflicts: emp?.fatigueScore > 70 ? ['High fatigue risk'] : undefined
      })
    }
  }
  return slots
}

export default function SmartSchedulerPage() {
  const [currentWeek, setCurrentWeek] = useState(new Date())
  const [schedule, setSchedule] = useState(generateMockSchedule)
  const [generating, setGenerating] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [settings, setSettings] = useState({
    maxConsecutiveShifts: 3,
    minRestHours: 10,
    balanceOvertime: true,
    respectPreferences: true,
    optimizeFatigue: true,
  })

  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 0 })
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))

  const stats = useMemo(() => ({
    filled: schedule.filter(s => s.employee).length,
    vacant: schedule.filter(s => !s.employee).length,
    conflicts: schedule.filter(s => s.conflicts?.length).length,
    coverage: Math.round((schedule.filter(s => s.employee).length / schedule.length) * 100)
  }), [schedule])

  const handleAutoGenerate = async () => {
    setGenerating(true)
    await new Promise(r => setTimeout(r, 2500))
    setSchedule(schedule.map(s => ({
      ...s,
      employee: s.employee || (s.aiRecommended ? { name: s.aiRecommended.name, role: s.aiRecommended.role, fatigueScore: 20 } : undefined),
      aiRecommended: undefined,
      conflicts: undefined
    })))
    setGenerating(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-900/20 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-8"
        >
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
              <Wand2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">AI Smart Scheduler</h1>
              <p className="text-emerald-300">Intelligent, fatigue-aware shift optimization</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <motion.button
              onClick={() => setShowSettings(true)}
              className="p-3 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-300 transition-colors"
              whileTap={{ scale: 0.95 }}
            >
              <Settings className="w-5 h-5" />
            </motion.button>
            <motion.button
              onClick={handleAutoGenerate}
              disabled={generating}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-xl text-white font-medium shadow-lg shadow-emerald-500/30 disabled:opacity-50"
              whileTap={{ scale: 0.95 }}
            >
              {generating ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  Optimizing...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Auto-Generate Optimal Schedule
                </>
              )}
            </motion.button>
          </div>
        </motion.div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Coverage', value: `${stats.coverage}%`, color: 'emerald', icon: CheckCircle },
            { label: 'Filled Shifts', value: stats.filled, color: 'blue', icon: Users },
            { label: 'Vacant', value: stats.vacant, color: 'amber', icon: Clock },
            { label: 'Conflicts', value: stats.conflicts, color: 'red', icon: AlertTriangle },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className={`bg-slate-800/50 backdrop-blur-sm rounded-xl border border-${stat.color}-500/30 p-4`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">{stat.label}</p>
                  <p className="text-2xl font-bold text-white">{stat.value}</p>
                </div>
                <stat.icon className={`w-8 h-8 text-${stat.color}-400 opacity-50`} />
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <motion.button 
                onClick={() => setCurrentWeek(subWeeks(currentWeek, 1))}
                className="p-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600"
                whileTap={{ scale: 0.9 }}
              >
                <ChevronLeft className="w-5 h-5" />
              </motion.button>
              <h2 className="text-xl font-semibold text-white">
                {format(weekStart, 'MMMM d')} - {format(addDays(weekStart, 6), 'd, yyyy')}
              </h2>
              <motion.button 
                onClick={() => setCurrentWeek(addWeeks(currentWeek, 1))}
                className="p-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600"
                whileTap={{ scale: 0.9 }}
              >
                <ChevronRight className="w-5 h-5" />
              </motion.button>
            </div>
            <button 
              onClick={() => setCurrentWeek(new Date())}
              className="px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg text-sm font-medium"
            >
              Today
            </button>
          </div>

          <div className="overflow-x-auto">
            <div className="min-w-[900px]">
              <div className="grid grid-cols-8 gap-2 mb-4">
                <div className="p-2"></div>
                {weekDays.map((day, i) => (
                  <div key={i} className="text-center">
                    <p className="text-slate-400 text-sm">{format(day, 'EEE')}</p>
                    <p className="text-white font-semibold">{format(day, 'd')}</p>
                  </div>
                ))}
              </div>

              {(['day', 'night', 'swing'] as const).map(shiftType => {
                const config = shiftConfig[shiftType]
                const Icon = config.icon
                return (
                  <div key={shiftType} className="grid grid-cols-8 gap-2 mb-2">
                    <div className={`p-3 rounded-lg ${config.color} border flex items-center gap-2`}>
                      <Icon className="w-4 h-4" />
                      <span className="text-sm font-medium">{shiftType}</span>
                    </div>
                    {weekDays.map((_, dayIndex) => {
                      const slot = schedule.find(s => s.day === dayIndex && s.shift === shiftType)
                      return (
                        <motion.div
                          key={`${dayIndex}-${shiftType}`}
                          className={`p-2 rounded-lg min-h-[80px] cursor-pointer transition-all ${
                            slot?.employee 
                              ? slot.conflicts?.length 
                                ? 'bg-red-500/10 border border-red-500/30' 
                                : 'bg-slate-700/50 border border-slate-600/50 hover:border-emerald-500/50'
                              : slot?.aiRecommended 
                                ? 'bg-emerald-500/10 border border-emerald-500/30 border-dashed'
                                : 'bg-slate-800/50 border border-slate-700/30 hover:border-slate-600'
                          }`}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          {slot?.employee ? (
                            <div>
                              <p className="text-white text-sm font-medium truncate">{slot.employee.name}</p>
                              <p className="text-slate-400 text-xs">{slot.employee.role}</p>
                              {slot.conflicts?.length ? (
                                <div className="flex items-center gap-1 mt-1 text-red-400 text-xs">
                                  <AlertTriangle className="w-3 h-3" />
                                  <span>Fatigue</span>
                                </div>
                              ) : (
                                <div className="flex items-center gap-1 mt-1 text-emerald-400 text-xs">
                                  <CheckCircle className="w-3 h-3" />
                                  <span>OK</span>
                                </div>
                              )}
                            </div>
                          ) : slot?.aiRecommended ? (
                            <div className="text-center">
                              <Wand2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                              <p className="text-emerald-400 text-xs font-medium">{slot.aiRecommended.name}</p>
                              <p className="text-emerald-500/60 text-xs">{slot.aiRecommended.score}% match</p>
                            </div>
                          ) : (
                            <div className="h-full flex items-center justify-center">
                              <span className="text-slate-600 text-xs">Empty</span>
                            </div>
                          )}
                        </motion.div>
                      )
                    })}
                  </div>
                )
              })}
            </div>
          </div>
        </motion.div>

        <AnimatePresence>
          {showSettings && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={() => setShowSettings(false)}
            >
              <motion.div 
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="bg-slate-900 rounded-2xl border border-slate-700 p-6 w-full max-w-md"
                onClick={e => e.stopPropagation()}
              >
                <h2 className="text-xl font-bold text-white mb-6">AI Scheduler Settings</h2>
                
                <div className="space-y-4">
                  <div>
                    <label className="text-slate-300 text-sm mb-2 block">Max Consecutive Shifts</label>
                    <input
                      type="range"
                      min="2"
                      max="5"
                      value={settings.maxConsecutiveShifts}
                      onChange={e => setSettings({ ...settings, maxConsecutiveShifts: +e.target.value })}
                      className="w-full"
                    />
                    <span className="text-emerald-400 font-semibold">{settings.maxConsecutiveShifts} shifts</span>
                  </div>
                  
                  <div>
                    <label className="text-slate-300 text-sm mb-2 block">Min Rest Between Shifts</label>
                    <input
                      type="range"
                      min="8"
                      max="14"
                      value={settings.minRestHours}
                      onChange={e => setSettings({ ...settings, minRestHours: +e.target.value })}
                      className="w-full"
                    />
                    <span className="text-emerald-400 font-semibold">{settings.minRestHours} hours</span>
                  </div>
                  
                  {[
                    { key: 'balanceOvertime', label: 'Balance Overtime Distribution' },
                    { key: 'respectPreferences', label: 'Respect Employee Preferences' },
                    { key: 'optimizeFatigue', label: 'Optimize for Fatigue Prevention' },
                  ].map(opt => (
                    <div key={opt.key} className="flex items-center justify-between py-2">
                      <span className="text-slate-300">{opt.label}</span>
                      <button
                        onClick={() => setSettings({ ...settings, [opt.key]: !settings[opt.key as keyof typeof settings] })}
                        className={`w-12 h-7 rounded-full transition-all ${settings[opt.key as keyof typeof settings] ? 'bg-emerald-500' : 'bg-slate-600'}`}
                      >
                        <div className={`w-5 h-5 rounded-full bg-white transform transition-transform ${settings[opt.key as keyof typeof settings] ? 'translate-x-6' : 'translate-x-1'}`} />
                      </button>
                    </div>
                  ))}
                </div>
                
                <button 
                  onClick={() => setShowSettings(false)}
                  className="w-full mt-6 py-3 bg-emerald-500 text-white rounded-xl font-medium"
                >
                  Save Settings
                </button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
