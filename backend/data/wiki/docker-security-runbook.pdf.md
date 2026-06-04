# docker-security-runbook.pdf

**Docker Security Runbook**
==========================

### Overview

This runbook defines baseline security controls for container images and runtime deployment to reduce supply chain risk, secret exposure, and privilege escalation inside containers.

### Key Requirements

* Use minimal base images such as `python:3.11-slim`, `node:20-alpine`, `distroless`, or approved golden images.
* Run containers as a non-root user with `readOnlyRootFilesystem=true` wherever the application permits it.
* Drop Linux capabilities by default and add only the specific capability required by the workload.

### Scanning and Remediation

* Pin package versions for production images and rebuild weekly for vulnerability patches.
* Do not copy sensitive files into an image layer.
* Run dependency and image scans in CI before publishing to the enterprise registry.

### Incident Response

* Revoke secrets immediately if found in an image, rotate downstream credentials, and quarantine the image tag.
* Capture container logs, image digest, deployment metadata, and registry audit events for investigation.
* Escalate suspected runtime compromise to Security Operations.

**Sources**
-----------

* `docker-security-runbook.pdf`
* `image-build-requirements.md`
