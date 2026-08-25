# Kubernetes Error Reference

## CrashLoopBackOff

CrashLoopBackOff occurs when a Kubernetes container repeatedly starts and then exits unsuccessfully.

Kubernetes increases the delay between restart attempts to prevent a failing application from continuously consuming resources.

Common causes:

- Application crashes during startup
- Missing environment variables
- Invalid application configuration
- Missing dependencies
- Incorrect container commands
- Failed connections to external services

Troubleshooting steps:

Check running pods:

~~~bash
kubectl get pods
~~~

Inspect pod details:

~~~bash
kubectl describe pod <pod-name>
~~~

View application logs:

~~~bash
kubectl logs <pod-name>
~~~

Common indicators:

- Container restart count continuously increases
- Pod status shows CrashLoopBackOff
- Application logs contain startup errors


## ImagePullBackOff

ImagePullBackOff occurs when Kubernetes cannot download the container image required to start a pod.

Common causes:

- Incorrect image name
- Missing container registry credentials
- Private registry authentication failure
- Image tag does not exist
- Network connectivity issues with the registry

Troubleshooting steps:

Inspect pod events:

~~~bash
kubectl describe pod <pod-name>
~~~

Check the configured image:

~~~yaml
image: example/application:v1
~~~

Verify image availability:

~~~bash
docker pull example/application:v1
~~~

Common errors:

- ErrImagePull
- ImagePullBackOff
- Unauthorized image access


## OOMKilled

OOMKilled means a container was terminated because it exceeded its configured memory limit.

OOM stands for Out Of Memory.

Common causes:

- Memory leak inside the application
- Incorrect memory limits
- Large data processing operations
- Unexpected traffic increases

Check container status:

~~~bash
kubectl describe pod <pod-name>
~~~

Look for:

~~~text
Reason: OOMKilled
~~~

Possible solutions:

- Increase memory limits
- Optimize application memory usage
- Investigate memory leaks
- Reduce workload size


## Kubernetes Pod Troubleshooting Summary

When a pod fails:

1. Check pod status:

~~~bash
kubectl get pods
~~~

2. Inspect events:

~~~bash
kubectl describe pod <pod-name>
~~~

3. Review logs:

~~~bash
kubectl logs <pod-name>
~~~

4. Check resource usage:

~~~bash
kubectl top pod <pod-name>
~~~

Common Kubernetes failure identifiers:

- CrashLoopBackOff
- ImagePullBackOff
- OOMKilled
- ErrImagePull
- ContainerCreating