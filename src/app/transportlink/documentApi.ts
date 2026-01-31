// API functions for submitting required documents for a trip

const DOC_API_BASE = "/api/transport/trips";

export async function submitPCS(tripId, data) {
  const res = await fetch(`${DOC_API_BASE}/${tripId}/documents/pcs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to submit PCS");
  return res.json();
}

export async function submitAOB(tripId, data) {
  const res = await fetch(`${DOC_API_BASE}/${tripId}/documents/aob`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to submit AOB");
  return res.json();
}

export async function submitABD(tripId, data) {
  const res = await fetch(`${DOC_API_BASE}/${tripId}/documents/abd`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to submit ABD");
  return res.json();
}

export async function uploadFacesheet(tripId, file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${DOC_API_BASE}/${tripId}/documents/facesheet`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload facesheet");
  return res.json();
}
