"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Mail, Phone, Calendar, Award, Clock, FileText, TrendingUp } from "lucide-react";

export default function PersonnelProfilePage() {
  const params = useParams();
  const [person, setPerson] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/hr/personnel/${params.id}`, { credentials: "include" })
      .then((r) => r.ok && r.json())
      .then((data) => setPerson(data))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) return <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center"><div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div></div>;
  if (!person) return <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6"><div className="text-center">Personnel not found</div></div>;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <Link href="/hr/personnel" className="inline-flex items-center gap-2 text-zinc-400 hover:text-zinc-100"><ArrowLeft size={20} />Back to Personnel</Link>
        
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8">
          <div className="flex gap-6">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center text-3xl font-bold">
              {person.first_name?.[0]}{person.last_name?.[0]}
            </div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold">{person.first_name} {person.last_name}</h1>
              <p className="text-zinc-400 text-lg">{person.job_title}</p>
              <div className="flex gap-4 mt-4 text-sm">
                {person.email && <div className="flex items-center gap-2"><Mail size={16} />{person.email}</div>}
                {person.phone && <div className="flex items-center gap-2"><Phone size={16} />{person.phone}</div>}
                <div className="flex items-center gap-2"><Calendar size={16} />Hired {new Date(person.hire_date).toLocaleDateString()}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><Award size={24} />Certifications</h2>
            <div className="space-y-3">
              <p className="text-zinc-500">Certifications data will load here</p>
            </div>
          </div>
          
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><Clock size={24} />Time Entries</h2>
            <div className="space-y-3">
              <p className="text-zinc-500">Time entries data will load here</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
