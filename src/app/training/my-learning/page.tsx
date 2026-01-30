"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  Award,
  Clock,
  TrendingUp,
  Download,
  Play,
  CheckCircle,
  Bookmark,
  Flame,
  Calendar,
  BarChart3,
} from "lucide-react";
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function MyLearning() {
  const [activeTab, setActiveTab] = useState<"in-progress" | "completed" | "bookmarked">("in-progress");

  const coursesInProgress = [
    {
      id: 1,
      title: "Advanced Cardiac Life Support",
      instructor: "Dr. Sarah Mitchell",
      progress: 68,
      thumbnail: "bg-gradient-to-br from-red-500 to-pink-600",
      totalLessons: 24,
      completedLessons: 16,
      timeSpent: "4h 32m",
      lastAccessed: "2 hours ago",
      nextLesson: "Cardiac Arrest Management",
    },
    {
      id: 2,
      title: "Trauma Assessment",
      instructor: "Dr. James Wilson",
      progress: 42,
      thumbnail: "bg-gradient-to-br from-emerald-500 to-teal-600",
      totalLessons: 18,
      completedLessons: 8,
      timeSpent: "2h 18m",
      lastAccessed: "Yesterday",
      nextLesson: "Multi-System Trauma",
    },
    {
      id: 3,
      title: "Hazmat Operations",
      instructor: "Capt. John Davis",
      progress: 85,
      thumbnail: "bg-gradient-to-br from-yellow-500 to-orange-600",
      totalLessons: 12,
      completedLessons: 10,
      timeSpent: "3h 45m",
      lastAccessed: "3 days ago",
      nextLesson: "Final Assessment",
    },
  ];

  const completedCourses = [
    {
      id: 1,
      title: "Pediatric Advanced Life Support",
      instructor: "Dr. Lisa Martinez",
      completedDate: "Jan 15, 2026",
      score: 98,
      ce: 6,
      thumbnail: "bg-gradient-to-br from-blue-500 to-cyan-600",
      certificateUrl: "#",
    },
    {
      id: 2,
      title: "Basic Life Support",
      instructor: "Lt. Mike Rodriguez",
      completedDate: "Jan 8, 2026",
      score: 95,
      ce: 4,
      thumbnail: "bg-gradient-to-br from-purple-500 to-indigo-600",
      certificateUrl: "#",
    },
    {
      id: 3,
      title: "EMS Safety & Wellness",
      instructor: "Chief Amy Chen",
      completedDate: "Dec 28, 2025",
      score: 100,
      ce: 2,
      thumbnail: "bg-gradient-to-br from-green-500 to-emerald-600",
      certificateUrl: "#",
    },
  ];

  const bookmarkedCourses = [
    {
      id: 1,
      title: "Tactical EMS Operations",
      instructor: "Lt. Mike Rodriguez",
      duration: "10 hours",
      ce: 10,
      thumbnail: "bg-gradient-to-br from-slate-700 to-slate-900",
    },
    {
      id: 2,
      title: "Disaster Response Leadership",
      instructor: "Chief Amy Chen",
      duration: "12 hours",
      ce: 12,
      thumbnail: "bg-gradient-to-br from-orange-500 to-red-600",
    },
  ];

  const learningStats = {
    totalHours: 47,
    coursesCompleted: 24,
    currentStreak: 12,
    longestStreak: 28,
    totalCE: 156,
  };

  const weeklyData = [
    { day: "Mon", hours: 2.5 },
    { day: "Tue", hours: 3.2 },
    { day: "Wed", hours: 1.8 },
    { day: "Thu", hours: 4.1 },
    { day: "Fri", hours: 2.9 },
    { day: "Sat", hours: 3.5 },
    { day: "Sun", hours: 2.2 },
  ];

  const monthlyProgress = [
    { month: "Aug", courses: 3 },
    { month: "Sep", courses: 5 },
    { month: "Oct", courses: 4 },
    { month: "Nov", courses: 6 },
    { month: "Dec", courses: 4 },
    { month: "Jan", courses: 2 },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            My Learning
          </h1>
          <p className="text-slate-400 mt-2">Track your progress and achievements</p>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl p-6"
          >
            <Flame className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-1">{learningStats.currentStreak}</div>
            <p className="text-orange-100 text-sm">Day Streak</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-2xl p-6"
          >
            <Clock className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-1">{learningStats.totalHours}h</div>
            <p className="text-blue-100 text-sm">Total Time</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-emerald-600 to-emerald-800 rounded-2xl p-6"
          >
            <CheckCircle className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-1">{learningStats.coursesCompleted}</div>
            <p className="text-emerald-100 text-sm">Completed</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-2xl p-6"
          >
            <Award className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-1">{learningStats.totalCE}</div>
            <p className="text-purple-100 text-sm">CE Credits</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="bg-gradient-to-br from-pink-600 to-pink-800 rounded-2xl p-6"
          >
            <TrendingUp className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-1">{learningStats.longestStreak}</div>
            <p className="text-pink-100 text-sm">Best Streak</p>
          </motion.div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Weekly Activity */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-2xl p-6"
            style={{ minWidth: 320, minHeight: 160 }}
          >
            <div className="flex items-center gap-2 mb-6">
              <BarChart3 size={24} />
              <h2 className="text-2xl font-bold">This Week</h2>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={weeklyData}>
                <defs>
                  <linearGradient id="colorHours" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="day" stroke="#94A3B8" />
                <YAxis stroke="#94A3B8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1E293B",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="hours"
                  stroke="#3B82F6"
                  fillOpacity={1}
                  fill="url(#colorHours)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Monthly Progress */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-2xl p-6"
          >
            <div className="flex items-center gap-2 mb-6">
              <Calendar size={24} />
              <h2 className="text-2xl font-bold">Monthly Progress</h2>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={monthlyProgress}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="month" stroke="#94A3B8" />
                <YAxis stroke="#94A3B8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1E293B",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="courses"
                  stroke="#10B981"
                  strokeWidth={3}
                  dot={{ fill: "#10B981", r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="flex gap-3"
        >
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setActiveTab("in-progress")}
            className={`px-6 py-3 rounded-xl font-semibold transition-all ${
              activeTab === "in-progress"
                ? "bg-gradient-to-r from-blue-600 to-emerald-600"
                : "bg-slate-800 hover:bg-slate-700"
            }`}
          >
            In Progress ({coursesInProgress.length})
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setActiveTab("completed")}
            className={`px-6 py-3 rounded-xl font-semibold transition-all ${
              activeTab === "completed"
                ? "bg-gradient-to-r from-blue-600 to-emerald-600"
                : "bg-slate-800 hover:bg-slate-700"
            }`}
          >
            Completed ({completedCourses.length})
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setActiveTab("bookmarked")}
            className={`px-6 py-3 rounded-xl font-semibold transition-all ${
              activeTab === "bookmarked"
                ? "bg-gradient-to-r from-blue-600 to-emerald-600"
                : "bg-slate-800 hover:bg-slate-700"
            }`}
          >
            Bookmarked ({bookmarkedCourses.length})
          </motion.button>
        </motion.div>

        {/* Content */}
        {activeTab === "in-progress" && (
          <div className="grid grid-cols-1 gap-6">
            {coursesInProgress.map((course, idx) => (
              <motion.div
                key={course.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8 + idx * 0.1 }}
                whileHover={{ scale: 1.01 }}
                className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-2xl p-6 hover:border-slate-600 transition-all"
              >
                <div className="flex items-start gap-6">
                  <div
                    className={`${course.thumbnail} w-32 h-32 rounded-xl flex items-center justify-center text-4xl font-bold flex-shrink-0`}
                  >
                    {course.title.slice(0, 1)}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold mb-2">{course.title}</h3>
                    <p className="text-slate-400 mb-4">{course.instructor}</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                      <div>
                        <div className="text-slate-400">Progress</div>
                        <div className="font-semibold text-blue-400">{course.progress}%</div>
                      </div>
                      <div>
                        <div className="text-slate-400">Lessons</div>
                        <div className="font-semibold">
                          {course.completedLessons}/{course.totalLessons}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400">Time Spent</div>
                        <div className="font-semibold">{course.timeSpent}</div>
                      </div>
                      <div>
                        <div className="text-slate-400">Last Accessed</div>
                        <div className="font-semibold">{course.lastAccessed}</div>
                      </div>
                    </div>
                    <div className="mb-4">
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-slate-400">Next: {course.nextLesson}</span>
                      </div>
                      <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${course.progress}%` }}
                          className="h-full bg-gradient-to-r from-blue-500 to-emerald-500"
                        />
                      </div>
                    </div>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="bg-gradient-to-r from-blue-600 to-emerald-600 px-6 py-3 rounded-xl font-semibold flex items-center gap-2"
                    >
                      <Play size={18} />
                      Continue Learning
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {activeTab === "completed" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {completedCourses.map((course, idx) => (
              <motion.div
                key={course.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 + idx * 0.1 }}
                whileHover={{ scale: 1.03, y: -5 }}
                className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-2xl overflow-hidden hover:border-slate-600 transition-all"
              >
                <div
                  className={`${course.thumbnail} h-48 flex items-center justify-center text-6xl font-bold relative`}
                >
                  {course.title.slice(0, 1)}
                  <div className="absolute top-4 right-4 bg-emerald-600 px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1">
                    <CheckCircle size={12} />
                    Completed
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="font-bold text-lg mb-2">{course.title}</h3>
                  <p className="text-sm text-slate-400 mb-4">{course.instructor}</p>
                  <div className="space-y-2 text-sm mb-4">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Completed</span>
                      <span className="font-semibold">{course.completedDate}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Score</span>
                      <span className="font-semibold text-emerald-400">{course.score}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">CE Credits</span>
                      <span className="font-semibold">{course.ce} CE</span>
                    </div>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full bg-slate-800 hover:bg-slate-700 py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-colors"
                  >
                    <Download size={18} />
                    Download Certificate
                  </motion.button>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {activeTab === "bookmarked" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {bookmarkedCourses.map((course, idx) => (
              <motion.div
                key={course.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 + idx * 0.1 }}
                whileHover={{ scale: 1.03, y: -5 }}
                className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-2xl overflow-hidden hover:border-slate-600 transition-all"
              >
                <div
                  className={`${course.thumbnail} h-48 flex items-center justify-center text-6xl font-bold relative`}
                >
                  {course.title.slice(0, 1)}
                  <div className="absolute top-4 right-4 bg-yellow-600 px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1">
                    <Bookmark size={12} />
                    Saved
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="font-bold text-lg mb-2">{course.title}</h3>
                  <p className="text-sm text-slate-400 mb-4">{course.instructor}</p>
                  <div className="flex items-center gap-4 text-sm text-slate-400 mb-4">
                    <div className="flex items-center gap-1">
                      <Clock size={14} />
                      {course.duration}
                    </div>
                    <div className="bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded">
                      {course.ce} CE
                    </div>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full bg-gradient-to-r from-blue-600 to-emerald-600 py-3 rounded-xl font-semibold flex items-center justify-center gap-2"
                  >
                    <BookOpen size={18} />
                    Enroll Now
                  </motion.button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
