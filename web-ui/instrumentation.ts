/**
 * Next.js Instrumentation
 * This runs before the server starts and can set up global configurations.
 */

export async function register() {
  // Allow self-signed certificates for internal Docker communication
  // This is necessary for server-side API calls to the backend with self-signed certs
  if (process.env.NODE_ENV === 'production') {
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
  }
}
