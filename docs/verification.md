# Verification guide

How to read this page: **Captured** means the output exists in [verification/captured](../verification/captured/) from the author's lab. **Expected, not captured** means the result follows from the configuration but no output was supplied, so check it yourself.

## Command validity on Junos 25.2R1.9 (vMX)

| Command | Status |
|---|---|
| `show isis adjacency`, `show isis database extensive`, `show route`, `show route table inet.3`, `show route protocol isis`, `show mpls interface`, `show bfd session`, `show bgp summary`, `show spring-traffic-engineering lsp`, `show interfaces terse`, `show route <prefix> detail` | Accepted (used in the captures) |
| `show mpls forwarding-table` | **Rejected** (`syntax error, expecting <command>` on R1) |
| `show source-packet-routing` | **Rejected** (same). Use `show spring-traffic-engineering lsp` |
| `show route pro` | Ambiguous; spell out `show route protocol isis` |
| `traceroute 10.10.9.1 routing-instance CUSTOMER_A no-resolve` | Accepted (captured after release 1.1.0) |
| `show route forwarding-table table CUSTOMER_A destination <ip> extensive` | Author's command, **no output captured** |

## Stage by stage

### Stage 1 and 2: base interfaces and IS-IS

| Command | Expected | If not |
|---|---|---|
| `show interfaces terse` | Core `ge-0/0/x.0` interfaces `up up` with `inet`, `iso`, `mpls` | Wrong interface, missing family |
| `show isis adjacency` | All core neighbours `L 2`, `Up`. R3 shows Router4, Router5, Router1; R6 shows Router5, Router4 (captured) | Check `family iso`, `level 1 disable`, `point-to-point` on both ends |
| `show route protocol isis` | Loopbacks 10.0.0.1 to 10.0.0.6 and all /30s in `inet.0` (captured on R2, R5, R6) | Adjacency missing, or IS-IS not on `lo0.0` |

### Stage 3: MPLS

| Command | Expected | If not |
|---|---|---|
| `show mpls interface` | All core interfaces `Up` (R3: ge-0/0/0 to ge-0/0/2; R5: ge-0/0/0 and ge-0/0/2; captured) | Add `family mpls` and `protocols mpls interface` |

### Stage 4: Segment Routing

| Command | Expected | If not |
|---|---|---|
| `show isis database extensive \| match SID` | SRGB `SID-Label: 800000`, `Range: 20000` from each router; `Node SID ... Value: N` for routers 1 to 6 (captured on R1) | Missing `source-packet-routing`, SRGB mismatch |
| `show route table inet.3` | A labelled route to each remote loopback, for example on R5 `10.0.0.6/32 ... Push 0` via R6 (captured) | `family mpls` missing, SID not advertised |
| `show route table mpls.0` | `800001` to `800006` swap entries; local adjacency labels 16 to 18 (captured) | Label does not equal SRGB base plus index |

### Stage 5: L3VPN

| Command | Expected | If not |
|---|---|---|
| `show bgp summary` on R1 and R6 | iBGP neighbour established (expected, not captured). On P routers: `BGP is not running` (captured on R3) | Loopback reachability, `local-address`, family |
| `show route table bgp.l3vpn.0` | R1 holds `10.0.0.6:65000:203.0.113.0/24` and `...:10.10.9.0/30`; R6 holds the `10.0.0.1:65000` routes (captured) | RT mismatch, session down |
| `show route table CUSTOMER_A.inet.0` | Customer prefixes both ways; R1 `203.0.113.0/24` from 10.0.0.6; R6 `10.64.99.0/24` from 10.0.0.1 (captured) | Import policy, `as-override`, PE-CE session |
| `show route 10.64.99.0/24` on R6 | BGP from 10.0.0.1, `AS path: 65100 I`, `Push 16, Push 800001(top)` (captured) | See matrix |

### Stage 6: SR-TE

| Command | Expected | If not |
|---|---|---|
| `show spring-traffic-engineering lsp` | `10.0.0.6  Up  R1_TO_R6_SRTE` (captured) | Segment list invalid, label outside SRGB |
| `show route table inet.3 10.0.0.6` | `SPRING-TE/8` active, ahead of `L-ISIS/14`; stack `Push 800006, Push 800004(top)` via 10.10.2.2 (captured) | See matrix |
| `show route 203.0.113.0/24 detail` | `VPN Label: 16`; primary `10.10.2.2` with `weight 0x1, selected`, secondary `10.10.3.2` with `weight 0xff` (captured) | Policy not resolving |
| `traceroute 10.10.9.1 routing-instance CUSTOMER_A no-resolve` | Hops 10.10.2.2 (R2), 10.10.4.2 (R4), 10.10.9.2 (R6 VRF interface), 10.10.9.1 (CE_02), with label stacks quoted at R2 and R4 (captured after release 1.1.0). R3 and R5 do not appear | Transit hops missing: see [C6](../configs/corrections.md) |

### Protection

| Command | Expected |
|---|---|
| `show bfd session` | Every core link `Up`, `Detect Time 3.000`, multiplier 3 (captured on R2 to R6) |

## After the release 1.1.0 changes (R1)

| Command | Expected | Captured |
|---|---|---|
| `show isis database extensive \| match "Area address"` | `49.0001 (3)` on every LSP, no `49 (1)` | Yes |
| `show route 10.0.0.6` | IS-IS next hop `10.10.3.2` only; `inet.3` still `SPRING-TE/8` active via `10.10.2.2` | Yes |
| `traceroute 10.10.9.1 routing-instance CUSTOMER_A no-resolve` | Hops R2 (10.10.2.2), R4 (10.10.4.2), then R6 and CE_02; not R3 | Yes |

Raw output: [R1-after-fixes.txt](../verification/captured/R1-after-fixes.txt).

## End to end from the hosts (VPCS)

Captured in [hosts.txt](../verification/captured/hosts.txt). The final line of each trace (`ICMP type:3, code:3, Destination port unreachable`) is the destination host answering, which is how VPCS ends a trace: it means the trace **arrived**.

| From | To | Hops (captured) | Reading |
|---|---|---|---|
| Host behind CE_01 | 203.0.113.10 | CE_01 LAN (10.64.99.1), R1 (10.10.1.2), R2 (10.10.2.2), R4 (10.10.4.2), R6 (10.10.9.2), CE_02 (10.10.9.1), host | Forward path follows the SR-TE primary R1, R2, R4, R6 |
| Host behind CE_02 | 10.64.99.10 | CE_02 LAN (203.0.113.1), R6 (10.10.9.2), R4 (10.10.6.1), R2 (10.10.4.1), R1 (10.10.1.2), CE_01 (10.10.1.1), host | Return path is plain SR/IGP forwarding (no SR-TE on R6) |

Replies come from the interface the probe arrived on, which is why R2 appears as 10.10.2.2 in one direction and 10.10.4.1 in the other. R6 replies from its VRF interface (10.10.9.2) in both directions.

## Quick health check (30 seconds)

```
show isis adjacency
show spring-traffic-engineering lsp
show route table inet.3 10.0.0.6
show route table CUSTOMER_A.inet.0
show bfd session
```

All adjacencies and sessions up, the LSP `Up`, `SPRING-TE` active for `10.0.0.6/32`, and customer prefixes from the remote site in the VRF.

## Automated checks

`python3 tools/audit.py` checks the **configuration** for consistency. It does not log in to devices. Results: [consistency-audit.md](consistency-audit.md).
