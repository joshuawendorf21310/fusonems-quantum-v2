"use client"

import Link from "next/link"

const moduleCards = [
  {
    title: "CAD",
    description: "Dispatch, incident, and unit tracking with compliance-ready logs.",
    href: "/cad",
  },
  {
    title: "ePCR",
    description: "Patient care records, workflows, and AI-assisted documentation.",
    href: "/epcr",
  },
  {
    title: "Billing",
    description: "Claims automation, denials, and reconciliation tooling.",
    href: "/billing",
  },
  {
    title: "Operations",
    description: "Scheduling, crew readiness, and operational analytics.",
    href: "/operations",
  },
  {
    title: "Analytics",
    description: "Executive dashboards, performance metrics, and alerts.",
    href: "/analytics",
  },
  {
    title: "Compliance",
    description: "Regulatory controls, QA/QI reviews, and audit trails.",
    href: "/compliance",
  },
]

export default function ModulesHome() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <div className="max-w-6xl mx-auto px-4 py-12 space-y-6">
        <header className="space-y-3">
          <p className="text-sm uppercase tracking-[0.4em] text-orange-400">FusionEMS Quantum</p>
          <h1 className="text-3xl font-semibold">Modules Explorer</h1>
          <p className="text-gray-400 max-w-2xl">
            Every mission-critical capability is one click away. Choose a module to review telemetry, manage incidents, or trigger workflows.
          </p>
        </header>

        <div className="grid gap-6 md:grid-cols-2">
          {moduleCards.map((card) => (
            <Link
              key={card.title}
              href={card.href}
              className="block rounded-2xl border border-white/10 bg-white/5 p-6 transition hover:border-orange-500/40 hover:bg-white/10"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">{card.title}</h2>
                <span className="text-xs uppercase tracking-[0.3em] text-orange-400">Open</span>
              </div>
              <p className="mt-4 text-sm text-gray-300">{card.description}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
