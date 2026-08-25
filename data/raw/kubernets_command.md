# Kubernetes Commands Reference

## kubectl Overview

kubectl is the command-line tool used to communicate with the Kubernetes API server.

Administrators and developers use kubectl to inspect resources, deploy applications, troubleshoot failures, and manage cluster state.


## Common Cluster Commands

List cluster nodes:

~~~bash
kubectl get nodes
~~~

Display cluster information:

~~~bash
kubectl cluster-info
~~~

View Kubernetes API resources:

~~~bash
kubectl api-resources
~~~


## Pod Management Commands

List all pods:

~~~bash
kubectl get pods
~~~

List pods in all namespaces:

~~~bash
kubectl get pods -A
~~~

Describe a pod:

~~~bash
kubectl describe pod <pod-name>
~~~

View pod logs:

~~~bash
kubectl logs <pod-name>
~~~

Follow live logs:

~~~bash
kubectl logs -f <pod-name>
~~~


## Deployment Commands

Create a deployment:

~~~bash
kubectl create deployment <name> --image=<image>
~~~

View deployments:

~~~bash
kubectl get deployments
~~~

Restart a deployment:

~~~bash
kubectl rollout restart deployment <deployment-name>
~~~

Check rollout status:

~~~bash
kubectl rollout status deployment <deployment-name>
~~~

Rollback a deployment:

~~~bash
kubectl rollout undo deployment <deployment-name>
~~~


## Configuration Inspection

View pod YAML configuration:

~~~bash
kubectl get pod <pod-name> -o yaml
~~~

View deployment YAML:

~~~bash
kubectl get deployment <deployment-name> -o yaml
~~~

Edit a resource:

~~~bash
kubectl edit deployment <deployment-name>
~~~


## Troubleshooting Commands

View recent events:

~~~bash
kubectl get events
~~~

View resource usage:

~~~bash
kubectl top pods
~~~

View container information:

~~~bash
kubectl describe container <container-name>
~~~

Common kubectl troubleshooting commands:

- kubectl get pods
- kubectl describe pod
- kubectl logs
- kubectl get events
- kubectl rollout restart
- kubectl rollout undo