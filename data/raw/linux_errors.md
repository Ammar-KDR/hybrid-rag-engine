# Linux System Errors Reference

## Out Of Memory (OOM) Killer

The Linux OOM Killer is a kernel mechanism that terminates processes when the system runs out of available memory.

The goal is to prevent the entire operating system from becoming unresponsive.

Common causes:

- Applications consuming excessive memory
- Memory leaks
- Insufficient RAM
- Incorrect application configuration


## Detecting OOM Events

Check kernel logs:

~~~bash
dmesg | grep -i oom
~~~

Search system logs:

~~~bash
journalctl | grep -i "out of memory"
~~~

Typical log message:

~~~text
Out of memory: Killed process 1234 (application)
~~~


## Solutions for OOM Problems

Possible solutions:

- Increase available memory
- Optimize application memory usage
- Limit application resource consumption
- Investigate memory leaks
- Configure swap space


# Segmentation Fault

A segmentation fault occurs when a program attempts to access memory that it is not allowed to access.

Common causes:

- Invalid memory access
- Dereferencing invalid pointers
- Buffer overflows
- Software bugs


Example error:

~~~text
Segmentation fault (core dumped)
~~~


## Troubleshooting Segmentation Faults

Check application logs:

~~~bash
journalctl -xe
~~~

Inspect core dumps:

~~~bash
coredumpctl list
~~~

Debug using:

~~~bash
gdb application core
~~~


# Permission Denied Errors

Permission denied occurs when a user or process attempts an operation without sufficient privileges.

Common causes:

- Incorrect file permissions
- Wrong ownership
- Missing sudo privileges


Check file permissions:

~~~bash
ls -l filename
~~~

Change ownership:

~~~bash
chown user:group filename
~~~

Change permissions:

~~~bash
chmod 755 filename
~~~


# Disk Space Errors

Low disk space can cause applications and services to fail.

Common symptoms:

- Unable to create files
- Database failures
- Log write failures
- Application crashes


Check disk usage:

~~~bash
df -h
~~~

Find large directories:

~~~bash
du -sh /*
~~~


# Service Startup Failures

A Linux service may fail to start because of:

- Invalid configuration
- Missing dependencies
- Port conflicts
- Permission problems


Check failed services:

~~~bash
systemctl --failed
~~~

View service status:

~~~bash
systemctl status <service-name>
~~~

View service logs:

~~~bash
journalctl -u <service-name>
~~~


# Common Linux Error Messages

## Cannot Allocate Memory

Indicates the system cannot provide enough memory for a process.

Possible causes:

- Memory exhaustion
- Resource limits
- Large application workload


## Address Already In Use

Occurs when an application attempts to bind to a port already occupied by another process.

Example:

~~~text
bind: Address already in use
~~~


Find the process using a port:

~~~bash
lsof -i :8080
~~~


## Connection Refused

Occurs when a connection reaches a machine but no service is listening on the requested port.

Possible causes:

- Service stopped
- Wrong port
- Firewall restrictions