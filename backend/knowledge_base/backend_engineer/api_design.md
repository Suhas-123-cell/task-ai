# API Design and REST Principles

A well-designed API is a contract that hides implementation detail behind
a stable, predictable interface. REST (Representational State Transfer)
organizes that contract around resources (nouns, e.g. /candidates,
/interview-sessions) rather than actions (verbs), and uses HTTP methods to
express intent: GET retrieves a representation without side effects
(idempotent and safe), POST creates a new resource or triggers a
non-idempotent action, PUT replaces a resource entirely (idempotent),
PATCH applies a partial update, and DELETE removes a resource
(idempotent).

Idempotency matters operationally: a client (or a retrying proxy) can
safely resend a GET, PUT, or DELETE without changing the outcome beyond
the first successful call, which is essential for building reliable
systems on top of unreliable networks. POST is the one common verb that
is not idempotent by default, which is why operations like "submit an
answer" or "create a session" that must not be accidentally duplicated
need either natural idempotency keys or careful client-side handling.

Status codes should communicate outcome precisely rather than defaulting
everything to 200 or 500: 200 for a successful read, 201 for a successful
creation (with a Location header pointing at the new resource), 204 for a
successful action with no response body, 400 for a malformed or invalid
request (client error, the client should not simply retry unmodified),
401 for missing/invalid authentication, 403 for authenticated-but-not-
authorized, 404 for a resource that does not exist, 409 for a conflict
(e.g. submitting an answer to an already-completed session), 422 for a
request that is well-formed JSON but fails semantic validation, and 500
for an unexpected server-side failure.

Versioning (e.g. a /v1/ path prefix) protects existing clients from
breaking changes as an API evolves; additive changes (new optional
fields) generally do not require a new version, while removing or
renaming fields, or changing a field's type or meaning, does.

Pagination, filtering, and sorting are essential once a resource
collection can grow unbounded (e.g. listing all interview sessions for a
candidate) -- returning an entire table in one response does not scale
and creates unpredictable latency; cursor-based pagination in particular
avoids the "shifting page" problem that offset-based pagination has when
rows are being inserted concurrently.

Finally, a REST API's OpenAPI/Swagger schema is not just documentation --
generated automatically by frameworks like FastAPI from type-annotated
request/response models, it doubles as a contract test: if the code and
the schema drift, client code generated from the schema breaks
immediately and visibly, rather than silently misbehaving in production.
