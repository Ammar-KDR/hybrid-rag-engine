# Docker Networking Reference

## Docker Network Overview

Docker networking allows containers to communicate with each other and with external systems.

Docker provides several network drivers:

- Bridge
- Host
- None
- Overlay


# Bridge Network

The bridge network is the default Docker network driver.

Containers connected to the same bridge network can communicate using container names.

Create a network:

~~~bash
docker network create app-network
~~~

Run a container using a network:

~~~bash
docker run --network app-network nginx
~~~


Inspect a network:

~~~bash
docker network inspect app-network
~~~


# Container DNS Resolution

Docker provides automatic DNS resolution between containers on the same network.

Example:

Container A can connect to Container B using:

~~~text
database
~~~

instead of an IP address.


Common DNS problems:

- Container cannot resolve another container name
- Incorrect network configuration
- Containers attached to different networks


# Port Mapping

Containers run in isolated network environments.

Ports must be published to make services accessible externally.

Example:

~~~bash
docker run -p 8080:80 nginx
~~~

Meaning:

- Host port: 8080
- Container port: 80


Check published ports:

~~~bash
docker ps
~~~


# Host Networking

The host network mode allows containers to share the host network stack.

Example:

~~~bash
docker run --network host nginx
~~~

Advantages:

- Lower network overhead
- Direct host access

Disadvantages:

- Reduced isolation
- Possible port conflicts


# Docker Network Troubleshooting

## Connection Refused

Connection refused means the network connection reached the container but no application accepted the request.

Possible causes:

- Application is not running
- Wrong container port
- Incorrect service configuration


Check running containers:

~~~bash
docker ps
~~~


Check container logs:

~~~bash
docker logs <container-id>
~~~


# Connection Timeout

A connection timeout occurs when a request does not receive a response.

Possible causes:

- Network misconfiguration
- Firewall rules
- Application overload
- Incorrect routing


# Inspecting Network Configuration

View container network information:

~~~bash
docker inspect <container-id>
~~~

View available networks:

~~~bash
docker network ls
~~~


# Common Docker Networking Errors

## Port Already Allocated

Occurs when another process is already using the requested host port.

Example:

~~~text
Bind for 0.0.0.0:8080 failed: port is already allocated
~~~


Find processes using a port:

~~~bash
lsof -i :8080
~~~


## Network Not Found

Occurs when a container references a Docker network that does not exist.

Example:

~~~text
network app-network not found
~~~


Solution:

Create the network:

~~~bash
docker network create app-network
~~~


# Docker Network Debugging Workflow

1. Check running containers:

~~~bash
docker ps
~~~

2. Inspect container network:

~~~bash
docker inspect <container-id>
~~~

3. Check available networks:

~~~bash
docker network ls
~~~

4. Test connectivity between containers:

~~~bash
docker exec <container-id> ping <other-container>
~~~