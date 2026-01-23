import { NextResponse } from "next/server"
import { z } from "zod"
import { sendEmail } from "@/services/email/postmark"
import { sendSms } from "@/services/comms/telnyx"
import {
  addThreadMessage,
  createThread,
  findQueueItem,
  updateQueueItem,
} from "@/lib/core/commsStore"
import { audit } from "@/lib/core/audit"

const emailRetrySchema = z.object({
  to: z.string().email(),
  subject: z.string(),
  html: z.string(),
  text: z.string().optional(),
  tag: z.string().optional(),
  metadata: z.record(z.string(), z.string()).optional(),
  threadId: z.string().optional(),
})

const smsRetrySchema = z.object({
  to: z.string(),
  from: z.string(),
  body: z.string(),
  threadId: z.string().optional(),
})

export async function POST(
  request: Request,
  context: { params: Promise<{ eventId: string }> }
) {
  const { eventId } = await context.params
  const queueItem = findQueueItem(eventId)
  if (!queueItem) {
    return NextResponse.json({ error: "Queue item not found" }, { status: 404 })
  }

  try {
    switch (queueItem.channel) {
      case "email": {
        const data = emailRetrySchema.parse(queueItem.payload)
        await sendEmail(data)
        updateQueueItem(queueItem.id, { status: "sent", error: undefined })
        const threadId =
          data.threadId ??
          createThread({
            channel: "email",
            title: data.subject,
            participants: [data.to],
            initialMessage: {
              direction: "outbound",
              body: data.html,
              status: "sent",
            },
          }).id

        if (data.threadId) {
          addThreadMessage(data.threadId, {
            direction: "outbound",
            body: data.html,
            status: "sent",
          })
        }

        audit("retry_email", "queue", queueItem.id, {
          threadId,
          to: data.to,
        })
        break
      }
      case "sms": {
        const data = smsRetrySchema.parse(queueItem.payload)
        await sendSms(data)
        updateQueueItem(queueItem.id, { status: "sent", error: undefined })
        const threadId =
          data.threadId ??
          createThread({
            channel: "sms",
            title: `SMS to ${data.to}`,
            participants: [data.to],
            initialMessage: {
              direction: "outbound",
              body: data.body,
              status: "sent",
            },
          }).id

        if (data.threadId) {
          addThreadMessage(data.threadId, {
            direction: "outbound",
            body: data.body,
            status: "sent",
          })
        }

        audit("retry_sms", "queue", queueItem.id, {
          threadId,
          to: data.to,
        })
        break
      }
      default: {
        return NextResponse.json(
          { error: "Retry not supported for this channel" },
          { status: 400 }
        )
      }
    }

    return NextResponse.json({ message: "Retry queued" })
  } catch (error) {
    updateQueueItem(queueItem.id, {
      status: "failed",
      error: (error as Error).message,
    })
    audit("retry_failed", "queue", queueItem.id, {
      error: (error as Error).message,
    })
    return NextResponse.json(
      { error: "Retry failed", detail: (error as Error).message },
      { status: 502 }
    )
  }
}
