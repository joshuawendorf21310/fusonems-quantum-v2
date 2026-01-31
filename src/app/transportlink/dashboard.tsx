"use client";

import React, { useEffect, useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute.jsx';
import { FACILITY_ROLES } from './facilityRoles';
import { listTransports, createTransport } from './transportApi';
// TODO: Import TransportCalendar, QuickBookButton

const Dashboard = () => {
  const [transports, setTransports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showQuickBook, setShowQuickBook] = useState(false);
  const [quickBookLoading, setQuickBookLoading] = useState(false);
  const [quickBookError, setQuickBookError] = useState(null);
  const [quickBookSuccess, setQuickBookSuccess] = useState(null);
  const [quickBookForm, setQuickBookForm] = useState({
    patient_name: '',
    requested_date: '',
    requested_time: '',
    pickup_location: '',
    destination: '',
    // Add other required fields as needed
  });

  const fetchTransports = () => {
    setLoading(true);
    setError(null);
    listTransports()
      .then(setTransports)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchTransports();
  }, []);
  const handleQuickBookChange = (e) => {
    const { name, value } = e.target;
    setQuickBookForm(f => ({ ...f, [name]: value }));
  };

  const handleQuickBookSubmit = async (e) => {
    e.preventDefault();
    setQuickBookLoading(true);
    setQuickBookError(null);
    setQuickBookSuccess(null);
    try {
      // Only send required fields for minimal Quick-Book
      const payload = {
        patient_name: quickBookForm.patient_name,
        requested_date: quickBookForm.requested_date,
        requested_time: quickBookForm.requested_time,
        pickup_location: quickBookForm.pickup_location,
        destination: quickBookForm.destination,
      };
      await createTransport(payload);
      setQuickBookSuccess('Transport request created!');
      setShowQuickBook(false);
      setQuickBookForm({ patient_name: '', requested_date: '', requested_time: '', pickup_location: '', destination: '' });
      fetchTransports();
    } catch (err) {
      setQuickBookError(err.message);
    } finally {
      setQuickBookLoading(false);
    }
  };

  // Status counts for summary
  const statusCounts = transports.reduce((acc, t) => {
    // Use t.status or t.trip_status depending on API
    const status = t.status || t.trip_status || 'unknown';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});

  return (
    <ProtectedRoute allowedRoles={FACILITY_ROLES}>
      <div>
        <h1>Facility Dashboard</h1>
        {loading && <p>Loading transports...</p>}
        {error && <p style={{color: 'red'}}>Error: {error}</p>}
        {!loading && !error && (
          <>
            <div className="status-summary" style={{ display: 'flex', gap: 16 }}>
              {Object.entries(statusCounts).map(([status, count]) => (
                <div key={status} style={{ border: '1px solid #ccc', padding: 8, borderRadius: 4 }}>
                  <strong>{status}</strong>
                  <div>{count} transports</div>
                </div>
              ))}
            </div>
            {/* Pass transports to TransportCalendar when implemented */}
            {/* <TransportCalendar transports={transports} /> */}

            <button style={{ margin: '24px 0' }} onClick={() => setShowQuickBook(true)}>
              Quick-Book Transport
            </button>

            {showQuickBook && (
              <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: 'rgba(0,0,0,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                <div style={{ background: '#fff', padding: 32, borderRadius: 8, minWidth: 320, boxShadow: '0 2px 16px #0002' }}>
                  <h2>Quick-Book Transport</h2>
                  <form onSubmit={handleQuickBookSubmit}>
                    <div style={{ marginBottom: 12 }}>
                      <label>Patient Name<br />
                        <input name="patient_name" value={quickBookForm.patient_name} onChange={handleQuickBookChange} required />
                      </label>
                    </div>
                    <div style={{ marginBottom: 12 }}>
                      <label>Date<br />
                        <input name="requested_date" type="date" value={quickBookForm.requested_date} onChange={handleQuickBookChange} required />
                      </label>
                    </div>
                    <div style={{ marginBottom: 12 }}>
                      <label>Time<br />
                        <input name="requested_time" type="time" value={quickBookForm.requested_time} onChange={handleQuickBookChange} required />
                      </label>
                    </div>
                    <div style={{ marginBottom: 12 }}>
                      <label>Pickup Location<br />
                        <input name="pickup_location" value={quickBookForm.pickup_location} onChange={handleQuickBookChange} required />
                      </label>
                    </div>
                    <div style={{ marginBottom: 12 }}>
                      <label>Destination<br />
                        <input name="destination" value={quickBookForm.destination} onChange={handleQuickBookChange} required />
                      </label>
                    </div>
                    {quickBookError && <div style={{ color: 'red', marginBottom: 8 }}>{quickBookError}</div>}
                    <div style={{ display: 'flex', gap: 12 }}>
                      <button type="submit" disabled={quickBookLoading}>
                        {quickBookLoading ? 'Booking...' : 'Book'}
                      </button>
                      <button type="button" onClick={() => setShowQuickBook(false)} disabled={quickBookLoading}>
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}
            {quickBookSuccess && <div style={{ color: 'green', marginTop: 12 }}>{quickBookSuccess}</div>}
          </>
        )}
      </div>
    </ProtectedRoute>
  );
};

export default Dashboard;
