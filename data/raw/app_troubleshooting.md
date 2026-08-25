# Application Troubleshooting Runbook

## Application Incident Overview

Application incidents occur when a service becomes unavailable, slow, or behaves unexpectedly.

Common incident categories:

- Application crashes
- Performance degradation
- Dependency failures
- Configuration problems
- Resource exhaustion


# Initial Investigation

When an application fails, collect basic information.

Important questions:

- Is the application running?
- When did the problem start?
- Are all users affected?
- Did a recent deployment occur?
- Are dependencies available?


# Application Health Checks

Health checks determine whether an application is operating correctly.


## Liveness Check

A liveness check determines whether the application process is alive.

A failed liveness check may cause the application to restart.


Example:

~~~http
GET /health
~~~


## Readiness Check

A readiness check determines whether the application can receive traffic.

A service may be running but not ready.


Example:

~~~http
GET /ready
~~~


# Application Logs

Logs provide information about application behavior.

Important log categories:

- Error messages
- Warnings
- Startup information
- Request failures


Common commands:

View application logs:

~~~bash
tail -f application.log
~~~

Search errors:

~~~bash
grep ERROR application.log
~~~


# Deployment Failures

Deployments can fail because of:

- Invalid configuration
- Missing dependencies
- Application startup errors
- Database connection failures
- Resource limitations


Common symptoms:

- New version unavailable
- Increased error rates
- Failed health checks


# Rollback Procedure

If a new deployment causes failures, rollback to the previous stable version.

Example:

~~~bash
kubectl rollout undo deployment <deployment-name>
~~~


Verify rollback:

~~~bash
kubectl rollout status deployment <deployment-name>
~~~


# Dependency Failures

Applications often depend on:

- Databases
- APIs
- Message queues
- External services


Common dependency failures:

- Connection timeout
- Authentication failure
- Service unavailable


Troubleshooting steps:

1. Check dependency availability.
2. Verify network connectivity.
3. Check credentials.
4. Review service logs.


# Resource Problems

Applications may fail because of limited resources.

Common resources:

- CPU
- Memory
- Disk space
- Network bandwidth


Check system resources:

~~~bash
top
~~~

Check memory:

~~~bash
free -h
~~~

Check disk:

~~~bash
df -h
~~~


# Incident Recovery Checklist

1. Identify affected service.
2. Check application status.
3. Review recent changes.
4. Inspect logs.
5. Check dependencies.
6. Validate configuration.
7. Recover service.
8. Confirm normal operation.


# Post Incident Analysis

After recovery:

Document:

- Root cause
- Impact
- Resolution steps
- Prevention actions

Common improvements:

- Better monitoring
- Automated testing
- Improved documentation
- Resource tuning