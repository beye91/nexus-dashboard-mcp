# Multi-stage build for Next.js Web UI with HTTPS Support
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the application with standalone output
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

# Install openssl for certificate debugging and verification
RUN apk add --no-cache openssl

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application from standalone output
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Copy http-proxy dependency for HTTPS wrapper
COPY --from=deps /app/node_modules/http-proxy ./node_modules/http-proxy
COPY --from=deps /app/node_modules/eventemitter3 ./node_modules/eventemitter3
COPY --from=deps /app/node_modules/requires-port ./node_modules/requires-port
COPY --from=deps /app/node_modules/follow-redirects ./node_modules/follow-redirects

# Copy custom HTTPS server wrapper
COPY --chown=nextjs:nodejs https-server.js ./

USER nextjs

# Default to HTTPS port
EXPOSE 7443

# Environment defaults
ENV PORT=7443
ENV HOSTNAME="0.0.0.0"
ENV SSL_ENABLED=true
ENV SSL_CERTFILE=/app/certs/server.crt
ENV SSL_KEYFILE=/app/certs/server.key

# BACKEND_API_URL for API proxying (HTTPS internal Docker network)
ENV BACKEND_API_URL=https://web-api:8443

# Allow self-signed certificates for internal communication
ENV NODE_TLS_REJECT_UNAUTHORIZED=0

# Use custom HTTPS server
CMD ["node", "https-server.js"]
