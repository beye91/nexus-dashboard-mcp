import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_API_URL || 'http://web-api:8000';

export async function POST(request: NextRequest) {
  try {
    // Get the session cookie to forward
    const sessionCookie = request.cookies.get('nexus_session');

    // Forward the request to the backend
    const backendResponse = await fetch(`${BACKEND_URL}/api/auth/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(sessionCookie && { Cookie: `nexus_session=${sessionCookie.value}` }),
      },
    });

    const data = await backendResponse.json();

    // Create the response
    const response = NextResponse.json(data, { status: backendResponse.status });

    // Forward Set-Cookie headers from backend (cookie deletion)
    const setCookieHeader = backendResponse.headers.get('set-cookie');
    if (setCookieHeader) {
      response.headers.set('Set-Cookie', setCookieHeader);
    }

    return response;
  } catch (error) {
    console.error('Logout proxy error:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}
