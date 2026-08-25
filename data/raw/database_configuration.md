# Database Configuration Reference

## Database Configuration Overview

Database configuration controls how applications connect to and interact with database systems.

Important configuration areas include:

- Connection settings
- Authentication
- Resource limits
- Performance tuning
- Backup configuration


# Connection Configuration

A database connection requires several parameters:

- Hostname
- Port
- Database name
- Username
- Password


Example:

~~~text
postgresql://username:password@database-host:5432/application_db
~~~


Common connection problems:

- Incorrect hostname
- Wrong database port
- Invalid credentials
- Database service unavailable


# PostgreSQL Configuration

## PostgreSQL Port

The default PostgreSQL port is:

~~~text
5432
~~~


Check PostgreSQL listening port:

~~~bash
netstat -tulpn | grep 5432
~~~


## max_connections

max_connections defines the maximum number of concurrent database connections.

Example:

~~~text
max_connections = 100
~~~


Increasing this value allows more clients but requires additional memory.


# MySQL Configuration

## MySQL Port

The default MySQL port is:

~~~text
3306
~~~


## Buffer Pool

The InnoDB buffer pool stores frequently accessed database pages in memory.

A properly configured buffer pool improves query performance.


# Connection Pool Configuration

Applications commonly use connection pools to reuse database connections.

Important settings:

## Maximum Pool Size

Controls the maximum number of active connections.

Example:

~~~text
maximumPoolSize=20
~~~


## Connection Timeout

Defines how long an application waits for an available connection.

Example:

~~~text
connectionTimeout=30000
~~~


Problems caused by incorrect pool configuration:

- Connection timeout errors
- Too many database connections
- Application slowdown


# Query Performance Configuration

## Query Timeout

Query timeout limits how long a query can execute.

Example:

~~~text
statement_timeout=30000
~~~


Useful for preventing:

- Long-running queries
- Resource exhaustion
- Database overload


## Slow Query Logging

Slow query logs record queries that exceed a configured execution time.

Example:

~~~text
slow_query_log=ON
~~~


Useful for identifying:

- Missing indexes
- Inefficient queries
- Performance bottlenecks


# Backup Configuration

Database backups protect against:

- Data loss
- Hardware failures
- Human mistakes
- Application errors


Common backup strategies:

## Full Backup

Stores the complete database state.

Advantages:

- Simple restore process

Disadvantages:

- Larger storage requirement


## Incremental Backup

Stores changes since the previous backup.

Advantages:

- Faster backup process

Disadvantages:

- More complex restoration


# Database Authentication Configuration

Authentication controls who can access the database.

Common methods:

- Password authentication
- Certificate authentication
- External identity providers


Common authentication errors:

~~~text
password authentication failed
~~~

Causes:

- Incorrect credentials
- User does not exist
- Authentication configuration problems


# Database Configuration Troubleshooting

Check database configuration:

~~~bash
cat postgresql.conf
~~~


Check active connections:

~~~sql
SELECT count(*) FROM pg_stat_activity;
~~~


Review database logs:

~~~bash
journalctl -u postgresql
~~~


Verify connectivity:

~~~bash
psql -h hostname -U username -d database
~~~