# Linux Process Debugging Reference

## Process Investigation

Linux processes represent running programs and services.

When an application becomes slow, unresponsive, or crashes, administrators investigate processes to identify resource usage and failures.


# Finding Processes

## ps Command

The ps command displays current processes.

Example:

~~~bash
ps aux
~~~

Useful information:

- Process ID (PID)
- CPU usage
- Memory usage
- Process owner
- Command name


Find a specific process:

~~~bash
ps aux | grep nginx
~~~


## pgrep

pgrep searches for processes by name.

Example:

~~~bash
pgrep nginx
~~~

Returns:

~~~text
1234
5678
~~~

where the values are process IDs.


# Process Resource Analysis

## CPU Usage

High CPU usage can indicate:

- Infinite loops
- Heavy computation
- Application bugs
- Excessive workload


Check CPU usage:

~~~bash
top
~~~

or:

~~~bash
htop
~~~


## Memory Usage

High memory usage can indicate:

- Memory leaks
- Large data processing
- Incorrect application limits


Check memory:

~~~bash
free -h
~~~

Inspect process memory:

~~~bash
ps aux --sort=-%mem
~~~


# Process Signals

Linux uses signals to communicate with processes.


## SIGTERM

SIGTERM requests graceful termination.

Example:

~~~bash
kill <pid>
~~~

Applications can handle SIGTERM and clean up resources before exiting.


## SIGKILL

SIGKILL immediately terminates a process.

Example:

~~~bash
kill -9 <pid>
~~~

The application cannot catch or ignore SIGKILL.


## SIGHUP

SIGHUP is commonly used to reload configuration.

Example:

~~~bash
kill -HUP <pid>
~~~


# Debugging Stuck Processes

## strace

strace monitors system calls made by a process.

Example:

~~~bash
strace -p <pid>
~~~

Useful for investigating:

- File access problems
- Network calls
- Process blocking


## lsof

lsof lists open files and network connections.

Example:

~~~bash
lsof -p <pid>
~~~

Find which process uses a port:

~~~bash
lsof -i :8080
~~~


# Zombie Processes

A zombie process is a terminated process whose exit status has not been collected by its parent process.

Check zombie processes:

~~~bash
ps aux | grep Z
~~~

Possible causes:

- Parent process not handling child processes
- Application bugs


# Debugging Application Crashes

When an application crashes:

1. Check process status:

~~~bash
ps aux
~~~

2. Check logs:

~~~bash
journalctl -xe
~~~

3. Check system resources:

~~~bash
top
~~~

4. Inspect crash information:

~~~bash
coredumpctl list
~~~


# Common Process Problems

## High CPU

Symptoms:

- System slowdown
- Increased response time
- High load average

Investigation:

- top
- htop
- ps


## High Memory Usage

Symptoms:

- OOM Killer activation
- Application crashes
- System instability

Investigation:

- free
- ps
- top


## Unresponsive Process

Possible causes:

- Deadlock
- Waiting on I/O
- Network timeout
- Resource exhaustion

Investigation:

- strace
- logs
- process state inspection