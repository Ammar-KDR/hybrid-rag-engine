# Linux Commands Reference

## Linux Command Line Overview

Linux command-line tools allow administrators to inspect systems, manage processes, troubleshoot failures, and monitor resources.

System administrators commonly use commands for:

- Process management
- File inspection
- Service management
- Network troubleshooting
- Resource monitoring


# Process Management Commands

## ps

The ps command displays running processes.

Example:

~~~bash
ps aux
~~~

Common uses:

- Finding active processes
- Checking resource usage
- Investigating application failures


## top

The top command provides a live view of running processes.

Example:

~~~bash
top
~~~

Displays:

- CPU usage
- Memory usage
- Running processes
- Process IDs


## htop

htop is an interactive process monitoring tool.

Example:

~~~bash
htop
~~~

Advantages:

- Easier process navigation
- Colorized resource information
- Interactive process management


## kill

The kill command sends signals to processes.

Example:

~~~bash
kill <process-id>
~~~

Force terminate a process:

~~~bash
kill -9 <process-id>
~~~

Signal 9 is SIGKILL and immediately terminates the process.


# Service Management

## systemctl

systemctl manages services running under systemd.

Check service status:

~~~bash
systemctl status nginx
~~~

Start a service:

~~~bash
systemctl start nginx
~~~

Stop a service:

~~~bash
systemctl stop nginx
~~~

Restart a service:

~~~bash
systemctl restart nginx
~~~


## journalctl

journalctl reads logs collected by systemd.

View service logs:

~~~bash
journalctl -u nginx
~~~

View recent logs:

~~~bash
journalctl -xe
~~~


# File and Storage Commands

## df

df displays filesystem disk usage.

Example:

~~~bash
df -h
~~~

Useful for identifying:

- Full disks
- Storage problems
- Capacity issues


## du

du estimates file and directory sizes.

Example:

~~~bash
du -sh /var/log
~~~


## ls

ls lists files and directories.

Example:

~~~bash
ls -lah
~~~


# System Information Commands

## uname

Displays system information.

Example:

~~~bash
uname -a
~~~

Shows:

- Kernel version
- Operating system information
- Architecture


## uptime

Displays system uptime and load averages.

Example:

~~~bash
uptime
~~~


# Network Commands

## ping

Tests network connectivity.

Example:

~~~bash
ping example.com
~~~


## curl

curl sends HTTP requests.

Example:

~~~bash
curl https://example.com
~~~

Useful for:

- API testing
- Checking service availability
- Debugging HTTP responses


## netstat

netstat displays network connections.

Example:

~~~bash
netstat -tulpn
~~~

Shows:

- Listening ports
- Active connections
- Network services


# Common Linux Troubleshooting Commands

Check running processes:

~~~bash
ps aux
~~~

Check system logs:

~~~bash
journalctl -xe
~~~

Check memory usage:

~~~bash
free -h
~~~

Check disk usage:

~~~bash
df -h
~~~

Check active services:

~~~bash
systemctl --failed
~~~