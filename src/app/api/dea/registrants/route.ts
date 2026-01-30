import { NextResponse } from "next/server"

// Dummy DEA registrants for compliance dashboard
const registrants = [
  {
    id: 1,
    provider_name: "Fusion EMS Medical Group",
    dea_number: "DEA1234567",
    registration_expiration: "2027-01-01",
    schedule_authorization: ["II", "III", "IV"],
    business_activity: "EMS Provider",
    metadata_last_verified: new Date().toISOString(),
    notes: "Compliant and current."
  },
]

export async function GET() {
  return NextResponse.json(registrants)
}
