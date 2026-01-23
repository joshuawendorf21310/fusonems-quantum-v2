import { NextResponse } from "next/server"
import { getQueueItems } from "@/lib/core/commsStore"

export async function GET() {
  return NextResponse.json(getQueueItems())
}
