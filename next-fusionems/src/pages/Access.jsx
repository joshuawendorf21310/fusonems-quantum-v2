import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Access.css';

const roles = [
  {
    key: 'admin',
    label: 'Agency Administrator',
    summary: 'Full agency oversight, compliance, and operational controls.',
    cta: 'Admin Access',
    style: 'admin',
  },
  {
    key: 'provider',
    label: 'Provider',
    summary: 'Clinical charting, shift operations, and patient care tools.',
    cta: 'Provider Access',
    style: 'provider',
  },
  {
    key: 'pilot',
    label: 'Pilot',
    summary: 'Aviation mission board, flight logs, and read-only patient context.',
    cta: 'Pilot Access',
    style: 'pilot',
  },
  {
    key: 'founder',
    label: 'Founder',
    summary: 'Executive controls, audit, and mission control. Highest security.',
    cta: 'Founder Access',
    style: 'founder',
  },
];

export default function Access() {
  const navigate = useNavigate();
  return (
    <div className="access-bg">
      <div className="access-gateway">
        <h1 className="access-title">FusionEMS Quantum Access Gateway</h1>
        <p className="access-desc">Select your role to begin. All access is intentional and auditable.</p>
        <div className="access-cards">
          {roles.map((role) => (
            <div
              key={role.key}
              className={`access-card ${role.style}`}
              onClick={() => navigate(`/login/${role.key}?intent=${role.key}`)}
              tabIndex={0}
              role="button"
              aria-label={role.label}
            >
              <div className="access-card-header">
                {role.key === 'pilot' && <span className="pilot-icon" aria-label="Aviation">✈️</span>}
                <span className="access-card-label">{role.label}</span>
              </div>
              <div className="access-card-summary">{role.summary}</div>
              <button className="access-card-cta">{role.cta}</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
