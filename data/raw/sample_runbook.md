# Authentication Runbook

## Token Errors

ERR_AUTH_1042 occurs when a user's refresh token has been revoked.

The client should request a new authentication session instead of repeatedly retrying the revoked token.

## Retry Configuration

The maximum authentication retry count is controlled by `MAX_RETRY_COUNT`.