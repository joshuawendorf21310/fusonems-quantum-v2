import { NextRequest, NextResponse } from 'next/server';
export async function GET(
  request: NextRequest,
  context: { params: Promise<{ unitId: string }> }
) {
  try {
    const { unitId } = await context.params
    const token = request.headers.get('Authorization')?.replace('Bearer ', '');
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const start_date = searchParams.get('start_date');
    const end_date = searchParams.get('end_date');

    const params_obj = new URLSearchParams();
    if (start_date) params_obj.append('start_date', start_date);
    if (end_date) params_obj.append('end_date', end_date);

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/fire-mdt/analytics/unit/${unitId}?${params_obj}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching unit performance:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
