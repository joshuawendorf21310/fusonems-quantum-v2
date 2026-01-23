import { NextResponse } from "next/server"
import { getThread } from "@/lib/core/commsStore"

export async function GET(
  request: Request,
  context: { params: Promise<{ id: string }> }
) {
  const { id } = await context.params
  const thread = getThread(id)
  if (!thread) {
    return NextResponse.json({ error: "Thread not found" }, { status: 404 })
  }
  return NextResponse.json(thread)
}
