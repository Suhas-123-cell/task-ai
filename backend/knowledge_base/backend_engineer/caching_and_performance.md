# Caching and Performance

Caching trades staleness risk for latency and throughput: instead of
recomputing an expensive result (a slow query, an external API call, a
heavy aggregation) on every request, a previously computed result is
stored somewhere cheaper to read from and reused until it is invalidated.
The core design questions for any cache are what to cache, where to put
it, and how to invalidate it -- and the third one is famously the hard
part ("there are only two hard things in computer science: cache
invalidation and naming things").

Cache placement forms a hierarchy by increasing latency and decreasing
cost per byte: in-process memory (fastest, but not shared across
processes or machines, and lost on restart), a shared in-memory store
like Redis or Memcached (shared across a fleet, survives individual
process restarts, adds a network hop), and a CDN or reverse-proxy cache
(closest to the end user, best for static or rarely-personalized
content).

Invalidation strategies include a time-to-live (TTL) expiry (simple,
bounded staleness, but can serve stale data until expiry or cause a
"thundering herd" of simultaneous cache misses when many keys expire
together), explicit invalidation on write (the write path deletes or
updates the relevant cache key, which keeps data fresher but couples the
write path to every place that caches derived data), and versioned/keyed
caching (e.g. keying a cache entry by a resource's updated_at timestamp
or a content hash, so a changed resource naturally produces a new,
distinct cache key and old entries simply age out unused).

Read-through and write-through/write-behind are common patterns: in a
read-through cache, the application always asks the cache first, and the
cache itself is responsible for fetching from the source of truth on a
miss; in write-through, every write goes to the cache and the backing
store together (simpler consistency, slower writes); in write-behind, the
write is acknowledged after hitting the cache and flushed to the backing
store asynchronously (faster writes, real risk of data loss on a crash
before the flush completes).

Beyond caching, general backend performance work follows a discipline:
measure before optimizing (profile to find the actual bottleneck rather
than guessing), understand whether the system is I/O-bound (waiting on
network/disk -- addressed with concurrency, connection pooling, batching)
or CPU-bound (addressed with algorithmic improvements, native
extensions, or horizontal scaling), and set explicit latency/throughput
budgets per component so a regression in one service is caught before it
silently degrades the whole request path.
