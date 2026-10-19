# SR-MPLS: IS-IS, MPLS and Segment Routing

This page follows the seven-question template for each technology: what it is, why it is used, how it is configured, what should happen, how to verify, what failure looks like, how to troubleshoot. Hands-on steps are in labs [01](../labs/01-base-and-isis/README.md) to [03](../labs/03-sr-mpls/README.md). Outputs quoted here come from [verification/captured](../verification/captured/).

## 1. IS-IS (the IGP that carries the SIDs)

| Question | Answer |
|---|---|
| What | A link-state IGP. Here it runs Level 2 only, with wide metrics, on point-to-point links. |
| Why | It builds the loopback reachability that MPLS, BGP and SR need, and its TLVs also carry the SR labels. |
| How | `family iso` on each core interface and loopback (NET on `lo0`), `protocols isis interface <if> level 1 disable` and `point-to-point`, `level 2 wide-metrics-only`. Stage file: [configs/stages/02-isis](../configs/stages/02-isis/). |
| Should happen | Every core link has an `Up` Level 2 adjacency; every loopback appears in `inet.0` as an IS-IS route. |
| Verify | `show isis adjacency`, `show route protocol isis` |
| Failure looks like | Missing adjacency, or a loopback missing from the routing table. |
| Troubleshoot | [troubleshooting matrix](troubleshooting.md): family `iso`, `level 1 disable` on one side only, point-to-point mismatch, wrong interface. |

Captured result (R3): three adjacencies, all `L 2`, `Up`, to Router4, Router5 and Router1.

## 2. MPLS (the forwarding plane)

| Question | Answer |
|---|---|
| What | Label switching on the core-facing interfaces. There is no LDP and no RSVP in this lab: labels come from IS-IS. |
| Why | Packets must carry labels for SR and for VPN traffic to be forwarded without BGP in the core. |
| How | `family mpls` on core interfaces and `protocols mpls interface <if>`. CE-facing interfaces (R1 ge-0/0/2, R6 ge-0/0/1) are deliberately **not** MPLS interfaces. `chassis network-services enhanced-ip` is set on every router. Stage file: [03-mpls](../configs/stages/03-mpls/). |
| Should happen | `show mpls interface` lists every core interface as `Up`. |
| Verify | `show mpls interface`; `show route table mpls.0` |
| Failure looks like | An interface missing from `show mpls interface`; labelled routes in `inet.3` that never use that interface. |
| Troubleshoot | Check `family mpls` and the `protocols mpls interface` entry on **both** ends of the link. |

Note: on this platform `show mpls forwarding-table` is rejected (syntax error on R1). Use `show route table mpls.0` and `show route table inet.3` instead.

## 3. Segment Routing (SR-MPLS)

### Concepts used here

| Term | Meaning in this lab |
|---|---|
| SRGB | The label block every router reserves for global SIDs: base **800000**, size **20000** (800000 to 819999). |
| Prefix-SID | A global identifier for a prefix, advertised in IS-IS as an index into the SRGB. |
| Node-SID | The Prefix-SID of a router's loopback. Here the index equals the router number. |
| Adjacency-SID | A local label that forces traffic out of one specific link (dynamic, 16 to 18 in the captures). |
| Label | SRGB base + index. R4's Node-SID index 4 becomes label 800004. |

| Router | Loopback | Node-SID index | Label | SRGB | Role |
|---|---|---|---|---|---|
| R1 | 10.0.0.1/32 | 1 | 800001 | 800000/20000 | PE, SR-TE headend |
| R2 | 10.0.0.2/32 | 2 | 800002 | 800000/20000 | P |
| R3 | 10.0.0.3/32 | 3 | 800003 | 800000/20000 | P |
| R4 | 10.0.0.4/32 | 4 | 800004 | 800000/20000 | P |
| R5 | 10.0.0.5/32 | 5 | 800005 | 800000/20000 | P |
| R6 | 10.0.0.6/32 | 6 | 800006 | 800000/20000 | PE |

### How IS-IS distributes the SIDs

Each router advertises its SRGB (`srgb start-label 800000`, `index-range 20000`) and its Node-SID index (`node-segment ipv4-index N`) in its IS-IS LSP. Every other router adds the index to the SRGB, so every router derives the same label for the same destination. From R1's captured `show isis database extensive`, the advertisement includes (abridged): an SR capability with SRGB `SID-Label: 800000`, `Range: 20000`, and a node SID with value 1, with the N, P and E flags set.

### How the forwarding path is built

1. IS-IS computes the shortest paths to every loopback (SPF).
2. For each remote Node-SID, a router installs a labelled route in `inet.3` (imposition, `Push`) and a transit entry in `mpls.0` (`Swap` or `Pop`).
3. A packet to R6's loopback enters R1 and gets label **800006** pushed. In release 1.0.0 R1 load-shared over R2 and R3 (captured: `10.0.0.6/32 ... metric 30` with two next hops); since 1.1.0 plain SR from R1 prefers R3 only, see [sr-te.md](sr-te.md).
4. Each transit router swaps 800006 for 800006 toward its next hop (captured on R2: `800006 ... to 10.10.4.2 via ge-0/0/1.0, Swap 800006`).
5. The router **adjacent** to the destination does not pop; it swaps to label 0 (see below) and R6 pops it.

### Explicit null instead of PHP

`explicit-null` is configured on every router. In the captures, adjacent Node-SIDs show `Push 0` or `Swap 0`, and the Node-SID flags include P and E. Effect: the penultimate router swaps to **label 0** (explicit null) instead of popping, so the destination always receives a labelled packet and pops it itself. Example from R2's `mpls.0`: `800004 ... to 10.10.4.2 via ge-0/0/1.0, Swap 0` (R4 is adjacent to R2). Label 0 with more labels below it appears as `0(S=0)` in `mpls.0` and is popped back into `mpls.0`. Note: the label stacks that traceroute quotes at R4 list only 800006 and 16, so label 0 is not visible there; the explicit-null behaviour rests on the `mpls.0` and `inet.3` entries.

- **Verify:** `show isis database extensive | match SID`, `show route table inet.3`, `show route table mpls.0`
- **Failure looks like:** a Node-SID missing from `inet.3`, or labels that do not match the SRGB base plus index.
- **Troubleshoot:** same SRGB on every router, unique index per router, `wide-metrics-only`, `family mpls` on the links.

## 4. Fast protection: BFD and post-convergence LFA

All six core routers run BFD (1000 ms interval, multiplier 3) and `post-convergence-lfa` on every core IS-IS interface. This is optional for SR itself but part of the captured lab.

- **Observed:** `show bfd session` is `Up` on every core link (R2: 2 sessions, R3: 3, R4: 3, R5: 2, R6: 2, each with `Detect Time 3.000`).
- **Observed:** `inet.3` and `mpls.0` list backup next hops with extra labels, for example on R1 `10.0.0.2/32` via R3 with `Push 800002, Push 800004(top)`.
- **Interpretation (Inferred):** these are post-convergence repair paths that use another router's Node-SID (here R4's) as an intermediate segment.
- Stage file: [07-protection](../configs/stages/07-protection/). The audit checks that BFD and LFA are configured on **both** ends of every core link.
