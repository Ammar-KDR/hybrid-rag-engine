# DNS Reference Guide

## DNS Overview

The Domain Name System (DNS) translates human-readable domain names into IP addresses.

Applications rely on DNS to locate:

- Web servers
- APIs
- Databases
- Internal services
- Cloud resources


Example:

~~~text
api.example.com
        |
        ↓
    192.168.1.50
~~~


# DNS Record Types

## A Record

An A record maps a domain name to an IPv4 address.

Example:

~~~text
example.com → 93.184.216.34
~~~


## AAAA Record

An AAAA record maps a domain name to an IPv6 address.

Example:

~~~text
example.com → 2001:db8::1
~~~


## CNAME Record

A CNAME record creates an alias for another domain.

Example:

~~~text
www.example.com → example.com
~~~


## MX Record

MX records define mail servers responsible for email delivery.


## TXT Record

TXT records store text information.

Common uses:

- Domain verification
- SPF records
- Security policies


# DNS Resolution Process

When a user accesses:

~~~text
api.example.com
~~~

The resolution process is:

1. Application checks local cache.
2. Operating system checks DNS resolver.
3. Resolver queries authoritative DNS servers.
4. IP address is returned.
5. Application connects to the destination.


# DNS Caching

DNS responses are cached to reduce lookup time.

Caching occurs at:

- Browser level
- Operating system level
- Local DNS resolver
- Network provider


Problems caused by stale cache:

- Old IP addresses
- Incorrect routing
- Delayed configuration changes


Clear local DNS cache:

Linux:

~~~bash
sudo systemctl restart systemd-resolved
~~~

Windows:

~~~bash
ipconfig /flushdns
~~~


# Common DNS Errors

## NXDOMAIN

NXDOMAIN means the requested domain does not exist.

Example:

~~~text
server.example.com: NXDOMAIN
~~~

Possible causes:

- Typo in hostname
- Missing DNS record
- Incorrect domain


## SERVFAIL

SERVFAIL means the DNS server failed to process the request.

Possible causes:

- DNS server failure
- Incorrect zone configuration
- DNSSEC problems


## DNS Timeout

A DNS timeout occurs when the resolver does not receive a response.

Possible causes:

- Network connectivity problems
- Unreachable DNS server
- Firewall restrictions


# DNS Troubleshooting Commands

## nslookup

Query DNS information:

~~~bash
nslookup example.com
~~~


## dig

Provides detailed DNS information:

~~~bash
dig example.com
~~~

Query specific records:

~~~bash
dig MX example.com
~~~


## host

Simple DNS lookup command:

~~~bash
host example.com
~~~


# DNS in Kubernetes

Kubernetes uses CoreDNS for internal service discovery.

Example service address:

~~~text
backend.default.svc.cluster.local
~~~


Common Kubernetes DNS issues:

- Service name cannot resolve
- CoreDNS pods are unhealthy
- Incorrect namespace
- Missing service


Check CoreDNS:

~~~bash
kubectl get pods -n kube-system
~~~


Check service DNS:

~~~bash
nslookup backend.default.svc.cluster.local
~~~


# DNS Security

Common DNS security concerns:

- DNS spoofing
- Cache poisoning
- Unauthorized DNS changes


Security mechanisms:

- DNSSEC
- Access-controlled DNS management
- Monitoring DNS queries