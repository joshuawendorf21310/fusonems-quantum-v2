"use client"

import Link from "next/link"

const internalPortals = [
  {
    name: "CAD Portal",
    icon: "cad",
    purpose: "Real-time emergency dispatch and incident management",
    users: "Dispatchers, Dispatch Supervisors",
    scope: ["Call intake", "Unit dispatch", "Incident lifecycle", "Unit status management"],
    notes: "Highest-permission environment, MFA required, immutable audit logs",
    gradient: "from-red-600 to-orange-600",
    link: "/cad"
  },
  {
    name: "Medical Transport Portal",
    icon: "transport",
    purpose: "Scheduled and non-emergency ground transport operations",
    users: "Transport coordinators, schedulers, ops supervisors",
    scope: ["Schedule transports", "Assign units", "Trip lifecycle tracking", "Operational notes"],
    notes: "Not real-time dispatch, separate from CAD authority",
    gradient: "from-orange-600 to-amber-600",
    link: "/transport"
  },
  {
    name: "Fire Module Portal",
    icon: "fire",
    purpose: "Fire-based EMS operations and reporting",
    users: "Fire officers, station captains, fire EMS administrators",
    scope: ["Incident summaries", "Staffing & readiness", "Fire/EMS reports", "QA/QI workflows"],
    notes: "Station- and battalion-scoped access",
    gradient: "from-red-700 to-red-500",
    link: "/fire"
  },
  {
    name: "HEMS Portal",
    icon: "hems",
    purpose: "Air medical operations coordination",
    users: "Flight coordinators, HEMS dispatch, supervisors",
    scope: ["Mission planning", "Aircraft & crew assignment", "Base-level operations", "Safety checks"],
    notes: "Separate authority from ground CAD",
    gradient: "from-sky-600 to-blue-600",
    link: "/hems"
  },
  {
    name: "Telehealth Portal",
    icon: "telehealth",
    purpose: "Remote clinical consultation and telemedicine",
    users: "Physicians, nurse practitioners, telehealth coordinators",
    scope: ["Video consultations", "Patient assessments", "Documentation", "Remote clinical support"],
    notes: "Clinical telemedicine only, no dispatch or billing access",
    gradient: "from-purple-600 to-pink-600",
    link: "/telehealth"
  },
  {
    name: "Pilot Portal",
    icon: "pilot",
    purpose: "Flight crew operational view",
    users: "Pilots, flight crew",
    scope: ["Mission details", "Assignment acknowledgments", "Status updates", "Safety confirmations"],
    notes: "Read-only or limited-write, no dispatch or billing access",
    gradient: "from-indigo-600 to-violet-600",
    link: "/pilot"
  },
  {
    name: "Compliance / QA-QI Portal",
    icon: "compliance",
    purpose: "Regulatory oversight and quality assurance",
    users: "Compliance officers, QA/QI staff, auditors",
    scope: ["Case review", "Regulatory reporting", "Audit trails", "Performance metrics"],
    notes: "Read-only by default, elevated permissions tightly controlled",
    gradient: "from-emerald-600 to-teal-600",
    link: "/founder/compliance/cms"
  },
  {
    name: "Administration Portal",
    icon: "admin",
    purpose: "System configuration and governance",
    users: "System administrators",
    scope: ["User & role management", "Permissions", "Agency / region configuration", "System policies"],
    notes: "Restricted to minimal users, fully audited",
    gradient: "from-gray-600 to-slate-600",
    link: "/admin"
  }
]

const externalPortals = [
  {
    name: "TransportLink Portal",
    icon: "facility",
    purpose: "Facility-facing transport request and tracking",
    users: "Hospitals, SNFs, ALFs",
    scope: ["Submit transport requests", "Upload supporting documents", "Track transport status", "Secure messaging"],
    excluded: ["Dispatch", "CAD access", "ePCR access", "Billing access"],
    notes: "Front door for facilities, not an EMS system",
    gradient: "from-cyan-600 to-teal-600",
    link: "/transportlink"
  },
  {
    name: "Provider Portal",
    icon: "provider",
    purpose: "External clinical coordination (non-EMS staff)",
    users: "Hospitals, clinics, referring providers",
    scope: ["Submit transport requests", "Upload orders", "View limited status updates"],
    notes: "Facility-scoped, read-only operational visibility",
    gradient: "from-violet-600 to-purple-600",
    link: "/provider"
  }
]

