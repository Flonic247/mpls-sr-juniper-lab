# Addressing and identifiers

Everything here comes from the configurations in [../configs/as-captured](../configs/as-captured/). Where the author's diagram differs, the configuration wins and the difference is listed in the [audit](consistency-audit.md).

## Routers, loopbacks and Segment Routing

| Router | Configured hostname | Loopback (lo0.0) | IS-IS NET | Node-SID index | Node-SID label | Role |
|---|---|---|---|---|---|---|
| R1 | Router1 | 10.0.0.1/32 | `49.0001.0100.0000.0001.00` (corrected in 1.1.0, see [C1](../configs/corrections.md)) | 1 | 800001 | PE, SR-TE headend |
| R2 | Router2 | 10.0.0.2/32 | `49.0001.0100.0000.0002.00` | 2 | 800002 | P |
| R3 | Router3 | 10.0.0.3/32 | `49.0001.0100.0000.0003.00` | 3 | 800003 | P |
| R4 | Router4 | 10.0.0.4/32 | `49.0001.0100.0000.0004.00` | 4 | 800004 | P |
| R5 | Router5 | 10.0.0.5/32 | `49.0001.0100.0000.0005.00` | 5 | 800005 | P |
| R6 | ROuter6 (typo) | 10.0.0.6/32 | `49.0001.0100.0000.0006.00` | 6 | 800006 | PE |
| CE_01 | CE_01_Router | 192.168.1.1/32 | none | none | none | Customer edge, AS 65100 |
| CE_02 | CE_02-Router | 192.168.2.1/32 | none | none | none | Customer edge, AS 65100 |

- **SRGB:** start 800000, range 20000 (labels 800000 to 819999), identical on R1 to R6.
- **Label rule:** label = SRGB start + Node-SID index.
- **IS-IS:** Level 2 only, wide metrics only, point-to-point interfaces, default metric 10 on every link, except R1 `ge-0/0/0.0` (toward R2), which is 100 since release 1.1.0.
- **Adjacency-SIDs** are allocated dynamically (labels in the 16 to 18 range in the captures) and depend on bring-up order, so this repository never hard-codes them.

## Point-to-point links

| Link | Subnet | Endpoint A | Endpoint B |
|---|---|---|---|
| CE_01 to R1 | 10.10.1.0/30 | CE_01 ge-0/0/0 `.1` | R1 ge-0/0/2 `.2` (VRF) |
| R1 to R2 | 10.10.2.0/30 | R1 ge-0/0/0 `.1` | R2 ge-0/0/0 `.2` |
| R1 to R3 | 10.10.3.0/30 | R1 ge-0/0/1 `.1` | R3 ge-0/0/2 `.2` |
| R2 to R4 | 10.10.4.0/30 | R2 ge-0/0/1 `.1` | R4 ge-0/0/2 `.2` |
| R3 to R5 | 10.10.5.0/30 | R3 ge-0/0/1 `.1` | R5 ge-0/0/2 `.2` |
| R4 to R6 | 10.10.6.0/30 | R4 ge-0/0/1 `.1` | R6 ge-0/0/2 `.2` |
| R5 to R6 | 10.10.7.0/30 | R5 ge-0/0/0 `.1` | R6 ge-0/0/0 `.2` |
| R3 to R4 | 10.10.8.0/30 | R3 ge-0/0/0 `.1` | R4 ge-0/0/0 `.2` |
| R6 to CE_02 | 10.10.9.0/30 | R6 ge-0/0/1 `.2` (VRF) | CE_02 ge-0/0/0 `.1` |

Core interface summary: R1 has ge-0/0/0 (R2), ge-0/0/1 (R3), ge-0/0/2 (CE_01). R2 has ge-0/0/0 (R1), ge-0/0/1 (R4). R3 has ge-0/0/0 (R4), ge-0/0/1 (R5), ge-0/0/2 (R1). R4 has ge-0/0/0 (R3), ge-0/0/1 (R6), ge-0/0/2 (R2). R5 has ge-0/0/0 (R6), ge-0/0/2 (R3). R6 has ge-0/0/0 (R5), ge-0/0/1 (CE_02), ge-0/0/2 (R4).

## Customer networks

| Site | CE LAN interface | Prefix | Host (from the author's diagram) |
|---|---|---|---|
| CE_01 | ge-0/0/1 `10.64.99.1/24` | 10.64.99.0/24 | VPC `.10/24` |
| CE_02 | ge-0/0/1 `203.0.113.1/24` | 203.0.113.0/24 (RFC 5737 documentation range) | VPC `.10/24` |

The host addresses `10.64.99.10` and `203.0.113.10` and their gateways (the CE LAN addresses `10.64.99.1` and `203.0.113.1`) are **confirmed by the host traces** ([hosts.txt](../verification/captured/hosts.txt)): the CE LAN address is hop 1 in each trace and each trace reaches the other host. The /24 mask comes from the author's diagram.

## BGP and VPN parameters

| Item | Value |
|---|---|
| Core AS | 65000 |
| Customer AS (both sites) | 65100 (the PEs use `as-override`) |
| iBGP | R1 10.0.0.1 and R6 10.0.0.6, loopback to loopback, `family inet-vpn unicast` |
| PE-CE eBGP | R1 10.10.1.2 with CE_01 10.10.1.1; R6 10.10.9.2 with CE_02 10.10.9.1 |
| VRF | `CUSTOMER_A`, `vrf-table-label` |
| Route distinguishers | R1 `10.0.0.1:65000`, R6 `10.0.0.6:65000` |
| Route target | `target:65000:1` exported and imported by both PEs (`target:65000:100` is also configured as `vrf-target` but has no observed effect, see [C2](../configs/corrections.md)) |
| VPN label (as advertised by R6, observed on R1) | 16 |

## SR-TE objects (R1 only)

| Object | Value |
|---|---|
| Path | `R1_TO_R6_SRTE` to 10.0.0.6, `sr-preference 100` |
| Primary segment list `SRTE_R1_R2_R4_R6` | hop 1 next-hop address 10.10.2.2 (R2), hop 2 label 800004 (R4), hop 3 label 800006 (R6) |
| Secondary segment list `SRTE_R1_R3_R5_R6` | hop 1 next-hop address 10.10.3.2 (R3), hop 2 label 800005 (R5), hop 3 label 800006 (R6) |

## Management plane (outside the lab design)

`fxp0` obtains an address by DHCP on every node. Those addresses are not part of this lab and are not documented.
