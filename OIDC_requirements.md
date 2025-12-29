# OIDC Provider Requirements and Compatibility

This document outlines the OIDC provider requirements and compatibility analysis for integrating tinyauth as an OIDC provider with various applications.

## Compatibility Analysis: Immich OIDC Requirements

### ✅ Fully Compatible Requirements

#### 1. ISSUER_URL
- **Immich expects:** Base URL of the OIDC provider
- **Our implementation:** Discovery endpoint at `/.well-known/openid-configuration` returns the issuer
- **Match:** ✅ Yes - Immich can use `https://auth.example.com` as the issuer URL

#### 2. CLIENT_ID
- **Immich expects:** Client identifier
- **Our implementation:** Supports client IDs configured in the config file
- **Match:** ✅ Yes - Configure a client with ID `immich` (or any name)

#### 3. CLIENT_SECRET
- **Immich expects:** Client secret
- **Our implementation:** Supports `clientSecret` or `clientSecretFile` in config
- **Match:** ✅ Yes - Standard client secret authentication

#### 4. SCOPE
- **Immich expects:** Scopes like `"openid profile email"`
- **Our implementation:** Supports these scopes (they're in our defaults)
- **Match:** ✅ Yes - Standard OIDC scopes supported

#### 5. Redirect URI
- **Immich expects:** `https://immich.example.com/auth/login` (or similar)
- **Our implementation:** Validates `redirect_uri` against configured `redirectUris` and redirects back with authorization code
- **Match:** ✅ Yes - As long as the redirect URI is in the client's `redirectUris` list

### Flow Compatibility

The authorization code flow matches perfectly:

1. **User accesses Immich** → Immich redirects to:
   ```
   https://auth.example.com/api/oidc/authorize?
     client_id=immich&
     redirect_uri=https://immich.example.com/auth/login&
     response_type=code&
     scope=openid profile email&
     state=...
   ```

2. **User authenticates with tinyauth** → Tinyauth redirects back to:
   ```
   https://immich.example.com/auth/login?code=...&state=...
   ```

3. **Immich exchanges code for tokens** → POST to `/api/oidc/token`

### Configuration Example for Immich

```yaml
oidc:
  enabled: true
  issuer: "https://auth.example.com"
  clients:
    immich:
      clientSecret: "your_secret_here"
      clientName: "Immich"
      redirectUris:
        - "https://immich.example.com/auth/login"
      scopes:
        - "openid"
        - "profile"
        - "email"
```

### Potential Considerations

1. **Discovery Endpoint Path:** Our discovery endpoint is at `/api/.well-known/openid-configuration` (under `/api`). Make sure Immich can access it at this path, or adjust routing if needed.

2. **Authorization Endpoint Path:** Our authorization endpoint is `/api/oidc/authorize`. The discovery document should point to the correct path.

3. **Token Endpoint:** We support both `client_secret_basic` (HTTP Basic Auth) and `client_secret_post` (form parameters), which should work with Immich.

### Verdict

✅ **Fully Compatible** - The redirect URI `https://immich.example.com/auth/login` will work perfectly as long as it's included in the client's `redirectUris` configuration. The flow matches the standard OIDC authorization code flow that Immich expects.

## Supporting Multiple Websites with the Same Client

Tinyauth supports configuring multiple redirect URIs for a single OIDC client, allowing you to use the same client credentials across multiple applications or websites. This is useful when:

- You have multiple instances of the same application (e.g., staging and production)
- You have multiple applications that should share the same authentication context
- You want to simplify client management by using one client for multiple services

### Configuration

Simply add multiple redirect URIs to the `redirectUris` array in your client configuration:

```yaml
oidc:
  enabled: true
  clients:
    shared-client:
      clientSecret: "your_shared_secret_here"
      clientName: "Shared Client for Multiple Apps"
      redirectUris:
        - "https://app1.example.com/auth/callback"
        - "https://app2.example.com/auth/callback"
        - "https://app3.example.com/auth/callback"
        - "http://localhost:3000/auth/callback"  # For local development
      scopes:
        - "openid"
        - "profile"
        - "email"
```

### How It Works

1. **Client Registration:** All redirect URIs are stored in the database for the client
2. **Authorization Request:** When an application initiates an OIDC flow, it includes its specific `redirect_uri` in the authorization request
3. **Validation:** Tinyauth validates that the provided `redirect_uri` matches one of the configured URIs for that client
4. **Redirect:** After authentication, tinyauth redirects back to the exact `redirect_uri` provided in the request

### Use Cases

#### Multiple Environments
```yaml
clients:
  myapp:
    clientSecret: "secret123"
    redirectUris:
      - "https://myapp.example.com/auth/callback"      # Production
      - "https://staging.myapp.example.com/auth/callback"  # Staging
      - "http://localhost:3000/auth/callback"          # Local dev
```

#### Multiple Applications
```yaml
clients:
  internal-apps:
    clientSecret: "shared_secret"
    redirectUris:
      - "https://app1.internal.example.com/callback"
      - "https://app2.internal.example.com/callback"
      - "https://app3.internal.example.com/callback"
```

#### Different Protocols/Ports
```yaml
clients:
  flexible-client:
    clientSecret: "secret"
    redirectUris:
      - "https://app.example.com/auth/callback"
      - "http://app.example.com:8080/auth/callback"
      - "https://app.example.com:8443/auth/callback"
```

### Security Considerations

1. **Exact Match Required:** The redirect URI in the authorization request must exactly match one of the configured URIs (including protocol, domain, port, and path)

2. **HTTPS Recommended:** For production, always use HTTPS redirect URIs to prevent token interception

3. **Domain Validation:** Consider using a consistent domain pattern for related applications to make management easier

4. **Secret Management:** Since multiple applications share the same client secret, ensure it's stored securely and rotated regularly

### Best Practices

1. **Use Descriptive Client Names:** Name your client to reflect its purpose (e.g., `internal-apps`, `production-services`)

2. **Group Related Applications:** Use one client for applications that should share the same authentication context

3. **Separate Clients for Different Security Levels:** Use different clients for public-facing vs internal applications

4. **Document Your Configuration:** Keep track of which applications use which client and redirect URIs

### Example: Complete Multi-Application Setup

```yaml
oidc:
  enabled: true
  issuer: "https://auth.example.com"
  accessTokenExpiry: 3600
  idTokenExpiry: 3600
  clients:
    # Production applications
    production:
      clientSecret: "prod_secret_xyz"
      clientName: "Production Applications"
      redirectUris:
        - "https://immich.example.com/auth/login"
        - "https://nextcloud.example.com/apps/oidc_login/oidc"
        - "https://grafana.example.com/login/generic_oauth"
      scopes:
        - "openid"
        - "profile"
        - "email"
    
    # Staging/Development
    staging:
      clientSecret: "staging_secret_abc"
      clientName: "Staging Environment"
      redirectUris:
        - "https://staging.example.com/auth/callback"
        - "http://localhost:3000/auth/callback"
        - "http://localhost:8080/auth/callback"
      scopes:
        - "openid"
        - "profile"
        - "email"
    
    # Internal tools
    internal:
      clientSecret: "internal_secret_def"
      clientName: "Internal Tools"
      redirectUris:
        - "https://internal.example.com/callback"
        - "https://admin.example.com/oidc/callback"
      scopes:
        - "openid"
        - "profile"
        - "email"
```

This configuration allows you to:
- Use the same client credentials across multiple production applications
- Maintain separate staging/development environments
- Keep internal tools isolated with their own client
- Easily add new applications by adding their redirect URI to the appropriate client

