import { NextResponse } from "next/server"
import { z } from "zod"
import { initiateCall } from "@/services/comms/telnyx"
import {
  addQueueItem,
  addThreadMessage,
  createThread,
  updateQueueItem,
} from "@/lib/core/commsStore"
import { audit } from "@/lib/core/audit"

const bodySchema = z.object({
  to: z.string().min(5),
  from: z.string().min(5),
  reason: z.string().optional(),
  threadId: z.string().optional(),
})

export async function POST(request: Request) {
  const payload = await request.json().catch(() => null)
  const parsed = bodySchema.safeParse(payload)
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Invalid payload", issues: parsed.error.format() },
      { status: 400 }
    )
  }

  const queueItem = addQueueItem({
    channel: "voice",
    payload: parsed.data,
  })

  try {
    const result = await initiateCall(parsed.data)
    updateQueueItem(queueItem.id, { status: "sent", error: undefined })
    const threadId =
      parsed.data.threadId ??
      createThread({
        channel: "voice",
        title: "Voice dispatch",
        participants: [parsed.data.to],
        initialMessage: {
          direction: "outbound",
          body: parsed.data.reason ?? "Call initiated",
          status: "queued",
        },
      }).id

    if (parsed.data.threadId) {
      addThreadMessage(parsed.data.threadId, {
        direction: "outbound",
        body: parsed.data.reason ?? "Call initiated",
        status: "queued",
      })
    }

    audit("send_voice", "queue", queueItem.id, {
      to: parsed.data.to,
      result,
      threadId,
    })
    return NextResponse.json({ message: "Call queued", threadId })
  } catch (error) {
    updateQueueItem(queueItem.id, {
      status: "failed",
      error: (error as Error).message,
    })
    audit("send_voice_failed", "queue", queueItem.id, {
      to: parsed.data.to,
      error: (error as Error).message,
    })
    return NextResponse.json(
      { error: "Voice send failed", detail: (error as Error).message },
      { status: 502 }
    )
  }
}
