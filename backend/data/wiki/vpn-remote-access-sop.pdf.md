# vpn-remote-access-sop.pdf

**VPN Remote Access Setup SOP**
=====================================

### Purpose

This Standard Operating Procedure (SOP) explains how employees and contractors request, configure, and troubleshoot VPN remote access.

### Key Steps

* **Access Request**: Submit a request in the IT service portal with business justification, manager approval, and identity provider account status.
* **Client Setup**: Install the approved VPN client from the internal software catalog, import the SSL profile, authenticate with corporate SSO, and verify certificate fingerprint.
* **SSL Certificates**: Obtain device certificates with business justification, manager approval, and expiry date; select the least-privilege access group for the required environment.

### Troubleshooting

* Identify authentication failures by checking password status, MFA enrollment, and group membership in the identity provider.
* Resolve DNS failures by disconnecting and reconnecting the client to refresh internal DNS search domains.
* Address slow connections by comparing latency to the nearest gateway and checking media traffic usage through the tunnel.

### Important Reminders

* Never export or share a VPN device certificate; report suspected compromise to IT Security immediately.
* Expired certificates require re-enrollment through the managed device portal.

**Sources**

* vpn-remote-access-sop.pdf
* [IT Service Portal Documentation](link to IT service portal documentation)
* [Endpoint Management Agent Configuration Guide](link to endpoint management agent configuration guide)
