"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import Logo from "@/components/Logo"
import TrustBadge from "@/components/marketing/TrustBadge"
import { SecurityHero, SecurityControls, SecurityStats, SecurityCTA } from "@/components/SecurityHero"
import {
  Hexagon,
  Video,
  Link2,
  CircleDollarSign,
  MapPin,
  ClipboardList,
  DollarSign,
  Flame,
  Truck,
  Shield,
  Activity,
  ShieldCheck,
  Zap,
  CalendarDays,
} from "lucide-react"

type BillingServiceType = "not-sure" | "fire-based" | "third-service" | "hems"

const BILLING_COPY: Record<BillingServiceType, { title: string; paragraphs: string[] }> = {
  "not-sure": {
    title: "Transport Billing Integrated Into the Workflow",
    paragraphs: [
      "Disconnected systems and manual handoffs are common sources of billing delay and revenue loss across EMS agencies of all types.",
      "FusionEMS Quantum delivers native transport billing aligned with dispatch, documentation, telehealth, and facility coordination—creating a continuous, auditable workflow from dispatch through reimbursement.",
      "When billing data remains connected to operations and clinical context, even modest improvements can have a measurable financial impact over time.",
    ],
  },
  "fire-based": {
    title: "Transport Billing Built for Fire-Based EMS",
    paragraphs: [
      "Fire-based EMS agencies operate in complex environments with mixed response types, shared resources, and documentation that often spans systems never designed to work together.",
      "FusionEMS Quantum treats transport billing as an extension of operations—not a back-office function. Dispatch activity, unit response data, patient care documentation, FusionCare™ telehealth encounters, and facility-scheduled transports are aligned into a single, auditable workflow.",
      "Because billing outcomes are shaped upstream, even small improvements in workflow continuity can materially impact reimbursement over time.",
    ],
  },
  "third-service": {
    title: "Transport Billing Designed for Third-Service EMS",
    paragraphs: [
      "Third-service EMS agencies depend on predictable reimbursement to sustain staffing, readiness, and response coverage—yet billing workflows are often fragmented across dispatch, documentation, and third-party systems.",
      "FusionEMS Quantum delivers native transport billing directly connected to CAD, patient care documentation, FusionCare™ telehealth encounters, and Transport Link™ facility requests.",
      "When documentation, clinical context, and transport data stay connected, billing outcomes become more predictable and defensible.",
    ],
  },
  hems: {
    title: "Transport Billing for High-Acuity and Air Medical Operations",
    paragraphs: [
      "HEMS and air medical programs face uniquely complex billing challenges, including advanced clinical documentation, strict payer scrutiny, and high-acuity justification requirements.",
      "FusionEMS Quantum integrates flight operations, clinical documentation, FusionCare™ telehealth consults, and transport billing into a single workflow designed to preserve clinical justification and audit defensibility.",
      "In high-acuity environments, documentation continuity is critical to financial sustainability.",
    ],
  },
}

