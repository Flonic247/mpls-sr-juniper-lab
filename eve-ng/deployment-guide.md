# EVE-NG deployment guide

This guide uses only what the author supplied: hostnames, Junos version, interface names and the topology. Anything the author did not state is marked **TBD** or **assumption**; no EVE-NG node names, port numbers or sizing are invented. Your diagram uses `vRouter` and `VPC` icons, which fits EVE-NG with VPCS hosts, but the emulator itself was not stated in the lab configurations.

## Nodes

| Node | Junos hostname | Image / version | Role |
|---|---|---|---|
| R1 | Router1 | Junos 25.2R1.9 (appears to be vMX) | PE, SR-TE headend |
| R2 to R5 | Router2 to Router5 | same | P routers |
| R6 | ROuter6 (typo as captured) | same | PE |
| CE_01 | CE_01_Router | same | Customer edge, AS 65100 |
| CE_02 | CE_02-Router | same | Customer edge, AS 65100 |
| Host 1 | n/a | VPCS (the `VPCS>` prompt appears in the captures) | `10.64.99.10/24`, gateway `10.64.99.1`, behind CE_01 ge-0/0/1 |
| Host 2 | n/a | VPCS | `203.0.113.10/24`, gateway `203.0.113.1`, behind CE_02 ge-0/0/1 |

Image files are not provided and not redistributed. **Resource sizing (CPU, RAM, disk): TBD.** Take it from your EVE-NG vMX template documentation; eight Junos nodes are the heavy part.

## Wiring (Junos interface names, from the configurations)

Connect each Junos interface to its peer. EVE-NG's own port labels for your template were not supplied, so map them yourself.

| # | End A | End B |
|---|---|---|
| 1 | CE_01 ge-0/0/0 | R1 ge-0/0/2 |
| 2 | R1 ge-0/0/0 | R2 ge-0/0/0 |
| 3 | R1 ge-0/0/1 | R3 ge-0/0/2 |
| 4 | R2 ge-0/0/1 | R4 ge-0/0/2 |
| 5 | R3 ge-0/0/0 | R4 ge-0/0/0 |
| 6 | R3 ge-0/0/1 | R5 ge-0/0/2 |
| 7 | R4 ge-0/0/1 | R6 ge-0/0/2 |
| 8 | R5 ge-0/0/0 | R6 ge-0/0/0 |
| 9 | R6 ge-0/0/1 | CE_02 ge-0/0/0 |
| 10 | CE_01 ge-0/0/1 | Host 1 eth0 |
| 11 | CE_02 ge-0/0/1 | Host 2 eth0 |

`fxp0` (management) was DHCP-addressed in the original lab and is not part of the design.

## Deployment sequence

1. Create the nodes and the 11 links above; start all nodes and wait for Junos to finish booting.
2. On each node set a root password and enter configuration mode (the published configurations contain no password).
3. Load the **stage files** lab by lab, all routers per stage ([labs/01](../labs/01-base-and-isis/README.md) to [labs/05](../labs/05-sr-te/README.md)), or load one router's file from [configs/as-captured](../configs/as-captured/) in a single step.
4. Use `commit confirmed 5`, then `commit`.
5. Configure the hosts (addresses and gateways confirmed by the traces; VPCS syntax): `ip 10.64.99.10/24 10.64.99.1` and `ip 203.0.113.10/24 203.0.113.1`. Then run `trace 203.0.113.10` from host 1 and compare with [verification/captured/hosts.txt](../verification/captured/hosts.txt).
6. Run the health check from the [README](../README.md#quick-start-about-5-minutes-of-reading) and compare with [docs/verification.md](../docs/verification.md).

## Not supplied

Startup-configuration packaging, EVE-NG lab export (`.unl`), node console order, and per-node resources. Contributions welcome ([CONTRIBUTING.md](../CONTRIBUTING.md)).
