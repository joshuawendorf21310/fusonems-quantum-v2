import { NextResponse } from "next/server"

// Dummy CMS enrollments for compliance dashboard
const enrollments = [
  {
    id: 1,
    provider_name: "Fusion EMS Medical Group",
    npi_number: "1234567890",
    enrollment_status: "active",
    pecos_enrollment_id: "PECOS12345",
    enrollment_type: "Medicare",
    effective_date: "2022-01-01",
    revalidation_due_date: "2026-01-01",
    medicare_id: "MED1234567",
    metadata_last_verified: new Date().toISOString(),
  },
]

export async function GET() {
  return NextResponse.json(enrollments)
}
