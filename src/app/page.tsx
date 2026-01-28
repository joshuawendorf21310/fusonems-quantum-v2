"use client"

import Link from "next/link"

const features = [
  {
    name: "Electronic Patient Care Reporting (ePCR)",
    description: "NEMSIS-compliant digital documentation with offline capability and real-time validation.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    gradient: "from-blue-600 to-cyan-600",
  },
  {
    name: "Computer-Aided Dispatch (CAD)",
    description: "Real-time incident management, resource allocation, and GPS-enabled unit tracking.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
      </svg>
    ),
    gradient: "from-orange-600 to-red-600",
  },
  {
    name: "Crew Scheduling",
    description: "Advanced shift management with automated coverage, time-off requests, and compliance tracking.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
    gradient: "from-purple-600 to-violet-600",
  },
  {
    name: "Revenue Cycle Management",
    description: "Automated billing, claims submission, payment processing, and collections optimization.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    gradient: "from-green-600 to-emerald-600",
  },
  {
    name: "Fleet Management",
    description: "Vehicle maintenance tracking, inventory control, inspection workflows, and asset lifecycle management.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    gradient: "from-cyan-600 to-teal-600",
  },
  {
    name: "Training & Certification",
    description: "Automated credential tracking, continuing education management, and skills verification.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
    gradient: "from-indigo-600 to-blue-600",
  },
  {
    name: "Fire RMS",
    description: "Comprehensive fire records management system for incident reporting, apparatus tracking, and NFIRS compliance.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
      </svg>
    ),
    gradient: "from-red-700 to-orange-600",
  },
  {
    name: "HEMS Aviation",
    description: "Specialized air medical operations with flight planning, weather integration, and aviation-specific compliance.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
      </svg>
    ),
    gradient: "from-sky-600 to-blue-700",
  },
  {
    name: "CareFusion Telehealth",
    description: "Integrated telemedicine platform enabling remote consultations, virtual triage, and physician oversight.",
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
    gradient: "from-pink-600 to-purple-600",
  },
]

const useCases = [
  {
    title: "EMS Agencies",
    description: "Complete operational control for municipal, private, and hospital-based emergency medical services.",
    benefits: [
      "Real-time dispatch coordination",
      "Automated billing and collections",
      "Crew scheduling and compliance",
      "Performance analytics and reporting",
    ],
    gradient: "from-blue-600 to-cyan-600",
  },
  {
    title: "Fire Departments",
    description: "Integrated fire-based EMS operations with comprehensive records management and NFIRS reporting.",
    benefits: [
      "Combined fire and EMS documentation",
      "Apparatus and equipment tracking",
      "Training and certification management",
      "Incident command integration",
    ],
    gradient: "from-red-600 to-orange-600",
  },
  {
    title: "Air Medical Services",
    description: "Aviation-specific workflows for helicopter and fixed-wing emergency medical transport operations.",
    benefits: [
      "Flight planning and weather integration",
      "Aviation regulatory compliance",
      "Multi-base coordination",
      "Specialized clinical protocols",
    ],
    gradient: "from-sky-600 to-blue-700",
  },
  {
    title: "Healthcare Networks",
    description: "Enterprise-scale coordination for integrated delivery networks and healthcare systems.",
    benefits: [
      "Multi-agency management",
      "Systemwide analytics and reporting",
      "Standardized protocols and workflows",
      "Telehealth integration",
    ],
    gradient: "from-purple-600 to-pink-600",
  },
]

