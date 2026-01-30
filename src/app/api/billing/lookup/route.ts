import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const {
      accountNumber,
      zipCode,
      authorizedRep,
      patientDob,
      patientLastName,
      representativeName,
      relationship,
    } = body

    if (!accountNumber || !zipCode) {
      return NextResponse.json(
        { error: 'Account number and ZIP code are required' },
        { status: 400 }
      )
    }

    if (authorizedRep && (!patientDob || !patientLastName || !representativeName || !relationship)) {
      return NextResponse.json(
        { error: 'Authorized representative: patient DOB, patient last name, your name, and relationship are required' },
        { status: 400 }
      )
    }

    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const payload: Record<string, string | boolean> = {
      account_number: accountNumber,
      zip_code: zipCode,
    }
    if (authorizedRep) {
      payload.authorized_rep = true
      payload.patient_dob = patientDob
      payload.patient_last_name = patientLastName
      payload.representative_name = representativeName
      payload.relationship = relationship
    }

    const response = await fetch(`${backendUrl}/api/v1/billing/lookup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Account not found' },
        { status: 404 }
      )
    }

    const data = await response.json()

    return NextResponse.json({
      success: true,
      account: {
        accountNumber: data.account_number,
        balance: data.balance,
        patientName: data.patient_name,
        serviceDate: data.service_date,
      }
    })

  } catch (error) {
    console.error('Billing lookup error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
