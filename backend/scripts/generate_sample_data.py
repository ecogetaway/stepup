from __future__ import annotations

from pathlib import Path
import sys

from fpdf import FPDF

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import settings

SOP_DIR = settings.SOP_DIR


SOP_DOCUMENTS = {
    "kafka-deploy-sop.pdf": {
        "title": "Kafka Consumer and Producer Deployment SOP",
        "sections": [
            (
                "Purpose and Scope",
                [
                    "This SOP covers deployment of Kafka consumers and producers for enterprise event streaming workloads.",
                    "It applies to services running in Kubernetes namespaces owned by the Platform Engineering team.",
                    "The procedure assumes a managed Kafka cluster, TLS enabled brokers, and CI/CD delivery through GitOps.",
                    "Teams must complete peer review and change approval before deploying to production topics.",
                ],
            ),
            (
                "Prerequisites",
                [
                    "Confirm topic ownership, retention policy, partition count, replication factor, and consumer group naming.",
                    "Create service credentials in the secrets manager and grant read or write ACLs for the exact topic prefix.",
                    "Validate bootstrap server DNS, schema registry URL, and client truststore configuration in staging.",
                    "Set resource requests for CPU and memory before enabling autoscaling in production.",
                ],
            ),
            (
                "Consumer Deployment Steps",
                [
                    "Package the consumer image with a pinned client library version and immutable image tag.",
                    "Configure bootstrap.servers, group.id, security.protocol=SASL_SSL, sasl.mechanism=SCRAM-SHA-512, and client.id.",
                    "Set enable.auto.commit=false for services that need exactly-once processing or downstream idempotency.",
                    "Deploy to staging first and verify lag with kafka-consumer-groups before promoting to production.",
                    "Roll out production with maxUnavailable=0 and watch consumer lag, rebalance count, and processing latency.",
                ],
            ),
            (
                "Producer Deployment Steps",
                [
                    "Enable acks=all, retries=10, linger.ms=20, compression.type=zstd, and idempotence for critical producers.",
                    "Register schemas before production release and verify compatibility mode with the data governance team.",
                    "Run a smoke test that publishes a canary event and confirms downstream consumption in the audit topic.",
                    "If message size exceeds the approved limit, redesign the payload or move binary content to object storage.",
                ],
            ),
            (
                "Monitoring and Rollback",
                [
                    "Dashboards must show consumer lag, broker error rate, producer request latency, and failed deserializations.",
                    "Alert when consumer lag exceeds 10000 messages for five minutes or when error rate exceeds 2 percent.",
                    "Rollback by reverting the GitOps manifest and confirming the previous image drains without duplicate processing.",
                    "For P1 data loss risks, pause the consumer group, preserve offsets, and escalate to the Kafka operations channel.",
                ],
            ),
        ],
    },
    "docker-security-runbook.pdf": {
        "title": "Docker and Container Security Runbook",
        "sections": [
            (
                "Objective",
                [
                    "This runbook defines baseline security controls for container images and runtime deployment.",
                    "It is mandatory for production workloads running on shared Kubernetes clusters.",
                    "The goal is to reduce supply chain risk, secret exposure, and privilege escalation inside containers.",
                ],
            ),
            (
                "Image Build Requirements",
                [
                    "Use minimal base images such as python:3.11-slim, node:20-alpine, distroless, or approved golden images.",
                    "Pin package versions for production images and rebuild weekly for vulnerability patches.",
                    "Do not copy .env files, SSH keys, cloud credentials, or local kubeconfig into an image layer.",
                    "Run dependency and image scans in CI before publishing to the enterprise registry.",
                ],
            ),
            (
                "Runtime Security",
                [
                    "Run containers as a non-root user and set readOnlyRootFilesystem=true wherever the application permits it.",
                    "Drop Linux capabilities by default and add only the specific capability required by the workload.",
                    "Use Kubernetes secrets or an external secrets operator instead of environment variables for high-risk tokens.",
                    "Set CPU and memory limits to prevent noisy neighbor incidents and accidental denial of service.",
                ],
            ),
            (
                "Scanning and Remediation",
                [
                    "Critical vulnerabilities must be remediated before production unless a time-bound exception is approved.",
                    "High vulnerabilities require a remediation plan within seven business days.",
                    "False positives must include scanner evidence, package path, exploitability rationale, and security approval.",
                    "Images with unresolved critical findings are blocked by the admission controller.",
                ],
            ),
            (
                "Incident Response",
                [
                    "If a secret is found in an image, revoke the secret immediately and rotate all downstream credentials.",
                    "Quarantine the image tag, identify deployments using the digest, and roll forward to a clean build.",
                    "Capture container logs, image digest, deployment metadata, and registry audit events for investigation.",
                    "For suspected runtime compromise, cordon the node and escalate to Security Operations.",
                ],
            ),
        ],
    },
    "vpn-remote-access-sop.pdf": {
        "title": "VPN Remote Access Setup SOP",
        "sections": [
            (
                "Purpose",
                [
                    "This SOP explains how employees and contractors request, configure, and troubleshoot VPN remote access.",
                    "VPN access is required for internal tools that are not exposed through zero-trust web gateways.",
                    "Access is reviewed quarterly and removed automatically when the identity provider account is disabled.",
                ],
            ),
            (
                "Access Request",
                [
                    "Submit an access request in the IT service portal with business justification, manager approval, and expiry date.",
                    "Select the least-privilege access group for the required environment: corporate, staging, production, or vendor.",
                    "Production VPN access requires approval from both the application owner and Security Operations.",
                    "The user must have MFA enabled before the VPN profile can be issued.",
                ],
            ),
            (
                "Client Setup",
                [
                    "Install the approved VPN client from the internal software catalog, not from an external download site.",
                    "Import the SSL profile provided by IT and verify the certificate fingerprint against the service portal record.",
                    "Authenticate with corporate SSO and approve the MFA push notification from a trusted device.",
                    "Confirm that split tunneling policy matches the assigned group before accessing internal resources.",
                ],
            ),
            (
                "SSL Certificates",
                [
                    "Device certificates are valid for one year and are rotated automatically by the endpoint management agent.",
                    "If certificate enrollment fails, verify device compliance, system time, and the root CA trust chain.",
                    "Never export or share a VPN device certificate; report suspected compromise to IT Security immediately.",
                    "Expired certificates require re-enrollment through the managed device portal.",
                ],
            ),
            (
                "Troubleshooting",
                [
                    "For authentication failures, confirm password status, MFA enrollment, and group membership in the identity provider.",
                    "For DNS failures, disconnect and reconnect the client to refresh internal DNS search domains.",
                    "For slow connections, compare latency to the nearest gateway and check whether media traffic is using the tunnel.",
                    "For repeated disconnects, collect client logs, gateway region, operating system version, and timestamped error codes.",
                ],
            ),
        ],
    },
}


