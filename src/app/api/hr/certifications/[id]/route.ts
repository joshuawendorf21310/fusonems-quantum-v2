import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const params = await context.params
  try {
    const authHeader = request.headers.get('authorization');
    if (!authHeader) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const org_id = searchParams.get('org_id');

    if (!org_id) {
      return NextResponse.json({ error: 'org_id is required' }, { status: 400 });
    }

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/hr/certifications/${params.id}?org_id=${org_id}`,
      { headers: { Authorization: authHeader } }
    );

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching certification:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function PUT(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const params = await context.params
  try {
    const authHeader = request.headers.get('authorization');
    if (!authHeader) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();

    if (!body.org_id) {
      return NextResponse.json({ error: 'org_id is required' }, { status: 400 });
    }

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/hr/certifications/${params.id}`, {
      method: 'PUT',
      headers: {
        Authorization: authHeader,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error updating certification:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const params = await context.params
  try {
    const authHeader = request.headers.get('authorization');
    if (!authHeader) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const org_id = searchParams.get('org_id');

    if (!org_id) {
      return NextResponse.json({ error: 'org_id is required' }, { status: 400 });
    }

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/hr/certifications/${params.id}?org_id=${org_id}`,
      {
        method: 'DELETE',
        headers: { Authorization: authHeader },
      }
    );

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    return NextResponse.json({ success: true }, { status: 204 });
  } catch (error) {
    console.error('Error deleting certification:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
