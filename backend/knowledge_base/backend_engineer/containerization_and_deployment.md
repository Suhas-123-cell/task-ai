# Containerization, Orchestration, and Deployment Pipelines

Containers package an application together with its exact runtime
dependencies (libraries, system packages, a pinned interpreter version)
into a single portable image, so "it works on my machine" stops being a
meaningful excuse: the same image runs identically in development, CI,
and production, because the container's filesystem and dependency
versions are fixed at build time rather than assembled fresh on each
target machine. Docker is the dominant tool for building (via a
Dockerfile, a declarative recipe of base image plus install/copy/build
steps) and running these images. A key practice is keeping images small
and layers cache-friendly: ordering Dockerfile steps so slowly-changing
layers (installing dependencies) come before frequently-changing layers
(copying application code) means a code-only change only rebuilds the
last layer, not the whole dependency install, dramatically speeding up
iterative builds.

A single container is easy to run, but a real production system needs
many containers (multiple replicas of a service, plus databases, caches,
and message queues) scheduled across many machines, restarted
automatically when they crash, and given a stable way to find each other
over the network -- this is what a container orchestrator like Kubernetes
provides. Kubernetes' core unit is the Pod (one or more tightly-coupled
containers scheduled together); a Deployment manages a desired number of
Pod replicas and handles rolling updates (replacing old Pods with new
ones a few at a time, so the service stays available throughout a
release); a Service gives a stable network identity/DNS name in front of
a Deployment's Pods, which come and go and get new IP addresses as they
are rescheduled. Kubernetes continuously reconciles observed state
against this declared desired state -- if a Pod crashes, the Deployment
controller notices the replica count has dropped below desired and
schedules a replacement, without a human needing to intervene.

CI/CD tooling (GitHub Actions, Jenkins, GitLab CI) automates the path
from a code change to a running container: a workflow triggered on push
or pull request typically runs linting and the test suite, then -- if
those pass -- builds a container image, tags it (often with the git
commit SHA, so every deployed image is traceable back to an exact
commit), pushes it to an image registry, and triggers a deployment
(updating the Kubernetes Deployment's image tag, or calling a platform
API for simpler setups). Secrets required during this pipeline (a
registry password, a cloud deployment credential) must be stored in the
CI platform's encrypted secrets store, never committed to the workflow
file or the repository itself, since a git history is effectively
permanent and public repository history is world-readable.

A minimal but effective production deployment checklist mirrors this
same chain end to end: a passing test suite gates the merge, the merge
gates an image build tagged to that exact commit, and the running
container's health check (an endpoint like this project's /api/health)
gates whether the orchestrator considers a new replica ready to receive
traffic -- so a broken deployment is caught by failing health checks and
automatically rolled back or held, rather than silently serving errors
to real users.
