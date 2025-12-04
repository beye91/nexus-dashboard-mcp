import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_API_URL || 'http://web-api:8000';

export async function GET(request: NextRequest) {
  try {
    // Get the session cookie to forward
    const sessionCookie = request.cookies.get('nexus_session');

    console.log('[/api/auth/me] Session cookie present:', !!sessionCookie);
    if (sessionCookie) {
      console.log('[/api/auth/me] Cookie value (first 20 chars):', sessionCookie.value.substring(0, 20) + '...');
    }

    // Forward the request to the backend
    const backendResponse = await fetch(`${BACKEND_URL}/api/auth/me`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(sessionCookie && { Cookie: `nexus_session=${sessionCookie.value}` }),
      },
    });

    const data = await backendResponse.json();

    console.log('[/api/auth/me] Backend response:', JSON.stringify(data));

    // Create the response
    return NextResponse.json(data, { status: backendResponse.status });
  } catch (error) {
    console.error('Auth check proxy error:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}
