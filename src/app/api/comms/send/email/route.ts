import { NextResponse } from "next/server"
import { z } from "zod"
import { sendEmail } from "@/services/email/postmark"
import { addQueueItem, addThreadMessage, createThread, updateQueueItem } from "@/lib/core/commsStore"
import { audit } from "@/lib/core/audit"

const bodySchema = z.object({
  to: z.string().email(),
  subject: z.string().min(1),
  html: z.string().min(1),
  text: z.string().optional(),
  tag: z.string().optional(),
  metadata: z.record(z.string(), z.string()).optional(),
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
    channel: "email",
    payload: parsed.data,
  })

  try {
    await sendEmail(parsed.data)
    updateQueueItem(queueItem.id, { status: "sent", error: undefined })
    const threadId =
      parsed.data.threadId ??
      createThread({
        channel: "email",
        title: parsed.data.subject,
        participants: [parsed.data.to],
        initialMessage: {
          direction: "outbound",
          body: parsed.data.html,
          status: "sent",
          metadata: {
            type: "email",
            subject: parsed.data.subject,
          },
        },
      }).id

    if (parsed.data.threadId) {
      addThreadMessage(parsed.data.threadId, {
        direction: "outbound",
        body: parsed.data.html,
        status: "sent",
        metadata: {
          type: "email",
          subject: parsed.data.subject,
        },
      })
    }

    audit("send_email", "queue", queueItem.id, {
      to: parsed.data.to,
      threadId,
    })

    return NextResponse.json({ message: "Email sent", threadId })
  } catch (error) {
    updateQueueItem(queueItem.id, {
      status: "failed",
      error: (error as Error).message,
    })
    audit("send_email_failed", "queue", queueItem.id, {
      to: parsed.data.to,
      error: (error as Error).message,
    })
    return NextResponse.json(
      { error: "Email send failed", detail: (error as Error).message },
      { status: 502 }
    )
  }
}
