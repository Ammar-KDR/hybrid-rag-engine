# Kubernetes Operations Guide

## Kubernetes Overview

Kubernetes is a container orchestration platform used to deploy, manage, and scale containerized applications.

A Kubernetes cluster consists of a control plane and worker nodes. The control plane manages the desired state of applications, while worker nodes run application workloads.

Kubernetes continuously compares the desired state defined by configuration files with the actual state of running resources. If the actual state differs, Kubernetes attempts to correct the difference automatically.

## Pods

A Pod is the smallest deployable unit in Kubernetes.

A Pod contains one or more containers that share:

- Network namespace
- Storage volumes
- Lifecycle configuration

Most applications run inside containers managed by Pods.

To inspect running Pods:

kubectl get pods

Detailed information about a Pod can be viewed using:

kubectl describe pod <pod-name>

Common Pod problems include:

- Image download failures
- Container crashes
- Resource exhaustion
- Configuration errors

## Deployments

Deployments manage the lifecycle of application Pods.

A Deployment provides:

- Replica management
- Rolling updates
- Version history
- Automatic recovery

Example:

kubectl create deployment nginx --image=nginx

If a container crashes, the Deployment controller attempts to create a healthy replacement Pod.

To restart a Deployment:

kubectl rollout restart deployment <deployment-name>

To view Deployment status:

kubectl rollout status deployment <deployment-name>

## Services

Pods have dynamic IP addresses. Services provide stable network access to Pods.

Common Service types:

- ClusterIP
- NodePort
- LoadBalancer

ClusterIP exposes applications internally inside the cluster.

LoadBalancer exposes applications externally through a cloud provider.

## Troubleshooting Failed Applications

When an application is unavailable, engineers should inspect resources in order.

First check Pods:

kubectl get pods

Then inspect events:

kubectl describe pod <pod-name>

Application logs can be retrieved using:

kubectl logs <pod-name>

Common recovery actions include:

- Restarting unhealthy Deployments
- Checking container logs
- Verifying configuration
- Reviewing resource limits

## ConfigMaps and Secrets

ConfigMaps store non-sensitive configuration values.

Secrets store sensitive information such as:

- Passwords
- API keys
- Certificates

Applications can consume these values through environment variables or mounted files.

## Rollbacks

Deployments maintain revision history.

If a new version causes failures, an application can be rolled back:

kubectl rollout undo deployment <deployment-name>

Rollback functionality allows teams to recover quickly from failed releases.