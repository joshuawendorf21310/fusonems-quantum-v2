import { NextRequest, NextResponse } from 'next/server';
export async function GET(
  request: NextRequest,
  context: { params: Promise<{ exportId: string }> }
) {
  const params = await context.params
  try {
    const token = request.headers.get('Authorization')?.replace('Bearer ', '');
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/fire-mdt/exports/nfirs/${params.exportId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const contentType = response.headers.get('content-type');
    
    if (contentType?.includes('application/json')) {
      const data = await response.json();
      return NextResponse.json(data);
    } else {
      const blob = await response.blob();
      const headers = new Headers();
      headers.set('Content-Type', contentType || 'application/octet-stream');
      const disposition = response.headers.get('content-disposition');
      if (disposition) headers.set('Content-Disposition', disposition);
      
      return new NextResponse(blob, {
        status: 200,
        headers,
      });
    }
  } catch (error) {
    console.error('Error downloading NFIRS export:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
