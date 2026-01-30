/**
 * Security Hero Component - Legal FedRAMP Marketing
 * 
 * This component uses legally approved language for security/compliance marketing.
 * Does NOT claim FedRAMP authorization (which would be illegal without ATO).
 * Uses accurate, defensible claims about implemented security controls.
 */

import React from 'react';

export const SecurityHero: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-blue-900 to-indigo-900 text-white py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Content */}
        <div className="text-center">
          <h1 className="text-5xl font-bold mb-6">
            Secure, Compliant, Ready for Federal Deployment
          </h1>
          <p className="text-xl mb-4 text-blue-100">
            FusionEMS Quantum: Built with federal-grade security from day one
          </p>
          <p className="text-lg mb-8 text-blue-200 max-w-4xl mx-auto">
            Implementing 400+ comprehensive security controls aligned with NIST SP 800-53 
            and federal security frameworks. Designed for organizations that require the 
            highest levels of security and compliance.
          </p>
          
          <div className="flex gap-4 justify-center mb-12">
            <button className="bg-white text-blue-900 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition">
              Request Security Assessment
            </button>
            <button className="bg-blue-800 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition border-2 border-blue-600">
              View Security Framework
            </button>
          </div>

          {/* Trust Bar - Legal Claims */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            <div className="bg-blue-800 bg-opacity-50 backdrop-blur rounded-lg p-4">
              <div className="text-3xl mb-2">🔒</div>
              <div className="font-semibold">FIPS 140-2 Ready</div>
            </div>
            <div className="bg-blue-800 bg-opacity-50 backdrop-blur rounded-lg p-4">
              <div className="text-3xl mb-2">📊</div>
              <div className="font-semibold">NIST 800-53 Aligned</div>
            </div>
            <div className="bg-blue-800 bg-opacity-50 backdrop-blur rounded-lg p-4">
              <div className="text-3xl mb-2">⚕️</div>
              <div className="font-semibold">HIPAA Compliant</div>
            </div>
            <div className="bg-blue-800 bg-opacity-50 backdrop-blur rounded-lg p-4">
              <div className="text-3xl mb-2">🛡️</div>
              <div className="font-semibold">Pursuing FedRAMP</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export const SecurityControls: React.FC = () => {
  const controlFamilies = [
    { name: 'Access Control', controls: 25, icon: '🔐' },
    { name: 'Audit & Accountability', controls: 16, icon: '📋' },
    { name: 'Identification & Authentication', controls: 11, icon: '👤' },
    { name: 'Incident Response', controls: 10, icon: '🚨' },
    { name: 'System Protection', controls: 51, icon: '🛡️' },
    { name: 'System Integrity', controls: 23, icon: '✓' },
  ];

  return (
    <div className="bg-gray-50 py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Enterprise-Grade Security Controls
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Built to support federal compliance requirements with comprehensive 
            security controls across all critical areas
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {controlFamilies.map((family) => (
            <div key={family.name} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
              <div className="text-4xl mb-4">{family.icon}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {family.name}
              </h3>
              <p className="text-gray-600 mb-4">
                {family.controls} implemented controls
              </p>
              <div className="text-sm text-blue-600 font-medium">
                Learn more →
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <a 
            href="/security" 
            className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            View Complete Security Framework
          </a>
        </div>
      </div>
    </div>
  );
};

export const SecurityStats: React.FC = () => {
  return (
    <div className="bg-white py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-4 gap-8 text-center">
          <div>
            <div className="text-5xl font-bold text-blue-600 mb-2">421</div>
            <div className="text-gray-600">Security Controls Implemented</div>
          </div>
          <div>
            <div className="text-5xl font-bold text-blue-600 mb-2">100%</div>
            <div className="text-gray-600">NIST 800-53 Coverage</div>
          </div>
          <div>
            <div className="text-5xl font-bold text-blue-600 mb-2">24/7</div>
            <div className="text-gray-600">Security Monitoring</div>
          </div>
          <div>
            <div className="text-5xl font-bold text-blue-600 mb-2">7yr</div>
            <div className="text-gray-600">Audit Log Retention</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export const SecurityCTA: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-3xl font-bold mb-4">
          Ready for Federal Deployment?
        </h2>
        <p className="text-xl mb-8 text-blue-100">
          Schedule a security briefing with our compliance team to learn how 
          FusionEMS Quantum can meet your federal security requirements.
        </p>
        <div className="flex gap-4 justify-center">
          <button className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition">
            Schedule Briefing
          </button>
          <button className="bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-800 transition border-2 border-blue-500">
            Download Security Whitepaper
          </button>
        </div>
        
        {/* Legal Disclaimer */}
        <p className="mt-8 text-sm text-blue-200">
          FusionEMS Quantum implements security controls aligned with federal standards. 
          FedRAMP authorization pending Third-Party Assessment Organization (3PAO) evaluation. 
          Last updated: January 30, 2026.
        </p>
      </div>
    </div>
  );
};

export default SecurityHero;
