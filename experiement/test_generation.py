from rag.generation.context_builder import ContextBuilder
from rag.generation.prompt import PromptBuilder
from rag.generation.generator import GeminiGenerationService
from rag.reranking.model import RerankedChunk

# use one of your real/synthetic RerankedChunk objects here

chunks = [
    RerankedChunk(
        chunk_id="f09d9ae5e752a0bf96b15dee70a98e8e18ca4cbf2f057be99713fe04365db798",
        text="""A liveness probe checks whether the application is still running correctly.

If the probe fails repeatedly, Kubernetes restarts the container.

Example:

~~~yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
~~~""",
        metadata={
            "source": r"data\raw\kubernets_configuration.md",
            "heading": "Liveness Probe",
            "heading_level": 2,
            "heading_path": ["Health Probes", "Liveness Probe"],
        },
        retrieval_score=0.60637033,
        retrieval_rank=7,
        reranker_score=3.7575929164886475,
        reranked_rank=1,
        final_score=3.7575929164886475,
        final_rank=1,
    ),

    RerankedChunk(
        chunk_id="e4bf708ad92740f593f7ca988394da16bad8b8ce07fa22759864d9c5a83d5943",
        text="""restartPolicy defines how Kubernetes handles container failures.

Available values:""",
        metadata={
            "source": r"data\raw\kubernets_configuration.md",
            "heading": "restartPolicy",
            "heading_level": 1,
            "heading_path": ["restartPolicy"],
        },
        retrieval_score=0.6652976,
        retrieval_rank=4,
        reranker_score=3.615353584289551,
        reranked_rank=2,
        final_score=3.615353584289551,
        final_rank=2,
    ),

    RerankedChunk(
        chunk_id="8e40ab883812e123a7a4278b61c825e6a2b8fc5148940009cfb031321783e3ba",
        text="""CrashLoopBackOff occurs when a Kubernetes container repeatedly starts and then exits unsuccessfully.

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
- Application logs contain startup errors""",
        metadata={
            "source": r"data\raw\kubernets_error.md",
            "heading": "CrashLoopBackOff",
            "heading_level": 2,
            "heading_path": [
                "Kubernetes Error Reference",
                "CrashLoopBackOff",
            ],
        },
        retrieval_score=0.5683365,
        retrieval_rank=9,
        reranker_score=2.693587303161621,
        reranked_rank=3,
        final_score=2.693587303161621,
        final_rank=3,
    ),

    RerankedChunk(
        chunk_id="89a27ac881f091b5b7dfbb7122d4398ac07eaa483433767784755bdda466376a",
        text="""Deployments manage the lifecycle of application Pods.

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

kubectl rollout status deployment <deployment-name>""",
        metadata={
            "source": r"data\raw\kubernetes.md",
            "heading": "Deployments",
            "heading_level": 2,
            "heading_path": [
                "Kubernetes Operations Guide",
                "Deployments",
            ],
        },
        retrieval_score=0.71166396,
        retrieval_rank=1,
        reranker_score=2.6440720558166504,
        reranked_rank=4,
        final_score=2.6440720558166504,
        final_rank=4,
    ),

    RerankedChunk(
        chunk_id="3b44298f10a047f2aec0cf432a9d4fb257181058d07adf47dd07f3839d5c30db",
        text="""Create a deployment:

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
~~~""",
        metadata={
            "source": r"data\raw\kubernets_command.md",
            "heading": "Deployment Commands",
            "heading_level": 2,
            "heading_path": [
                "Kubernetes Commands Reference",
                "Deployment Commands",
            ],
        },
        retrieval_score=0.6656511,
        retrieval_rank=3,
        reranker_score=2.003678321838379,
        reranked_rank=5,
        final_score=2.003678321838379,
        final_rank=5,
    ),
]

context = ContextBuilder().build(chunks)

prompt = PromptBuilder().build(
    question="What command restarts a Kubernetes deployment?",
    context=context,
)

generator = GeminiGenerationService()

result = generator.generate(prompt)

print("=" * 60)
print("ANSWER")
print("=" * 60)
print(result.text)

print()
print("MODEL:", result.model)
print("INPUT TOKENS:", result.input_tokens)
print("OUTPUT TOKENS:", result.output_tokens)
print("TOTAL TOKENS:", result.total_tokens)
print("LATENCY MS:", round(result.latency_ms, 2))