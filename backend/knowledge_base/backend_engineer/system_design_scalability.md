# System Design and Scalability Fundamentals

Scaling a backend system means growing its capacity to serve more load
(requests, data, users) without a proportional degradation in latency or
reliability. The first fork in the road is vertical scaling (a bigger
machine: more CPU, RAM, faster disk) versus horizontal scaling (more
machines running the same service behind a load balancer). Vertical
scaling is simpler (no distributed-systems concerns) but hits a hard
ceiling and a single point of failure; horizontal scaling has no
practical ceiling and improves fault tolerance, but requires the service
to be stateless (or externalize its state) so any instance can handle any
request.

Externalizing state is the crux of making a service horizontally
scalable: session data, uploaded files, and application state must live
in a shared store (a database, Redis, object storage) rather than in an
individual server's memory or local disk, otherwise a client's second
request might land on a different instance than their first and find
none of their prior context.

A load balancer distributes incoming requests across instances using a
strategy such as round robin (simple, ignores instance load), least
connections (routes to the currently least-busy instance), or consistent
hashing (routes requests with the same key, e.g. a session ID, to the
same instance -- useful when some state genuinely cannot be externalized
cheaply, at the cost of uneven load if that key distribution is skewed).

As a single database becomes a bottleneck, common mitigations, roughly in
order of increasing complexity, are: adding read replicas (route read
traffic to replicas, keep writes on the primary -- introduces replication
lag, so reads-after-write consistency needs care), vertical scaling of
the database itself, caching hot reads in front of the database, and
finally sharding (partitioning data across multiple database instances by
some key, e.g. candidate_id) when a single primary can no longer hold or
serve the write volume at all -- sharding is powerful but adds real
complexity (cross-shard queries and transactions become hard), so it is
usually the last resort, not the first tool reached for.

Asynchronous processing via message queues (Kafka, RabbitMQ, SQS)
decouples a fast, synchronous request path from slow downstream work: an
API can accept a request, enqueue the heavy work, and return
immediately, while one or more worker processes consume the queue at
their own pace -- this improves perceived latency for the client and lets
the heavy-work capacity scale independently of the API's request rate,
at the cost of the system becoming eventually consistent for that
work rather than immediately consistent.
