# Kubernetes Networking Reference

## Kubernetes Service Discovery

Kubernetes provides internal service discovery to allow applications to communicate using service names instead of fixed IP addresses.

Each service receives a stable DNS name.

Example:

~~~text
database-service.default.svc.cluster.local
~~~

Applications can use this DNS name to connect to other services inside the cluster.


## Service Types

Kubernetes supports different service types for exposing applications.


## ClusterIP

ClusterIP exposes a service internally inside the Kubernetes cluster.

Example:

~~~yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP
~~~

Common use cases:

- Internal microservice communication
- Backend APIs
- Database access


## NodePort

NodePort exposes a service through a port on every cluster node.

Example:

~~~yaml
spec:
  type: NodePort
~~~

Common use cases:

- Development environments
- Testing external access


## LoadBalancer

LoadBalancer creates an external load balancer through the cloud provider.

Example:

~~~yaml
spec:
  type: LoadBalancer
~~~

Common use cases:

- Public applications
- Production services


# Kubernetes Network Policies

Network policies control communication between pods.

They define:

- Which pods can communicate
- Which ports are allowed
- Which traffic is blocked


Example:

~~~yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api
~~~

Network policy problems can cause:

- Connection refused errors
- Timeout errors
- Services unable to communicate


# DNS Troubleshooting

Kubernetes uses CoreDNS for service name resolution.

Common DNS problems:

- Service name cannot be resolved
- CoreDNS pods are unhealthy
- Incorrect namespace references


Check CoreDNS:

~~~bash
kubectl get pods -n kube-system
~~~

Check DNS configuration:

~~~bash
kubectl describe service <service-name>
~~~


# Common Kubernetes Networking Errors

## Connection Refused

Connection refused occurs when a service is reachable but no application is accepting connections.

Possible causes:

- Application is not running
- Wrong service port
- Incorrect container configuration


## Connection Timeout

Connection timeout occurs when a request does not receive a response within the expected time.

Possible causes:

- Network policies blocking traffic
- Firewall restrictions
- Application overload


## DNS Resolution Failure

DNS failures occur when applications cannot resolve service names.

Common errors:

- NXDOMAIN
- SERVFAIL
- DNS lookup timeout


# Troubleshooting Commands

Check services:

~~~bash
kubectl get services
~~~

Check endpoints:

~~~bash
kubectl get endpoints
~~~

Test DNS inside a pod:

~~~bash
nslookup <service-name>
~~~

Test network connectivity:

~~~bash
curl http://<service-name>:<port>
~~~