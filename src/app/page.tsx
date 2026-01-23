"use client"

import { motion, type Variants } from "framer-motion"
import Image from "next/image"
import Link from "next/link"

const portalCards = [
  { name: "CareFusion", desc: "Clinical billing separation", badge: "CareFusion", href: "/coming-soon?portal=carefusion" },
  { name: "CAD", desc: "Dispatch & signaling", badge: "CAD", href: "/coming-soon?portal=cad" },
  { name: "ePCR", desc: "Structured PCR workflows", badge: "ePCR", href: "/coming-soon?portal=epcr" },
  { name: "NEMSIS", desc: "Schema & audit builder", badge: "NEMSIS", href: "/coming-soon?portal=nemsis" },
  { name: "NFIRS", desc: "Fire incident reporting", badge: "NFIRS", href: "/coming-soon?portal=nfirs" },
  { name: "Billing", desc: "Ledger, claims, denials", badge: "Billing", href: "/coming-soon?portal=billing" },
  { name: "Patient Portal", desc: "Payments + secure status", badge: "Patient", href: "/coming-soon?portal=patient" },
  { name: "Compliance", desc: "RBAC + audit hooks", badge: "Compliance", href: "/coming-soon?portal=compliance" },
  { name: "CrewLink", desc: "Crew telemetry & shifts", badge: "CrewLink", href: "/coming-soon?portal=crewlink" },
  { name: "Inventory", desc: "Medical supplies + lifecycle", badge: "Inventory", href: "/coming-soon?portal=inventory" },
  { name: "Founder Command", desc: "Control plane & insights", badge: "Founder", href: "/coming-soon?portal=founder" },
]

const badgeTags = ["Mission-ready", "Audit-friendly", "CSP-secure"]

const heroVariants: Variants = {
  hidden: { opacity: 0, y: 36 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.8, ease: [0.33, 1, 0.68, 1] },
  },
}

const gridVariants: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.08,
    },
  },
}

const cardVariants: Variants = {
  hidden: { opacity: 0, y: 24, scale: 0.98 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.4, ease: [0.35, 0, 0.25, 1] },
  },
}

export default function Home() {
  return (
    <main className="page-shell">
      <div className="glow-bg" aria-hidden="true" />
      <div className="page-container">
        <motion.section
          className="glass-panel hero-panel"
          initial="hidden"
          animate="visible"
          variants={heroVariants}
          role="banner"
          aria-label="FusionEMS Quantum hero"
        >
          <div className="hero-header">
            <div className="logo-row">
              <Image
                src="/assets/logo-header.svg"
                alt="FusionEMS Quantum"
                width={140}
                height={32}
                priority
              />
              <span className="badge glow" aria-label="enterprise badge">
                Enterprise
              </span>
            </div>
            <div className="hero-nav">
              <Link className="cta-button cta-secondary" href="/coming-soon" aria-label="Open command gate">
                Command Gate
              </Link>
              <Link className="cta-button cta-primary" href="/coming-soon" aria-label="Launch portal grid">
                Portal Grid
              </Link>
            </div>
          </div>

          <h1 className="hero-heading">
            FusionEMS Quantum
            <br />
            The Regulated EMS Operating System
          </h1>

          <p className="hero-subtitle">
            High-trust founders, compliance teams, and operations deserve a cinematic control plane
            with motion, security, and audit in every pulse. Built for DigitalOcean-scale resilience
            with Telnyx/Postmark/Stripe-ready integrations.
          </p>

          <div className="cta-row">
            <Link className="cta-button cta-primary" href="/coming-soon" aria-label="Explore portals">
              Explore Portals
            </Link>
            <Link className="cta-button cta-secondary" href="/coming-soon" aria-label="Download platform brief">
              Download Brief
            </Link>
          </div>
        </motion.section>

        <motion.section
          className="portal-section"
          initial="hidden"
          animate="visible"
          variants={gridVariants}
          aria-label="Portal launch grid"
        >
          <p className="section-title">Portal Launch Grid</p>
          <motion.div className="portal-grid">
            {portalCards.map((card) => (
              <motion.article key={card.name} className="portal-card" variants={cardVariants}>
                <strong>{card.name}</strong>
                <p>{card.desc}</p>
                <ul aria-label={`${card.name} highlights`}>
                  {badgeTags.map((tag) => (
                    <li key={tag}>{tag}</li>
                  ))}
                </ul>
                <Link
                  className="cta-button cta-secondary"
                  href={card.href}
                  aria-label={`${card.name} portal`}
                >
                  Visit
                </Link>
              </motion.article>
            ))}
          </motion.div>
        </motion.section>
      </div>
    </main>
  )
}
