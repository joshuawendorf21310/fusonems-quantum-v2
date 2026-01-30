import { NextRequest, NextResponse } from "next/server"

// Dummy handler for Ollama AI compliance agent integration
export async function POST(req: NextRequest) {
  const { prompt } = await req.json()
  // Simulate AI response for compliance Q&A
  const answer = `Ollama AI Compliance Agent: This is a simulated response to your query: "${prompt}". For official compliance documentation, see the Compliance Center or contact compliance@fusionems.com.`
  return NextResponse.json({ answer })
}
