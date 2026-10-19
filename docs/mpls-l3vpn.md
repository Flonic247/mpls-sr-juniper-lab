# MPLS L3VPN with MP-BGP

Hands-on steps: [lab 04](../labs/04-l3vpn/README.md).

| Question | Answer |
|---|---|
| What | One customer VPN (`CUSTOMER_A`) joining two customer sites across the core. R1 and R6 are the PEs; CE_01 and CE_02 are the CEs. |
| Why | Customer routes stay separate from the core routing table, and the core (R2 to R5) never needs customer routes or BGP. |
| How | A VRF on each PE, PE-CE eBGP, and iBGP `inet-vpn` between the PE loopbacks. Stage file: [05-l3vpn](../configs/stages/05-l3vpn/). |

## Building blocks

| Piece | Configuration | Role |
|---|---|---|
| VRF `CUSTOMER_A` | `instance-type vrf`, PE-CE interface inside it | Separate routing table per customer |
| Route distinguisher | R1 `10.0.0.1:65000`, R6 `10.0.0.6:65000` | Makes the same customer prefix unique in BGP |
| Route target | Both PEs export and import `target:65000:1` | Decides which VRFs install which routes |
| VPN label | `vrf-table-label`; R6 advertises label 16 | Inner label that selects the VRF at the egress PE |
| iBGP | `group L3VPN`, loopback to loopback, `family inet-vpn unicast` | Carries VPN routes between PEs |
| PE-CE eBGP | AS 65000 to AS 65100 | Exchanges customer prefixes |
| `as-override` | On both PE-CE groups | Both CEs are AS 65100; without it each CE would drop the other site's routes (AS-path loop) |

## Control plane and data plane

- **Control plane:** CE_01 advertises 10.64.99.0/24 to R1. R1 exports it into BGP as a VPN route with RD `10.0.0.1:65000`, RT `65000:1` and a VPN label. R6 imports it into `CUSTOMER_A` because the RT matches, and advertises it to CE_02. The reverse happens for 203.0.113.0/24.
- **Data plane:** the VPN route's next hop is the remote PE loopback. It resolves in `inet.3` to an SR path, so the packet carries **[transport labels] + [VPN label]**. Only the PEs look at the VPN label.
- **BGP-free core:** captured on R3: `show bgp summary` returns `BGP is not running`.

## What the captures show

- R1, `show route`: `203.0.113.0/24` and `10.10.9.0/30` in the VRF, learned from R6 over BGP with `VPN Label: 16`, next hop `10.0.0.6`, resolved by SPRING-TE.
- R6, `show route 10.64.99.0/24`: BGP route from `10.0.0.1`, AS path `65100 I`, `Push 16, Push 800001(top)`.
- R1's `mpls.0` has a `16` entry of protocol `VPN` that pops into `lsi.0 (CUSTOMER_A)`, the result of `vrf-table-label`.

## Verify

| Command | Expect |
|---|---|
| `show bgp summary` (on R1 and R6) | Neighbour `10.0.0.6` / `10.0.0.1` established |
| `show route table bgp.l3vpn.0` | The remote PE's routes, with RD `10.0.0.x:65000` |
| `show route table CUSTOMER_A.inet.0` | Local CE routes, remote CE routes, both PE-CE /30s |
| `show bgp summary instance CUSTOMER_A` | CE neighbour established (standard Junos; **not captured**) |
| `show route advertising-protocol bgp 10.10.9.1 table CUSTOMER_A` | What R6 sends to CE_02 (**not captured**) |

**Captured:** a traceroute from R1's VRF to CE_02's PE-CE address 10.10.9.1 crosses R2, R4 and R6 and reaches CE_02. Host-to-host traces also succeed in both directions (10.64.99.10 and 203.0.113.10, see [hosts.txt](../verification/captured/hosts.txt)), so the L3VPN works end to end. **Not captured:** CE-side routing tables. At the PE level, routes are present in both directions (R1 sees 203.0.113.0/24, R6 sees 10.64.99.0/24).

Known configuration issues here: redundant `vrf-target`, a non-filtering `EXPORT_TO_CE02`, and a misspelled import policy name. See [corrections](../configs/corrections.md).

Troubleshooting: [matrix](troubleshooting.md) (BGP VPNv4 session failure, L3VPN route missing, CE route missing).
