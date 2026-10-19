# Design decisions

Each decision is stated as visible in the configuration. The *Reason* column is the engineering rationale; where the author has not stated it, it is marked **inferred**.

| Decision | What the configuration shows | Reason |
|---|---|---|
| SR-MPLS over IS-IS, no LDP or RSVP | `source-packet-routing` under IS-IS; no `protocols ldp` or `rsvp` | One protocol distributes both reachability and labels (inferred) |
| IS-IS Level 2 only | `level 1 disable` on every interface; `level 2 wide-metrics-only` | Flat single-level core; wide metrics are required by SR |
| Point-to-point IS-IS interfaces | `point-to-point` on all core links | No DIS election on routed links (inferred) |
| SRGB 800000/20000, index = router number | Identical on R1 to R6 | Predictable labels: R*n* is always 80000*n* |
| `explicit-null` | On all core routers | The egress always receives a labelled packet; visible as `Swap 0` and `Push 0` |
| BGP-free core | BGP only on R1 and R6 | P routers hold no customer or BGP state |
| Same customer AS (65100) at both sites with `as-override` | Both CEs `local-as 65100`; PEs `as-override` | Lets two sites share one ASN across the VPN |
| Unique RD per PE, one shared RT | RDs `10.0.0.1:65000`, `10.0.0.6:65000`; RT `65000:1` | Standard full-mesh VPN topology |
| `vrf-table-label` | On both PEs | Egress lookup in the VRF by VPN label (shown as `lsi.0` entry) |
| SR-TE with static segment lists on the ingress PE only | Segment lists on R1; none elsewhere | Only the headend carries path state |
| IS-IS metric 100 on R1 `ge-0/0/0.0` (added in 1.1.0) | `set protocols isis interface ge-0/0/0.0 level 2 metric 100` | Makes the IGP prefer R3 so the SR-TE primary via R2 is a true detour |
| First hop as an IP address | `hope1 ip-address 10.10.2.2` | Pins the outgoing link without spending a label |
| Secondary path | `SRTE_R1_R3_R5_R6` | Standby that avoids R2, R4 (inferred from weights 0x1 and 0xff) |
| BFD (1000 ms x3) and post-convergence LFA on all core links | Same on R1 to R6 | Sub-second failure detection and precomputed repair paths |
| Customer addressing | 10.64.99.0/24 and 203.0.113.0/24 | Private and documentation space, safe to publish |

## Known design limitations

1. **The metric that creates the detour is directional.** `level 2 metric 100` on R1 `ge-0/0/0.0` affects only R1's outbound IGP choice; the return direction is unchanged. The secondary path is still an equal-cost IGP path.
2. **Unidirectional TE.** No SR-TE on R6, so return traffic is ECMP.
3. **Single customer, two PEs.** No route reflector is needed or used.
4. **Policy asymmetry at the PE-CE edge.** R6 has an export policy toward CE_02; R1 has none toward CE_01.
