import React from 'react'

interface TrustBadgeProps {
  icon: 'shield' | 'lock' | 'activity' | 'headset' | string
  text: string
  variant?: 'default' | 'compact' | 'large'
}

const iconSize = { default: 16, compact: 14, large: 24 }

function iconSvg(icon: string, size: number) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const }
  switch (icon) {
    case 'shield':
      return <svg {...common}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
    case 'lock':
      return <svg {...common}><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
    case 'activity':
      return <svg {...common}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
    case 'headset':
      return <svg {...common}><path d="M3 18v-6a9 9 0 0 1 18 0v6" /><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z" /></svg>
    default:
      return <svg {...common}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
  }
}

export default function TrustBadge({ icon, text, variant = 'default' }: TrustBadgeProps) {
  const size = iconSize[variant]
  const iconEl = iconSvg(icon, size)

  const gapClass = variant === "compact" ? "gap-1.5" : variant === "large" ? "gap-3" : "gap-2"
  const iconWrapClass = variant === "compact" ? "w-3.5 h-3.5" : variant === "large" ? "w-7 h-7" : "w-4 h-4"
  const textClass =
    variant === "compact"
      ? "text-[11px] font-semibold whitespace-nowrap"
      : variant === "large"
        ? "text-[1rem] font-semibold whitespace-nowrap"
        : "text-xs font-semibold whitespace-nowrap"

  return (
    <div
      className={["inline-flex items-center", gapClass, "text-white/65 hover:text-white/85 transition-colors"].join(" ")}
      aria-label={text}
    >
      <span className={`inline-flex items-center justify-center text-orange-400 ${iconWrapClass}`}>
        {iconEl}
      </span>
      <span className={textClass}>{text}</span>
    </div>
  )
}
