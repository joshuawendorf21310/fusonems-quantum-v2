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
      <span className={`header-lockup ${className}`.trim()}>
        <span className="logo-icon-wrap">
          <Image
            src={`${logoSrc.icon}?v=${LOGO_VERSION}`}
            alt=""
            width={iconSize}
            height={iconSize}
            className={active ? 'logo-icon-active' : ''}
            priority
            aria-hidden
          />
        </span>
        <span className="text-white font-semibold text-lg tracking-tight whitespace-nowrap">
          FusionEMS <span className="text-orange-400">Quantum</span>
        </span>
      </span>
    )
  }

  if (variant === 'header') {
    return (
      <Image
        src={`${logoSrc.header}?v=${LOGO_VERSION}`}
        alt="FusionEMS Quantum logo"
        width={width ?? 180}
        height={height ?? 48}
        className={className}
        priority
        aria-label="FusionEMS Quantum logo"
      />
    )
  }

  const dimensions = {
    width: width ?? defaultDimensions[variant === 'full' ? 'full' : 'icon'].width,
    height: height ?? defaultDimensions[variant === 'full' ? 'full' : 'icon'].height,
  }

  return (
    <Image
      src={`${logoSrc[variant]}?v=${LOGO_VERSION}`}
      alt="FusionEMS Quantum logo"
      width={dimensions.width}
      height={dimensions.height}
      className={className}
      priority
      aria-label="FusionEMS Quantum logo"
    />
  )
}
