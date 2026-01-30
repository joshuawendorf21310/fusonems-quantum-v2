import React from 'react'
import Image from 'next/image'

interface LogoProps {
  variant?: 'full' | 'header' | 'icon' | 'headerLockup'
  className?: string
  width?: number
  height?: number
  /** When true (default for headerLockup), icon has subtle pulse/glow */
  active?: boolean
}

const LOGO_VERSION = '20260130'

const logoSrc = {
  full: '/assets/logo-full.svg',
  header: '/assets/logo-header.svg',
  icon: '/assets/logo-mark-quantum.svg',
}

export default function Logo({
  variant = 'header',
  className = '',
  width,
  height,
  active = true,
}: LogoProps) {
  const defaultDimensions = {
    full: { width: 400, height: 120 },
    header: { width: 180, height: 48 },
    icon: { width: 512, height: 512 },
  }

  // Professional header: icon (active) + company name
  if (variant === 'headerLockup') {
    const iconSize = 40
    return (
      <span className={`header-lockup ${className}`.trim()} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span className="logo-icon-wrap" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, width: iconSize, height: iconSize }}>
          <Image
            src={`${logoSrc.icon}?v=${LOGO_VERSION}`}
            alt=""
            width={iconSize}
            height={iconSize}
            className={active ? 'logo-icon-active' : ''}
            style={{ width: iconSize, height: iconSize, maxWidth: iconSize, maxHeight: iconSize }}
            priority
            aria-hidden
          />
        </span>
        <span className="text-white font-semibold text-lg tracking-tight whitespace-nowrap" style={{ color: '#fff', fontWeight: 600, fontSize: 18, letterSpacing: '-0.025em', whiteSpace: 'nowrap' }}>
          FusionEMS <span className="text-orange-400" style={{ color: '#fb923c' }}>Quantum</span>
        </span>
      </span>
    )
  }

  if (variant === 'header') {
    const w = width ?? 180
    const h = height ?? 48
    return (
      <Image
        src={`${logoSrc.header}?v=${LOGO_VERSION}`}
        alt="FusionEMS Quantum logo"
        width={w}
        height={h}
        className={className}
        style={{ width: w, height: h, maxWidth: w, maxHeight: h }}
        priority
        aria-label="FusionEMS Quantum logo"
      />
    )
  }

  // For icon and full variants, use passed dimensions or reasonable defaults
  const finalWidth = width ?? (variant === 'icon' ? 40 : defaultDimensions[variant === 'full' ? 'full' : 'icon'].width)
  const finalHeight = height ?? (variant === 'icon' ? 40 : defaultDimensions[variant === 'full' ? 'full' : 'icon'].height)

  return (
    <Image
      src={`${logoSrc[variant]}?v=${LOGO_VERSION}`}
      alt="FusionEMS Quantum logo"
      width={finalWidth}
      height={finalHeight}
      className={className}
      style={{ width: finalWidth, height: finalHeight, maxWidth: finalWidth, maxHeight: finalHeight }}
      priority
      aria-label="FusionEMS Quantum logo"
    />
  )
}