class SOPPdf(FPDF):
    def header(self) -> None:
        self.set_font("Arial", "B", 10)
        self.set_text_color(79, 70, 229)
        self.cell(0, 8, "Enterprise Knowledge Copilot Sample SOP", border=0, ln=1)
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(107, 114, 128)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def add_section(pdf: SOPPdf, heading: str, bullets: list[str]) -> None:
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(17, 24, 39)
    pdf.multi_cell(0, 8, heading)
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(55, 65, 81)

    for bullet in bullets:
        pdf.multi_cell(0, 6, f"- {bullet}")
    pdf.ln(3)


def write_pdf(filename: str, title: str, sections: list[tuple[str, list[str]]]) -> Path:
    pdf = SOPPdf()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(17, 24, 39)
    pdf.multi_cell(0, 10, title)
    pdf.ln(4)

    for index, (heading, bullets) in enumerate(sections):
        if index in {2, 4}:
            pdf.add_page()
        add_section(pdf, heading, bullets)

    output_path = SOP_DIR / filename
    pdf.output(str(output_path))
    return output_path


def main() -> None:
    SOP_DIR.mkdir(parents=True, exist_ok=True)
    written_paths = [
        write_pdf(filename, document["title"], document["sections"])
        for filename, document in SOP_DOCUMENTS.items()
    ]

    print("Generated SOP PDFs:")
    for path in written_paths:
        print(f"- {path}")


if __name__ == "__main__":
    main()
