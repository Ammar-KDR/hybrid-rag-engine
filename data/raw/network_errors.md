# Network Errors Reference

## Network Troubleshooting Overview

Network failures can prevent applications, services, and users from communicating successfully.

Common network problems include:

- Connection refused
- Connection timeout
- DNS resolution failures
- TLS handshake failures
- Authentication failures


# Connection Refused

## Definition

Connection refused occurs when a client reaches a server, but no application is accepting connections on the requested port.

The network path is available, but the destination service is unavailable.


Example error:

~~~text
Connection refused
ECONNREFUSED
~~~


## Common Causes

- Service is stopped
- Application failed during startup
- Incorrect port number
- Service listening only on localhost
- Firewall rules rejecting connections


## Troubleshooting

Check whether the service is running:

~~~bash
systemctl status <service-name>
~~~

Check listening ports:

~~~bash
netstat -tulpn
~~~

Test connectivity:

~~~bash
curl http://hostname:port
~~~


# Connection Timeout

## Definition

A connection timeout occurs when a client sends a request but does not receive a response within the expected period.

Unlike connection refused, the destination may not be reachable.


Example error:

~~~text
Connection timed out
~~~


## Common Causes

- Network routing problems
- Firewall blocking traffic
- High server load
- Incorrect network configuration
- Packet loss


## Troubleshooting

Test network connectivity:

~~~bash
ping <hostname>
~~~

Check route:

~~~bash
traceroute <hostname>
~~~

Test service response:

~~~bash
curl -v http://hostname:port
~~~


# DNS Resolution Errors

DNS converts domain names into IP addresses.

DNS problems prevent applications from locating services.


## NXDOMAIN

NXDOMAIN means the requested domain name does not exist.

Example:

~~~text
DNS_PROBE_FINISHED_NXDOMAIN
~~~


Common causes:

- Incorrect hostname
- Missing DNS record
- Typographical errors


## SERVFAIL

SERVFAIL indicates that the DNS server failed to complete the request.

Common causes:

- DNS server problems
- Invalid DNS configuration
- Temporary resolver failures


## DNS Troubleshooting

Lookup a domain:

~~~bash
nslookup example.com
~~~

Query DNS records:

~~~bash
dig example.com
~~~


# TLS Handshake Failure

## Definition

A TLS handshake failure occurs when a client and server cannot establish a secure encrypted connection.


Example error:

~~~text
TLS handshake failed
~~~


## Common Causes

- Expired certificate
- Invalid certificate chain
- Unsupported TLS version
- Incorrect server configuration


## Troubleshooting

Check certificate:

~~~bash
openssl s_client -connect example.com:443
~~~

Verify certificate expiration:

~~~bash
openssl x509 -in certificate.pem -text -noout
~~~


# HTTP Error Codes

## 400 Bad Request

The server cannot process the request because it is invalid.

Possible causes:

- Invalid request format
- Missing parameters


## 401 Unauthorized

Authentication is required.

Possible causes:

- Missing token
- Expired credentials
- Invalid login information


## 403 Forbidden

The server understood the request but denied access.

Possible causes:

- Missing permissions
- Access control rules


## 404 Not Found

The requested resource does not exist.

Possible causes:

- Incorrect URL
- Removed resource


## 500 Internal Server Error

The server encountered an unexpected failure.

Possible causes:

- Application bugs
- Database failures
- Configuration errors


# Network Debugging Workflow

1. Check DNS resolution:

~~~bash
nslookup <domain>
~~~

2. Test connectivity:

~~~bash
ping <host>
~~~

3. Check port availability:

~~~bash
telnet <host> <port>
~~~

4. Inspect application response:

~~~bash
curl -v <url>
~~~

5. Review service logs:

~~~bash
journalctl -xe
~~~