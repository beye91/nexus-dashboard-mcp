#!/bin/bash
# Start FastAPI Web API with HTTPS for external access and HTTP for internal container communication

echo "Starting FastAPI Web API..."

SSL_ENABLED="${SSL_ENABLED:-true}"
SSL_CERTFILE="${SSL_CERTFILE:-/app/certs/server.crt}"
SSL_KEYFILE="${SSL_KEYFILE:-/app/certs/server.key}"
WEB_API_PORT="${WEB_API_PORT:-8444}"
INTERNAL_HTTP_PORT="${INTERNAL_HTTP_PORT:-8000}"

if [ "$SSL_ENABLED" = "true" ]; then
    if [ -f "$SSL_CERTFILE" ] && [ -f "$SSL_KEYFILE" ]; then
        echo "Starting with HTTPS on port $WEB_API_PORT and HTTP on port $INTERNAL_HTTP_PORT"
        # Start HTTP server in background for internal container communication
        python -m uvicorn src.api.web_api:app --host 0.0.0.0 --port "$INTERNAL_HTTP_PORT" &
        # Start HTTPS server in foreground for external access
        exec python -m uvicorn src.api.web_api:app --host 0.0.0.0 --port "$WEB_API_PORT" --ssl-certfile "$SSL_CERTFILE" --ssl-keyfile "$SSL_KEYFILE"
    else
        echo "ERROR: SSL certificates not found"
        echo "  Certificate: $SSL_CERTFILE (exists: $(test -f $SSL_CERTFILE && echo yes || echo no))"
        echo "  Key: $SSL_KEYFILE (exists: $(test -f $SSL_KEYFILE && echo yes || echo no))"
        exit 1
    fi
else
    echo "Starting with HTTP on port $WEB_API_PORT"
    exec python -m uvicorn src.api.web_api:app --host 0.0.0.0 --port "$WEB_API_PORT"
fi
