import { NextResponse } from "next/server"
import { getAuditEvents } from "@/lib/core/audit"

export async function GET() {
  return NextResponse.json(getAuditEvents())
}
