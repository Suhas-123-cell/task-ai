# Backend Security Fundamentals

Authentication answers "who are you"; authorization answers "what are
you allowed to do." Conflating the two is a common source of security
bugs -- a system can correctly authenticate a user via a valid token and
still need a separate, explicit check that this particular user is
allowed to perform this particular action on this particular resource
(e.g. a candidate should not be able to fetch another candidate's
interview report just because they are authenticated).

JSON Web Tokens (JWTs) are a common stateless authentication mechanism: a
signed token encodes claims (user id, roles, expiry) that the server can
verify without a database lookup, by checking the signature against a
secret or public key. The tradeoff versus server-side session storage is
that a JWT cannot be easily revoked before its expiry (since the server
does not track which tokens it has issued), so short expiry times plus a
refresh-token mechanism are standard practice, and secrets used to sign
tokens must never be hardcoded or committed to source control -- they
belong in environment variables or a secrets manager.

Input validation is the first line of defense against injection attacks.
SQL injection arises from building queries via raw string
concatenation of user input; parameterized queries (or an ORM like
SQLAlchemy, used in this project) prevent it structurally, by always
sending user data as bound parameters rather than as part of the SQL
text, so user input can never be interpreted as SQL syntax. The same
principle -- never directly interpolate untrusted input into a command
that will be interpreted -- applies to shell command construction, HTML
rendering (cross-site scripting, or XSS), and NoSQL query construction.

CORS (Cross-Origin Resource Sharing) is a browser-enforced mechanism that
restricts which origins (scheme + host + port) a web page's JavaScript
may make requests to; a backend must explicitly allow the frontend's
origin (via an Access-Control-Allow-Origin response header) for the
browser to permit the response to be read by the calling page's script --
this is a browser-side protection, not a server-side security boundary,
so a permissive or wildcard CORS policy does not, by itself, expose data
that proper authentication/authorization would otherwise protect, but a
missing or overly broad CORS policy is still routinely flagged in
security reviews because it is easy to misconfigure and easy to verify.

Rate limiting and request size limits protect against both malicious
abuse and accidental self-inflicted overload (e.g. a buggy client
retrying in a tight loop), and should be applied at the edge (a reverse
proxy or API gateway) so that abusive traffic is rejected before it
consumes application-server or database resources.
