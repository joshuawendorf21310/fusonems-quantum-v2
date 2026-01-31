import React, { useState } from 'react';
import { submitPCS, submitAOB, submitABD, uploadFacesheet } from '../../app/transportlink/documentApi';

const REQUIRED_DOCS = [
  { type: 'PCS', label: 'Patient Care Summary' },
  { type: 'AOB', label: 'Authorization of Benefits' },
  { type: 'ABD', label: 'Advance Beneficiary Notice' },
  { type: 'FACESHEET', label: 'Facesheet Upload' },
];


export default function DocumentWorkflowModal({ trip, onClose, updateTrip, onAllComplete }) {
  const [step, setStep] = useState(0);
  const [completed, setCompleted] = useState([false, false, false, false]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form state for each doc type
  const [pcsForm, setPcsForm] = useState({ summary: '', items: '' });
  const [aobForm, setAobForm] = useState({ insurance: '', signature: '' });
  const [abdForm, setAbdForm] = useState({ accepted: false, signature: '' });
  const [facesheetFile, setFacesheetFile] = useState(null);

  // Update completed state from trip.documents if available
  React.useEffect(() => {
    if (trip.documents && Array.isArray(trip.documents)) {
      setCompleted([
        !!trip.documents.find(d => d.type === 'PCS' && d.status === 'complete'),
        !!trip.documents.find(d => d.type === 'AOB' && d.status === 'complete'),
        !!trip.documents.find(d => d.type === 'ABD' && d.status === 'complete'),
        !!trip.documents.find(d => d.type === 'FACESHEET' && d.status === 'complete'),
      ]);
    }
  }, [trip.documents]);

  // Auto-close if all docs complete
  React.useEffect(() => {
    if (completed.every(Boolean)) {
      if (onAllComplete) onAllComplete();
    }
  }, [completed, onAllComplete]);

  const handlePrev = () => {
    setStep(s => Math.max(s - 1, 0));
    setError(null); setSuccess(null);
  };
  const handleNext = () => {
    setStep(s => Math.min(s + 1, REQUIRED_DOCS.length - 1));
    setError(null); setSuccess(null);
  };

  // Submission handlers for each doc type
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      if (step === 0) {
        await submitPCS(trip.id || trip.trip_id, pcsForm);
      } else if (step === 1) {
        await submitAOB(trip.id || trip.trip_id, aobForm);
      } else if (step === 2) {
        await submitABD(trip.id || trip.trip_id, abdForm);
      } else if (step === 3) {
        if (!facesheetFile) throw new Error('Please select a file');
        await uploadFacesheet(trip.id || trip.trip_id, facesheetFile);
      }
      setSuccess('Submitted!');
      if (updateTrip) await updateTrip(trip.id || trip.trip_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // AI Assist stub handler
  const handleAIAssist = async () => {
    alert('AI Assist not yet implemented. This will call the backend extraction endpoint and autofill fields.');
  };

  // Render form for current step
  let formContent = null;
  if (step === 0) {
    formContent = (
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 8 }}>
          <label>Summary<br />
            <textarea name="summary" value={pcsForm.summary} onChange={e => setPcsForm(f => ({ ...f, summary: e.target.value }))} required />
          </label>
        </div>
        <div style={{ marginBottom: 8 }}>
          <label>Items (comma separated)<br />
            <input name="items" value={pcsForm.items} onChange={e => setPcsForm(f => ({ ...f, items: e.target.value }))} required />
          </label>
        </div>
        <button type="submit" disabled={loading || completed[0]}>Submit PCS</button>
        <button type="button" style={{ marginLeft: 8 }} onClick={handleAIAssist}>AI Assist</button>
      </form>
    );
  } else if (step === 1) {
    formContent = (
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 8 }}>
          <label>Insurance Info<br />
            <input name="insurance" value={aobForm.insurance} onChange={e => setAobForm(f => ({ ...f, insurance: e.target.value }))} required />
          </label>
        </div>
        <div style={{ marginBottom: 8 }}>
          <label>Signature (type name)<br />
            <input name="signature" value={aobForm.signature} onChange={e => setAobForm(f => ({ ...f, signature: e.target.value }))} required />
          </label>
        </div>
        <button type="submit" disabled={loading || completed[1]}>Submit AOB</button>
        <button type="button" style={{ marginLeft: 8 }} onClick={handleAIAssist}>AI Assist</button>
      </form>
    );
  } else if (step === 2) {
    formContent = (
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 8 }}>
          <label>
            <input type="checkbox" checked={abdForm.accepted} onChange={e => setAbdForm(f => ({ ...f, accepted: e.target.checked }))} />
            Patient accepts responsibility
          </label>
        </div>
        <div style={{ marginBottom: 8 }}>
          <label>Signature (type name)<br />
            <input name="signature" value={abdForm.signature} onChange={e => setAbdForm(f => ({ ...f, signature: e.target.value }))} required />
          </label>
        </div>
        <button type="submit" disabled={loading || completed[2]}>Submit ABD</button>
        <button type="button" style={{ marginLeft: 8 }} onClick={handleAIAssist}>AI Assist</button>
      </form>
    );
  } else if (step === 3) {
    formContent = (
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 8 }}>
          <label>Upload Facesheet (PDF or image)<br />
            <input type="file" accept="application/pdf,image/*" onChange={e => setFacesheetFile(e.target.files[0])} required />
          </label>
        </div>
        <button type="submit" disabled={loading || completed[3]}>Upload Facesheet</button>
        <button type="button" style={{ marginLeft: 8 }} onClick={handleAIAssist}>AI Assist</button>
      </form>
    );
  }

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: 'rgba(0,0,0,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div style={{ background: '#fff', padding: 32, borderRadius: 8, minWidth: 400, boxShadow: '0 2px 16px #0002', maxWidth: 600 }}>
        <h2>Complete Required Documents</h2>
        <div style={{ marginBottom: 16 }}>
          <strong>Trip:</strong> {trip.patient_name} ({trip.requested_date || trip.date_requested})
        </div>
        <div style={{ marginBottom: 24 }}>
          <h3>Step {step + 1}: {REQUIRED_DOCS[step].label}</h3>
          <div style={{ minHeight: 120, border: '1px solid #eee', borderRadius: 4, padding: 16, background: '#fafbfc' }}>
            {formContent}
            {error && <div style={{ color: 'red', marginTop: 8 }}>{error}</div>}
            {success && <div style={{ color: 'green', marginTop: 8 }}>{success}</div>}
            {completed[step] && <div style={{ color: 'green', marginTop: 8 }}>Step complete!</div>}
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <button onClick={onClose}>Cancel</button>
          <div>
            <button onClick={handlePrev} disabled={step === 0} style={{ marginRight: 8 }}>Back</button>
            <button onClick={handleNext} disabled={step === REQUIRED_DOCS.length - 1 || !completed[step]}>Next</button>
          </div>
        </div>
      </div>
    </div>
  );
}