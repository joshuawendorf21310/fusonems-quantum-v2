import { NextResponse } from "next/server"
import { z } from "zod"
import { sendFax } from "@/services/comms/telnyx"
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
  fileUrl: z.string().url().optional(),
  fileName: z.string().optional(),
  threadId: z.string().optional(),
})

export async function POST(request: Request) {
  const formData = await request.formData()
  const file = formData.get("file")
  const fileBuffer = file instanceof File ? await file.arrayBuffer() : undefined
  const parsed = bodySchema.safeParse({
    to: formData.get("to")?.toString(),
    from: formData.get("from")?.toString(),
    fileUrl: formData.get("fileUrl")?.toString(),
    fileName: formData.get("fileName")?.toString(),
    threadId: formData.get("threadId")?.toString(),
  })

  if (!parsed.success) {
    return NextResponse.json(
      { error: "Invalid fax payload", issues: parsed.error.format() },
      { status: 400 }
    )
  }

  if (!parsed.data.fileUrl && !fileBuffer) {
    return NextResponse.json(
      { error: "Fax requires a fileUrl or uploaded file" },
      { status: 400 }
    )
  }

  const queueItem = addQueueItem({
    channel: "fax",
    payload: { ...parsed.data },
  })

  try {
    const response = await sendFax({
      to: parsed.data.to,
      from: parsed.data.from,
      fileUrl: parsed.data.fileUrl,
      fileBuffer,
      fileName: parsed.data.fileName,
    })
    updateQueueItem(queueItem.id, { status: "sent", error: undefined })
    const threadId =
      parsed.data.threadId ??
      createThread({
        channel: "fax",
        title: "Fax transmission",
        participants: [parsed.data.to],
        initialMessage: {
          direction: "outbound",
          body: "Fax sent",
          status: "sent",
        },
      }).id

    if (parsed.data.threadId) {
      addThreadMessage(parsed.data.threadId, {
        direction: "outbound",
        body: "Fax sent",
        status: "sent",
      })
    }

    audit("send_fax", "queue", queueItem.id, {
      to: parsed.data.to,
      response,
      threadId,
    })
    return NextResponse.json({ message: "Fax sent", threadId })
  } catch (error) {
    updateQueueItem(queueItem.id, {
      status: "failed",
      error: (error as Error).message,
    })
    audit("send_fax_failed", "queue", queueItem.id, {
      to: parsed.data.to,
      error: (error as Error).message,
    })
    return NextResponse.json(
      { error: "Fax send failed", detail: (error as Error).message },
      { status: 502 }
    )
  }
}
