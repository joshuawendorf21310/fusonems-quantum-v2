"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  ArrowLeft,
  PlayCircle,
  CheckCircle,
  Clock,
  Award,
  Users,
  Star,
  BookOpen,
  FileText,
  Video,
  Download,
  Share2,
} from "lucide-react";

interface CourseDetail {
  id: number;
  course_code: string;
  course_name: string;
  course_description: string;
  course_category: string;
  duration_hours: number;
  ceu_credits: number;
  grants_certification: boolean;
  certification_name: string | null;
  prerequisites: string[];
  active: boolean;
}

interface Enrollment {
  id: number;
  enrollment_date: string;
  progress_percentage: number;
  status: string;
  completion_date: string | null;
  score: number | null;
}

interface Lesson {
  id: number;
  title: string;
  duration: number;
  completed: boolean;
  type: string;
}

export default function CourseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params.id as string;

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [enrollment, setEnrollment] = useState<Enrollment | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);

  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        const [courseRes, enrollmentRes] = await Promise.all([
          fetch(`/api/training/courses/${courseId}`, { credentials: "include" }),
          fetch(`/api/training/enrollments?course_id=${courseId}`, { credentials: "include" }),
        ]);

        if (courseRes.ok) {
          const courseData = await courseRes.json();
          setCourse(courseData);
        }

        if (enrollmentRes.ok) {
          const enrollmentData = await enrollmentRes.json();
          if (enrollmentData.length > 0) {
            setEnrollment(enrollmentData[0]);
          }
        }
      } catch (error) {
        console.error("Error fetching course:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchCourseData();
  }, [courseId]);

  const handleEnroll = async () => {
    setEnrolling(true);
    try {
      const res = await fetch(`/api/training/enrollments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ course_id: parseInt(courseId) }),
      });

      if (res.ok) {
        const newEnrollment = await res.json();
        setEnrollment(newEnrollment);
      }
    } catch (error) {
      console.error("Error enrolling:", error);
    } finally {
      setEnrolling(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
        <div className="max-w-4xl mx-auto text-center py-12">
          <h1 className="text-2xl font-bold mb-4">Course Not Found</h1>
          <Link href="/training/courses" className="text-blue-400 hover:text-blue-300">
            Return to Courses
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Link
            href="/training/courses"
            className="inline-flex items-center gap-2 text-zinc-400 hover:text-zinc-100 mb-4"
          >
            <ArrowLeft size={20} />
            Back to Courses
          </Link>
        </motion.div>

        {/* Course Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8"
        >
          <div className="flex flex-col lg:flex-row gap-8">
            <div className="flex-1">
              <div className="inline-block px-3 py-1 bg-blue-600 rounded-lg text-sm font-medium mb-3">
                {course.course_category}
              </div>
              <h1 className="text-4xl font-bold mb-4">{course.course_name}</h1>
              <p className="text-zinc-400 text-lg mb-6">{course.course_description}</p>

              <div className="flex flex-wrap gap-6 mb-6">
                <div className="flex items-center gap-2">
                  <Clock className="text-zinc-400" size={20} />
                  <span>{course.duration_hours} hours</span>
                </div>
                <div className="flex items-center gap-2">
                  <Award className="text-emerald-400" size={20} />
                  <span>{course.ceu_credits} CEU Credits</span>
                </div>
                {course.grants_certification && (
                  <div className="flex items-center gap-2">
                    <Star className="text-yellow-400" size={20} />
                    <span>Certification: {course.certification_name}</span>
                  </div>
                )}
              </div>

              {enrollment ? (
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-zinc-400">Progress</span>
                      <span className="text-blue-400 font-semibold">
                        {enrollment.progress_percentage}%
                      </span>
                    </div>
                    <div className="h-3 bg-zinc-800 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${enrollment.progress_percentage}%` }}
                        className="h-full bg-gradient-to-r from-blue-500 to-emerald-500"
                      />
                    </div>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="bg-gradient-to-r from-blue-600 to-emerald-600 px-8 py-4 rounded-xl font-semibold text-lg flex items-center gap-2"
                  >
                    <PlayCircle size={24} />
                    {enrollment.progress_percentage > 0 ? "Continue Learning" : "Start Course"}
                  </motion.button>
                </div>
              ) : (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleEnroll}
                  disabled={enrolling}
                  className="bg-gradient-to-r from-blue-600 to-emerald-600 px-8 py-4 rounded-xl font-semibold text-lg flex items-center gap-2 disabled:opacity-50"
                >
                  <Award size={24} />
                  {enrolling ? "Enrolling..." : "Enroll Now"}
                </motion.button>
              )}
            </div>

            <div className="lg:w-80">
              <div className="bg-zinc-800 rounded-xl p-6 space-y-4">
                <h3 className="font-bold text-lg mb-4">Course Details</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Course Code</span>
                    <span className="font-mono">{course.course_code}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Duration</span>
                    <span>{course.duration_hours} hours</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">CEU Credits</span>
                    <span>{course.ceu_credits}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Level</span>
                    <span className="capitalize">{course.course_category}</span>
                  </div>
                </div>

                {course.prerequisites && course.prerequisites.length > 0 && (
                  <div className="pt-4 border-t border-zinc-700">
                    <h4 className="font-semibold mb-2">Prerequisites</h4>
                    <ul className="space-y-1 text-sm text-zinc-400">
                      {course.prerequisites.map((prereq, idx) => (
                        <li key={idx}>• {prereq}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="pt-4 border-t border-zinc-700 space-y-2">
                  <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm">
                    <Share2 size={16} />
                    Share Course
                  </button>
                  <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm">
                    <Download size={16} />
                    Download Syllabus
                  </button>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Course Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6"
        >
          <h2 className="text-2xl font-bold mb-6">Course Content</h2>
          <div className="space-y-3">
            {lessons.length === 0 ? (
              <div className="text-center py-8 text-zinc-500">
                <BookOpen size={48} className="mx-auto mb-3 opacity-50" />
                <p>Course content will be available after enrollment</p>
              </div>
            ) : (
              lessons.map((lesson, idx) => (
                <motion.div
                  key={lesson.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + idx * 0.05 }}
                  className="flex items-center gap-4 p-4 bg-zinc-800 rounded-lg border border-zinc-700 hover:border-zinc-600 cursor-pointer"
                >
                  <div className="w-10 h-10 rounded-full bg-zinc-700 flex items-center justify-center">
                    {lesson.completed ? (
                      <CheckCircle className="text-emerald-400" size={20} />
                    ) : lesson.type === "video" ? (
                      <Video className="text-zinc-400" size={20} />
                    ) : (
                      <FileText className="text-zinc-400" size={20} />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold">{lesson.title}</div>
                    <div className="text-sm text-zinc-400">{lesson.duration} min</div>
                  </div>
                  {lesson.completed && (
                    <div className="text-emerald-400 text-sm font-medium">Completed</div>
                  )}
                </motion.div>
              ))
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
