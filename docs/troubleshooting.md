# Troubleshooting

Commands are standard Junos for this platform. The ones marked * have not been run in this lab. Section "Seen in this lab" lists problems that are real in the captured material.

## Matrix

| Symptom | Possible cause | Verification | Corrective action |
|---|---|---|---|
| IS-IS adjacency down | `family iso` missing; interface not under `protocols isis`; `level 1 disable` or `point-to-point` on one side only; wrong interface or IP | `show isis adjacency`; `show interfaces terse`; `show isis interface` | Fix the family or interface on **both** ends; match level and point-to-point settings |
| MPLS labels missing / no labelled route | `family mpls` or `protocols mpls interface` missing on a link; SR not enabled | `show mpls interface`; `show route table inet.3`; `show route table mpls.0` | Add both statements on both ends of the link |
| Node-SID missing | `node-segment ipv4-index` absent; IS-IS not enabled on `lo0.0`; `wide-metrics-only` missing | `show isis database extensive \| match SID` | Configure the index; enable IS-IS on `lo0.0` |
| Incorrect SRGB | Different `start-label` or `index-range` on a router; index outside range | Compare `SID-Label:` and `Range:` in `show isis database extensive` | Make SRGB identical on all routers |
| L3VPN route missing | RT export/import mismatch; import policy does not match; session down; VRF interface wrong | `show route table bgp.l3vpn.0`; `show route table CUSTOMER_A.inet.0`; `show route table bgp.l3vpn.0 hidden`* | Align RTs; fix the policy; see next rows |
| BGP VPNv4 session failure | Loopbacks not reachable; wrong `local-address`; `family inet-vpn unicast` missing on one side; AS mismatch | `show bgp summary`; `show bgp neighbor 10.0.0.6`*; `show route 10.0.0.6` | Fix IS-IS reachability to the loopback; match family and AS |
| CE route missing | PE-CE eBGP down; CE export policy; `as-override` missing (same AS 65100 at both sites); PE export policy | `show bgp summary instance CUSTOMER_A`*; `show route advertising-protocol bgp 10.10.9.1 table CUSTOMER_A`*; `show route receive-protocol bgp 10.10.9.1 table CUSTOMER_A`* | Fix the session or policy; keep `as-override` on both PEs |
| SR-TE policy inactive | Segment list invalid; label outside the SRGB; first-hop address wrong; destination wrong | `show spring-traffic-engineering lsp`; `show route table inet.3 10.0.0.6` | Correct the hop list; labels must be SRGB base plus index |
| SR-TE path not following the intended path | Route resolved through L-ISIS, not SPRING-TE; wrong segment list; in release 1.0.0 an equal-cost IGP path matched it, so it was indistinguishable (fixed by metric 100 in 1.1.0) | `show route table inet.3 10.0.0.6` (which protocol is active); traceroute | Check protocol preference and stack; for a visible difference see lab 05 variant |
| Incorrect segment list | Typo in a label (for example 800044); wrong first-hop address | Compare each hop with `show isis database extensive \| match SID` and the link table | Rewrite the hop; the audit script resolves each hop to a router |
| Missing MPLS on an interface | `family mpls` or `protocols mpls interface` absent | `show mpls interface`; `show interfaces terse` | Add both |
| Traceroute through the core shows `*` hops | Transit router lacks `mpls icmp-tunneling` | Compare `show configuration protocols mpls` across R2 to R5 | Add `set protocols mpls icmp-tunneling` |
| BFD session not up | BFD configured on one end only | `show bfd session` on both ends | Configure both ends with identical timers |

## Seen in this lab

| Observation | Where | Effect |
|---|---|---|
| R1 NET malformed (`49.0001.0100.0001.00`) | R1 IS-IS database showed area `49` vs `49.0001` | None (Level 2 only). **Fixed in release 1.1.0.** [C1](../configs/corrections.md) |
| `mpls icmp-tunneling` missing on R5 | R5 config | Traceroute hops via R5 (secondary path) may not appear. [C6](../configs/corrections.md) |
| `show mpls forwarding-table` / `show source-packet-routing` rejected | R1 capture | Use `show route table mpls.0` and `show spring-traffic-engineering lsp` |
| `show route pro` ambiguous | R2, R5 captures | Type the full `protocol` keyword |
| Primary SR-TE path was one of three ECMP IGP paths | R1 `inet.3` (release 1.0.0) | SR-TE and IGP forwarding looked the same. **Fixed in 1.1.0** with metric 100 on R1 `ge-0/0/0.0` |
| `EXPORT_TO_CE02` has no terminating reject | R6 config | Does not restrict advertisements. [C5](../configs/corrections.md) |

## Practice exercises

Four break-and-fix drills are in [lab 06](../labs/06-troubleshooting/README.md).
