# Session Management and Token Revocation

This module implements a secure server-side session store for JWT token revocation in the FusonEMS Quantum platform.

## Overview

JWT tokens are stateless by design, which makes them difficult to revoke. This implementation adds a database-backed session store that enables secure token revocation while maintaining the benefits of JWT authentication.

## Features

- **Server-side session tracking**: Each JWT is tied to a database session record
- **Session revocation**: Individual sessions can be revoked (e.g., on logout)
- **User-wide revocation**: All sessions for a user can be revoked at once (e.g., password reset, admin ban)
- **Session expiration**: Expired sessions are automatically rejected
- **Audit trail**: All session lifecycle events are logged for security auditing
- **OIDC support**: Session management works with both local and OIDC authentication

## Database Schema

The `auth_sessions` table stores session metadata:

```python
- id: Primary key
- org_id: Organization foreign key
- user_id: User foreign key
- jwt_jti: JWT ID claim (unique identifier for the token)
- created_at: Session creation timestamp
- last_seen_at: Last authentication timestamp (updated on each request)
- expires_at: Session expiration timestamp
- revoked_at: Revocation timestamp (NULL if active)
- revoked_reason: Reason for revocation (e.g., "logout", "password_reset", "admin_ban")
- csrf_secret: CSRF token for this session
- ip_address: IP address from session creation
- user_agent: User agent string from session creation
```

## JWT Claims

JWTs now include the following session-related claims:

```json
{
  "sub": "user_id",
  "org": "org_id",
  "jti": "unique_jwt_id",
  "iat": "issued_at_timestamp",
  "exp": "expiration_timestamp"
}
```

## Authentication Flow

### Registration / Login

1. User provides credentials
2. System validates credentials
3. System generates unique JWT ID (`jti`)
4. System creates session record in database
5. System generates JWT with `jti` claim
6. JWT and CSRF token are set as cookies
7. Audit event is logged

### Request Authentication

1. User makes authenticated request with JWT
2. System decodes JWT and extracts `jti`
3. System queries database for session by `jti`
4. System checks if session is:
   - Present (exists in database)
   - Not revoked (`revoked_at` is NULL)
   - Not expired (`expires_at` > current time)
5. If valid, request proceeds
6. System updates `last_seen_at` timestamp
7. If invalid, returns 401 Unauthorized

### Logout

1. User initiates logout
2. System extracts `jti` from JWT
3. System marks session as revoked with reason "logout"
4. System clears auth cookies
5. Audit event is logged

## Admin Operations

### Revoke All User Sessions

Administrators can revoke all sessions for a user:

```bash
POST /api/auth/admin/revoke-user-sessions
Content-Type: application/json
Authorization: Bearer <admin_jwt>

{
  "user_id": 123,
  "reason": "password_reset"
}
```

Common use cases:
- Password reset completion
- Account compromise
- Admin-initiated account suspension
- Security policy enforcement

Response:
```json
{
  "status": "ok",
  "revoked_count": 5
}
```

## Session Cleanup

Old expired sessions can be cleaned up periodically:

```python
from services.auth.session_service import cleanup_expired_sessions

# Delete sessions expired more than 30 days ago
count = cleanup_expired_sessions(db, older_than_days=30)
```

This should be run as a scheduled background task.

## Security Considerations

### Session Validation
- Every authenticated request validates the session in real-time
- Revoked sessions are immediately rejected
- Expired sessions are automatically rejected

### Audit Trail
All session lifecycle events are logged:
- `auth.session.created` - Session creation (login/register)
- `auth.session.revoked` - Session revocation (logout)
- `auth.oidc.login` - OIDC login with session
- `auth.oidc.session.revoked` - OIDC logout with session revocation
- `auth.admin.sessions.revoked` - Admin-initiated session revocation

### CSRF Protection
Each session has a unique `csrf_secret` that can be used for CSRF token validation.

### Session Metadata
IP address and user agent are recorded to help detect suspicious activity.

## API Examples

### Check Current Session

```bash
GET /api/auth/me
Authorization: Bearer <jwt>
```

Returns user information if session is valid, 401 if revoked/expired.

### Logout (Revoke Current Session)

```bash
POST /api/auth/logout
Authorization: Bearer <jwt>
```

Revokes the current session and clears cookies.

### Admin: Revoke All User Sessions

```bash
POST /api/auth/admin/revoke-user-sessions
Authorization: Bearer <admin_jwt>
Content-Type: application/json

{
  "user_id": 456,
  "reason": "account_suspended"
}
```

## Testing

Comprehensive tests are available in `tests/test_session_management.py`:

```bash
pytest tests/test_session_management.py -v
```

Tests cover:
- Session creation and retrieval
- Session revocation
- User-wide session revocation
- Login/logout flow with sessions
- Revoked session rejection
- Expired session rejection
- Session cleanup

## Migration Notes

The `auth_sessions` table is automatically created on application startup via SQLAlchemy's `Base.metadata.create_all()`.

For existing deployments:
1. Deploy the updated code
2. Restart the application
3. The `auth_sessions` table will be created automatically
4. Existing JWTs without `jti` will continue to work but won't have session tracking
5. New logins will create sessions with full tracking
6. Old JWTs will naturally expire based on their `exp` claim

## Performance Considerations

- Database query on every authenticated request (session lookup by `jti`)
- Consider adding database indexes on frequently queried columns (already included)
- Consider implementing session caching (Redis) for high-traffic deployments
- `last_seen_at` updates can be made async or batched if needed

## Future Enhancements

Potential improvements:
- Redis caching for session lookups
- Session management UI (view active sessions, remote logout)
- Geographic/IP-based anomaly detection
- Device fingerprinting integration
- Suspicious activity alerts
- Session concurrency limits
