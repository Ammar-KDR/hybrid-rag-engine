# Database Administration Guide

## Database Fundamentals

Databases store and organize application data.

Common database systems include:

- PostgreSQL
- MySQL
- MongoDB

Relational databases organize information into tables containing rows and columns.

## SQL Queries

SQL is used to interact with relational databases.

Example:

SELECT * FROM users;

Queries can retrieve, insert, update, and delete information.

Poorly written queries can create performance problems.

## Indexes

Indexes improve query performance by allowing databases to locate data faster.

Without indexes, databases may scan entire tables.

Example:

A user lookup by email can become faster when an index exists on the email column.

However, indexes also increase storage requirements and can slow writes.

## Transactions

Transactions group database operations into a single unit.

A transaction follows ACID principles:

Atomicity:
All operations succeed or none do.

Consistency:
Data remains valid.

Isolation:
Transactions do not interfere incorrectly.

Durability:
Committed data survives failures.

## Backups

Backups protect against:

- Hardware failures
- Human mistakes
- Data corruption

Common backup strategies:

- Full backups
- Incremental backups
- Automated snapshots

## Replication

Database replication creates copies of data across multiple servers.

Replication improves:

- Availability
- Read scalability
- Disaster recovery

## Database Troubleshooting

Common database problems include:

- Slow queries
- Connection failures
- Locking issues
- High CPU usage

Useful investigation steps:

- Check active queries
- Review database logs
- Inspect indexes
- Monitor resource usage

Performance problems often require analyzing query execution plans.