export default function HomePage() {
  const [billingServiceType, setBillingServiceType] = useState<BillingServiceType>("not-sure")

  // Handle smooth scrolling for hash links
  useEffect(() => {
    const handleHashClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      const link = target.closest('a[href^="#"]') as HTMLAnchorElement
      if (link) {
        const hash = link.getAttribute('href')
        if (hash && hash.startsWith('#')) {
          e.preventDefault()
          const id = hash.substring(1)
          const element = document.getElementById(id)
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' })
            // Update URL without jumping
            window.history.pushState(null, '', hash)
          }
        }
      }
    }

    // Handle initial hash on page load
    if (window.location.hash) {
      const id = window.location.hash.substring(1)
      setTimeout(() => {
        const element = document.getElementById(id)
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 100)
    }

    document.addEventListener('click', handleHashClick)
    return () => document.removeEventListener('click', handleHashClick)
  }, [])

  return (
    <div className="homepage-wrapper">
      <div className="bg-motion" aria-hidden>
        <div className="bg-orb bg-orb--1" />
        <div className="bg-orb bg-orb--2" />
        <div className="bg-orb bg-orb--3" />
      </div>

      <header className="top-bar">
        <div className="top-bar-container">
          <Link href="/" className="logo-section" aria-label="FusionEMS Quantum home">
            <Logo variant="headerLockup" active />
          </Link>
          <nav className="quick-nav" aria-label="Primary">
            <Link href="#modules" className="nav-item">Modules</Link>
            <Link href="#fusioncare" className="nav-item">FusionCare</Link>
            <Link href="#transport-link" className="nav-item">Transport Link</Link>
            <Link href="/portals" className="nav-item">Architecture</Link>
            <Link href="#stats" className="nav-item">Performance</Link>
            <Link href="#contact" className="nav-item">Contact</Link>
            <Link href="/pricing" className="nav-item">Pricing</Link>
            <Link href="/fusionems-scheduling" className="nav-item">Scheduling</Link>
            <Link href="/billing" className="nav-item nav-item--pay">Pay a Bill</Link>
          </nav>
          <div className="top-bar-actions">
            <Link href="/login" className="btn-access">Launch</Link>
          </div>
        </div>
      </header>

      <main className="home-main">
        {/* 1. HERO — Enterprise-grade, explicit FusionCare, Transport Link, Billing */}
        <section className="hero-redesign">
          <div className="hero-inner">
            <div className="hero-visual hero-anim-wrap">
              <span className="hero-icon-active">
                <Logo variant="icon" width={120} height={120} className="hero-logo" />
              </span>
            </div>
            <div className="hero-copy">
              <h1 className="hero-title hero-anim hero-anim-1">
                FusionEMS <span className="hero-title-accent text-gradient">Quantum</span>
              </h1>
              <p className="hero-tagline hero-anim hero-anim-2">
                The intelligence and operations engine for EMS, Fire, and HEMS.
              </p>
              <p className="hero-desc hero-anim hero-anim-3">
                Dispatch, Transport Link, and transport billing in one pipeline. FusionCare is a separate clinical module linked to billing. Built for auditability and mission-critical workflows.
              </p>
              <div className="hero-cta hero-anim hero-anim-4">
                <Link href="/demo" className="btn-primary">Request a Demo</Link>
                <Link href="/billing" className="btn-pay">Pay a Bill</Link>
              </div>
              <div className="hero-trust hero-anim hero-anim-5">
                <TrustBadge icon="shield" text="NEMSIS" variant="large" />
                <TrustBadge icon="lock" text="HIPAA" variant="large" />
                <TrustBadge icon="activity" text="Audit trails" variant="large" />
                <TrustBadge icon="headset" text="24/7 support" variant="large" />
              </div>
            </div>
          </div>
        </section>

        {/* 2. SECURITY HERO — Federal-Grade Security */}
        <SecurityHero />
        
        {/* 2.5. SECURITY STATS */}
        <SecurityStats />

        {/* 3. WHAT IS FUSIONEMS QUANTUM? — Explainer */}
        <section id="quantum-explainer" className="section-redesign section-explainer section-anim">
          <div className="section-divider section-divider--top" aria-hidden />
          <div className="section-head">
            <span className="section-label">Platform</span>
            <h2 className="section-title">What is FusionEMS Quantum?</h2>
            <p className="section-desc section-desc--wide">
              FusionEMS Quantum is a real-time intelligence and operations engine. It provides a shared layer for decisions, data, and workflows across dispatch and billing operations. It is the foundation for CAD, Transport Link, and Transport Billing. FusionCare is a separate telehealth module linked to billing only.
            </p>
          </div>
        </section>

        {/* 4. SECURITY CONTROLS — Comprehensive Implementation */}
        <SecurityControls />

        {/* 5. ECOSYSTEM OVERVIEW — One system, specialized components */}
        <section id="ecosystem" className="section-redesign ecosystem-section section-anim">
          <div className="section-head">
            <span className="section-label">Ecosystem</span>
            <h2 className="section-title">One platform, specialized components</h2>
          </div>
          <div className="ecosystem-grid">
            <div className="ecosystem-card ecosystem-card--core ecosystem-card-anim ecosystem-card-anim-1">
              <span className="ecosystem-card-icon" aria-hidden><Hexagon className="w-6 h-6" /></span>
              <h3 className="ecosystem-card-title">FusionEMS Quantum™</h3>
              <p className="ecosystem-card-sub">Core Platform</p>
              <p className="ecosystem-card-desc">Real-time intelligence and operations engine. Shared data, decision logic, and workflows for dispatch, compliance, and audit.</p>
              <p className="ecosystem-card-user"><strong>Who:</strong> Operations, IT, leadership.</p>
              <p className="ecosystem-card-role"><strong>Role:</strong> Foundation for CAD, ePCR, Transport Link, and Transport Billing.</p>
            </div>
            <div className="ecosystem-card ecosystem-card--fusioncare ecosystem-card-anim ecosystem-card-anim-2">
              <span className="ecosystem-card-icon" aria-hidden><Video className="w-6 h-6" /></span>
              <h3 className="ecosystem-card-title">FusionCare™</h3>
              <p className="ecosystem-card-sub">Telehealth & Clinical Oversight</p>
              <p className="ecosystem-card-desc">FusionCare is its own separate module. Telehealth and clinical oversight: live video consults, medical control, specialist escalation, and documentation-backed clinical decisions. Linked to billing only—not tied to CAD or ePCR.</p>
              <p className="ecosystem-card-user"><strong>Who:</strong> Physicians, medical control, telehealth coordinators, EMS and HEMS clinicians.</p>
              <p className="ecosystem-card-role"><strong>Role:</strong> Standalone clinical module; linked to billing for encounter data and reimbursement.</p>
            </div>
            <div className="ecosystem-card ecosystem-card--transportlink ecosystem-card-anim ecosystem-card-anim-3">
              <span className="ecosystem-card-icon" aria-hidden><Link2 className="w-6 h-6" /></span>
              <h3 className="ecosystem-card-title">Transport Link™</h3>
              <p className="ecosystem-card-sub">Facility Scheduling Portal</p>
              <p className="ecosystem-card-desc">External, facility-facing portal. Hospitals, nursing homes, and assisted living centers schedule transports, track status and ETAs, and coordinate discharges. Requests flow directly into dispatch, operations, and billing.</p>
              <p className="ecosystem-card-user"><strong>Who:</strong> Hospitals, SNFs, ALFs, facility staff.</p>
              <p className="ecosystem-card-role"><strong>Role:</strong> Single entry point for facility requests; no phone tag or re-keying.</p>
              <Link href="/portals/transportlink/login" className="btn-secondary btn-sm mt-3">Facility Login</Link>
            </div>
            <div className="ecosystem-card ecosystem-card--billing ecosystem-card-anim ecosystem-card-anim-4">
              <span className="ecosystem-card-icon" aria-hidden><CircleDollarSign className="w-6 h-6" /></span>
              <h3 className="ecosystem-card-title">Transport Billing</h3>
              <p className="ecosystem-card-sub">Revenue & Reimbursement Engine</p>
              <p className="ecosystem-card-desc">Native, end-to-end transport billing. Connects CAD activity, clinical documentation, and Transport Link requests into one auditable revenue workflow; links to FusionCare for encounter data. Reduces handoffs, re-keying, and revenue leakage.</p>
              <p className="ecosystem-card-user"><strong>Who:</strong> Billing, finance, compliance.</p>
              <p className="ecosystem-card-role"><strong>Role:</strong> Single revenue pipeline from dispatch through reimbursement.</p>
              <Link href="/demo" className="btn-primary btn-sm mt-3">Request a Demo</Link>
            </div>
          </div>
        </section>

        {/* 4. FUSIONCARE SECTION — Separate module, linked to billing only */}
        <section id="fusioncare" className="fusioncare-section section-anim">
          <div className="fusioncare-inner">
            <span className="section-label section-label--light">Clinical</span>
            <h2 className="fusioncare-title">FusionCare™ — Telehealth & Clinical Oversight</h2>
            <p className="fusioncare-lead">FusionCare is its own separate module—not tied to CAD or ePCR. Clinical decision support, medical control, and live video consults. Linked to billing only.</p>
            <ul className="fusioncare-list">
              <li>Clinical decision support and medical control</li>
              <li>Live video consults and specialist escalation</li>
              <li>Documentation for care and billing defensibility</li>
              <li>Separate system; linked to billing only</li>
            </ul>
            <p className="fusioncare-note">Used by EMS, Fire, and HEMS for remote clinical oversight. Standalone module.</p>
            <Link href="/portals/carefusion/login" className="btn-secondary">FusionCare Login</Link>
          </div>
        </section>

        {/* 5. TRANSPORT LINK SECTION — Facility-facing */}
        <section id="transport-link" className="transportlink-section">
          <div className="transportlink-inner">
            <span className="section-label">Facility Portal</span>
            <h2 className="transportlink-title">Transport Link™</h2>
            <p className="transportlink-lead">Facility-facing scheduling and coordination. Designed for hospitals, SNFs, and assisted living centers.</p>
            <ul className="transportlink-list">
              <li>Schedule transports</li>
              <li>Track status and ETAs</li>
              <li>Coordinate discharges</li>
              <li>Requests flow directly into dispatch, operations, and billing</li>
            </ul>
            <Link href="/portals/transportlink/login" className="btn-primary">Facility Login</Link>
          </div>
        </section>

        {/* 6. TRANSPORT BILLING — Primary differentiator */}
        <section id="billing" className="billing-redesign section-anim">
          <div className="billing-inner">
            <span className="section-label section-label--light">Revenue</span>
            <h2 className="billing-title">{BILLING_COPY[billingServiceType].title}</h2>
            <p className="billing-lead">What type of service best describes your agency?</p>
            <div className="billing-selector" role="group" aria-label="Service type">
              {(
                [
                  { value: "fire-based" as const, label: "Fire-Based EMS" },
                  { value: "third-service" as const, label: "Third-Service EMS" },
                  { value: "hems" as const, label: "HEMS / Air Medical" },
                  { value: "not-sure" as const, label: "Not Sure / Other" },
                ] as const
              ).map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setBillingServiceType(opt.value)}
                  className={`billing-selector-btn ${billingServiceType === opt.value ? "billing-selector-btn--active" : ""}`}
                  aria-pressed={billingServiceType === opt.value}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <div className="billing-copy-panel">
              {BILLING_COPY[billingServiceType].paragraphs.map((p, i) => (
                <p key={i} className="billing-desc">{p}</p>
              ))}
            </div>
            <p className="billing-pricing-note">
              Pricing is transparent, usage-aligned, and replaces traditional third-party billing vendors without percentage-of-revenue fees.
            </p>
            <div className="billing-cta">
              <Link href="/billing/roi" className="btn-secondary">Estimate ROI by ZIP Code</Link>
            </div>
          </div>
        </section>

        {/* 7. SECURITY CTA — Ready for Federal Deployment */}
        <SecurityCTA />

        {/* 8. TRUST & COMPLIANCE — Early placement already in hero; reinforce */}
        <section id="trust" className="trust-section section-anim">
          <div className="section-divider section-divider--top" aria-hidden />
          <div className="trust-inner">
            <h2 className="trust-title">Trust & Compliance</h2>
            <div className="trust-grid">
              <div className="trust-item trust-item-card"><TrustBadge icon="lock" text="HIPAA Compliant" /></div>
              <div className="trust-item trust-item-card"><TrustBadge icon="shield" text="FIPS 140-2 Ready" /></div>
              <div className="trust-item trust-item-card"><TrustBadge icon="activity" text="NIST 800-53 Aligned" /></div>
              <div className="trust-item trust-item-card"><TrustBadge icon="headset" text="Pursuing FedRAMP" /></div>
            </div>
            <p className="trust-note">
              Built with federal-grade security controls. 421 implemented security controls 
              aligned with FedRAMP High Impact requirements. Designed for public-sector 
              accountability and operational reliability.
            </p>
          </div>
        </section>

        {/* Modules — Platform workspaces */}
        <section id="modules" className="section-redesign section-anim">
          <div className="section-head">
            <span className="section-label">Workspaces</span>
            <h2 className="section-title">Modules</h2>
            <p className="section-desc">Specialized workspaces for dispatch, clinical, billing, and compliance.</p>
            <Link href="/modules" className="section-link">View all modules</Link>
          </div>
          <div className="module-grid">
            {[
              { title: "CAD", desc: "Dispatch, incident lifecycle, unit status.", href: "/cad", Icon: MapPin },
              { title: "ePCR", desc: "Clinical documentation, validations, exports.", href: "/epcr", Icon: ClipboardList },
              { title: "Billing", desc: "Transport billing, claims, denials, analytics.", href: "/billing/dashboard", Icon: DollarSign },
              { title: "Scheduling", desc: "Crew scheduling, shifts, availability, swaps.", href: "/fusionems-scheduling", Icon: CalendarDays },
              { title: "Fire RMS", desc: "Inspections, hydrants, preplans, CRR.", href: "/fire/rms", Icon: Flame },
              { title: "Fleet", desc: "Vehicles, DVIR, inspections, maintenance.", href: "/fleet", Icon: Truck },
              { title: "Compliance", desc: "HIPAA, CJIS, DEA, CMS.", href: "/compliance", Icon: Shield },
            ].map((m) => (
              <Link key={m.title} href={m.href} className="module-card">
                <span className="module-card-icon" aria-hidden><m.Icon className="w-5 h-5" /></span>
                <span className="module-card-title">{m.title}</span>
                <span className="module-card-desc">{m.desc}</span>
              </Link>
            ))}
          </div>
        </section>

        {/* Performance */}
        <section id="stats" className="stats-redesign section-anim">
          <div className="section-divider section-divider--top" aria-hidden />
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-icon" aria-hidden><Activity className="w-8 h-8" /></span>
              <span className="stat-value">99.9%</span>
              <span className="stat-label">Uptime</span>
              <span className="stat-note">Designed for critical operations</span>
            </div>
            <div className="stat-card">
              <span className="stat-icon" aria-hidden><ShieldCheck className="w-8 h-8" /></span>
              <span className="stat-value">End-to-end</span>
              <span className="stat-label">Audit</span>
              <span className="stat-note">Event trails & RBAC</span>
            </div>
            <div className="stat-card">
              <span className="stat-icon" aria-hidden><Zap className="w-8 h-8" /></span>
              <span className="stat-value">&lt;100ms</span>
              <span className="stat-label">Response</span>
              <span className="stat-note">Operator-first interactions</span>
            </div>
          </div>
        </section>

        {/* Contact */}
        <section id="contact" className="contact-redesign section-anim">
          <div className="contact-inner">
            <span className="section-label">Demo</span>
            <h2 className="contact-title">See FusionEMS Quantum in your environment</h2>
            <p className="contact-desc">We tailor the demo to your service area, protocols, and compliance needs.</p>
            <div className="contact-cta">
              <Link href="/demo" className="btn-primary">Request a Demo</Link>
              <Link href="/portals" className="btn-secondary">Architecture</Link>
            </div>
            <p className="contact-email">
              <span className="text-[var(--charcoal-400)]">Or email </span>
              <a href="mailto:support@fusionemsquantum.com" className="text-orange-400 font-semibold hover:underline">support@fusionemsquantum.com</a>
            </p>
          </div>
        </section>

        <footer className="footer-redesign">
          <div className="footer-inner">
            <span>&copy; {new Date().getFullYear()} FusionEMS Quantum</span>
            <nav className="footer-links">
              <Link href="/portals" className="footer-link">Architecture</Link>
              <Link href="/pricing" className="footer-link">Pricing</Link>
              <Link href="/fusionems-scheduling" className="footer-link">Scheduling</Link>
              <Link href="/demo" className="footer-link">Demo</Link>
              <Link href="/billing" className="footer-link footer-link--pay">Pay a Bill</Link>
            </nav>
          </div>
        </footer>
      </main>
    </div>
  )
}
