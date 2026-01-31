"use client";

import React, { useEffect, useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute.jsx';
import { FACILITY_ROLES } from './facilityRoles';
import { listTransports, getTransport } from './transportApi';
// TODO: Import BookingList, BulkActions

import DocumentWorkflowModal from '@/components/transportlink/DocumentWorkflowModal';
import { useState as useToastState } from 'react';

const STATUS_OPTIONS = [
  'pending',
  'confirmed',
  'in-transit',
  'completed',
  'cancelled',
];

const Bookings = () => {
  // Store trips as a map for fast update
  const [trips, setTrips] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [selected, setSelected] = useState([]);
  const [docModalTrip, setDocModalTrip] = useState(null); // trip object for modal

  useEffect(() => {
    setLoading(true);
    listTransports()
      .then(list => {
        const map = {};
        list.forEach(t => { map[t.id || t.trip_id] = t; });
        setTrips(map);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const tripList = Object.values(trips);
  const filtered = statusFilter
    ? tripList.filter(t => (t.status || t.trip_status) === statusFilter)
    : tripList;

  const toggleSelect = (id) => {
    setSelected(sel => sel.includes(id) ? sel.filter(x => x !== id) : [...sel, id]);
  };

  // Toast for completion
  const [toast, setToast] = useToastState(null);

  return (
    <ProtectedRoute allowedRoles={FACILITY_ROLES}>
      <div>
        <h1>Manage Bookings</h1>
        {toast && (
          <div style={{ position: 'fixed', top: 24, right: 24, background: '#222', color: '#fff', padding: 16, borderRadius: 8, zIndex: 2000 }}>
            {toast}
            <button style={{ marginLeft: 16 }} onClick={() => setToast(null)}>✕</button>
          </div>
        )}
        {loading && <p>Loading bookings...</p>}
        {error && <p style={{color: 'red'}}>Error: {error}</p>}
        {!loading && !error && (
          <>
            <div style={{ marginBottom: 16 }}>
              <label>Status Filter: </label>
              <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                <option value="">All</option>
                {STATUS_OPTIONS.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
            <form>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th></th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Patient</th>
                    <th>Status</th>
                    <th>Document Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(t => {
                    // Compute doc status indicator from backend fields
                    let docState = 'missing';
                    if (t.documents && Array.isArray(t.documents)) {
                      const total = t.documents.length;
                      const complete = t.documents.filter(d => d.status === 'complete').length;
                      if (complete === 0) docState = 'missing';
                      else if (complete < total) docState = 'partial';
                      else docState = 'complete';
                    } else if (t.compliance_status || t.document_status) {
                      if ((t.compliance_status || t.document_status) === 'complete') docState = 'complete';
                      else if ((t.compliance_status || t.document_status) === 'incomplete') docState = 'missing';
                      else docState = 'partial';
                    }
                    const docIcon = docState === 'complete' ? '✔' : docState === 'partial' ? '🟡' : '⚠';
                    const docLabel = docState === 'complete' ? 'Docs Complete' : docState === 'partial' ? 'Partial' : 'Missing Docs';
                    const incomplete = docState !== 'complete';
                    return (
                      <tr key={t.id || t.trip_id} style={{ borderBottom: '1px solid #eee' }}>
                        <td>
                          <input
                            type="checkbox"
                            checked={selected.includes(t.id || t.trip_id)}
                            onChange={() => toggleSelect(t.id || t.trip_id)}
                            disabled={incomplete}
                            title={incomplete ? 'Required documents must be completed before submission' : ''}
                          />
                        </td>
                        <td>{t.requested_date || t.date_requested || '-'}</td>
                        <td>{t.requested_time || t.time_requested || '-'}</td>
                        <td>{t.patient_summary?.name || t.patient_name || '-'}</td>
                        <td>{t.status || t.trip_status}</td>
                        <td>
                          <span title={docLabel} style={{ fontWeight: 'bold', marginRight: 4 }}>{docIcon}</span>
                          {docLabel}
                          {incomplete && (
                            <button
                              type="button"
                              style={{ marginLeft: 8 }}
                              onClick={() => setDocModalTrip(t)}
                            >
                              Complete Required Documents
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {/* Bulk actions placeholder */}
              <div style={{ marginTop: 16 }}>
                <button type="button" disabled={selected.length === 0}>
                  Request Documentation (Bulk)
                </button>
                <button type="button" disabled={selected.length === 0} style={{ marginLeft: 8 }}>
                  Approve Selected
                </button>
              </div>
            </form>
            {docModalTrip && (
              <DocumentWorkflowModal
                trip={trips[docModalTrip.id || docModalTrip.trip_id]}
                onClose={() => setDocModalTrip(null)}
                updateTrip={async (id) => {
                  const trip = await getTransport(id);
                  setTrips(trips => ({ ...trips, [id]: trip }));
                }}
                onAllComplete={() => {
                  setDocModalTrip(null);
                  setToast('All required documents complete!');
                  setTimeout(() => setToast(null), 4000);
                }}
              />
            )}
          </>
        )}
      </div>
    </ProtectedRoute>
  );
};

export default Bookings;
