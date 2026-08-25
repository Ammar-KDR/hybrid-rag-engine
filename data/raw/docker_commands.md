# Docker Commands Reference

## Docker Overview

Docker commands allow developers and administrators to create, manage, inspect, and troubleshoot containers.

Common Docker operations include:

- Building images
- Running containers
- Managing storage
- Inspecting failures
- Debugging applications


# Container Management

## List Containers

List running containers:

~~~bash
docker ps
~~~

List all containers:

~~~bash
docker ps -a
~~~

The `-a` option includes stopped containers.


## Run a Container

Start a container from an image:

~~~bash
docker run nginx
~~~

Run a container in detached mode:

~~~bash
docker run -d nginx
~~~

Map a port:

~~~bash
docker run -p 8080:80 nginx
~~~


## Stop Containers

Stop a running container:

~~~bash
docker stop <container-id>
~~~

Remove a stopped container:

~~~bash
docker rm <container-id>
~~~


# Container Inspection

## Docker Logs

View container logs:

~~~bash
docker logs <container-id>
~~~

Follow logs continuously:

~~~bash
docker logs -f <container-id>
~~~

Useful for:

- Application errors
- Startup failures
- Runtime debugging


## Docker Inspect

Inspect detailed container information:

~~~bash
docker inspect <container-id>
~~~

Provides:

- Network configuration
- Mounted volumes
- Environment variables
- Container state


## Container Status

Check container state:

~~~bash
docker ps -a
~~~

Common states:

- Created
- Running
- Exited
- Restarting


# Docker Image Management

## List Images

~~~bash
docker images
~~~

## Pull Image

Download an image:

~~~bash
docker pull nginx
~~~

## Remove Image

~~~bash
docker rmi <image-id>
~~~


# Building Images

Build an image from Dockerfile:

~~~bash
docker build -t application:v1 .
~~~

Common build problems:

- Missing dependencies
- Invalid Dockerfile syntax
- Failed package installation


# Docker Exec

Execute commands inside a running container:

~~~bash
docker exec -it <container-id> bash
~~~

Useful for:

- Inspecting files
- Debugging applications
- Checking environment variables


# Container Exit Codes

Containers return exit codes when they terminate.

Common exit codes:

## Exit Code 0

The application exited successfully.


## Exit Code 1

Generic application failure.


## Exit Code 137

Usually indicates the container was terminated by SIGKILL.

Common causes:

- Out Of Memory (OOM)
- Resource limits exceeded


## Exit Code 139

Usually indicates a segmentation fault.

Common causes:

- Invalid memory access
- Application crash


# Docker Troubleshooting Workflow

When a container fails:

1. Check container status:

~~~bash
docker ps -a
~~~

2. Review logs:

~~~bash
docker logs <container-id>
~~~

3. Inspect configuration:

~~~bash
docker inspect <container-id>
~~~

4. Enter the container:

~~~bash
docker exec -it <container-id> bash
~~~

5. Check resource usage:

~~~bash
docker stats
~~~