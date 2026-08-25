# Docker Storage Reference

## Docker Container Storage Overview

Containers are temporary by default.

When a container is removed, any data stored inside the container filesystem is lost.

Docker provides storage mechanisms to preserve data beyond the lifecycle of a container.

Main storage options:

- Volumes
- Bind mounts
- Temporary storage


# Docker Volumes

Volumes are the recommended method for storing persistent application data.

Docker manages the storage location and lifecycle of volumes.

Create a volume:

~~~bash
docker volume create database-data
~~~

List volumes:

~~~bash
docker volume ls
~~~

Inspect a volume:

~~~bash
docker volume inspect database-data
~~~


# Using Volumes With Containers

Run a container with a volume:

~~~bash
docker run \
-v database-data:/var/lib/mysql \
mysql
~~~

The data stored in:

~~~text
/var/lib/mysql
~~~

will persist even if the container is removed.


# Bind Mounts

Bind mounts connect a directory from the host machine directly into a container.

Example:

~~~bash
docker run \
-v /host/project:/app \
application
~~~

Common uses:

- Development environments
- Sharing source code
- Local testing


# Volume vs Bind Mount

## Volumes

Advantages:

- Managed by Docker
- Easier backup and migration
- Better isolation
- Recommended for production databases


## Bind Mounts

Advantages:

- Direct host file access
- Useful for development

Disadvantages:

- Depends on host filesystem structure
- Easier to create permission problems


# Persistent Database Storage

Databases require persistent storage because removing a container should not delete data.

Examples:

- MySQL data directory
- PostgreSQL data directory
- MongoDB database files


Example:

~~~bash
docker run \
-d \
-v postgres-data:/var/lib/postgresql/data \
postgres
~~~


# Docker Storage Problems

## Data Lost After Container Removal

Cause:

- Data stored only inside container filesystem

Solution:

Use Docker volumes.

Example:

~~~bash
docker volume create application-data
~~~


## Permission Problems

Symptoms:

- Container cannot write files
- Application fails during startup

Possible causes:

- Incorrect ownership
- Incorrect filesystem permissions
- User mismatch between host and container


Check permissions:

~~~bash
ls -la /path/to/data
~~~


# Disk Space Problems

Docker images and containers consume disk space over time.

Check Docker disk usage:

~~~bash
docker system df
~~~


Clean unused resources:

~~~bash
docker system prune
~~~


# Inspecting Container Storage

View mounted volumes:

~~~bash
docker inspect <container-id>
~~~

Look for:

~~~text
Mounts
~~~


# Docker Storage Troubleshooting Workflow

1. Check container configuration:

~~~bash
docker inspect <container-id>
~~~

2. Verify volumes:

~~~bash
docker volume ls
~~~

3. Inspect volume details:

~~~bash
docker volume inspect <volume-name>
~~~

4. Check filesystem permissions:

~~~bash
ls -la <path>
~~~

5. Check available disk space:

~~~bash
df -h
~~~