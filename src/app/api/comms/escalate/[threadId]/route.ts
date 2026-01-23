import { NextResponse } from "next/server"
import { z } from "zod"
import { addEscalation, getThread } from "@/lib/core/commsStore"
import { audit } from "@/lib/core/audit"

const bodySchema = z.object({
  reason: z.string().min(3),
  user: z.string().optional(),
})

export async function POST(
  request: Request,
  context: { params: Promise<{ threadId: string }> }
) {
  const { threadId } = await context.params
  const parsedBody = bodySchema.safeParse(await request.json().catch(() => null))
  if (!parsedBody.success) {
    return NextResponse.json(
      { error: "Invalid escalation payload", issues: parsedBody.error.format() },
      { status: 400 }
    )
  }

  const thread = getThread(threadId)
  if (!thread) {
    return NextResponse.json({ error: "Thread not found" }, { status: 404 })
  }

  const escalation = addEscalation(threadId, parsedBody.data.reason, parsedBody.data.user)

  audit("escalate_thread", "thread", threadId, {
    reason: parsedBody.data.reason,
    user: parsedBody.data.user,
    escalationId: escalation?.id,
  })

  return NextResponse.json({ message: "Escalation recorded", escalation })
}
