'use client'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Brain, TrendingUp, TrendingDown, AlertTriangle, Users, Target, Zap, BarChart3, RefreshCw, ChevronRight, Sparkles, Shield, Clock, Heart } from 'lucide-react'
import { LineChart, Line, AreaChart, Area, RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const turnoverRisk = [
  { name: 'Sarah Johnson', role: 'Paramedic', risk: 87, factors: ['High OT', 'Low engagement', 'Certification expiring'] },
  { name: 'Mike Chen', role: 'EMT-B', risk: 72, factors: ['Commute distance', 'Pay below market'] },
  { name: 'Lisa Park', role: 'EMT-A', risk: 65, factors: ['Limited advancement', 'Schedule conflicts'] },
]

const shiftRecommendations = [
  { shift: 'Monday Day - Unit 201', score: 94, reason: 'Optimal skill match, preferred hours, low fatigue score' },
  { shift: 'Wednesday Night - Unit 105', score: 88, reason: 'High performance history, partner compatibility' },
  { shift: 'Friday Swing - Unit 302', score: 76, reason: 'Coverage needed, overtime opportunity' },
]

const performancePredictions = [
  { name: 'John Smith', current: 4.2, predicted: 4.5, trend: 'up', factors: ['Recent training', 'Mentorship program'] },
  { name: 'Emily Davis', current: 3.8, predicted: 3.4, trend: 'down', factors: ['High call volume', 'Approaching burnout'] },
  { name: 'Chris Wilson', current: 4.0, predicted: 4.3, trend: 'up', factors: ['Leadership potential', 'Certification completion'] },
]

const teamChemistry = [
  { pair: 'Johnson + Smith', score: 96, callsCompleted: 245, patientRating: 4.9 },
  { pair: 'Chen + Wilson', score: 91, callsCompleted: 189, patientRating: 4.7 },
  { pair: 'Davis + Park', score: 78, callsCompleted: 156, patientRating: 4.3 },
]

const sentimentTrend = [
  { month: 'Aug', score: 72 }, { month: 'Sep', score: 68 }, { month: 'Oct', score: 75 },
  { month: 'Nov', score: 71 }, { month: 'Dec', score: 78 }, { month: 'Jan', score: 82 },
]

const radarData = [
  { metric: 'Engagement', value: 82 },
  { metric: 'Satisfaction', value: 78 },
  { metric: 'Retention', value: 85 },
  { metric: 'Performance', value: 88 },
  { metric: 'Development', value: 72 },
  { metric: 'Wellness', value: 76 },
]

export default function AIInsightsPage() {
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = () => {
    setRefreshing(true)
    setTimeout(() => setRefreshing(false), 2000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">AI Workforce Intelligence</h1>
                <p className="text-purple-300">Predictive analytics powered by machine learning</p>
              </div>
            </div>
          </div>
          <motion.button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 rounded-xl text-purple-300 transition-colors"
            whileTap={{ scale: 0.95 }}
          >
            <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh Insights
          </motion.button>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2 bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-red-500/30 p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-white">Turnover Risk Prediction</h2>
                  <p className="text-slate-400 text-sm">AI-identified flight risks requiring attention</p>
                </div>
              </div>
              <span className="px-3 py-1 bg-red-500/20 text-red-400 text-sm rounded-full">3 High Risk</span>
            </div>
            
            <div className="space-y-4">
              {turnoverRisk.map((emp, i) => (
                <motion.div
                  key={emp.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + i * 0.1 }}
                  className="flex items-center gap-4 p-4 bg-slate-900/50 rounded-xl border border-slate-700/50 hover:border-red-500/30 transition-colors cursor-pointer"
                >
                  <div className="relative">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center text-white font-bold">
                      {emp.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div className={`absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${emp.risk > 80 ? 'bg-red-500' : emp.risk > 60 ? 'bg-orange-500' : 'bg-yellow-500'} text-white`}>
                      {emp.risk}
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="text-white font-medium">{emp.name}</h3>
                      <span className={`text-sm font-bold ${emp.risk > 80 ? 'text-red-400' : emp.risk > 60 ? 'text-orange-400' : 'text-yellow-400'}`}>
                        {emp.risk}% Risk
                      </span>
                    </div>
                    <p className="text-slate-400 text-sm">{emp.role}</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {emp.factors.map((f, j) => (
                        <span key={j} className="px-2 py-1 bg-slate-800 text-slate-300 text-xs rounded-lg">{f}</span>
                      ))}
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-500" />
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-purple-500/30 p-6"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <Heart className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Workforce Sentiment</h2>
                <p className="text-slate-400 text-sm">Employee mood analysis</p>
              </div>
            </div>
            
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%" minWidth={320} minHeight={160}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#475569" />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <Radar name="Score" dataKey="value" stroke="#a855f7" fill="#a855f7" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            
            <div className="mt-4 pt-4 border-t border-slate-700">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-sm">Overall Score</span>
                <span className="text-2xl font-bold text-purple-400">82%</span>
              </div>
              <div className="flex items-center gap-2 mt-2 text-emerald-400 text-sm">
                <TrendingUp className="w-4 h-4" />
                <span>+4% from last month</span>
              </div>
            </div>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-emerald-500/30 p-6"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                <Zap className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Optimal Shift Recommendations</h2>
                <p className="text-slate-400 text-sm">AI-powered scheduling suggestions for you</p>
              </div>
            </div>
            
            <div className="space-y-3">
              {shiftRecommendations.map((rec, i) => (
                <motion.div
                  key={rec.shift}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 + i * 0.1 }}
                  className="p-4 bg-slate-900/50 rounded-xl border border-slate-700/50 hover:border-emerald-500/30 transition-colors cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-white font-medium">{rec.shift}</h3>
                    <div className="flex items-center gap-1">
                      <Sparkles className="w-4 h-4 text-emerald-400" />
                      <span className="text-emerald-400 font-bold">{rec.score}%</span>
                    </div>
                  </div>
                  <p className="text-slate-400 text-sm">{rec.reason}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-blue-500/30 p-6"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Target className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Performance Predictions</h2>
                <p className="text-slate-400 text-sm">30-day performance forecast</p>
              </div>
            </div>
            
            <div className="space-y-3">
              {performancePredictions.map((pred, i) => (
                <motion.div
                  key={pred.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.1 }}
                  className="p-4 bg-slate-900/50 rounded-xl border border-slate-700/50"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-white font-medium">{pred.name}</h3>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400">{pred.current}</span>
                      <span className="text-slate-500">→</span>
                      <span className={pred.trend === 'up' ? 'text-emerald-400' : 'text-red-400'}>{pred.predicted}</span>
                      {pred.trend === 'up' ? <TrendingUp className="w-4 h-4 text-emerald-400" /> : <TrendingDown className="w-4 h-4 text-red-400" />}
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {pred.factors.map((f, j) => (
                      <span key={j} className={`px-2 py-1 text-xs rounded-lg ${pred.trend === 'up' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>{f}</span>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-cyan-500/30 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                <Users className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Team Chemistry Scoring</h2>
                <p className="text-slate-400 text-sm">AI-analyzed partner compatibility based on performance data</p>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {teamChemistry.map((team, i) => (
              <motion.div
                key={team.pair}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6 + i * 0.1 }}
                className="p-4 bg-slate-900/50 rounded-xl border border-slate-700/50 text-center"
              >
                <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                  <span className="text-2xl font-bold text-white">{team.score}</span>
                </div>
                <h3 className="text-white font-medium mb-2">{team.pair}</h3>
                <div className="flex justify-center gap-4 text-sm">
                  <div>
                    <p className="text-slate-400">Calls</p>
                    <p className="text-white font-semibold">{team.callsCompleted}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">Rating</p>
                    <p className="text-emerald-400 font-semibold">{team.patientRating}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
