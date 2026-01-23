import { ServerClient } from "postmark"
import { CommsError } from "@/services/comms/CommsError"

const token = process.env.POSTMARK_SERVER_TOKEN
const defaultSender = process.env.POSTMARK_SOURCE_EMAIL ?? "no-reply@fusionems.app"

function getClient() {
  if (!token) {
    throw new CommsError("Missing POSTMARK_SERVER_TOKEN", { statusCode: 500 })
  }
  return new ServerClient(token)
}

export type SendEmailOptions = {
  to: string
  subject: string
  html: string
  text?: string
  tag?: string
  metadata?: Record<string, string>
}

export async function sendEmail(options: SendEmailOptions) {
  try {
    const client = getClient()
    const payload: Parameters<ServerClient["sendEmail"]>[0] = {
      From: defaultSender,
      To: options.to,
      Subject: options.subject,
      HtmlBody: options.html,
      TextBody: options.text,
      Tag: options.tag,
      Metadata: options.metadata,
    }
    return await client.sendEmail(payload)
  } catch (error) {
    throw new CommsError("Postmark send failed", {
      statusCode: 502,
      details: error,
    })
  }
}
