from rag.embedding.service import EmbeddingService
import numpy as np

service = EmbeddingService()


text = "Kubernetes pods run containers"

a = "Kubernetes pods contain containers"

b = "Pods are Kubernetes units that run containers"

c = "The restaurant serves Italian food"

vector1 = service.embed_text(a)
vector2 = service.embed_text(b)
vector3 = service.embed_text(c)


print(service.info)
print(vector1[:5])
print(vector2[:5])
print(vector3[:5])

print ("sim a and b",np.array(vector1) @ np.array(vector2))
print ("sim a and b",np.array(vector1) @ np.array(vector3))


