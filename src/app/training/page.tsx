"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Flame,
  TrendingUp,
  Trophy,
  Calendar,
  Award,
  PlayCircle,
  ChevronRight,
  Clock,
  Target,
  Zap,
  Star,
  BookOpen,
  Users,
  AlertCircle,
} from "lucide-react";
import {
  CircularProgressbar,
  buildStyles,
} from "react-circular-progressbar";
import "react-circular-progressbar/dist/styles.css";
import { PageShell } from "@/components/PageShell";

interface DashboardStats {
  total_courses: number;
  enrolled_courses: number;
  completed_courses: number;
  total_xp: number;
  streak_days: number;
  upcoming_certifications: number;
}

interface Course {
  id: number;
  course_name: string;
  progress: number;
  next_lesson: string;
  time_remaining: string;
  color: string;
}

interface Certification {
  id: number;
  certification_type: string;
  expiration_date: string;
  days_until_expiry: number;
  status: string;
}

export default function TrainingDashboard() {
  const [streak, setStreak] = useState(0);
  const [streakAnimation, setStreakAnimation] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [courses, setCoursesInProgress] = useState<Course[]>([]);
  const [certifications, setCertifications] = useState<Certification[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, coursesRes, certsRes] = await Promise.all([
          fetch("/api/training/dashboard/stats", { credentials: "include" }),
          fetch("/api/training/enrollments?status=in_progress&limit=3", { credentials: "include" }),
          fetch("/api/training/certifications/expiring?days=30", { credentials: "include" }),
        ]);

        if (statsRes.ok) {
          const data = await statsRes.json();
          setStats(data);
          setStreak(data.streak_days || 0);
          setStreakAnimation(true);
        }
        if (coursesRes.ok) setCoursesInProgress(await coursesRes.json());
        if (certsRes.ok) setCertifications(await certsRes.json());
      } catch (error) {
        console.error("Error fetching training data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <PageShell title="Training & Education" requireAuth={true}>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell title="Training & Education" requireAuth={true}>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-between items-center"
        >
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
              Training Dashboard
            </h1>
            <p className="text-slate-400 mt-2">Continue your learning journey</p>
          </div>
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="bg-gradient-to-r from-blue-600 to-emerald-600 px-6 py-3 rounded-xl cursor-pointer shadow-lg shadow-blue-500/50"
          >
            <span className="font-semibold">Browse Courses</span>
          </motion.div>
        </motion.div>

        {/* Streak & Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl p-6 relative overflow-hidden"
          >
            <div className="absolute -right-8 -top-8 opacity-20">
              <Flame size={120} />
            </div>
            <div className="relative z-10">
              <Flame className="mb-3" size={32} />
              <div className="text-5xl font-bold mb-2">
                {streakAnimation && (
                  <motion.span
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                  >
                    {streak}
                  </motion.span>
                )}
              </div>
              <p className="text-orange-100">Day Learning Streak</p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-2xl p-6"
          >
            <BookOpen className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-2">{stats?.enrolled_courses || 0}</div>
            <p className="text-blue-100">Courses In Progress</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-emerald-600 to-emerald-800 rounded-2xl p-6"
          >
            <Award className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-2">{stats?.completed_courses || 0}</div>
            <p className="text-emerald-100">Completed Courses</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-2xl p-6"
          >
            <Trophy className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-2">{stats?.total_xp || 0}</div>
            <p className="text-purple-100">Total XP Points</p>
          </motion.div>
        </div>

        {/* Courses in Progress */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6"
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Continue Learning</h2>
            <Link href="/training/my-learning" className="text-blue-400 hover:text-blue-300 flex items-center gap-2">
              View All <ChevronRight size={16} />
            </Link>
          </div>
          {courses.length === 0 ? (
            <div className="text-center py-8 text-zinc-500">
              <BookOpen size={48} className="mx-auto mb-3 opacity-50" />
              <p>No courses in progress. Browse the catalog to get started!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {courses.map((course, idx) => (
                <motion.div
                  key={course.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + idx * 0.1 }}
                  whileHover={{ scale: 1.02, y: -5 }}
                  className="bg-zinc-800 rounded-xl p-6 border border-zinc-700 hover:border-zinc-600 transition-all cursor-pointer"
                >
                  <div className="flex items-start gap-4">
                    <div style={{ width: 80, height: 80 }}>
                      <CircularProgressbar
                        value={course.progress}
                        text={`${course.progress}%`}
                        styles={buildStyles({
                          textColor: "#fff",
                          pathColor: course.color,
                          trailColor: "#27272a",
                          textSize: "20px",
                        })}
                      />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold mb-2">{course.course_name}</h3>
                      <div className="text-sm text-zinc-400 mb-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Clock size={14} />
                          {course.time_remaining} remaining
                        </div>
                        <div className="text-zinc-500">Next: {course.next_lesson}</div>
                      </div>
                      <Link href={`/training/courses/${course.id}`}>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          className="bg-gradient-to-r from-blue-600 to-emerald-600 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 w-full justify-center"
                        >
                          <PlayCircle size={16} />
                          Resume
                        </motion.button>
                      </Link>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>

        {/* Upcoming Certifications Alert */}
        {certifications.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-orange-900/20 border border-orange-700 rounded-2xl p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle className="text-orange-500" size={24} />
              <h2 className="text-xl font-bold">Certifications Expiring Soon</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {certifications.slice(0, 3).map((cert) => (
                <div key={cert.id} className="bg-zinc-800 rounded-lg p-4 border border-orange-700">
                  <div className="font-semibold mb-1">{cert.certification_type}</div>
                  <div className="text-sm text-zinc-400">
                    Expires in {cert.days_until_expiry} days
                  </div>
                  <div className="text-xs text-orange-400 mt-1">
                    {new Date(cert.expiration_date).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
            <Link
              href="/training/certifications"
              className="mt-4 inline-block text-orange-400 hover:text-orange-300 text-sm"
            >
              View all certifications →
            </Link>
          </motion.div>
        )}

        {/* Recommended Courses & Leaderboard */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-2xl p-6"
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Quick Actions</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Browse Courses", icon: BookOpen, href: "/training/courses" },
                { label: "Certifications", icon: Award, href: "/training/certifications" },
                { label: "Skill Checks", icon: Target, href: "/training/skillchecks" },
                { label: "Leaderboard", icon: Trophy, href: "/training/leaderboard" },
              ].map((action, idx) => (
                <Link key={idx} href={action.href}>
                  <motion.div
                    whileHover={{ scale: 1.05, y: -5 }}
                    whileTap={{ scale: 0.95 }}
                    className="bg-zinc-800 rounded-xl p-6 text-center cursor-pointer border border-zinc-700 hover:border-zinc-600"
                  >
                    <action.icon className="mx-auto mb-3" size={32} />
                    <div className="font-semibold text-sm">{action.label}</div>
                  </motion.div>
                </Link>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6"
          >
            <div className="flex items-center gap-2 mb-6">
              <Calendar size={24} />
              <h2 className="text-2xl font-bold">Upcoming</h2>
            </div>
            <div className="space-y-3">
              {stats && stats.upcoming_certifications > 0 ? (
                <div className="bg-zinc-800 rounded-xl p-4 border-l-4 border-orange-500">
                  <div className="font-semibold mb-1">Certifications Due</div>
                  <div className="text-sm text-zinc-400">
                    {stats.upcoming_certifications} certification(s) expiring soon
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-zinc-500">
                  <Calendar size={48} className="mx-auto mb-3 opacity-50" />
                  <p className="text-sm">No upcoming deadlines</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </PageShell>
  );
}
