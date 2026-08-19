# Production Platform Operations Runbook

This runbook describes common operational procedures for the production platform. It covers authentication incidents, database availability, application health, and deployment recovery. Engineers should use the relevant section during incident investigation and record any unusual behavior in the incident timeline.

# Authentication

Authentication services issue access and refresh tokens to users after successful login. Access tokens are intentionally short-lived, while refresh tokens allow clients to obtain new access tokens without forcing the user to authenticate again.

## Token Errors

`ERR_AUTH_1042` occurs when a user's refresh token has been revoked. Revocation may happen after a password reset, an administrator action, suspicious account activity, or an explicit logout from all devices.

The client should request a new authentication session instead of repeatedly retrying the revoked token. Retrying the same refresh token will not recover the session because the token has already been invalidated by the authentication service.

Repeated failures should be checked in the authentication logs. Engineers should confirm the user identifier, token creation time, revocation time, and the service instance that rejected the request before escalating the incident.

### Expired Access Tokens

An expired access token normally produces an HTTP `401 Unauthorized` response. This is expected behavior and does not necessarily indicate a platform incident.

The client should attempt the configured refresh-token flow. If the refresh token is still valid, the authentication service will issue a replacement access token and normal requests can continue.

## Retry Configuration

The maximum authentication retry count is controlled by `MAX_RETRY_COUNT`. Production clients should use bounded retries with exponential backoff instead of retrying failed authentication requests indefinitely.

A high retry count can increase load on the authentication service during an outage. A very low retry count, however, may cause temporary network failures to appear as permanent authentication failures to users.

The default production value is:

```text
MAX_RETRY_COUNT=3
```

Changes to this value should be tested before deployment. Engineers should inspect authentication latency, error rates, and request volume after modifying retry behavior.

# Database Operations

The production application uses PostgreSQL as its primary transactional database. Database incidents can affect authentication, account management, payments, and other services even when the application processes themselves remain healthy.

## Connection Pool Exhaustion

Connection pool exhaustion occurs when the application attempts to open more database connections than the configured pool allows. Symptoms may include increased request latency, timeout errors, and messages indicating that no connections are available.

Before increasing the pool size, engineers should determine why connections are being held. Common causes include long-running queries, transactions that are not committed or rolled back, application code that fails to release connections, or sudden increases in request traffic.

Increasing the pool limit without identifying the cause may move the failure from the application to PostgreSQL itself. Too many concurrent connections can increase memory consumption and reduce database performance.

During investigation, check the number of active and idle connections, query duration, transaction age, application instance count, and recent deployment activity. Compare these values with normal production baselines.

If a specific application instance is leaking connections, remove that instance from service and confirm that the pool begins to recover. Restarting every application instance simultaneously should be avoided unless the incident requires it because doing so can generate a sudden wave of new database connections.

## Slow Queries

A slow query should first be identified using database monitoring or query logs. Record the query duration, frequency, affected endpoint, and execution plan when available.

Do not immediately add an index simply because a query is slow. The problem may instead be caused by lock contention, unexpectedly large result sets, poor join behavior, outdated statistics, or another workload consuming database resources.

# Application Health

Application instances expose health endpoints that are used by the load balancer and deployment platform.

## Readiness Checks

The readiness endpoint determines whether an application instance should receive production traffic. An instance may be running but still report itself as not ready while required dependencies are unavailable.

A failed readiness check should not automatically be treated as an application crash. Engineers should inspect dependency health, database connectivity, configuration loading, and startup migrations.

### Liveness Checks

Liveness checks answer a different question. They determine whether the process is still functioning and whether restarting the instance may be appropriate.

Readiness and liveness signals should not be treated as interchangeable. A temporary database outage may make an application unready without requiring the process to be restarted.

# Deployment Recovery

Deployments should be monitored for changes in error rate, latency, resource consumption, and health-check failures.

## Failed Deployment

If a new release causes a significant production regression, first stop further rollout of the affected version. Preserve relevant logs and deployment metadata before taking recovery actions.

Compare the current release with the previous known-good version. Confirm whether the incident began immediately after deployment and whether all application instances are affected.

If rollback is considered safe, restore the previous known-good release and monitor the system until key health indicators return to expected levels.

## Post-Recovery Validation

After recovery, verify authentication, database access, core API requests, background workers, and externally visible health endpoints.

The incident should not be considered resolved solely because application processes are running. Engineers should verify that users can successfully complete critical workflows and that error rates have returned to normal levels.
