# Docker Container Management Guide

## Docker Overview

Docker is a platform for building, packaging, and running applications inside containers.

A container packages:

- Application code
- Runtime dependencies
- Libraries
- Configuration

Containers provide consistent execution environments across development and production systems.

## Images

A Docker image is a read-only template used to create containers.

Images are created from Dockerfiles.

Example:

FROM python:3.12

COPY app.py /app/

CMD ["python", "app.py"]

Images can be downloaded from registries:

docker pull nginx

Available images:

docker images

## Containers

A container is a running instance of an image.

Create a container:

docker run nginx

List running containers:

docker ps

Stop a container:

docker stop <container-id>

Remove a container:

docker rm <container-id>

## Container Storage

Containers are temporary by default.

When a container is removed, data stored inside the container filesystem is lost.

Volumes provide persistent storage.

Create a volume:

docker volume create database-data

Run a container with a volume:

docker run -v database-data:/var/lib/mysql mysql

Volumes are commonly used for databases and applications requiring persistent files.

## Docker Networking

Containers can communicate using Docker networks.

Create a network:

docker network create app-network

Containers connected to the same network can communicate using container names.

## Docker Compose

Docker Compose defines multi-container applications.

A compose file describes:

- Services
- Networks
- Volumes
- Environment variables

Example services:

- Web application
- Database
- Cache

Compose starts all services together:

docker compose up

## Troubleshooting Containers

Common container problems include:

- Application crashes
- Incorrect environment variables
- Port conflicts
- Missing dependencies

Useful commands:

docker logs <container>

docker inspect <container>

docker exec -it <container> bash

Logs are usually the first place to investigate application failures.