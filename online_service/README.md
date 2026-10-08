# Online service foundation

This is a read-only scaffold, not a deployed service. No accounts, save uploads, analytics, shared economy, or multiplayer are implemented. The desktop game remains fully offline by default, and local saves are authoritative.

## API v1

- GET /api/v1/health → {"api_version":1,"status":"ok","service":"starstruck-atelier"}
- GET /api/v1/capabilities → {"api_version":1,"features":[],"local_saves_authoritative":true}
- Unknown routes return JSON 404; write methods are unsupported.

## Local server

From the repository root: python -m online_service.server. It binds to 127.0.0.1:8080 by default. HOST and PORT configure the process.

## VPS preparation

Build/run with docker compose -f online_service/compose.yaml up --build -d when deployment is explicitly requested. The Compose service exposes only the VPS loopback interface. Configure the existing HTTPS reverse proxy for atelier-api.reqlabs.co.uk to forward to 127.0.0.1:8080. Add DNS and a valid TLS certificate for that hostname before enabling clients. Use the reverse proxy for request limits and access policy. No DNS, certificates, containers or VPS settings have been changed by adding this scaffold.

## Optional desktop connection

ATELIER_ONLINE_ENABLED=true opts into a single background health request at startup. ATELIER_API_URL overrides the default https://atelier-api.reqlabs.co.uk origin. Leave the flag unset while there is no deployed API. Invalid configuration disables the client. Requests have a three-second timeout, bounded response size, no automatic retries, and return results through a queue polled by the UI. Closing the game never waits for a request. No game state is included in requests.

Future features should introduce explicit versioned contracts and tests behind this adapter. Save synchronization needs a separately agreed identity and conflict policy; none is assumed here.
