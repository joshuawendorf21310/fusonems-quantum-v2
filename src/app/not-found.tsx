"use client"

import Link from "next/link"

export default function NotFound() {
  return (
    <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center px-6">
      <div className="relative flex w-full max-w-4xl flex-col gap-10 rounded-[34px] border border-white/20 bg-gradient-to-br from-[#020202] via-[#070707] to-[#0f0510] p-10 shadow-[0_30px_90px_rgba(0,0,0,0.85)]">
        <div className="absolute -left-10 top-6 h-32 w-32 rounded-full bg-gradient-to-br from-orange-500/30 to-red-600/0 blur-3xl" />
        <div className="absolute -right-10 bottom-10 h-24 w-24 rounded-full bg-gradient-to-br from-white/10 to-transparent blur-3xl" />
        <header className="space-y-4">
          <p className="text-xs font-semibold uppercase tracking-[0.6em] text-orange-300">FusionEMS Quantum</p>
          <h1 className="text-5xl font-black leading-tight">404 — Page not found</h1>
          <p className="text-base text-slate-300">
            The patient portal you are looking for slipped behind the scenes. We&apos;ll take you back to the secure entry point.
          </p>
        </header>
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold text-slate-400">Need assistance?</p>
            <p className="text-sm text-slate-500">Email <span className="text-orange-400">support@fusionemsquantum.com</span> or call 1-888-EMS-HELP.</p>
          </div>
          <Link
            href="/portals/patient/login"
            className="inline-flex items-center justify-center rounded-2xl bg-gradient-to-r from-orange-500 to-red-500 px-8 py-3 text-sm font-semibold text-white shadow-lg shadow-orange-500/50 transition hover:opacity-90"
          >
            Return to Patient Portal
          </Link>
        </div>
      </div>
    </div>
  )
}
