import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_API_URL || 'http://web-api:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    console.log('[/api/auth/login] Received login request for:', body.username);

    // Forward the request to the backend
    const backendResponse = await fetch(`${BACKEND_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await backendResponse.json();

    console.log('[/api/auth/login] Backend response status:', backendResponse.status);
    console.log('[/api/auth/login] Token present in response:', !!data.token);

    // Create the response
    const response = NextResponse.json(data, { status: backendResponse.status });

    // If login successful, set the session cookie ourselves
    // The backend returns the token in the response body, so we can set it here
    // This ensures the cookie is set correctly for the browser's domain
    if (backendResponse.ok && data.token) {
      console.log('[/api/auth/login] Setting session cookie, token length:', data.token.length);
      response.cookies.set({
        name: 'nexus_session',
        value: data.token,
        httpOnly: true,
        secure: false, // Allow non-HTTPS for development
        sameSite: 'lax',
        path: '/',
        maxAge: 24 * 60 * 60, // 24 hours
      });
      console.log('[/api/auth/login] Cookie set successfully');
    }

    return response;
  } catch (error) {
    console.error('Login proxy error:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}
