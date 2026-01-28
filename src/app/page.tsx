"use client"

import Link from "next/link"

const portals = [
  {
    name: "Patient Portal",
    description: "Bill pay, records access, and inquiries",
    link: "/portals/patient/login",
    gradient: "from-blue-600 to-cyan-600",
    icon: (
      <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
    users: "Patients, Legal Guardians",
  },
  {
    name: "EMS Portal",
    description: "Crew operations, scheduling, and documentation",
    link: "/portals/ems/login",
    gradient: "from-red-600 to-orange-600",
    icon: (
      <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    users: "Paramedics, EMTs, Dispatchers",
  },
  {
    name: "Fire Portal",
    description: "Fire-based EMS operations and reporting",
    link: "/portals/fire/login",
    gradient: "from-red-700 to-red-500",
    icon: (
      <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
      </svg>
    ),
    users: "Fire Officers, Station Captains",
  },
  {
    name: "Carefusion Telehealth Portal",
    description: "Remote clinical consultation and telemedicine",
    link: "/portals/carefusion/login",
    gradient: "from-purple-600 to-pink-600",
    icon: (
      <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
    users: "Physicians, Nurse Practitioners",
  },
  {
    name: "TransportLink Portal",
    description: "Facility-facing transport request and tracking",
    link: "/portals/transportlink/login",
    gradient: "from-cyan-600 to-teal-600",
    icon: (
      <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
    users: "Hospitals, SNFs, ALFs",
  },
  {
    name: "Dispatch Portal",
    description: "Real-time emergency dispatch and incident management",
    link: "/portals/dispatch/login",
    gradient: "from-orange-600 to-amber-600",
    icon: (
      <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
      </svg>
    ),
    users: "Dispatchers, Dispatch Supervisors",
  },
  {
    name: "Scheduling Portal",
    description: "Crew scheduling and shift management",
    link: "/portals/scheduling/login",
    gradient: "from-violet-600 to-purple-600",
    icon: (
      <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
    users: "Schedulers, Crew Members, Supervisors",
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-orange-600/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl"></div>
      </div>

      <div className="relative">
        <nav className="border-b border-gray-800/50 backdrop-blur-xl bg-black/20">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xl">Q</span>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">FusionEMS Quantum</h1>
                  <p className="text-xs text-gray-400">Enterprise EMS Operating System</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <Link href="/about" className="text-gray-400 hover:text-white transition-colors text-sm">
                  About
                </Link>
                <Link href="/support" className="text-gray-400 hover:text-white transition-colors text-sm">
                  Support
                </Link>
                <Link href="/contact" className="text-gray-400 hover:text-white transition-colors text-sm">
                  Contact
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-6 py-16">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-bold text-white mb-4">
              Welcome to <span className="bg-gradient-to-r from-orange-500 to-red-600 bg-clip-text text-transparent">FusionEMS Quantum</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              The complete platform for modern EMS operations. Six integrated modules powering dispatch, patient care, billing, fleet operations, analytics, and compliance for emergency medical services.
            </p>
          </div>

          <div className="mb-12">
            <h3 className="text-2xl font-bold text-white mb-6 text-center">Access Portals</h3>
            <p className="text-gray-400 text-center mb-8">Select your portal to sign in</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            {portals.map((portal) => (
              <Link
                key={portal.name}
                href={portal.link}
                className="group bg-gray-900/30 backdrop-blur-xl border border-gray-800/50 rounded-2xl p-8 hover:border-gray-700 transition-all hover:shadow-2xl hover:scale-105"
              >
                <div className={`inline-flex items-center justify-center w-16 h-16 rounded-xl bg-gradient-to-br ${portal.gradient} mb-6 group-hover:scale-110 transition-transform`}>
                  {portal.icon}
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">{portal.name}</h3>
                <p className="text-gray-400 mb-4">{portal.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">{portal.users}</span>
                  <svg className="w-5 h-5 text-gray-600 group-hover:text-orange-500 group-hover:translate-x-1 transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </div>
              </Link>
            ))}
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-orange-500/10 mb-4">
                <svg className="w-8 h-8 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-white mb-2">HIPAA Compliant</h4>
              <p className="text-sm text-gray-400">End-to-end encryption and secure authentication</p>
            </div>
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-cyan-500/10 mb-4">
                <svg className="w-8 h-8 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-white mb-2">99.9% Uptime</h4>
              <p className="text-sm text-gray-400">Enterprise-grade reliability and performance</p>
            </div>
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-500/10 mb-4">
                <svg className="w-8 h-8 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-white mb-2">24/7 Support</h4>
              <p className="text-sm text-gray-400">Always available technical and clinical support</p>
            </div>
          </div>
        </main>

        <footer className="border-t border-gray-800/50 mt-16">
          <div className="max-w-7xl mx-auto px-6 py-8">
            <div className="flex flex-col md:flex-row items-center justify-between">
              <p className="text-gray-500 text-sm">2024 FusionEMS Quantum. All rights reserved.</p>
              <div className="flex items-center space-x-6 mt-4 md:mt-0">
                <Link href="/privacy" className="text-gray-500 hover:text-gray-400 text-sm transition-colors">
                  Privacy
                </Link>
                <Link href="/terms" className="text-gray-500 hover:text-gray-400 text-sm transition-colors">
                  Terms
                </Link>
                <Link href="/security" className="text-gray-500 hover:text-gray-400 text-sm transition-colors">
                  Security
                </Link>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}
