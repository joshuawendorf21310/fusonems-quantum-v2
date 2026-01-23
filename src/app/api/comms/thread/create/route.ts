import { NextResponse } from "next/server"
import { z } from "zod"
import { createThread } from "@/lib/core/commsStore"
import { audit } from "@/lib/core/audit"

const schema = z.object({
  channel: z.enum(["email", "sms", "fax", "voice"]),
  title: z.string().min(3),
  participants: z.array(z.string()).min(1),
  initialMessage: z
    .object({
      direction: z.enum(["outbound", "inbound"]),
      body: z.string(),
      status: z.string(),
      metadata: z.record(z.string(), z.unknown()).optional(),
    })
    .optional(),
})

export async function POST(request: Request) {
  const payload = await request.json().catch(() => null)
  const parsed = schema.safeParse(payload)
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Invalid thread payload", issues: parsed.error.format() },
      { status: 400 }
    )
  }

  const thread = createThread({
    channel: parsed.data.channel,
    title: parsed.data.title,
    participants: parsed.data.participants,
    initialMessage: parsed.data.initialMessage,
  })
  audit("create_thread", "thread", thread.id, {
    channel: thread.channel,
    participants: thread.participants,
  })
  return NextResponse.json(thread)
}
