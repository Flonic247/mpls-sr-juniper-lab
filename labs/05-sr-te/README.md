# Lab 05: SR-TE (stage 6)

**Objective:** steer R1-to-R6 traffic over R1-R2-R4-R6, with R1-R3-R5-R6 as the secondary.

**Stage file:** [06-sr-te/R1.set](../../configs/stages/06-sr-te/R1.set). Only R1 is configured.

## Configuration (R1)

```
set protocols source-packet-routing segment-list SRTE_R1_R2_R4_R6 hope1 ip-address 10.10.2.2
set protocols source-packet-routing segment-list SRTE_R1_R2_R4_R6 hope2 label 800004
set protocols source-packet-routing segment-list SRTE_R1_R2_R4_R6 hope3 label 800006
set protocols source-packet-routing segment-list SRTE_R1_R3_R5_R6 hope1 ip-address 10.10.3.2
set protocols source-packet-routing segment-list SRTE_R1_R3_R5_R6 hope2 label 800005
set protocols source-packet-routing segment-list SRTE_R1_R3_R5_R6 hope3 label 800006
set protocols source-packet-routing source-routing-path R1_TO_R6_SRTE to 10.0.0.6
set protocols source-packet-routing source-routing-path R1_TO_R6_SRTE sr-preference 100
set protocols source-packet-routing source-routing-path R1_TO_R6_SRTE primary SRTE_R1_R2_R4_R6
set protocols source-packet-routing source-routing-path R1_TO_R6_SRTE secondary SRTE_R1_R3_R5_R6
set protocols source-packet-routing traffic-engineering database
```

## Explanation

- Each segment list is a sequence of hops: a next-hop **address** for the first hop, then Node-SID **labels** (800004 is R4, 800006 is R6).
- The route to 10.0.0.6 becomes `SPRING-TE` (preference 8) in `inet.3` and beats `L-ISIS` (14), so VPN traffic follows it automatically.
- Details and per-router behaviour: [sr-te.md](../../docs/sr-te.md).
- **Detour (since release 1.1.0):** R1's IS-IS metric toward R2 is 100 (`set protocols isis interface ge-0/0/0.0 level 2 metric 100`, in [stage 02](../../configs/stages/02-isis/R1.set)), so the IGP prefers R3 while the primary SR-TE path crosses R2. In release 1.0.0 all metrics were 10 and the policy only pinned one of three equal-cost paths.

## Verify

```
show spring-traffic-engineering lsp
show route table inet.3 10.0.0.6
show route 203.0.113.0/24 detail
traceroute 10.10.9.1 routing-instance CUSTOMER_A no-resolve
```

Captured on R1:

```
To                        State        LSPname
10.0.0.6                  Up           R1_TO_R6_SRTE


Total displayed LSPs: 1 (Up: 1, Down: 0, Initializing: 0)
```

Also captured: `10.0.0.6/32` active as `SPRING-TE/8`, next hop `10.10.2.2` with `Push 800006, Push 800004(top)` and `weight 0x1, selected`; secondary `10.10.3.2` with `weight 0xff`; `VPN Label: 16`. The VRF traceroute is shown below.

## Seeing the detour: IGP path versus SR-TE path

Captured on R1 after the 1.1.0 changes (full output in [R1-after-fixes.txt](../../verification/captured/R1-after-fixes.txt)):

```
10.0.0.6/32        *[IS-IS/18] 00:00:10, metric 30
                    >  to 10.10.3.2 via ge-0/0/1.0
10.0.0.6/32        *[SPRING-TE/8] 00:03:37, metric 1, metric2 30
                    >  to 10.10.2.2 via ge-0/0/0.0, Push 800006, Push 800004(top)
                       to 10.10.3.2 via ge-0/0/1.0, Push 800006, Push 800005(top)
                    [L-ISIS/14] 00:00:10, metric 30
                    >  to 10.10.3.2 via ge-0/0/1.0, Push 800006
                       to 10.10.2.2 via ge-0/0/0.0, Push 800006
```

Reading it: the IGP route (`IS-IS/18`) uses only `10.10.3.2` (R3). The `SPRING-TE/8` route is still active in `inet.3` through `10.10.2.2` (R2) with `Push 800006, Push 800004(top)`; the secondary goes through R3 with `800005`. The IGP cost of the primary is 120 (100 + 10 + 10) against 30, so SR-TE is a genuine detour. The metric is directional: it only changes R1's outbound choice.

Captured traceroute from R1's VRF to CE_02's PE-CE address:

```
traceroute to 10.10.9.1 (10.10.9.1), 30 hops max, 52 byte packets
 1  10.10.2.2  5.632 ms  4.639 ms  11.596 ms
     MPLS Label=800004 CoS=0 TTL=1 S=0
     MPLS Label=800006 CoS=0 TTL=1 S=0
     MPLS Label=16 CoS=0 TTL=1 S=1
 2  10.10.4.2  4.343 ms  4.095 ms  3.473 ms
     MPLS Label=800006 CoS=0 TTL=1 S=0
     MPLS Label=16 CoS=0 TTL=2 S=1
 3  10.10.9.2  4.014 ms  3.509 ms  3.583 ms
 4  10.10.9.1  26.433 ms  6.066 ms  4.523 ms
```

Hop 1 is R2 (10.10.2.2) with the stack 800004, 800006, 16; hop 2 is R4 (10.10.4.2) with 800006, 16; hop 3 is R6's VRF interface and hop 4 is CE_02. R3 and R5 never appear. Compare this with the IGP route above (next hop R3): the traffic follows the SR-TE path, not the IGP path. R2 and R4 return the hops because `mpls icmp-tunneling` is configured there. The host-to-host trace in [lab 04](../04-l3vpn/README.md) takes the same forward path.

To remove the detour (for comparison): `delete protocols isis interface ge-0/0/0.0 level 2 metric`, use `commit confirmed 5`. The traceroute above would look the same, because VPN traffic follows the SPRING-TE route either way; the detour shows in the routing tables.

## Troubleshoot

| Symptom | Check |
|---|---|
| LSP not `Up` | Labels inside the SRGB; hop 1 address is R2's address on the R1 to R2 link |
| Route shows only `L-ISIS` | Policy not resolving; compare with `show spring-traffic-engineering lsp` |
| Path looks unchanged | In release 1.0.0 (all metrics 10) an equal-cost IGP path matched the SR-TE path. Check the metric on R1 `ge-0/0/0.0` |
