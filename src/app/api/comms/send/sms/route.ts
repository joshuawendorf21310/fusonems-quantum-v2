import { NextResponse } from "next/server"
import { z } from "zod"
import { sendSms } from "@/services/comms/telnyx"
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
  body: z.string().min(1),
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
    channel: "sms",
    payload: parsed.data,
  })

  try {
    const response = await sendSms(parsed.data)
    updateQueueItem(queueItem.id, { status: "sent", error: undefined })

    const threadId =
      parsed.data.threadId ??
      createThread({
        channel: "sms",
        title: `SMS to ${parsed.data.to}`,
        participants: [parsed.data.to],
        initialMessage: {
          direction: "outbound",
          body: parsed.data.body,
          status: "sent",
        },
      }).id

    if (parsed.data.threadId) {
      addThreadMessage(parsed.data.threadId, {
        direction: "outbound",
        body: parsed.data.body,
        status: "sent",
      })
    }

    audit("send_sms", "queue", queueItem.id, {
      to: parsed.data.to,
      response,
      threadId,
    })
    return NextResponse.json({ message: "SMS queued", threadId })
  } catch (error) {
    updateQueueItem(queueItem.id, {
      status: "failed",
      error: (error as Error).message,
    })
    audit("send_sms_failed", "queue", queueItem.id, {
      to: parsed.data.to,
      error: (error as Error).message,
    })
    return NextResponse.json(
      { error: "SMS send failed", detail: (error as Error).message },
      { status: 502 }
    )
  }
}
