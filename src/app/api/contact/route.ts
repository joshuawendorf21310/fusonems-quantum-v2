import { NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  const { name, email, organization, subject, message } = await req.json()

  // Send email to support@fusionemsquantum.com (replace with real email integration in production)
  // For now, just log and simulate success
  console.log("Contact form submission:", { name, email, organization, subject, message })

  // TODO: Integrate with real email service (e.g., nodemailer, SendGrid, etc.)
  // Example: await sendMail({ to: 'support@fusionemsquantum.com', ... })

  return NextResponse.json({ ok: true })
}
