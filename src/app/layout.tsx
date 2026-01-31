import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "../lib/auth-context";
import GlobalSearch from "../components/GlobalSearch";
import MustChangePasswordGuard from "../components/MustChangePasswordGuard";
import BannerAcceptanceGuard from "../components/BannerAcceptanceGuard";
import { ErrorBoundary } from "../components/ErrorBoundary";

export const metadata: Metadata = {
  title: "FusionEMS Quantum | The Regulated EMS Operating System",
  description:
    "Enterprise EMS operating system unifying CAD, ePCR, billing, compliance, and operational automation. NEMSIS-compliant, HIPAA-aligned, mission-critical support.",
  keywords: "EMS software, CAD system, ePCR, NEMSIS, HIPAA, EMS billing, ambulance dispatch, emergency medical services",
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://fusionemsquantum.com"),
  openGraph: {
    title: "FusionEMS Quantum | The Regulated EMS Operating System",
    description: "Enterprise EMS platform for CAD, ePCR, billing, and compliance.",
    images: ['/assets/logo-social.svg'],
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: "FusionEMS Quantum | Regulated EMS OS",
    description: "Enterprise EMS operating system. NEMSIS-compliant. HIPAA-aligned.",
    images: ['/assets/logo-social.svg'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <ErrorBoundary>
          <AuthProvider>
            <MustChangePasswordGuard />
            <BannerAcceptanceGuard />
            <GlobalSearch />
            {children}
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}
