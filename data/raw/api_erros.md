# API Error Reference

## API Troubleshooting Overview

APIs allow applications and services to communicate with each other.

API failures can occur because of:

- Invalid requests
- Authentication problems
- Service failures
- Network issues
- Rate limiting
- Configuration errors


# HTTP Status Codes

## 400 Bad Request

A 400 error means the server cannot process the request because the request format is invalid.

Common causes:

- Missing required parameters
- Invalid JSON payload
- Incorrect request format


Example:

~~~http
HTTP/1.1 400 Bad Request
~~~


Troubleshooting:

- Validate request payload
- Check API documentation
- Verify required fields


# 401 Unauthorized

A 401 error means authentication is required or failed.

Common causes:

- Missing authentication token
- Expired token
- Invalid credentials


Example:

~~~http
HTTP/1.1 401 Unauthorized
~~~


Troubleshooting:

- Check authorization header
- Refresh authentication token
- Verify user credentials


# 403 Forbidden

A 403 error means authentication succeeded but access is denied.

Common causes:

- Insufficient permissions
- Missing roles
- Access policies blocking request


Example:

~~~http
HTTP/1.1 403 Forbidden
~~~


Troubleshooting:

- Check user permissions
- Review access policies
- Verify role assignments


# 404 Not Found

A 404 error means the requested resource does not exist.

Common causes:

- Incorrect endpoint URL
- Deleted resource
- Wrong API version


Example:

~~~http
GET /api/v2/users/123
~~~

Possible issue:

~~~text
Endpoint does not exist
~~~


# 429 Too Many Requests

A 429 error means the client exceeded the allowed request rate.

Common causes:

- Too many API requests
- Missing rate limit handling
- Traffic spikes


Solutions:

- Implement retries
- Add exponential backoff
- Reduce request frequency


# 500 Internal Server Error

A 500 error indicates an unexpected server-side failure.

Common causes:

- Application bugs
- Database failures
- Invalid server configuration
- Unhandled exceptions


Troubleshooting:

Check:

- Application logs
- Database connectivity
- Recent deployments


# 502 Bad Gateway

A 502 error occurs when a gateway receives an invalid response from an upstream service.

Common causes:

- Backend service unavailable
- Incorrect proxy configuration
- Service crashes


# 503 Service Unavailable

A 503 error means the service is temporarily unavailable.

Common causes:

- Service overload
- Maintenance
- Failed health checks


# API Authentication Problems

Common authentication mechanisms:

- API keys
- JWT tokens
- OAuth tokens
- Basic authentication


JWT token problems:

- Expired token
- Invalid signature
- Incorrect claims


Example error:

~~~text
Invalid token
~~~


# API Debugging Commands

Test API endpoint:

~~~bash
curl -v https://api.example.com/users
~~~


Send headers:

~~~bash
curl \
-H "Authorization: Bearer token" \
https://api.example.com/users
~~~


Send JSON request:

~~~bash
curl \
-X POST \
-H "Content-Type: application/json" \
-d '{"name":"example"}' \
https://api.example.com/users
~~~


# API Troubleshooting Workflow

1. Verify endpoint URL.
2. Check authentication.
3. Validate request payload.
4. Inspect response status code.
5. Review application logs.
6. Check dependent services.
7. Confirm recovery after changes.