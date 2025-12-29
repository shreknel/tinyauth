# OIDC Validation Setup

This directory contains a docker-compose setup for testing tinyauth's OIDC provider functionality with a minimal test client.

## Setup

1. **Build the OIDC test client image:**
   ```bash
   docker build -t oidc-whoami-test:latest .
   ```

2. **Start the services:**
   ```bash
   docker-compose up
   ```

## Services

### tinyauth
- **URL:** http://auth.example.test:3000
- **Credentials:** `user` / `pass`
- **OIDC Discovery:** http://auth.example.test:3000/api/.well-known/openid-configuration
- **OIDC Client ID:** `testclient`
- **OIDC Client Secret:** `test-secret-123`

**Note:** The domain `auth.example.test` is used to satisfy cookie domain validation requirements (needs at least 3 domain parts and not in public suffix list). The docker-compose file includes `extra_hosts` to map this domain to 127.0.0.1. If accessing from outside Docker, add `127.0.0.1 auth.example.test` to your `/etc/hosts` file (or `C:\Windows\System32\drivers\etc\hosts` on Windows).

### oidc-whoami
- **Callback URL:** http://localhost:8765/callback
- **Purpose:** Minimal OIDC test client that validates the OIDC flow

## Testing

1. Start the services with `docker-compose up`
2. The oidc-whoami container will attempt to open a browser (may fail in Docker)
3. If the browser doesn't open, manually navigate to the authorization URL printed in the logs
4. Login with `user` / `pass`
5. After successful authentication, the test client will display the ID token claims

## Configuration

The tinyauth configuration is in `config.yaml`:
- OIDC is enabled
- Single user: `user` with password `pass`
- OIDC client `testclient` is configured with redirect URI `http://localhost:8765/callback`

## Notes

- The oidc-whoami container uses `network_mode: "host"` to allow the callback to work properly
- The redirect URI must match exactly what's configured in tinyauth
- Data is persisted in the `./data` directory

