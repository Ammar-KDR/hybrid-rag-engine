# Database Errors Reference

## Database Troubleshooting Overview

Database failures can affect application availability, performance, and data consistency.

Common database problems include:

- Connection failures
- Slow queries
- Deadlocks
- Resource exhaustion
- Transaction failures


# Database Connection Errors

## Connection Refused

A database connection refused error occurs when the client cannot establish a connection to the database server.

Example:

~~~text
connection refused
~~~


Common causes:

- Database service is stopped
- Incorrect hostname
- Incorrect port
- Database is not listening for connections


Troubleshooting:

Check database service:

~~~bash
systemctl status postgresql
~~~

Check listening ports:

~~~bash
netstat -tulpn
~~~


## Connection Pool Exhausted

Connection pool exhaustion occurs when an application uses all available database connections.

Example:

~~~text
too many connections
~~~

Common causes:

- Connection leaks
- Long-running queries
- Insufficient pool size


Solutions:

- Increase connection pool size
- Close unused connections
- Optimize slow queries


# Slow Query Problems

## Slow Queries

A slow query takes longer than expected to execute.

Common causes:

- Missing indexes
- Large table scans
- Inefficient joins
- Poor query design


Identify slow queries using:

- Query logs
- Database monitoring
- Execution plans


Example:

~~~sql
EXPLAIN SELECT * FROM users WHERE email='example@test.com';
~~~


# Database Indexes

Indexes improve query performance by allowing faster data lookup.

Without indexes:

~~~text
Full table scan
        |
        ↓
Check every row
~~~


With indexes:

~~~text
Index lookup
        |
        ↓
Direct row access
~~~


Common index problems:

- Missing indexes
- Too many indexes
- Outdated statistics


# Deadlocks

A deadlock occurs when two transactions wait for each other indefinitely.

Example:

Transaction A:

~~~text
Locks table users
Waits for orders
~~~


Transaction B:

~~~text
Locks table orders
Waits for users
~~~


The database cannot continue until one transaction is terminated.


Symptoms:

- Transaction timeout
- Deadlock detected errors
- Failed writes


Solutions:

- Keep transactions short
- Access tables in consistent order
- Retry failed transactions


# Transaction Failures

Transactions group database operations into a single logical unit.

A transaction follows ACID properties:

## Atomicity

All operations succeed or none succeed.


## Consistency

Database state remains valid.


## Isolation

Transactions do not interfere incorrectly.


## Durability

Committed data survives failures.


# Database Configuration Problems

Common configuration issues:

- Incorrect connection strings
- Invalid credentials
- Wrong database port
- Insufficient resources


Example connection string:

~~~text
postgresql://user:password@localhost:5432/database
~~~


# Database Troubleshooting Commands

Check database processes:

~~~bash
ps aux | grep postgres
~~~


Check service status:

~~~bash
systemctl status postgresql
~~~


View logs:

~~~bash
journalctl -u postgresql
~~~


Check active connections:

~~~sql
SELECT * FROM pg_stat_activity;
~~~


# Common Database Error Messages

## Too Many Connections

Cause:

- Connection pool exhaustion
- Applications opening excessive connections


## Lock Timeout

Cause:

- Long-running transactions
- Database contention


## Duplicate Key Error

Cause:

- Insert operation violates unique constraint


## Authentication Failed

Cause:

- Incorrect username or password
- Invalid authentication configuration