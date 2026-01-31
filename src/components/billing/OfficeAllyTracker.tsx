type OfficeAllyTrackerProps = {
  batchId?: string
  submittedAt?: string
  status?: string
  ackPayload?: Record<string, unknown>
}

export default function OfficeAllyTracker({ batchId, submittedAt, status, ackPayload }: OfficeAllyTrackerProps) {
  return (
    <div
      style={{
        padding: "1rem",
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.08)",
        background: "rgba(12,12,12,0.8)",
      }}
    >
      <p style={{ margin: 0, color: "#f7f6f3", fontWeight: 600 }}>Office Ally Batch</p>
      <p style={{ margin: "0.25rem 0 0", color: "#ffb347" }}>{batchId || "Not submitted"}</p>
      <p style={{ margin: "0.2rem 0 0", fontSize: "0.8rem", color: "#bbb" }}>
        Status: {status || "idle"}
      </p>
      {submittedAt && (
        <p style={{ margin: "0.2rem 0 0", fontSize: "0.75rem", color: "#777" }}>
          Submitted at {new Date(submittedAt).toLocaleString()}
        </p>
      )}
      {ackPayload && (
        <p style={{ margin: "0.35rem 0 0", fontSize: "0.72rem", color: "#777" }}>
          Ack: {ackPayload?.status || "N/A"}
        </p>
      )}
    </div>
  )
}
