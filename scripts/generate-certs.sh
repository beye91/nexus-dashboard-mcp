#!/bin/sh
# Self-signed certificate generation script for Nexus Dashboard MCP
# This script generates certificates on first container startup
#
# Configuration via environment variables:
#   CERT_DIR        - Directory to store certificates (default: /app/certs)
#   CERT_DAYS       - Certificate validity in days (default: 365)
#   CERT_CN         - Certificate Common Name (default: nexus-dashboard)
#   CERT_ORG        - Certificate Organization (default: Nexus MCP)
#   CERT_SERVER_IP  - Server IP to include in SANs (optional)

set -e

# Install openssl if not present (Alpine Linux)
if ! command -v openssl > /dev/null 2>&1; then
    echo "Installing openssl..."
    apk add --no-cache openssl
fi

CERT_DIR="${CERT_DIR:-/app/certs}"
CERT_DAYS="${CERT_DAYS:-365}"
CERT_CN="${CERT_CN:-nexus-dashboard}"
CERT_ORG="${CERT_ORG:-Nexus MCP}"
CERT_SERVER_IP="${CERT_SERVER_IP:-}"

echo "=== Nexus Dashboard MCP Certificate Generator ==="
echo "Certificate directory: $CERT_DIR"
echo "Certificate validity: $CERT_DAYS days"
echo "Common Name: $CERT_CN"

# Create certificate directory
mkdir -p "$CERT_DIR"

# Check if certificates already exist
if [ -f "$CERT_DIR/server.crt" ] && [ -f "$CERT_DIR/server.key" ]; then
    echo "Certificates already exist, skipping generation."
    echo "To regenerate certificates:"
    echo "  1. Stop containers: docker compose down"
    echo "  2. Remove volume: docker volume rm nexus-mcp-certs"
    echo "  3. Start containers: docker compose up"
    exit 0
fi

# Build Subject Alternative Names (SANs) dynamically
SAN_LIST="DNS:localhost,DNS:web-api,DNS:web-ui,IP:127.0.0.1"

if [ -n "$CERT_SERVER_IP" ]; then
    SAN_LIST="${SAN_LIST},IP:${CERT_SERVER_IP}"
    echo "Including server IP in certificate SANs: $CERT_SERVER_IP"
fi

echo "Generating self-signed certificate..."
echo "SANs: $SAN_LIST"

# Generate self-signed certificate with RSA 4096-bit key
openssl req -x509 -newkey rsa:4096 -nodes \
    -out "$CERT_DIR/server.crt" \
    -keyout "$CERT_DIR/server.key" \
    -days "$CERT_DAYS" \
    -subj "/CN=${CERT_CN}/O=${CERT_ORG}/C=US" \
    -addext "subjectAltName=${SAN_LIST}" \
    -addext "keyUsage=digitalSignature,keyEncipherment" \
    -addext "extendedKeyUsage=serverAuth"

# Set permissions - readable by all users in container (self-signed cert for internal use)
chmod 644 "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/server.crt"

echo ""
echo "=== Certificate generated successfully ==="
echo "Certificate: $CERT_DIR/server.crt"
echo "Private key: $CERT_DIR/server.key"
echo ""

# Display certificate info
echo "Certificate details:"
openssl x509 -in "$CERT_DIR/server.crt" -noout -subject -dates -ext subjectAltName 2>/dev/null || true

echo ""
echo "Certificate generation complete!"
