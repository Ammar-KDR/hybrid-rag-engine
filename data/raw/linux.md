# Linux System Administration Guide

## Linux Overview

Linux is an operating system widely used for servers, cloud infrastructure, and development environments.

Linux systems are managed through:

- Command-line tools
- Configuration files
- System services

## Processes

A process is a running instance of a program.

View running processes:

ps aux

Monitor processes:

top

or:

htop

Processes consume resources such as:

- CPU
- Memory
- Disk access

High CPU usage can indicate inefficient applications or excessive workloads.

## Memory Management

Linux uses RAM to store active data.

Memory issues may cause:

- Slow applications
- Process termination
- System instability

Check memory usage:

free -h

The operating system may use swap space when physical memory is exhausted.

## File Permissions

Linux controls access through permissions.

Permissions include:

- Read
- Write
- Execute

Example:

chmod 755 script.sh

Ownership can be changed using:

chown user:file file.txt

Incorrect permissions commonly cause application startup failures.

## System Services

Linux services run background processes.

Systemd manages many Linux services.

Check service status:

systemctl status service-name

Restart a service:

systemctl restart service-name

View logs:

journalctl -u service-name

## Disk Management

Disk space problems can prevent applications from writing files.

Check disk usage:

df -h

Find large files:

du -sh *

Log files should be monitored because they can grow continuously.

## SSH Access

SSH provides secure remote access.

Connect:

ssh user@server

Common SSH problems include:

- Incorrect keys
- Firewall restrictions
- Wrong permissions