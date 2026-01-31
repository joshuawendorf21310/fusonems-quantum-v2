'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Brain,
  Activity,
  Heart,
  TrendingUp,
  Users,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  ChevronRight,
  RefreshCw,
  Shield,
  Target,
  Sparkles,
} from 'lucide-react';

interface PredictiveInsights {
  timestamp: string;
  crew_count: number;
  fatigue_summary: {
    critical_count: number;
    high_count: number;
    action_required: boolean;
  };
  wellness_summary: {
    alerts_count: number;
    intervention_required: boolean;
    critical_required: boolean;
  };
  demand_forecast: {
    avg_daily_calls: number;
    peak_day: string;
    staffing_adequate: boolean;
  };
  skill_health: {
    concerns_count: number;
    training_recommended: boolean;
  };
}

interface FatigueScore {
  user_id: number;
  user_name?: string;
  overall_score: number;
  risk_level: string;
  recommendations: string[];
}

interface WellnessAlert {
  user_id: number;
  user_name?: string;
  severity: string;
  recommendation: string;
}

interface DemandPrediction {
  date: string;
  predicted_calls: number;
  recommended_staff: number;
  factors: string[];
}

export default function PredictiveDashboard() {
  const [insights, setInsights] = useState<PredictiveInsights | null>(null);
  const [topFatigueRisks, setTopFatigueRisks] = useState<FatigueScore[]>([]);
  const [wellnessAlerts, setWellnessAlerts] = useState<WellnessAlert[]>([]);
  const [weeklyForecast, setWeeklyForecast] = useState<DemandPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };

      const [insightsRes, fatigueRes, wellnessRes, forecastRes] = await Promise.all([
        fetch('/api/v1/scheduling/predictive/dashboard/insights', { headers }),
        fetch('/api/v1/scheduling/predictive/fatigue/high-risk?threshold=moderate', { headers }),
        fetch('/api/v1/scheduling/predictive/wellness/alerts?threshold=concern', { headers }),
        fetch('/api/v1/scheduling/predictive/demand/weekly', { headers }),
      ]);

      if (insightsRes.ok) setInsights(await insightsRes.json());
      if (fatigueRes.ok) setTopFatigueRisks((await fatigueRes.json()).slice(0, 5));
      if (wellnessRes.ok) setWellnessAlerts((await wellnessRes.json()).slice(0, 5));
      if (forecastRes.ok) {
        const data = await forecastRes.json();
        setWeeklyForecast(data.predictions || []);
      }
    } catch (error) {
      console.error('Failed to fetch predictive data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-400 bg-red-500/20';
      case 'high': return 'text-orange-400 bg-orange-500/20';
      case 'moderate': return 'text-yellow-400 bg-yellow-500/20';
      default: return 'text-green-400 bg-green-500/20';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-500/10';
      case 'intervention': return 'border-orange-500 bg-orange-500/10';
      case 'concern': return 'border-yellow-500 bg-yellow-500/10';
      default: return 'border-zinc-600 bg-zinc-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <Brain className="w-12 h-12 text-orange-500 animate-pulse mx-auto mb-4" />
          <p className="text-zinc-400">Loading predictive insights...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <Brain className="w-8 h-8 text-orange-500" />
              <h1 className="text-3xl font-bold">Predictive Intelligence</h1>
              <span className="px-2 py-1 text-xs bg-orange-500/20 text-orange-400 rounded-full">
                AI-Powered
              </span>
            </div>
            <p className="text-zinc-400">Patent-pending workforce optimization algorithms</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center space-x-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Link href="/scheduling/predictive/fatigue">
            <div className={`p-6 rounded-xl border transition-all hover:scale-105 cursor-pointer ${
              insights?.fatigue_summary.action_required 
                ? 'border-red-500 bg-red-500/10' 
                : 'border-zinc-700 bg-zinc-900'
            }`}>
              <div className="flex items-center justify-between mb-4">
                <Activity className={`w-8 h-8 ${
                  insights?.fatigue_summary.action_required ? 'text-red-400' : 'text-orange-400'
                }`} />
                {insights?.fatigue_summary.action_required && (
                  <AlertTriangle className="w-5 h-5 text-red-400 animate-pulse" />
                )}
              </div>
              <h3 className="text-lg font-semibold mb-1">Fatigue Monitor</h3>
              <div className="flex items-baseline space-x-2">
                <span className="text-3xl font-bold text-red-400">
                  {insights?.fatigue_summary.critical_count || 0}
                </span>
                <span className="text-zinc-400">critical</span>
                <span className="text-xl font-bold text-orange-400">
                  {insights?.fatigue_summary.high_count || 0}
                </span>
                <span className="text-zinc-400">high</span>
              </div>
            </div>
          </Link>

          <Link href="/scheduling/predictive/wellness">
            <div className={`p-6 rounded-xl border transition-all hover:scale-105 cursor-pointer ${
              insights?.wellness_summary.critical_required
                ? 'border-red-500 bg-red-500/10'
                : insights?.wellness_summary.intervention_required
                ? 'border-orange-500 bg-orange-500/10'
                : 'border-zinc-700 bg-zinc-900'
            }`}>
              <div className="flex items-center justify-between mb-4">
                <Heart className={`w-8 h-8 ${
                  insights?.wellness_summary.critical_required ? 'text-red-400' : 'text-pink-400'
                }`} />
                {insights?.wellness_summary.alerts_count > 0 && (
                  <span className="px-2 py-1 text-xs bg-orange-500 text-white rounded-full">
                    {insights.wellness_summary.alerts_count}
                  </span>
                )}
              </div>
              <h3 className="text-lg font-semibold mb-1">Wellness Center</h3>
              <div className="flex items-baseline space-x-2">
                <span className="text-3xl font-bold">
                  {insights?.wellness_summary.alerts_count || 0}
                </span>
                <span className="text-zinc-400">active alerts</span>
              </div>
            </div>
          </Link>

          <Link href="/scheduling/predictive/skills">
            <div className={`p-6 rounded-xl border transition-all hover:scale-105 cursor-pointer ${
              insights?.skill_health.training_recommended
                ? 'border-yellow-500 bg-yellow-500/10'
                : 'border-zinc-700 bg-zinc-900'
            }`}>
              <div className="flex items-center justify-between mb-4">
                <Target className="w-8 h-8 text-blue-400" />
                {insights?.skill_health.training_recommended && (
                  <Sparkles className="w-5 h-5 text-yellow-400" />
                )}
              </div>
              <h3 className="text-lg font-semibold mb-1">Skills Matrix</h3>
              <div className="flex items-baseline space-x-2">
                <span className="text-3xl font-bold text-yellow-400">
                  {insights?.skill_health.concerns_count || 0}
                </span>
                <span className="text-zinc-400">skill gaps</span>
              </div>
            </div>
          </Link>

          <Link href="/scheduling/predictive/demand">
            <div className="p-6 rounded-xl border border-zinc-700 bg-zinc-900 transition-all hover:scale-105 cursor-pointer">
              <div className="flex items-center justify-between mb-4">
                <TrendingUp className="w-8 h-8 text-green-400" />
                {insights?.demand_forecast.staffing_adequate ? (
                  <CheckCircle className="w-5 h-5 text-green-400" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-orange-400" />
                )}
              </div>
              <h3 className="text-lg font-semibold mb-1">Demand Forecast</h3>
              <div className="flex items-baseline space-x-2">
                <span className="text-3xl font-bold text-green-400">
                  {Math.round(insights?.demand_forecast.avg_daily_calls || 0)}
                </span>
                <span className="text-zinc-400">avg calls/day</span>
              </div>
            </div>
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-zinc-900 rounded-xl border border-zinc-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center space-x-2">
                <Activity className="w-5 h-5 text-orange-400" />
                <span>Top Fatigue Risks</span>
              </h2>
              <Link href="/scheduling/predictive/fatigue" className="text-orange-400 hover:text-orange-300 text-sm flex items-center">
                View All <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            
            {topFatigueRisks.length === 0 ? (
              <div className="text-center py-8 text-zinc-500">
                <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
                <p>No elevated fatigue risks detected</p>
              </div>
            ) : (
              <div className="space-y-3">
                {topFatigueRisks.map((risk) => (
                  <div key={risk.user_id} className="flex items-center justify-between p-3 bg-zinc-800 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${getRiskColor(risk.risk_level)}`}>
                        <span className="text-sm font-bold">{Math.round(risk.overall_score)}</span>
                      </div>
                      <div>
                        <p className="font-medium">{risk.user_name || `User ${risk.user_id}`}</p>
                        <p className="text-xs text-zinc-400 capitalize">{risk.risk_level} risk</p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${getRiskColor(risk.risk_level)}`}>
                      {risk.risk_level}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-zinc-900 rounded-xl border border-zinc-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center space-x-2">
                <Heart className="w-5 h-5 text-pink-400" />
                <span>Wellness Alerts</span>
              </h2>
              <Link href="/scheduling/predictive/wellness" className="text-orange-400 hover:text-orange-300 text-sm flex items-center">
                View All <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            
            {wellnessAlerts.length === 0 ? (
              <div className="text-center py-8 text-zinc-500">
                <Heart className="w-12 h-12 mx-auto mb-2 text-green-500" />
                <p>No wellness concerns detected</p>
              </div>
            ) : (
              <div className="space-y-3">
                {wellnessAlerts.map((alert) => (
                  <div key={alert.user_id} className={`p-3 rounded-lg border ${getSeverityColor(alert.severity)}`}>
                    <div className="flex items-center justify-between mb-1">
                      <p className="font-medium">{alert.user_name || `User ${alert.user_id}`}</p>
                      <span className={`px-2 py-1 text-xs rounded-full capitalize ${
                        alert.severity === 'critical' ? 'bg-red-500 text-white' :
                        alert.severity === 'intervention' ? 'bg-orange-500 text-white' :
                        'bg-yellow-500 text-black'
                      }`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-sm text-zinc-400">{alert.recommendation}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="bg-zinc-900 rounded-xl border border-zinc-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              <span>7-Day Demand Forecast</span>
            </h2>
            <Link href="/scheduling/predictive/demand" className="text-orange-400 hover:text-orange-300 text-sm flex items-center">
              Full Forecast <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          
          <div className="grid grid-cols-7 gap-2">
            {weeklyForecast.map((day) => {
              const isHighDemand = day.predicted_calls > 50;
              const date = new Date(day.date);
              return (
                <div key={day.date} className={`p-3 rounded-lg text-center ${
                  isHighDemand ? 'bg-orange-500/20 border border-orange-500/50' : 'bg-zinc-800'
                }`}>
                  <p className="text-xs text-zinc-400 mb-1">
                    {date.toLocaleDateString('en-US', { weekday: 'short' })}
                  </p>
                  <p className="text-sm font-medium mb-2">
                    {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </p>
                  <p className={`text-2xl font-bold ${isHighDemand ? 'text-orange-400' : 'text-white'}`}>
                    {Math.round(day.predicted_calls)}
                  </p>
                  <p className="text-xs text-zinc-400">calls</p>
                  <div className="mt-2 pt-2 border-t border-zinc-700">
                    <p className="text-sm">
                      <Users className="w-3 h-3 inline mr-1" />
                      {day.recommended_staff}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
          <Link href="/scheduling/predictive/pairing">
            <div className="p-4 bg-zinc-900 rounded-xl border border-zinc-700 hover:border-orange-500 transition-colors cursor-pointer">
              <Users className="w-6 h-6 text-purple-400 mb-2" />
              <h3 className="font-medium">Crew Pairing</h3>
              <p className="text-sm text-zinc-400">AI mentorship matching</p>
            </div>
          </Link>
          <Link href="/scheduling/predictive/swaps">
            <div className="p-4 bg-zinc-900 rounded-xl border border-zinc-700 hover:border-orange-500 transition-colors cursor-pointer">
              <RefreshCw className="w-6 h-6 text-blue-400 mb-2" />
              <h3 className="font-medium">Smart Swaps</h3>
              <p className="text-sm text-zinc-400">Intelligent shift exchange</p>
            </div>
          </Link>
          <Link href="/scheduling/predictive/optimizer">
            <div className="p-4 bg-zinc-900 rounded-xl border border-zinc-700 hover:border-orange-500 transition-colors cursor-pointer">
              <Zap className="w-6 h-6 text-yellow-400 mb-2" />
              <h3 className="font-medium">Auto-Optimizer</h3>
              <p className="text-sm text-zinc-400">One-click scheduling</p>
            </div>
          </Link>
          <Link href="/scheduling">
            <div className="p-4 bg-zinc-900 rounded-xl border border-zinc-700 hover:border-orange-500 transition-colors cursor-pointer">
              <Clock className="w-6 h-6 text-green-400 mb-2" />
              <h3 className="font-medium">Schedule</h3>
              <p className="text-sm text-zinc-400">Back to calendar</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
