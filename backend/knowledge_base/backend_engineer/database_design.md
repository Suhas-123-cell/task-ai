# Database Design and Data Modeling

Good schema design starts from the entities and relationships the domain
actually has, then normalizes to eliminate redundant, update-inconsistent
data. First normal form requires atomic column values (no comma-separated
lists in a single cell); second normal form eliminates partial
dependencies on a composite key; third normal form eliminates transitive
dependencies (a non-key column depending on another non-key column rather
than directly on the primary key). In practice, most OLTP schemas target
third normal form and then deliberately denormalize specific hot paths
once profiling shows a real need, rather than denormalizing speculatively.

Primary keys uniquely identify a row; foreign keys enforce referential
integrity, ensuring a child row cannot reference a parent that does not
exist, and ON DELETE CASCADE/RESTRICT/SET NULL policies determine what
happens to dependents when a parent is removed. Indexes speed up lookups
and joins on the indexed column(s) at the cost of slower writes (every
insert/update must also update the index) and additional storage --
a classic space/write-time-versus-read-time tradeoff, so indexes should be
added deliberately based on actual query patterns, not defensively on
every column.

Transactions bundle multiple statements into a single atomic unit,
guaranteeing the ACID properties: Atomicity (all statements succeed or
none do), Consistency (the database moves between valid states),
Isolation (concurrent transactions do not observe each other's
intermediate state, to a degree controlled by the isolation level), and
Durability (once committed, the result survives a crash). Isolation
levels (read uncommitted, read committed, repeatable read, serializable)
trade consistency guarantees against concurrency/throughput; most web
applications default to read committed and only reach for stricter
levels around specific invariants (e.g. preventing double-spend logic in
a payments table).

Choosing between SQL and NoSQL is a modeling decision, not a
popularity contest: relational databases enforce a schema and strong
consistency and excel when data has many relationships that must stay
consistent (e.g. this project's Candidate -> InterviewSession -> Question
-> Answer chain, where referential integrity matters for traceability);
document/key-value stores trade schema flexibility and horizontal
scalability for weaker consistency guarantees and are well suited to
high-volume, loosely-structured, or rapidly-evolving data. A vector
database (used elsewhere in this system for RAG retrieval) is a further
specialization: optimized specifically for approximate nearest-neighbor
search over high-dimensional embeddings, a workload relational indexes
are not built for.
