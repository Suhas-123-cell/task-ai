# Concurrency, Async I/O, and Python's asyncio

Concurrency lets a program make progress on multiple tasks without
necessarily executing them literally at the same instant (which is
parallelism, a stronger and distinct property requiring multiple CPU
cores). A backend service almost always spends most of its time waiting:
on the database, on a downstream HTTP call, on disk. Concurrency exists
to keep the CPU busy with other useful work during that waiting instead
of blocking a whole thread or process on it.

Python's Global Interpreter Lock (GIL) means only one thread executes
Python bytecode at a time in the standard CPython interpreter, so
traditional multithreading in Python does not give CPU parallelism for
pure-Python code (it still helps for I/O-bound work, because a thread
blocked on I/O releases the GIL). This is a key reason async I/O
(asyncio, and frameworks built on it like FastAPI) became the dominant
pattern for high-concurrency Python web services: a single-threaded event
loop can juggle thousands of concurrent I/O-bound requests, because each
`await` point voluntarily yields control back to the event loop instead of
blocking the thread, at a fraction of the memory/scheduling overhead of
one OS thread per request.

The tradeoff is that async code requires the entire call chain from the
request handler down to the actual I/O call to be async-aware ("async
all the way down"); calling a blocking, synchronous library function
(e.g. an old synchronous database driver) from inside an async handler
stalls the entire event loop for every concurrent request, not just the
one making the call -- a subtle but severe failure mode that async
frameworks generally do not protect you from automatically.

For genuinely CPU-bound work (e.g. embedding generation, image
processing, heavy scoring logic), asyncio does not help, because there is
no I/O wait to overlap -- the fix is either running that work in a
separate process pool (via multiprocessing or a task queue like Celery/
RQ, sidestepping the GIL by using separate interpreter processes) or
offloading it to a natively-compiled library that releases the GIL
internally during its computation (as NumPy and PyTorch do). Choosing
between "make this endpoint async" and "make this endpoint call a
background worker" is really a question of whether the work is I/O-bound
(async) or CPU-bound/long-running (background job with a status the
client can poll).
