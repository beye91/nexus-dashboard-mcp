/**
 * HTTPS Wrapper for Next.js Standalone Server
 *
 * This script starts the Next.js standalone server on an internal port
 * and creates an HTTPS server that proxies requests to it.
 *
 * Environment Variables:
 *   SSL_ENABLED    - Enable HTTPS (default: true)
 *   SSL_CERTFILE   - Path to SSL certificate (default: /app/certs/server.crt)
 *   SSL_KEYFILE    - Path to SSL private key (default: /app/certs/server.key)
 *   PORT           - External HTTPS port (default: 7443)
 *   HOSTNAME       - Server hostname (default: 0.0.0.0)
 */

// IMPORTANT: Set this BEFORE requiring any modules to allow self-signed certs
// This is necessary for internal Docker communication with self-signed certificates
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

const { createServer: createHttpsServer } = require('https');
const { createServer: createHttpServer } = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const httpProxy = require('http-proxy');

const sslEnabled = process.env.SSL_ENABLED === 'true';
const hostname = process.env.HOSTNAME || '0.0.0.0';
const externalPort = parseInt(process.env.PORT || '7443', 10);
const internalPort = 3000; // Next.js standalone runs on this port internally

// Create proxy to forward requests to Next.js
const proxy = httpProxy.createProxyServer({
  target: `http://127.0.0.1:${internalPort}`,
  ws: true,
  xfwd: true,
});

proxy.on('error', (err, req, res) => {
  console.error('Proxy error:', err.message);
  if (res.writeHead) {
    res.writeHead(502, { 'Content-Type': 'text/plain' });
    res.end('Bad Gateway');
  }
});

// Start Next.js standalone server on internal port
console.log('Starting Next.js standalone server...');
const nextProcess = spawn('node', ['server.js'], {
  env: {
    ...process.env,
    PORT: internalPort.toString(),
    HOSTNAME: '127.0.0.1',
    // Ensure self-signed certs are accepted for internal API calls
    NODE_TLS_REJECT_UNAUTHORIZED: '0',
  },
  stdio: ['inherit', 'pipe', 'pipe'],
});

nextProcess.stdout.on('data', (data) => {
  process.stdout.write(`[Next.js] ${data}`);
});

nextProcess.stderr.on('data', (data) => {
  process.stderr.write(`[Next.js] ${data}`);
});

nextProcess.on('error', (err) => {
  console.error('Failed to start Next.js:', err);
  process.exit(1);
});

nextProcess.on('exit', (code) => {
  console.log(`Next.js process exited with code ${code}`);
  process.exit(code || 0);
});

// Wait for Next.js to be ready, then start HTTPS proxy
const waitForNextjs = () => {
  const checkServer = () => {
    const req = require('http').request({
      hostname: '127.0.0.1',
      port: internalPort,
      path: '/',
      method: 'HEAD',
      timeout: 1000,
    }, (res) => {
      startProxy();
    });

    req.on('error', () => {
      setTimeout(checkServer, 500);
    });

    req.end();
  };

  setTimeout(checkServer, 2000);
};

const startProxy = () => {
  let server;

  const requestHandler = (req, res) => {
    proxy.web(req, res);
  };

  if (sslEnabled) {
    const certFile = process.env.SSL_CERTFILE || '/app/certs/server.crt';
    const keyFile = process.env.SSL_KEYFILE || '/app/certs/server.key';

    if (!fs.existsSync(certFile)) {
      console.error(`SSL certificate not found: ${certFile}`);
      process.exit(1);
    }
    if (!fs.existsSync(keyFile)) {
      console.error(`SSL key not found: ${keyFile}`);
      process.exit(1);
    }

    const httpsOptions = {
      key: fs.readFileSync(keyFile),
      cert: fs.readFileSync(certFile),
    };

    server = createHttpsServer(httpsOptions, requestHandler);

    // Handle WebSocket upgrades for hot reload
    server.on('upgrade', (req, socket, head) => {
      proxy.ws(req, socket, head);
    });

    server.listen(externalPort, hostname, () => {
      console.log(`> HTTPS proxy ready on https://${hostname}:${externalPort}`);
      console.log(`  Proxying to http://127.0.0.1:${internalPort}`);
      console.log(`  SSL Certificate: ${certFile}`);
    });
  } else {
    server = createHttpServer(requestHandler);

    server.on('upgrade', (req, socket, head) => {
      proxy.ws(req, socket, head);
    });

    server.listen(externalPort, hostname, () => {
      console.log(`> HTTP proxy ready on http://${hostname}:${externalPort}`);
      console.log(`  Proxying to http://127.0.0.1:${internalPort}`);
    });
  }
};

// Handle graceful shutdown
process.on('SIGTERM', () => {
  console.log('Received SIGTERM, shutting down...');
  nextProcess.kill('SIGTERM');
});

process.on('SIGINT', () => {
  console.log('Received SIGINT, shutting down...');
  nextProcess.kill('SIGINT');
});

waitForNextjs();
