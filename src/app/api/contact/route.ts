import { NextRequest, NextResponse } from "next/server"

// Simple validation
function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function sanitizeString(str: string, maxLength: number = 1000): string {
  return String(str || '').trim().slice(0, maxLength)
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    
    // Validate and sanitize input
    const name = sanitizeString(body.name, 100)
    const email = sanitizeString(body.email, 254)
    const organization = sanitizeString(body.organization, 200)
    const subject = sanitizeString(body.subject, 200)
    const message = sanitizeString(body.message, 5000)
    
    // Validation
    if (!name || name.length < 2) {
      return NextResponse.json({ ok: false, error: "Name is required (min 2 characters)" }, { status: 400 })
    }
    
    if (!email || !validateEmail(email)) {
      return NextResponse.json({ ok: false, error: "Valid email is required" }, { status: 400 })
    }
    
    if (!message || message.length < 10) {
      return NextResponse.json({ ok: false, error: "Message is required (min 10 characters)" }, { status: 400 })
    }
    
    // Log submission for now (will be stored/emailed)
    const timestamp = new Date().toISOString()
    console.log(`[CONTACT FORM] ${timestamp}`)
    console.log(`  From: ${name} <${email}>`)
    console.log(`  Organization: ${organization || 'Not provided'}`)
    console.log(`  Subject: ${subject || 'No subject'}`)
    console.log(`  Message: ${message.slice(0, 100)}${message.length > 100 ? '...' : ''}`)
    
    // Forward to backend API if configured
    const backendUrl = process.env.NEXT_PUBLIC_API_URL
    if (backendUrl) {
      try {
        const response = await fetch(`${backendUrl}/api/contact`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, organization, subject, message, timestamp }),
        })
        
        if (!response.ok) {
          console.error('[CONTACT FORM] Backend API error:', response.status)
          // Continue anyway - we logged the submission
        }
      } catch (backendError) {
        console.error('[CONTACT FORM] Failed to forward to backend:', backendError)
        // Continue anyway - we logged the submission
      }
    }
    
    return NextResponse.json({ 
      ok: true, 
      message: "Thank you for your message. We'll get back to you soon." 
    })
    
  } catch (error) {
    console.error('[CONTACT FORM] Error processing submission:', error)
    return NextResponse.json(
      { ok: false, error: "Failed to process your message. Please try again." }, 
      { status: 500 }
    )
  }
}
