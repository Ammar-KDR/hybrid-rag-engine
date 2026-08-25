# Kubernetes Configuration Reference

## imagePullPolicy

imagePullPolicy controls when Kubernetes pulls a container image from a registry.

The setting determines whether Kubernetes should always download the image or reuse a locally cached image.

Available values:

## Always

Kubernetes always pulls the image before starting the container.

Example:

~~~yaml
imagePullPolicy: Always
~~~

Use cases:

- Frequently updated images
- Development environments
- Latest image tags


## IfNotPresent

Kubernetes uses the local image if it already exists.

If the image is missing locally, Kubernetes downloads it.

Example:

~~~yaml
imagePullPolicy: IfNotPresent
~~~

This is commonly used for versioned production images.


## Never

Kubernetes never pulls the image.

The image must already exist on the node.

Example:

~~~yaml
imagePullPolicy: Never
~~~

Useful for:

- Offline environments
- Local development clusters


# restartPolicy

restartPolicy defines how Kubernetes handles container failures.

Available values:

## Always

The container is restarted whenever it exits.

Example:

~~~yaml
restartPolicy: Always
~~~

This is the default behavior for pods created by controllers.

## OnFailure

The container restarts only when it exits with a failure code.

Example:

~~~yaml
restartPolicy: OnFailure
~~~

## Never

The container is not restarted after termination.

Example:

~~~yaml
restartPolicy: Never
~~~


# Health Probes

Kubernetes uses probes to determine application health.

## Liveness Probe

A liveness probe checks whether the application is still running correctly.

If the probe fails repeatedly, Kubernetes restarts the container.

Example:

~~~yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
~~~


## Readiness Probe

A readiness probe checks whether the application can receive traffic.

A container can be running but not ready.

Example:

~~~yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
~~~


## Startup Probe

A startup probe protects slow-starting applications.

Kubernetes waits for the startup probe before enabling other health checks.

Example:

~~~yaml
startupProbe:
  httpGet:
    path: /startup
    port: 8080
~~~


# Resource Configuration

## CPU Requests and Limits

CPU requests define guaranteed CPU resources.

CPU limits define the maximum CPU usage.

Example:

~~~yaml
resources:
  requests:
    cpu: "500m"
  limits:
    cpu: "1"
~~~


## Memory Requests and Limits

Memory requests define guaranteed memory.

Memory limits prevent containers from consuming unlimited memory.

Example:

~~~yaml
resources:
  requests:
    memory: "512Mi"
  limits:
    memory: "1Gi"
~~~


# Common Configuration Problems

Incorrect imagePullPolicy can cause:

- ImagePullBackOff
- outdated images
- failed deployments

Incorrect resource limits can cause:

- OOMKilled
- slow applications
- container restarts

Incorrect probes can cause:

- unnecessary restarts
- traffic being sent to unhealthy applications