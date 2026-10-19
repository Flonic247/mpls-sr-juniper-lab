# Verification captures

Raw, unedited terminal output from the author's lab (carriage returns removed). No credentials are present. Prompts such as `root@Router1>` are the lab's own.

| File | Router | Commands captured |
|---|---|---|
| [captured/R1.txt](captured/R1.txt) | R1 | `show route`, `show route table inet.3`, `show isis database extensive`, `show isis adjacency`, `show spring-traffic-engineering lsp`, `show interfaces terse`, `show route 203.0.113.0/24 detail`, plus two rejected commands |
| [captured/R1-after-fixes.txt](captured/R1-after-fixes.txt) | R1 | After the 1.1.0 changes: `show isis adjacency`, `show isis database extensive \| match "Area address"`, `show route 10.0.0.6`, `show route table inet.3 10.0.0.6`, VRF `traceroute` to 10.10.9.1 (labels quoted at R2 and R4) |
| [captured/hosts.txt](captured/hosts.txt) | Hosts (VPCS) | `trace 203.0.113.10` from the CE_01 host and `trace 10.64.99.10` from the CE_02 host |
| [captured/R2.txt](captured/R2.txt) | R2 | `show bfd session`, `show mpls interface`, `show isis adjacency`, `show route protocol isis` (includes `inet.3` and `mpls.0`) |
| [captured/R3.txt](captured/R3.txt) | R3 | `show bgp summary` (BGP not running), `show bfd session`, `show mpls interface`, `show isis adjacency` |
| [captured/R4.txt](captured/R4.txt) | R4 | `show bfd session`, `show mpls interface`, `show isis adjacency` |
| [captured/R5.txt](captured/R5.txt) | R5 | `show bfd session`, `show mpls interface`, `show isis adjacency`, `show route protocol isis` |
| [captured/R6.txt](captured/R6.txt) | R6 | `show bfd session`, `show mpls interface`, `show isis adjacency`, `show route protocol isis`, `show route 10.64.99.0/24` |

Not captured: any output from CE_01 or CE_02, end-to-end ping or traceroute between the hosts, and `show bgp summary` on the PEs. Contributions of these are welcome (see [CONTRIBUTING.md](../CONTRIBUTING.md)). How to interpret the captures: [docs/verification.md](../docs/verification.md).