const benefits = [
  {
    title: "Real-time Operations",
    description: "Live situational awareness with GPS tracking, automated dispatching, and instant communication across all units and facilities.",
    icon: (
      <svg className="w-12 h-12 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    title: "AI-Powered Insights",
    description: "Predictive analytics for demand forecasting, resource optimization, and clinical decision support powered by machine learning.",
    icon: (
      <svg className="w-12 h-12 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
  {
    title: "Complete Compliance",
    description: "Built-in regulatory compliance for HIPAA, NEMSIS, NFIRS, state reporting requirements, and agency-specific protocols.",
    icon: (
      <svg className="w-12 h-12 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    title: "Seamless Integration",
    description: "Open APIs and pre-built integrations with hospital systems, CAD vendors, billing clearinghouses, and third-party applications.",
    icon: (
      <svg className="w-12 h-12 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
      </svg>
    ),
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-zinc-800/50 backdrop-blur-xl bg-zinc-950/80">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">Q</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">FusionEMS Quantum</h1>
                <p className="text-xs text-zinc-400">Enterprise EMS Platform</p>
              </div>
            </div>
            <div className="flex items-center space-x-6">
              <Link href="#features" className="text-zinc-400 hover:text-white transition-colors text-sm">
                Features
              </Link>
              <Link href="#solutions" className="text-zinc-400 hover:text-white transition-colors text-sm">
                Solutions
              </Link>
              <Link href="/portals" className="text-zinc-400 hover:text-white transition-colors text-sm">
                Portals
              </Link>
              <Link href="/contact" className="text-zinc-400 hover:text-white transition-colors text-sm">
                Contact
              </Link>
              <Link
                href="/demo"
                className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg text-white text-sm font-medium hover:from-cyan-500 hover:to-blue-500 transition-all"
              >
                Request Demo
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main>
        <section className="relative pt-32 pb-20 px-6 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-600/20 via-blue-600/20 to-transparent"></div>
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl"></div>
          
          <div className="relative max-w-7xl mx-auto text-center">
            <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight">
              <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-blue-500 bg-clip-text text-transparent">
                FusionEMS Quantum
              </span>
              <br />
              <span className="text-zinc-100">Next-Generation Emergency</span>
              <br />
              <span className="text-zinc-100">Medical Services Platform</span>
            </h1>
            <p className="text-xl text-zinc-400 max-w-3xl mx-auto mb-10 leading-relaxed">
              The comprehensive operating system for modern EMS agencies. Unified platform combining ePCR, CAD, billing, scheduling, fleet management, and analytics into one powerful solution.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                href="/demo"
                className="px-8 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg text-white font-semibold hover:from-cyan-500 hover:to-blue-500 transition-all shadow-lg shadow-cyan-600/25 hover:shadow-cyan-600/40"
              >
                Request Demo
              </Link>
              <Link
                href="#features"
                className="px-8 py-4 bg-zinc-800 border border-zinc-700 rounded-lg text-white font-semibold hover:bg-zinc-700 hover:border-zinc-600 transition-all"
              >
                View Features
              </Link>
            </div>
          </div>
        </section>

        <section id="features" className="py-20 px-6 bg-zinc-900/50">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-white mb-4">Comprehensive Platform Features</h2>
              <p className="text-xl text-zinc-400 max-w-3xl mx-auto">
                Everything your agency needs to operate efficiently, from dispatch to patient care to revenue cycle management.
              </p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature) => (
                <div
                  key={feature.name}
                  className="group bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-all hover:shadow-xl hover:shadow-zinc-950/50"
                >
                  <div className={`inline-flex items-center justify-center w-14 h-14 rounded-lg bg-gradient-to-br ${feature.gradient} mb-4 group-hover:scale-110 transition-transform`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">{feature.name}</h3>
                  <p className="text-zinc-400 leading-relaxed">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="solutions" className="py-20 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-white mb-4">Built for Your Operation</h2>
              <p className="text-xl text-zinc-400 max-w-3xl mx-auto">
                Tailored solutions for every type of emergency medical service provider.
              </p>
            </div>
            <div className="grid md:grid-cols-2 gap-8">
              {useCases.map((useCase) => (
                <div
                  key={useCase.title}
                  className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 hover:border-zinc-700 transition-all"
                >
                  <div className={`inline-flex px-4 py-2 rounded-lg bg-gradient-to-r ${useCase.gradient} mb-4`}>
                    <h3 className="text-xl font-bold text-white">{useCase.title}</h3>
                  </div>
                  <p className="text-zinc-300 mb-6 leading-relaxed">{useCase.description}</p>
                  <ul className="space-y-3">
                    {useCase.benefits.map((benefit) => (
                      <li key={benefit} className="flex items-start gap-3">
                        <svg className="w-5 h-5 text-cyan-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-zinc-400">{benefit}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 px-6 bg-zinc-900/50">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-white mb-4">Platform Benefits</h2>
              <p className="text-xl text-zinc-400 max-w-3xl mx-auto">
                Advanced capabilities that transform how emergency medical services operate.
              </p>
            </div>
            <div className="grid md:grid-cols-2 gap-8">
              {benefits.map((benefit) => (
                <div
                  key={benefit.title}
                  className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 hover:border-zinc-700 transition-all"
                >
                  <div className="mb-4">{benefit.icon}</div>
                  <h3 className="text-2xl font-bold text-white mb-3">{benefit.title}</h3>
                  <p className="text-zinc-400 leading-relaxed">{benefit.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold text-white mb-4">Enterprise-Grade Security & Reliability</h2>
              <p className="text-xl text-zinc-400 max-w-3xl mx-auto mb-12">
                Built with the highest standards for healthcare data security and operational continuity.
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-blue-500/10 mb-4">
                  <svg className="w-10 h-10 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <h4 className="text-xl font-semibold text-white mb-2">HIPAA Compliant</h4>
                <p className="text-zinc-400 leading-relaxed">Full HIPAA compliance with end-to-end encryption, audit logging, and secure authentication.</p>
              </div>
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-500/10 mb-4">
                  <svg className="w-10 h-10 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h4 className="text-xl font-semibold text-white mb-2">SOC 2 Type II Certified</h4>
                <p className="text-zinc-400 leading-relaxed">Independently verified security controls and operational excellence.</p>
              </div>
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-cyan-500/10 mb-4">
                  <svg className="w-10 h-10 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h4 className="text-xl font-semibold text-white mb-2">99.9% Uptime SLA</h4>
                <p className="text-zinc-400 leading-relaxed">Enterprise-grade infrastructure with redundancy and 24/7 monitoring.</p>
              </div>
            </div>
            <div className="mt-12 text-center">
              <div className="inline-flex items-center justify-center gap-8 px-8 py-4 bg-zinc-900 border border-zinc-800 rounded-xl">
                <div className="flex items-center gap-2">
                  <svg className="w-6 h-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-white font-semibold">24/7 Technical Support</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span className="text-white font-semibold">256-bit AES Encryption</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-6 h-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-white font-semibold">NEMSIS v3.5 Compliant</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 px-6 bg-gradient-to-br from-cyan-900/20 via-blue-900/20 to-zinc-900">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-4xl font-bold text-white mb-6">Ready to Transform Your Operations?</h2>
            <p className="text-xl text-zinc-300 mb-8">
              Join leading EMS agencies nationwide who trust FusionEMS Quantum for their mission-critical operations.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                href="/demo"
                className="px-8 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg text-white font-semibold hover:from-cyan-500 hover:to-blue-500 transition-all shadow-lg shadow-cyan-600/25 hover:shadow-cyan-600/40"
              >
                Request a Demo
              </Link>
              <Link
                href="/contact"
                className="px-8 py-4 bg-zinc-800 border border-zinc-700 rounded-lg text-white font-semibold hover:bg-zinc-700 hover:border-zinc-600 transition-all"
              >
                Contact Sales
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-zinc-800 bg-zinc-950">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">Q</span>
                </div>
                <span className="text-white font-bold">FusionEMS Quantum</span>
              </div>
              <p className="text-zinc-400 text-sm leading-relaxed">
                Next-generation emergency medical services platform powering agencies nationwide.
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Product</h4>
              <ul className="space-y-2">
                <li><Link href="#features" className="text-zinc-400 hover:text-white text-sm transition-colors">Features</Link></li>
                <li><Link href="#solutions" className="text-zinc-400 hover:text-white text-sm transition-colors">Solutions</Link></li>
                <li><Link href="/integrations" className="text-zinc-400 hover:text-white text-sm transition-colors">Integrations</Link></li>
                <li><Link href="/security" className="text-zinc-400 hover:text-white text-sm transition-colors">Security</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Resources</h4>
              <ul className="space-y-2">
                <li><Link href="/documentation" className="text-zinc-400 hover:text-white text-sm transition-colors">Documentation</Link></li>
                <li><Link href="/support" className="text-zinc-400 hover:text-white text-sm transition-colors">Support</Link></li>
                <li><Link href="/training" className="text-zinc-400 hover:text-white text-sm transition-colors">Training</Link></li>
                <li><Link href="/api" className="text-zinc-400 hover:text-white text-sm transition-colors">API Reference</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-2">
                <li><Link href="/about" className="text-zinc-400 hover:text-white text-sm transition-colors">About</Link></li>
                <li><Link href="/contact" className="text-zinc-400 hover:text-white text-sm transition-colors">Contact</Link></li>
                <li><Link href="/partners" className="text-zinc-400 hover:text-white text-sm transition-colors">Partners</Link></li>
                <li><Link href="/news" className="text-zinc-400 hover:text-white text-sm transition-colors">News</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-zinc-800 pt-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <p className="text-zinc-500 text-sm">2026 FusionEMS Quantum. All rights reserved.</p>
              <div className="flex items-center gap-6">
                <Link href="/privacy" className="text-zinc-500 hover:text-zinc-400 text-sm transition-colors">
                  Privacy Policy
                </Link>
                <Link href="/terms" className="text-zinc-500 hover:text-zinc-400 text-sm transition-colors">
                  Terms of Service
                </Link>
                <Link href="/compliance" className="text-zinc-500 hover:text-zinc-400 text-sm transition-colors">
                  Compliance
                </Link>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
