"use client";
import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { NemsisRecordActions } from "@/components/epcr";

const glassmorphism = {
  background: "rgba(17, 17, 17, 0.8)",
  border: "1px solid rgba(255, 107, 53, 0.2)",
};

export default function EmsEpcrDetail() {
  const params = useParams();
  const router = useRouter();
  const recordId = params?.id as string;
  const [record, setRecord] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (!recordId) return;
    setLoading(true);
    fetch(`/api/epcr/records/${recordId}`)
      .then((r) => r.json())
      .then((data) => {
        setRecord(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [recordId]);

  if (loading) return <div style={{ color: "#f7f6f3", padding: "2rem" }}>Loading...</div>;
  if (!record) return <div style={{ color: "#f7f6f3", padding: "2rem" }}>Record not found</div>;

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #000000 0%, #0a0a0a 100%)",
        color: "#f7f6f3",
        minHeight: "100vh",
        padding: "2rem",
        fontFamily: "'Inter', -apple-system, sans-serif",
      }}
    >
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 800, color: "#ff6b35" }}>
              HEMS ePCR - {record.patient?.first_name} {record.patient?.last_name}
            </h1>
            <p style={{ margin: "0.5rem 0 0 0", fontSize: "12px", color: "#888" }}>
              {record.record_id} • {record.created_at}
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <NemsisRecordActions recordId={recordId} stateCode="WI" compact />
            <button
              onClick={() => router.back()}
              style={{
                background: "transparent",
                color: "#ff6b35",
                border: "1px solid rgba(255, 107, 53, 0.5)",
                padding: "12px 24px",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              ← Back
            </button>
          </div>
        </div>

        {/* Patient Section */}
        <div style={{ ...glassmorphism, padding: "1.5rem", marginBottom: "1.5rem" }}>
          <h2 style={{ margin: "0 0 1rem 0", color: "#ff6b35", fontSize: "16px" }}>Patient Information</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", fontSize: "14px" }}>
            <div>
              <div style={{ color: "#888", fontSize: "12px", marginBottom: "4px" }}>Name</div>
              <div>{record.patient?.first_name} {record.patient?.last_name}</div>
            </div>
            <div>
              <div style={{ color: "#888", fontSize: "12px", marginBottom: "4px" }}>DOB</div>
              <div>{record.patient?.date_of_birth}</div>
            </div>
            <div>
              <div style={{ color: "#888", fontSize: "12px", marginBottom: "4px" }}>Phone</div>
              <div>{record.patient?.phone}</div>
            </div>
            <div>
              <div style={{ color: "#888", fontSize: "12px", marginBottom: "4px" }}>Address</div>
              <div>{record.patient?.address}</div>
            </div>
          </div>
        </div>

        {/* Assessment Section */}
        <div style={{ ...glassmorphism, padding: "1.5rem", marginBottom: "1.5rem" }}>
          <h2 style={{ margin: "0 0 1rem 0", color: "#ff6b35", fontSize: "16px" }}>Chief Complaint & Assessment</h2>
          <div style={{ marginBottom: "1rem" }}>
            <div style={{ color: "#888", fontSize: "12px", marginBottom: "4px" }}>Chief Complaint</div>
            <div>{record.chief_complaint}</div>
          </div>
          <div>
            <div style={{ color: "#888", fontSize: "12px", marginBottom: "4px" }}>Assessment Notes</div>
            <div style={{ background: "rgba(10, 10, 10, 0.5)", padding: "1rem", minHeight: "100px" }}>
              {record.assessment || "No assessment documented"}
            </div>
          </div>
        </div>

        {/* Vitals Section */}
        {record.vitals && (
          <div style={{ ...glassmorphism, padding: "1.5rem", marginBottom: "1.5rem" }}>
            <h2 style={{ margin: "0 0 1rem 0", color: "#ff6b35", fontSize: "16px" }}>Vital Signs</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem", fontSize: "14px" }}>
              {record.vitals.heart_rate && (
                <div>
                  <div style={{ color: "#888", fontSize: "12px" }}>HR</div>
                  <div style={{ fontSize: "18px", fontWeight: 600, color: "#ff6b35" }}>
                    {record.vitals.heart_rate} bpm
                  </div>
                </div>
              )}
              {record.vitals.systolic_bp && (
                <div>
                  <div style={{ color: "#888", fontSize: "12px" }}>BP</div>
                  <div style={{ fontSize: "18px", fontWeight: 600, color: "#ff6b35" }}>
                    {record.vitals.systolic_bp}/{record.vitals.diastolic_bp}
                  </div>
                </div>
              )}
              {record.vitals.respiratory_rate && (
                <div>
                  <div style={{ color: "#888", fontSize: "12px" }}>RR</div>
                  <div style={{ fontSize: "18px", fontWeight: 600, color: "#ff6b35" }}>
                    {record.vitals.respiratory_rate}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Raw JSON */}
        <div style={{ ...glassmorphism, padding: "1.5rem" }}>
          <h2 style={{ margin: "0 0 1rem 0", color: "#ff6b35", fontSize: "16px" }}>Raw Data</h2>
          <pre
            style={{
              background: "rgba(10, 10, 10, 0.5)",
              padding: "1rem",
              overflow: "auto",
              fontSize: "11px",
              color: "#888",
            }}
          >
            {JSON.stringify(record, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
