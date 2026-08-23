# Network Troubleshooting Guide

## Network Fundamentals

Computer networks allow systems to communicate by exchanging data packets.

Important networking concepts include:

- IP addresses
- Ports
- Protocols
- DNS
- Routing

Every device communicating on a network requires an address.

## IP Addresses

An IP address identifies a device on a network.

IPv4 addresses contain four numerical sections.

Example:

192.168.1.10

Private IP addresses are used inside local networks, while public IP addresses are reachable from the internet.

## DNS

DNS converts human-readable domain names into IP addresses.

Example:

example.com

is translated into:

93.184.216.34

DNS problems can cause applications to fail even when network connectivity exists.

A system may successfully reach an IP address but fail to access a hostname because DNS resolution is broken.

## HTTP and HTTPS

HTTP is the protocol used for web communication.

Common HTTP methods:

- GET
- POST
- PUT
- DELETE

HTTPS adds encryption using TLS certificates.

Common HTTP status codes:

200:
Request successful

404:
Resource not found

500:
Server error

## TCP Communication

TCP provides reliable communication between systems.

TCP ensures:

- Ordered delivery
- Error detection
- Retransmission

Applications use ports to identify services.

Example:

HTTP:
Port 80

HTTPS:
Port 443

## Network Troubleshooting

Common network issues:

- High latency
- Packet loss
- DNS failures
- Firewall blocking
- Incorrect routing

Useful commands:

ping

Tests connectivity between hosts.

traceroute

Shows the path packets take through the network.

nslookup

Checks DNS resolution.

curl

Tests HTTP services.

## Firewalls

Firewalls control allowed network traffic.

A firewall rule may block:

- Incoming connections
- Outgoing connections
- Specific ports

When an application cannot connect, engineers should verify firewall rules before changing application code.