const publicPortals = [
  {
    name: "Patient Portal",
    icon: "patient",
    purpose: "Patient self-service",
    users: "Patients, legal guardians",
    scope: ["View invoices", "Make payments", "Download receipts", "Submit billing inquiries"],
    notes: "No operational or clinical system access",
    gradient: "from-green-600 to-emerald-600",
    link: "/billing"
  },
  {
    name: "Payment Portal",
    icon: "payment",
    purpose: "Secure payment processing",
    users: "Patients (public), Billing staff (internal)",
    scope: ["Invoice lookup", "Card / ACH payments", "Receipts"],
    notes: "PCI-isolated, minimal data exposure",
    gradient: "from-amber-600 to-yellow-600",
    link: "/billing/payments"
  }
]

const getIcon = (icon: string) => {
  const icons: Record<string, React.ReactNode> = {
    cad: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>,
    transport: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>,
    fire: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" /></svg>,
    hems: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>,
    pilot: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>,
    compliance: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>,
    telehealth: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>,
    admin: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
    facility: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>,
    provider: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>,
    patient: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>,
    payment: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>,
    external: <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
  }
  return icons[icon] || icons.admin
}

export default function PortalsPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-[#0a0a0a]/95 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center">
              <span className="text-white font-black text-lg">Q</span>
            </div>
            <div className="hidden sm:block">
              <div className="text-white font-black text-lg tracking-tight">FusionEMS Quantum</div>
              <div className="text-[10px] text-gray-500 tracking-widest uppercase">Enterprise EMS Platform</div>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            <Link href="/#modules" className="text-sm text-gray-400 hover:text-white transition-colors">Modules</Link>
            <Link href="/portals" className="text-sm text-orange-500 font-medium">Portals</Link>
            <Link href="/#contact" className="text-sm text-gray-400 hover:text-white transition-colors">Contact</Link>
          </nav>

          <Link href="/login" className="px-4 py-2 rounded-lg bg-gradient-to-r from-orange-500 to-red-600 text-white text-sm font-semibold hover:opacity-90 transition-opacity">
            Launch Platform
          </Link>
        </div>
      </header>

      <main className="pt-32 pb-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex px-4 py-1.5 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-500 text-xs font-semibold tracking-wider uppercase mb-6">
              Platform Architecture
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white mb-6 tracking-tight">
              Multi-Portal Enterprise Architecture
            </h1>
            <p className="text-lg text-gray-400 max-w-3xl mx-auto mb-10">
              Built on a secure, role-based architecture with strict access boundaries and comprehensive audit controls. Each portal serves a specific user type with precisely scoped permissions.
            </p>
            <div className="flex flex-wrap justify-center gap-6">
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/[0.02] border border-white/5">
                <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                <span className="text-sm text-gray-300">NEMSIS-Compliant</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/[0.02] border border-white/5">
                <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                <span className="text-sm text-gray-300">HIPAA-Aligned</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/[0.02] border border-white/5">
                <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                <span className="text-sm text-gray-300">99.9% Uptime SLA</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/[0.02] border border-white/5">
                <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                <span className="text-sm text-gray-300">24/7 Support</span>
              </div>
            </div>
          </div>

          <section className="mb-20">
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-orange-500 font-mono text-sm">01</span>
                <div className="flex-1 h-px bg-gradient-to-r from-orange-500/50 to-transparent"></div>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-white mb-2">
                Internal EMS Platform Portals
              </h2>
              <p className="text-gray-400">
                SSO-enabled, role-based, regulated operational control for EMS personnel
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {internalPortals.map((portal, i) => (
                <Link
                  key={i}
                  href={portal.link}
                  className="group p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/20 hover:bg-white/[0.04] transition-all duration-300"
                >
                  <div className="flex items-start gap-4 mb-4">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${portal.gradient} flex items-center justify-center text-white shrink-0`}>
                      {getIcon(portal.icon)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-bold text-white mb-1 group-hover:text-orange-400 transition-colors">
                        {portal.name}
                      </h3>
                      <p className="text-sm text-gray-400 line-clamp-2">{portal.purpose}</p>
                    </div>
                  </div>

                  <div className="text-xs text-gray-500 mb-3">
                    <span className="text-gray-400 font-medium">Users:</span> {portal.users}
                  </div>

                  <div className="mb-4">
                    <div className="flex flex-wrap gap-1.5">
                      {portal.scope.map((item, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-white/5 text-xs text-gray-400">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                    <p className="text-xs text-gray-500 italic flex-1">{portal.notes}</p>
                    <span className="text-orange-500 text-sm ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      Open
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </section>

          <section className="mb-20">
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-orange-500 font-mono text-sm">02</span>
                <div className="flex-1 h-px bg-gradient-to-r from-orange-500/50 to-transparent"></div>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-white mb-2">
                External Facility & Partner Portals
              </h2>
              <p className="text-gray-400">
                Controlled visibility for hospitals, SNFs, ALFs — no EMS operational control
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {externalPortals.map((portal, i) => (
                <Link
                  key={i}
                  href={portal.link}
                  className="group p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/20 hover:bg-white/[0.04] transition-all duration-300"
                >
                  <div className="flex items-start gap-4 mb-4">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${portal.gradient} flex items-center justify-center text-white shrink-0`}>
                      {getIcon(portal.icon)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-bold text-white mb-1 group-hover:text-orange-400 transition-colors">
                        {portal.name}
                      </h3>
                      <p className="text-sm text-gray-400 line-clamp-2">{portal.purpose}</p>
                    </div>
                  </div>

                  <div className="text-xs text-gray-500 mb-3">
                    <span className="text-gray-400 font-medium">Users:</span> {portal.users}
                  </div>

                  <div className="mb-3">
                    <div className="flex flex-wrap gap-1.5">
                      {portal.scope.map((item, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-white/5 text-xs text-gray-400">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>

                  {portal.excluded && (
                    <div className="mb-4">
                      <p className="text-xs font-medium text-red-400 mb-1.5">Not Included:</p>
                      <div className="flex flex-wrap gap-1.5">
                        {portal.excluded.map((item, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded bg-red-500/10 text-xs text-red-400">
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                    <p className="text-xs text-gray-500 italic flex-1">{portal.notes}</p>
                    <span className="text-orange-500 text-sm ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      Open
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </section>

          <section className="mb-20">
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-orange-500 font-mono text-sm">03</span>
                <div className="flex-1 h-px bg-gradient-to-r from-orange-500/50 to-transparent"></div>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-white mb-2">
                Public / Self-Service Portals
              </h2>
              <p className="text-gray-400">
                Isolated, scoped access for patients — no EMS operational access
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {publicPortals.map((portal, i) => (
                <Link
                  key={i}
                  href={portal.link}
                  className="group p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/20 hover:bg-white/[0.04] transition-all duration-300"
                >
                  <div className="flex items-start gap-4 mb-4">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${portal.gradient} flex items-center justify-center text-white shrink-0`}>
                      {getIcon(portal.icon)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-bold text-white mb-1 group-hover:text-orange-400 transition-colors">
                        {portal.name}
                      </h3>
                      <p className="text-sm text-gray-400 line-clamp-2">{portal.purpose}</p>
                    </div>
                  </div>

                  <div className="text-xs text-gray-500 mb-3">
                    <span className="text-gray-400 font-medium">Users:</span> {portal.users}
                  </div>

                  <div className="mb-4">
                    <div className="flex flex-wrap gap-1.5">
                      {portal.scope.map((item, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-white/5 text-xs text-gray-400">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                    <p className="text-xs text-gray-500 italic flex-1">{portal.notes}</p>
                    <span className="text-orange-500 text-sm ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      Open
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </section>

          <section className="mb-20">
            <div className="p-8 sm:p-12 rounded-2xl bg-gradient-to-br from-orange-500/10 to-red-600/5 border border-orange-500/20 text-center">
              <div className="flex items-center justify-center gap-3 mb-4">
                <span className="text-orange-500 font-mono text-sm">05</span>
                <div className="w-12 h-px bg-gradient-to-r from-transparent via-orange-500/50 to-transparent"></div>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-white mb-4">
                Platform Portal Gateway
              </h2>
              <p className="text-lg text-gray-400 mb-6 max-w-3xl mx-auto">
                Central access point for all users. Single sign-on with role resolution and portal routing. Internal EMS users and external facility users operate in separate authentication domains.
              </p>
              <div className="inline-flex px-6 py-3 rounded-xl bg-orange-500/10 border border-orange-500/30">
                <span className="text-sm text-orange-400 font-semibold">
                  One login, many portals — but only what the user is entitled to
                </span>
              </div>
            </div>
          </section>

          <section className="mb-16">
            <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/10 text-center">
              <h3 className="text-xl font-bold text-white mb-4">
                Master Summary
              </h3>
              <p className="text-gray-400 max-w-4xl mx-auto leading-relaxed">
                The platform consists of <span className="text-orange-400 font-semibold">internal EMS operational portals</span>, 
                <span className="text-orange-400 font-semibold"> external facility and provider portals</span>, 
                <span className="text-orange-400 font-semibold"> patient and payment portals</span>, and 
                <span className="text-orange-400 font-semibold"> controlled interoperability with independent clinical systems</span> such as CareFusion — 
                each with <span className="text-orange-400 font-semibold">strict access boundaries and audit controls</span>.
              </p>
            </div>
          </section>

          <section className="text-center">
            <Link 
              href="/demo" 
              className="inline-flex px-8 py-4 rounded-xl bg-gradient-to-r from-orange-500 to-red-600 text-white font-bold hover:opacity-90 transition-opacity"
            >
              Request Enterprise Demo
            </Link>
            <p className="text-sm text-gray-500 mt-4">
              See the complete platform architecture in action
            </p>
          </section>
        </div>
      </main>

      <footer className="border-t border-white/5 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center">
                  <span className="text-white font-black text-sm">Q</span>
                </div>
                <span className="text-white font-bold">FusionEMS Quantum</span>
              </div>
              <p className="text-sm text-gray-500">Enterprise-grade EMS platform for modern emergency services.</p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Platform</h4>
              <div className="space-y-2">
                <Link href="/#modules" className="block text-sm text-gray-500 hover:text-gray-300 transition-colors">Modules</Link>
                <Link href="/portals" className="block text-sm text-gray-500 hover:text-gray-300 transition-colors">Portals</Link>
                <Link href="/pricing" className="block text-sm text-gray-500 hover:text-gray-300 transition-colors">Pricing</Link>
              </div>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <div className="space-y-2">
                <Link href="/about" className="block text-sm text-gray-500 hover:text-gray-300 transition-colors">About</Link>
                <Link href="/careers" className="block text-sm text-gray-500 hover:text-gray-300 transition-colors">Careers</Link>
                <Link href="/contact" className="block text-sm text-gray-500 hover:text-gray-300 transition-colors">Contact</Link>
              </div>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Legal</h4>
              <div className="space-y-2">
                <Link href="/privacy" className="block text-sm text-gray-500 hover:text-gray-300 transition-colors">Privacy</Link>
                <Link href="/terms" className="block text-sm text-gray-500 hover:text-gray-300 transition-colors">Terms</Link>
                <Link href="/security" className="block text-sm text-gray-500 hover:text-gray-300 transition-colors">Security</Link>
              </div>
            </div>
          </div>
          <div className="pt-8 border-t border-white/5 text-center">
            <p className="text-sm text-gray-600">
              2024 FusionEMS Quantum. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
