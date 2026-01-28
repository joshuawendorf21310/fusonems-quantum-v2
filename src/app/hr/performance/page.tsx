"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { TrendingUp, Star, Calendar, FileText } from "lucide-react";

export default function PerformancePage() {
  const [reviews, setReviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/hr/performance/reviews", { credentials: "include" })
      .then((r) => r.ok && r.json())
      .then((data) => setReviews(data || []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center"><div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div></div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">Performance Reviews</h1>
          <button className="px-6 py-2 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-lg flex items-center gap-2"><FileText size={20} />New Review</button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[{label: "Total Reviews", value: reviews.length}, {label: "Completed", value: reviews.filter(r => r.status === "completed").length}, {label: "Pending", value: reviews.filter(r => r.status === "pending").length}, {label: "Avg Rating", value: "4.2"}].map((stat, idx) => (
            <div key={idx} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6"><div className="text-3xl font-bold text-blue-400">{stat.value}</div><div className="text-sm text-zinc-400 mt-1">{stat.label}</div></div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {reviews.length === 0 ? <div className="col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl p-12 text-center"><FileText size={64} className="mx-auto mb-4 text-zinc-600" /><p className="text-zinc-500">No performance reviews found</p></div> : reviews.map((review) => (
            <motion.div key={review.id} whileHover={{ y: -2 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <div className="flex items-start justify-between mb-4">
                <div><Link href={`/hr/personnel/${review.personnel_id}`} className="text-xl font-bold text-blue-400 hover:text-blue-300">{review.personnel_name}</Link><p className="text-sm text-zinc-400">{review.review_period}</p></div>
                <div className="flex items-center gap-2 bg-yellow-500/20 px-3 py-1 rounded-lg"><Star className="text-yellow-400" size={16} /><span className="font-bold text-yellow-400">{review.overall_rating}</span></div>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-zinc-400">Reviewer:</span><span>{review.reviewer_name}</span></div>
                <div className="flex justify-between"><span className="text-zinc-400">Review Date:</span><span>{new Date(review.review_date).toLocaleDateString()}</span></div>
                <div className="flex justify-between"><span className="text-zinc-400">Status:</span><span className={`px-2 py-1 rounded text-xs ${review.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-yellow-500/20 text-yellow-400'}`}>{review.status}</span></div>
              </div>
              {review.summary && <div className="mt-4 pt-4 border-t border-zinc-800 text-sm text-zinc-400">{review.summary}</div>}
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
