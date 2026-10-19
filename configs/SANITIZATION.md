# Sanitisation record

The files in `as-captured/` are the lab configurations exactly as exported (`show configuration | display set`), with only the following changes. Everything else, including typos, is preserved on purpose. Known problems are documented in [corrections.md](corrections.md), never silently fixed.

| Removed or replaced | Why | Applies to |
|---|---|---|
| `set system root-authentication encrypted-password "..."` (line removed) | Credential hash | All 8 devices |
| `set interfaces fxp0 unit 0 family inet dhcp vendor-id Juniper-vmx-VM...` becomes `set interfaces fxp0 unit 0 family inet dhcp` | VM-specific identifier | All 8 devices |
| `set interfaces fxp0 unit 0 family inet6 dhcpv6-client vendor-id Juniper:vmx:VM...` (line removed) | VM-specific identifier | All 8 devices |
| Line `Router# run show configuration \| display set` (CLI prompt echo) | Not configuration | CE_02 |

Not present in the source material, so nothing to remove: SNMP communities, API keys, TACACS/RADIUS secrets, usernames other than `root`, company names, and public addresses other than `203.0.113.0/24` (RFC 5737 documentation range).

Not changed but worth knowing: `set system processes dhcp-service traceoptions ...` is lab debug logging with no function in this design. `fxp0` is the out-of-band management port and is not part of the lab topology.

**If you publish your own fork:** re-run [tools/audit.py](../tools/audit.py); its `Secrets` check fails if a password hash or a VM identifier reappears in `as-captured/`.
