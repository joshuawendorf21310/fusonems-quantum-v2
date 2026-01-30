"use client";
import React, { useRef, useState } from "react"

interface SpacesUploadWidgetProps {
  orgId: string
  bucket: "business" | "personal" | "family"
  onUploaded?: (key: string) => void
}

export default function SpacesUploadWidget({ orgId, bucket, onUploaded }: SpacesUploadWidgetProps) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError("")
    const formData = new FormData()
    formData.append("file", file)
    try {
      const res = await fetch(`/api/spaces/upload?orgId=${orgId}&bucket=${bucket}`, {
        method: "POST",
        body: formData
      })
      if (!res.ok) throw new Error("Upload failed")
      const data = await res.json()
      onUploaded?.(data.key)
    } catch {
      setError("Upload failed")
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="mb-2">
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        onChange={handleFileChange}
      />
      <button className="btn-secondary" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
        {uploading ? "Uploading..." : `Upload to ${bucket} bucket`}
      </button>
      {error && <div className="text-red-600 text-sm mt-1">{error}</div>}
    </div>
  )
}
