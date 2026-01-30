import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const params = await context.params
  try {
    const token = request.headers.get('Authorization')?.replace('Bearer ', '');
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/fire/hydrants/${params.id}/flow-test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      return NextResponse.json({ error: 'Failed to record flow test' }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error('Error recording flow test:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
