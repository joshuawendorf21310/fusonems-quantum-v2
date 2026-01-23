import { randomUUID } from "crypto"
import { CommsError } from "@/services/comms/CommsError"

const TELNYX_BASE = "https://api.telnyx.com/v2"

function getApiKey() {
  const key = process.env.TELNYX_API_KEY
  if (!key) {
    throw new CommsError("Missing TELNYX_API_KEY", { statusCode: 500 })
  }
  return key
}

async function telnyxFetch(path: string, options: RequestInit = {}) {
  const headers: HeadersInit = {
    Authorization: `Bearer ${getApiKey()}`,
    ...(options.headers ?? {}),
  }
  const response = await fetch(`${TELNYX_BASE}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const body = await response.text()
    throw new CommsError("Telnyx request failed", {
      statusCode: response.status,
      details: body,
    })
  }

  return response.json()
}

export type SendSmsOptions = {
  to: string
  from: string
  body: string
}

export type SendFaxOptions = {
  to: string
  from: string
  fileUrl?: string
  fileBuffer?: ArrayBuffer
  fileName?: string
}

export type InitiateCallOptions = {
  to: string
  from: string
  reason?: string
}

async function uploadFile(buffer: ArrayBuffer, fileName = "document.pdf") {
  const key = getApiKey()
  const formData = new FormData()
  formData.append("file", new Blob([buffer]), fileName)
  const response = await fetch(`${TELNYX_BASE}/files`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
    },
    body: formData,
  })
  if (!response.ok) {
    const body = await response.text()
    throw new CommsError("Telnyx file upload failed", {
      statusCode: response.status,
      details: body,
    })
  }
  const data = await response.json()
  return data?.data?.id ?? data?.data?.file_url
}

export async function sendSms(options: SendSmsOptions) {
  return telnyxFetch("/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      to: options.to,
      from: options.from,
      body: options.body,
    }),
  })
}

export async function sendFax(options: SendFaxOptions) {
  if (!options.fileUrl && !options.fileBuffer) {
    throw new CommsError("Missing fax file (url or buffer required)", { statusCode: 400 })
  }

  let mediaUrl = options.fileUrl
  if (!mediaUrl && options.fileBuffer) {
    mediaUrl = (await uploadFile(options.fileBuffer, options.fileName)) as string
  }
  if (!mediaUrl) {
    throw new CommsError("Unable to upload fax document", { statusCode: 500 })
  }

  return telnyxFetch("/faxes", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      to: options.to,
      from: options.from,
      media: [{ media_url: mediaUrl }],
    }),
  })
}

export async function initiateCall(options: InitiateCallOptions) {
  // Placeholder: log and return stub data to allow UI flows to proceed
  return {
    id: randomUUID(),
    to: options.to,
    from: options.from,
    reason: options.reason,
    status: "queued",
    provider: "telnyx",
  }
}
