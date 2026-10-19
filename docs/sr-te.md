# SR-TE: engineering R1 to R6

Hands-on steps: [lab 05](../labs/05-sr-te/README.md). Diagrams: [topology.md](topology.md).

## Three ways to forward the same traffic

| Mode | Who decides the path | State in the network | In this lab |
|---|---|---|---|
| **IGP shortest path** | Hop-by-hop SPF, no labels required | None | `10.0.0.6/32` learned as IS-IS/18, metric 30 |
| **SR-MPLS** | Still the IGP's shortest path, but traffic carries a Node-SID label | One label per node, in every router | `10.0.0.6/32` as L-ISIS/14 in `inet.3`, `Push 800006` |
| **SR-TE** | The headend, which pushes a stack of segments describing the path | Only on the headend | `10.0.0.6/32` as SPRING-TE/8 in `inet.3`, stack of labels |

## What is configured (R1 only)

| Object | Value |
|---|---|
| Path | `R1_TO_R6_SRTE`, to `10.0.0.6`, `sr-preference 100` |
| Primary | `SRTE_R1_R2_R4_R6`: hop 1 address `10.10.2.2`, hop 2 label `800004`, hop 3 label `800006` |
| Secondary | `SRTE_R1_R3_R5_R6`: hop 1 address `10.10.3.2`, hop 2 label `800005`, hop 3 label `800006` |
| Other | `set protocols source-packet-routing traffic-engineering database` (purpose not verified in the captures) |

Stage file: [06-sr-te/R1.set](../configs/stages/06-sr-te/R1.set).

## The segments of the primary path

| Hop | Configured as | Meaning | On the wire |
|---|---|---|---|
| 1 | `ip-address 10.10.2.2` | Send the packet to R2 over R1's ge-0/0/0. This is a next-hop address, **not** a label. | No label; selects the outgoing interface |
| 2 | `label 800004` | Node-SID of R4: go to R4 | Top label |
| 3 | `label 800006` | Node-SID of R6: then go to R6 | Second label |

Observed on R1 (`show route table inet.3` and the VPN route detail): next hop `10.10.2.2 via ge-0/0/0.0`, `Push 800006, Push 800004(top)`. For a VPN prefix the VPN label is pushed first, giving `Push 16, Push 800006, Push 800004(top)`.

## Headend and why

**R1 is the headend** because it is the ingress PE: the router where customer traffic enters the SR domain and where labels are imposed. SR-TE needs state only there. R2 to R6 have no SR-TE configuration and do not know the path exists; they only swap labels.

## What each transit router does

| Router | Action | Evidence |
|---|---|---|
| R1 | Pushes `16`, `800006`, `800004` (top); sends to 10.10.2.2 | Captured: R1 `inet.3` and route detail |
| R2 | Receives `800004`, consumes it toward R4 (R4 is adjacent and uses explicit null) | Captured: traceroute hop 1 shows 800004, 800006, 16; R2 `mpls.0`: `800004 ... Swap 0` |
| R4 | Receives `800006` and `16`, forwards toward R6 (R6 is adjacent) | Captured: traceroute hop 2 shows 800006, 16. The forwarding action is inferred; R4's `mpls.0` was not captured |
| R6 | Pops the VPN label `16` into VRF `CUSTOMER_A` and delivers to CE_02 | Captured: traceroute hop 3 is R6's VRF interface 10.10.9.2, hop 4 is CE_02. The pop itself is inferred from `vrf-table-label` |

## How VPN traffic is steered onto the policy

The VPN routes from R6 have BGP next hop `10.0.0.6`. BGP resolves that next hop in `inet.3`, where `10.0.0.6/32` exists twice: `SPRING-TE/8` (the SR-TE path) and `L-ISIS/14` (plain SR). The lower preference wins, so **all** R1-to-R6 labelled traffic follows the SR-TE stack with no extra steering policy.

## Backup behaviour

R1's route has two next hops: `10.10.2.2` with `weight 0x1, selected` (primary) and `10.10.3.2` with `weight 0xff` (secondary). **Inferred:** the higher weight marks the secondary as a standby used only if the primary is down. The primary-failure test was not captured.

## Two things to know before presenting this lab (updated for release 1.1.0)

1. **The engineered path is a genuine detour (since release 1.1.0).** R1's IS-IS metric on `ge-0/0/0.0` (toward R2) is 100. Captured on R1: `show route 10.0.0.6` selects IS-IS via `10.10.3.2` (R3) only, while in `inet.3` `SPRING-TE/8` stays active via `10.10.2.2` with `Push 800006, Push 800004(top)`; the L-ISIS route to the same destination prefers `10.10.3.2` and lists `10.10.2.2` as a non-selected next hop (inferred: a protection next hop). The primary's IGP cost is 120 (100 + 10 + 10) against 30 for the IGP path. The secondary R1-R3-R5-R6 is still an equal-cost IGP path, so it is a natural standby and not a detour. In release 1.0.0 all metrics were 10 and the primary was one of three equal-cost paths, so SR-TE only pinned a path.
2. **It is one-way.** R6 has no SR-TE. Captured on R6: the route to 10.64.99.0/24 pushes `16, 800001` and load-shares over R4 and R5. The host trace from the CE_02 side crosses R6, R4, R2, R1 ([hosts.txt](../verification/captured/hosts.txt)). That is one of the equal-cost plain-SR paths, so it mirrors the forward path here through ordinary forwarding, not through SR-TE; other flows may use R5 or R3.

## Verify

| Command | Expect |
|---|---|
| `show spring-traffic-engineering lsp` | `R1_TO_R6_SRTE` to `10.0.0.6`, state `Up` (captured) |
| `show route table inet.3 10.0.0.6` | `SPRING-TE/8` active, two labels, next hop 10.10.2.2 |
| `show route 10.0.0.6` | IS-IS next hop 10.10.3.2 only, so the engineered path differs from the IGP path (captured after the 1.1.0 changes) |
| `show route 203.0.113.0/24 table CUSTOMER_A detail` | `VPN Label: 16` and the SR-TE stack |
| `traceroute 10.10.9.1 routing-instance CUSTOMER_A no-resolve` | R2 (10.10.2.2) with labels 800004, 800006, 16, then R4 (10.10.4.2) with 800006, 16, then R6 (10.10.9.2), then CE_02 (10.10.9.1) (captured after release 1.1.0) |

Failure looks like: LSP not `Up`, route to `10.0.0.6` shown only as L-ISIS, or a label stack that does not match the segment list. See the [troubleshooting matrix](troubleshooting.md).
