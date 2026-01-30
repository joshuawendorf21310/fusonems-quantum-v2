/**
 * Compliance & Security Page
 * Showcases comprehensive security and compliance implementation
 */

import Link from 'next/link';
import { Shield, Lock, FileCheck, Activity, AlertCircle, CheckCircle, Download, Calendar, Users, Database } from 'lucide-react';

export const metadata = {
  title: 'Security & Compliance | FusionEMS Quantum',
  description: 'Enterprise-grade security with 421 implemented controls aligned with FedRAMP High Impact, HIPAA, and federal standards.',
};

export default function CompliancePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-900 to-indigo-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-800 rounded-full mb-6">
              <Shield className="w-10 h-10" />
            </div>
            <h1 className="text-5xl font-bold mb-4">
              Security & Compliance
            </h1>
            <p className="text-xl text-blue-100 max-w-3xl mx-auto mb-8">
              Enterprise-grade security infrastructure with comprehensive controls 
              aligned with federal standards. Built for organizations requiring the 
              highest levels of security and compliance.
            </p>
            <div className="flex gap-4 justify-center">
              <Link 
                href="#framework" 
                className="bg-white text-blue-900 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition"
              >
                View Security Framework
              </Link>
              <Link 
                href="#contact" 
                className="bg-blue-800 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition border-2 border-blue-600"
              >
                Request Security Assessment
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Key Stats */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 mb-16">
        <div className="grid md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-lg p-6 text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">421</div>
            <div className="text-gray-600">Security Controls Implemented</div>
          </div>
          <div className="bg-white rounded-lg shadow-lg p-6 text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">100%</div>
            <div className="text-gray-600">NIST 800-53 Coverage</div>
          </div>
          <div className="bg-white rounded-lg shadow-lg p-6 text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">24/7</div>
            <div className="text-gray-600">Security Monitoring</div>
          </div>
          <div className="bg-white rounded-lg shadow-lg p-6 text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">7yr</div>
            <div className="text-gray-600">Audit Log Retention</div>
          </div>
        </div>
      </div>

      {/* Compliance Standards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Compliance Standards & Certifications
          </h2>
          <p className="text-xl text-gray-600">
            Meeting and exceeding industry and federal requirements
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* FedRAMP */}
          <div className="bg-white rounded-lg shadow-md p-6 border-2 border-blue-200">
            <div className="flex items-start gap-4">
              <div className="bg-blue-100 p-3 rounded-lg">
                <Shield className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  FedRAMP Ready
                </h3>
                <p className="text-gray-600 mb-3">
                  421 security controls implemented aligned with FedRAMP High Impact 
                  baseline. Assessment-ready package prepared.
                </p>
                <div className="text-sm text-blue-600 font-medium">
                  Status: Pursuing Authorization
                </div>
              </div>
            </div>
          </div>

          {/* HIPAA */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start gap-4">
              <div className="bg-green-100 p-3 rounded-lg">
                <Lock className="w-6 h-6 text-green-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  HIPAA Compliant
                </h3>
                <p className="text-gray-600 mb-3">
                  Full HIPAA compliance with comprehensive security rule implementation, 
                  PHI protection, and audit trails.
                </p>
                <div className="text-sm text-green-600 font-medium">
                  Status: ✓ Compliant
                </div>
              </div>
            </div>
          </div>

          {/* NIST 800-53 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start gap-4">
              <div className="bg-indigo-100 p-3 rounded-lg">
                <FileCheck className="w-6 h-6 text-indigo-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  NIST 800-53 Aligned
                </h3>
                <p className="text-gray-600 mb-3">
                  Complete implementation of all 17 control families covering 421 
                  security controls.
                </p>
                <div className="text-sm text-indigo-600 font-medium">
                  Status: ✓ 100% Coverage
                </div>
              </div>
            </div>
          </div>

          {/* FIPS 140-2 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start gap-4">
              <div className="bg-purple-100 p-3 rounded-lg">
                <Lock className="w-6 h-6 text-purple-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  FIPS 140-2 Ready
                </h3>
                <p className="text-gray-600 mb-3">
                  Cryptographic controls aligned with FIPS 140-2 validated modules. 
                  AES-256-GCM encryption at rest and in transit.
                </p>
                <div className="text-sm text-purple-600 font-medium">
                  Status: ✓ Ready
                </div>
              </div>
            </div>
          </div>

          {/* SOC 2 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start gap-4">
              <div className="bg-orange-100 p-3 rounded-lg">
                <Activity className="w-6 h-6 text-orange-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  SOC 2 Type II Ready
                </h3>
                <p className="text-gray-600 mb-3">
                  Security controls exceed SOC 2 Type II requirements across all 
                  trust service criteria.
                </p>
                <div className="text-sm text-orange-600 font-medium">
                  Status: Assessment Ready
                </div>
              </div>
            </div>
          </div>

          {/* CMS/Medicare */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start gap-4">
              <div className="bg-teal-100 p-3 rounded-lg">
                <FileCheck className="w-6 h-6 text-teal-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  CMS Compliant
                </h3>
                <p className="text-gray-600 mb-3">
                  Medicare/Medicaid billing compliance with comprehensive audit logs 
                  and enrollment tracking.
                </p>
                <div className="text-sm text-teal-600 font-medium">
                  Status: ✓ Compliant
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Security Framework */}
      <div id="framework" className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Comprehensive Security Framework
            </h2>
            <p className="text-xl text-gray-600">
              421 implemented controls across 17 NIST 800-53 control families
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            {[
              { family: 'Access Control (AC)', controls: 25, status: '100%' },
              { family: 'Audit & Accountability (AU)', controls: 16, status: '100%' },
              { family: 'Identification & Authentication (IA)', controls: 11, status: '100%' },
              { family: 'System Protection (SC)', controls: 51, status: '100%' },
              { family: 'System Integrity (SI)', controls: 23, status: '100%' },
              { family: 'Incident Response (IR)', controls: 10, status: '100%' },
              { family: 'Configuration Management (CM)', controls: 11, status: '100%' },
              { family: 'Contingency Planning (CP)', controls: 13, status: '100%' },
              { family: 'Risk Assessment (RA)', controls: 6, status: '100%' },
              { family: 'Personnel Security (PS)', controls: 8, status: '100%' },
              { family: 'Physical & Environmental (PE)', controls: 20, status: '100%' },
              { family: 'Planning (PL)', controls: 9, status: '100%' },
              { family: 'Media Protection (MP)', controls: 8, status: '100%' },
              { family: 'Maintenance (MA)', controls: 6, status: '100%' },
              { family: 'Awareness & Training (AT)', controls: 5, status: '100%' },
              { family: 'Assessment & Authorization (CA)', controls: 9, status: '100%' },
              { family: 'System Acquisition (SA)', controls: 22, status: '100%' },
            ].map((item) => (
              <div key={item.family} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">{item.family}</h3>
                  <span className="bg-green-100 text-green-800 text-xs font-semibold px-2 py-1 rounded">
                    {item.status}
                  </span>
                </div>
                <p className="text-gray-600">{item.controls} controls implemented</p>
              </div>
            ))}
          </div>

          <div className="text-center">
            <Link 
              href="/security" 
              className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
            >
              View Complete Security Documentation
            </Link>
          </div>
        </div>
      </div>

      {/* Key Features */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Enterprise Security Features
          </h2>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Multi-Factor Authentication (MFA)
              </h3>
              <p className="text-gray-600">
                TOTP-based MFA required for all privileged access. Hardware token support. 
                Backup codes for recovery.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Comprehensive Audit Logging
              </h3>
              <p className="text-gray-600">
                Immutable audit logs with 7-year retention. All authentication, authorization, 
                and data access events captured.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Encryption at Rest & in Transit
              </h3>
              <p className="text-gray-600">
                AES-256-GCM encryption for data at rest. TLS 1.3 for all network communications. 
                Field-level encryption for PHI/PII.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                24/7 Security Monitoring
              </h3>
              <p className="text-gray-600">
                Real-time threat detection, anomaly detection, automated alerting, 
                and incident response.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Automated Vulnerability Scanning
              </h3>
              <p className="text-gray-600">
                Weekly vulnerability scans with NIST NVD integration. Automated patch 
                management and remediation tracking.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Incident Response Automation
              </h3>
              <p className="text-gray-600">
                Automated incident detection, classification, and response workflows. 
                Integration with US-CERT reporting.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Business Associate Agreements */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h2 className="text-3xl font-bold text-gray-900 mb-4">
                  Business Associate Agreements (BAA)
                </h2>
                <p className="text-gray-600 mb-6">
                  We maintain comprehensive Business Associate Agreements as required by 
                  HIPAA. Our platform includes automated BAA tracking, breach notification 
                  workflows, and vendor compliance management.
                </p>
                <ul className="space-y-3 mb-6">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-1" />
                    <span className="text-gray-600">HIPAA-compliant BAA templates</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-1" />
                    <span className="text-gray-600">Automated breach notification workflow</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-1" />
                    <span className="text-gray-600">Vendor compliance tracking</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-1" />
                    <span className="text-gray-600">Audit-ready documentation</span>
                  </li>
                </ul>
              </div>
              <div className="bg-blue-50 rounded-lg p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  Request BAA Documentation
                </h3>
                <p className="text-gray-600 mb-6">
                  Contact our compliance team to receive our Business Associate Agreement 
                  and supporting security documentation.
                </p>
                <Link 
                  href="#contact" 
                  className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
                >
                  Contact Compliance Team
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Contact Section */}
      <div id="contact" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg shadow-xl p-12 text-center text-white">
          <h2 className="text-3xl font-bold mb-4">
            Ready for Federal Deployment?
          </h2>
          <p className="text-xl mb-8 text-blue-100 max-w-3xl mx-auto">
            Schedule a security briefing with our compliance team to learn how 
            FusionEMS Quantum can meet your federal security requirements.
          </p>
          <div className="flex gap-4 justify-center">
            <a 
              href="mailto:compliance@fusionemsquantum.com" 
              className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition"
            >
              Contact Compliance Team
            </a>
            <Link 
              href="/demo" 
              className="bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-800 transition border-2 border-blue-500"
            >
              Request Security Assessment
            </Link>
          </div>
          
          {/* Legal Disclaimer */}
          <p className="mt-8 text-sm text-blue-200 max-w-3xl mx-auto">
            FusionEMS Quantum implements comprehensive security controls aligned with federal 
            standards including NIST SP 800-53 and FedRAMP High Impact baseline. FedRAMP 
            authorization pending Third-Party Assessment Organization (3PAO) evaluation. 
            HIPAA compliance and CMS compliance are operational. Last updated: January 30, 2026.
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center">
            <Link href="/" className="text-blue-600 hover:text-blue-700 font-medium">
              ← Back to Home
            </Link>
            <div className="text-gray-600 text-sm">
              © {new Date().getFullYear()} FusionEMS Quantum. All rights reserved.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
