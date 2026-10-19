# Lab 04: MPLS L3VPN (stage 5)

**Objective:** connect CE_01 (10.64.99.0/24) and CE_02 (203.0.113.0/24) through VRF `CUSTOMER_A` on R1 and R6, using iBGP `inet-vpn` between the PE loopbacks.

**Stage files:** [05-l3vpn](../../configs/stages/05-l3vpn/): [R1](../../configs/stages/05-l3vpn/R1.set), [R6](../../configs/stages/05-l3vpn/R6.set), [CE_01](../../configs/stages/05-l3vpn/CE_01.set), [CE_02](../../configs/stages/05-l3vpn/CE_02.set).

## Configuration (R1)

```
set policy-options policy-statement Customer_A_Export term 1 then community add RT_CE01
set policy-options policy-statement Customer_A_Export term 1 then accept
set policy-options policy-statement Cutomer_A_Import term 1 from protocol bgp
set policy-options policy-statement Cutomer_A_Import term 1 from protocol direct
set policy-options policy-statement Cutomer_A_Import term 1 from community RT_CE01
set policy-options policy-statement Cutomer_A_Import term 1 then accept
set policy-options community RT_CE01 members target:65000:1
set routing-instances CUSTOMER_A instance-type vrf
set routing-instances CUSTOMER_A protocols bgp group Customer_A type external
set routing-instances CUSTOMER_A protocols bgp group Customer_A local-address 10.10.1.2
set routing-instances CUSTOMER_A protocols bgp group Customer_A peer-as 65100
set routing-instances CUSTOMER_A protocols bgp group Customer_A local-as 65000
set routing-instances CUSTOMER_A protocols bgp group Customer_A as-override
set routing-instances CUSTOMER_A protocols bgp group Customer_A neighbor 10.10.1.1
set routing-instances CUSTOMER_A interface ge-0/0/2.0
set routing-instances CUSTOMER_A route-distinguisher 10.0.0.1:65000
set routing-instances CUSTOMER_A vrf-import Cutomer_A_Import
set routing-instances CUSTOMER_A vrf-export Customer_A_Export
set routing-instances CUSTOMER_A vrf-target target:65000:100
set routing-instances CUSTOMER_A vrf-table-label
set protocols bgp group L3VPN type internal
set protocols bgp group L3VPN local-address 10.0.0.1
set protocols bgp group L3VPN family inet-vpn unicast
set protocols bgp group L3VPN neighbor 10.0.0.6
```

## Explanation

- The VRF holds the PE-CE interface and its own BGP group; RD `10.0.0.1:65000` keeps the prefix unique.
- Export adds `target:65000:1`; import accepts routes carrying it. R6 uses the same RT, so routes flow both ways.
- Both CEs are AS 65100, so the PEs use `as-override` toward them.
- `vrf-table-label` gives the VPN label (16) a VRF lookup at the egress PE.
- **Known issues:** redundant `vrf-target`, non-filtering `EXPORT_TO_CE02`, misspelled `Cutomer_A_Import` ([corrections](../../configs/corrections.md)).

## Verify

```
show bgp summary
show route table bgp.l3vpn.0
show route table CUSTOMER_A.inet.0
```

Captured on R6, `show route 10.64.99.0/24` (VRF part):

```
10.64.99.0/24      *[BGP/170] 23:57:46, localpref 100, from 10.0.0.1
                      AS path: 65100 I, validation-state: unverified
                       to 10.10.6.1 via ge-0/0/2.0, Push 16, Push 800001(top)
                    >  to 10.10.7.1 via ge-0/0/0.0, Push 16, Push 800001(top)
```

Expected: the same pattern on R1 for `203.0.113.0/24` from 10.0.0.6. CE-side routing tables were **not** captured. End to end, the VPCS host traces (captured) reach the far host in both directions:

```
trace to 203.0.113.10, 8 hops max, press Ctrl+C to stop
 1   10.64.99.1   0.581 ms  0.467 ms  0.534 ms
 2   10.10.1.2   1.508 ms  1.297 ms  1.733 ms
 3   10.10.2.2   4.426 ms  4.002 ms  4.273 ms
 4   10.10.4.2   6.122 ms  5.246 ms  4.484 ms
 5   10.10.9.2   4.018 ms  4.924 ms  4.290 ms
 6   10.10.9.1   4.417 ms  4.651 ms  4.037 ms
 7   *203.0.113.10   6.763 ms (ICMP type:3, code:3, Destination port unreachable)

trace to 10.64.99.10, 8 hops max, press Ctrl+C to stop
 1   203.0.113.1   0.835 ms  0.623 ms  0.462 ms
 2   10.10.9.2   1.400 ms  1.435 ms  1.466 ms
 3   10.10.6.1   5.200 ms  4.517 ms  4.781 ms
 4   10.10.4.1   5.819 ms  5.673 ms  5.259 ms
 5   10.10.1.2   5.300 ms  4.953 ms  5.317 ms
 6   10.10.1.1   5.162 ms  5.374 ms  4.711 ms
 7   *10.64.99.10   5.105 ms (ICMP type:3, code:3, Destination port unreachable)
```

The last line of each trace is the far host answering, which is how VPCS ends a trace. Forward: CE_01, R1, R2, R4, R6, CE_02. Return: CE_02, R6, R4, R2, R1, CE_01. Only the forward direction is engineered (SR-TE on R1); see [lab 05](../05-sr-te/README.md).

## Troubleshoot

| Symptom | Check |
|---|---|
| Routes missing in the VRF | RT export on one PE equals RT import on the other; session up |
| CE does not learn the far site | `as-override` on the PE; export policy toward the CE |
| iBGP down | Loopback reachability (lab 01), `local-address`, `family inet-vpn unicast` |
