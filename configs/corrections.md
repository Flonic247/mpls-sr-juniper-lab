# Corrections and recommended improvements

The configurations in [as-captured/](as-captured/) are the source of truth: they are what produced the outputs in [verification/captured/](../verification/captured/). This page lists every place where the captured configuration looks incorrect or improvable, **separately**, so nothing is silently changed.

Status key: **Observed** means supported by captured output. **Inferred** means reasoned from the configuration. **Untested** means the commands below were not run in the lab; test them before relying on them.

## C1. R1 IS-IS NET is malformed (ERROR) - APPLIED in release 1.1.0

**Status:** applied and verified by the author on R1. Captured afterwards ([R1-after-fixes.txt](../verification/captured/R1-after-fixes.txt)): both IS-IS adjacencies `Up`, and every LSP now shows `Area address: 49.0001 (3)`. The original R1 file is kept in [history/](history/1.0.0-junos25.2R1.9/R1.set).

- **Captured:** `set interfaces lo0 unit 0 family iso address 49.0001.0100.0001.00`
- **Problem:** The other five routers use `49.0001.0100.0000.000N.00`. R1's NET is missing one 16-bit group, so R1 ends up in area `49` with system-ID `0001.0100.0001`, not area `49.0001`.
- **Evidence (Observed):** In R1's IS-IS database the other routers advertise `Area address: 49.0001 (3)` while Router1 advertises `Area address: 49 (1)`. The author's diagram table also lists `49.0001.0100.0000.0001.00`.
- **Why it still works:** Every IS-IS interface is `level 1 disable`, so only Level 2 adjacencies form, and Level 2 ignores area mismatches.
- **Corrected (Untested):**

```
delete interfaces lo0 unit 0 family iso address 49.0001.0100.0001.00
set interfaces lo0 unit 0 family iso address 49.0001.0100.0000.0001.00
```

Changing the NET changes R1's IS-IS system-ID, so expect a brief IS-IS reconvergence on R1. Use `commit confirmed`.

## C2. `vrf-target` is redundant next to explicit import/export policies (WARNING)

- **Captured (R1 and R6):** `vrf-target target:65000:100` together with `vrf-import` and `vrf-export` policies that use `target:65000:1`.
- **Evidence (Observed):** VPN routes learned from R6 on R1 carry `target:65000:1`, not `target:65000:100`.
- **Interpretation (Inferred):** The explicit policies decide import and export, so `vrf-target` has no visible effect and misleads readers.
- **Corrected (Untested):** on R1 and R6

```
delete routing-instances CUSTOMER_A vrf-target
```

## C3. Route-target community names suggest per-CE targets but carry one value (WARNING)

`RT_CE01` (R1) and `RT_CE02` (R6) both equal `target:65000:1`. That is correct for a full-mesh VPN, but the names imply two different targets. Optional rename (Untested):

```
rename policy-options community RT_CE01 to community RT_CUSTOMER_A    # R1
rename policy-options community RT_CE02 to community RT_CUSTOMER_A    # R6
```

## C4. Policy name typo (WARNING, cosmetic)

`Cutomer_A_Import` is misspelled on both PEs but used consistently, so it works. Optional fix (Untested), on R1 and R6:

```
copy policy-options policy-statement Cutomer_A_Import to policy-statement Customer_A_Import
set routing-instances CUSTOMER_A vrf-import Customer_A_Import
delete routing-instances CUSTOMER_A vrf-import Cutomer_A_Import
delete policy-options policy-statement Cutomer_A_Import
```

## C5. R6 `EXPORT_TO_CE02` does not filter (WARNING)

- **Captured:** one unnamed term: `from route-filter 10.64.99.0/24 exact`, `then accept`.
- **Problem (Inferred):** A route that does not match falls through to the BGP default export policy, which advertises active BGP routes. The policy therefore does not restrict anything. R1 has no equivalent policy toward CE_01.
- **If the intent is "send CE_02 only the CE_01 LAN" (Untested):**

```
delete policy-options policy-statement EXPORT_TO_CE02
set policy-options policy-statement EXPORT_TO_CE02 term CE01_LAN from route-filter 10.64.99.0/24 exact
set policy-options policy-statement EXPORT_TO_CE02 term CE01_LAN then accept
set policy-options policy-statement EXPORT_TO_CE02 term REST then reject
```

- **Verify before and after:** `show route advertising-protocol bgp 10.10.9.1 table CUSTOMER_A`. CE_02 output was not captured, so the current behaviour is unconfirmed.

## C6. R5 lacks `mpls icmp-tunneling` (WARNING)

R2, R3 and R4 have `set protocols mpls icmp-tunneling`; R5, also a transit router (on the secondary path), does not. The author's notes say it is needed so transit routers can return ICMP errors for labelled packets (traceroute through the core). Add for consistency (Untested):

```
set protocols mpls icmp-tunneling
```

## C7. Hostname and description typos (cosmetic)

`ROuter6` (host-name on R6, visible in IS-IS output), `" Connecion to Router3"` and `"COneection to Router2"` (R4), `" COnnection to Router1"` (R3), and leading spaces in several descriptions. CE_02's BGP group is named `TO_Router1` but peers with R6; CE_02's export policy is `EXP_o_Router6` (CE_01: `EXP_o_Router1`). All functional.

## C8. CE_01 static reject duplicates the connected route (WARNING)

`set routing-options static route 10.64.99.0/24 reject` on CE_01 is inactive while `ge-0/0/1` is up (the connected route wins). It only becomes active if the LAN interface goes down, which would keep advertising a prefix that blackholes traffic. CE_02 has no equivalent, so the two CEs behave differently when the LAN is down. Decide intentionally; both options are valid for a lab.

## Recommended improvements (not corrections)

| # | Suggestion | Commands (Untested) | Why |
|---|---|---|---|
| I1 | Disable IS-IS Level 1 globally | `set protocols isis level 1 disable` on all core routers | R1's database shows its own Level 1 LSP even though every interface is L1-disabled. A global disable removes L1 state entirely. |
| I2 (applied in 1.1.0) | Make the engineered path differ from the IGP path | On R1: `set protocols isis interface ge-0/0/0.0 level 2 metric 100` | All links have metric 10, so R1 to R6 has three equal-cost paths and the SR-TE primary path is one of them. With the higher metric on R1's link to R2, IGP traffic uses R3 while SR-TE still goes via R2. Details in [labs/05-sr-te](../labs/05-sr-te/README.md). |
| I3 | Add SR-TE on R6 for the return direction | Same structure as R1 with R6 as headend: first hop an adjacent core router's address, then the Node-SID of the intermediate router, then 800001 (R1) | Return traffic currently follows the plain SR/ECMP path (Observed on R6). |

**I2 status:** applied on R1 in release 1.1.0 and verified (captured): `show route 10.0.0.6` now selects IS-IS via `10.10.3.2` only, while `show route table inet.3 10.0.0.6` keeps `SPRING-TE/8` active via `10.10.2.2` with `Push 800006, Push 800004(top)`. The IGP cost of the SR-TE primary is now 120 (100 + 10 + 10) against 30 for the IGP path. The metric is directional: it affects only R1's outbound choice, so the return direction (R6 to R1) is unchanged.
