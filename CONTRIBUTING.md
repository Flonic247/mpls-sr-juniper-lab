# Contributing

Thanks for helping. This lab is only useful if it stays accurate, so the rules are strict about evidence.

## Ground rules

1. **No invented data.** Do not add commands, IPs, labels or SIDs that did not come from a real lab. Label anything else *Inferred*, *Untested* or *Assumption*.
2. **`configs/as-captured/` is read-only history.** Fixes go in [configs/corrections.md](configs/corrections.md) with evidence and a separate corrected version.
3. **Captures are raw.** Add outputs to `verification/captured/` unedited, except for removing secrets. Say which Junos version and platform produced them.
4. **Junos set-format only** for configuration, one statement per line.
5. **Mermaid** for diagrams, so they diff cleanly.

## Before you open a pull request

- Remove passwords, hashes, SNMP communities, keys, usernames, company names and real public IPs. See [configs/SANITIZATION.md](configs/SANITIZATION.md).
- Run `python3 tools/audit.py` and `python3 tools/check_links.py`. The audit must not report a *new* ERROR or a secret.
- If you change a router configuration, update the matching stage file; the audit checks that the stage files add up to the as-captured file.
- Update [CHANGELOG.md](CHANGELOG.md).

## Most wanted

CE_01 and CE_02 outputs, end-to-end ping and traceroute between the hosts, `show bgp summary` on R1 and R6, R4's `mpls.0`, a captured primary-path failover, and EVE-NG sizing and interface-mapping details.

## Style

Short, direct English. Explain *why*, show the command, show the expected result, say what failure looks like. Be kind in reviews.
