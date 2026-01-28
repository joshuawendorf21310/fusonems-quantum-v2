"use client"

import Link from "next/link"

export default function CareFusionPortalSelector() {
  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 -right-20 w-96 h-96 bg-gradient-to-br from-cyan-600 to-blue-600 rounded-full opacity-10 blur-3xl"></div>
        <div className="absolute bottom-20 -left-20 w-96 h-96 bg-gradient-to-br from-purple-600 to-pink-600 rounded-full opacity-10 blur-3xl"></div>
      </div>

      <div className="relative z-10 w-full max-w-5xl">
        <Link href="/" className="absolute -top-16 left-0 text-gray-400 hover:text-white transition-colors flex items-center space-x-2">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back to Home</span>
        </Link>

        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-600 via-purple-600 to-pink-600 mb-6">
            <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <h1 className="text-5xl font-bold text-white mb-4">CareFusion Telehealth</h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Select your portal to access secure healthcare services
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <Link href="/portals/carefusion/patient/login">
            <div className="group bg-gradient-to-br from-cyan-600 to-blue-600 rounded-2xl p-8 hover:scale-105 transition-transform duration-300 cursor-pointer border-2 border-transparent hover:border-cyan-400">
              <div className="flex items-center justify-center w-16 h-16 bg-white/20 backdrop-blur-sm rounded-xl mb-6">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h2 className="text-3xl font-bold text-white mb-3">Patient Portal</h2>
              <p className="text-white/80 mb-6">
                Access your health records, schedule virtual appointments, and manage your healthcare
              </p>
              <div className="flex items-center text-white font-semibold">
                <span>Sign in as Patient</span>
                <svg className="w-5 h-5 ml-2 group-hover:translate-x-2 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>
            </div>
          </Link>

          <Link href="/portals/carefusion/provider/login">
            <div className="group bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl p-8 hover:scale-105 transition-transform duration-300 cursor-pointer border-2 border-transparent hover:border-purple-400">
              <div className="flex items-center justify-center w-16 h-16 bg-white/20 backdrop-blur-sm rounded-xl mb-6">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <h2 className="text-3xl font-bold text-white mb-3">Provider Portal</h2>
              <p className="text-white/80 mb-6">
                Deliver remote care with integrated clinical tools and patient management
              </p>
              <div className="flex items-center text-white font-semibold">
                <span>Sign in as Provider</span>
                <svg className="w-5 h-5 ml-2 group-hover:translate-x-2 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>
            </div>
          </Link>
        </div>

        <div className="mt-12 text-center">
          <p className="text-gray-500 text-sm">
            Secure HIPAA-compliant telehealth platform powered by FusionEMS Quantum
          </p>
        </div>
      </div>
    </div>
  )
}
