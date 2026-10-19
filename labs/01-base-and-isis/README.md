# Lab 01: Base interfaces and IS-IS (stages 1 and 2)

**Objective:** bring up addressing on all nine links and a Level 2 IS-IS adjacency on every core link, so that every loopback is reachable.

**Devices:** R1 to R6 (and CE_01, CE_02 for stage 1 only).
**Stage files:** [01-base](../../configs/stages/01-base/) and [02-isis](../../configs/stages/02-isis/). Set a root password first (see [configs/SANITIZATION.md](../../configs/SANITIZATION.md)).

Load each stage on every router in the same order (all routers finish a stage before the next stage starts):

```
configure
load set terminal          # paste the router's stage file, then press Ctrl-D
commit confirmed 5
commit
```

## Configuration (R1, stage 2 shown; stage 1 holds hostname, interface addresses and loopbacks)

```
set interfaces ge-0/0/0 unit 0 family iso
set interfaces ge-0/0/1 unit 0 family iso
set interfaces lo0 unit 0 family iso address 49.0001.0100.0000.0001.00
set protocols isis interface ge-0/0/0.0 level 1 disable
set protocols isis interface ge-0/0/0.0 point-to-point
set protocols isis interface ge-0/0/0.0 level 2 metric 100
set protocols isis interface ge-0/0/1.0 level 1 disable
set protocols isis interface ge-0/0/1.0 point-to-point
set protocols isis interface lo0.0 level 1 disable
set protocols isis interface lo0.0 passive
set protocols isis level 2 wide-metrics-only
```

Other routers use the same pattern with their own interfaces and NET: [R2](../../configs/stages/02-isis/R2.set), [R3](../../configs/stages/02-isis/R3.set), [R4](../../configs/stages/02-isis/R4.set), [R5](../../configs/stages/02-isis/R5.set), [R6](../../configs/stages/02-isis/R6.set).

## Explanation

- `family iso` plus a NET on `lo0` turns on IS-IS addressing; `level 1 disable` and `level 2 wide-metrics-only` make the core a single Level 2 domain.
- `point-to-point` avoids a designated router on routed links.
- `lo0.0` is `passive`: its address is advertised but no adjacency is attempted.
- **History:** in release 1.0.0 R1's NET was malformed ([C1](../../configs/corrections.md)). It is corrected in 1.1.0; R1's database now shows `Area address: 49.0001 (3)` like the other routers (captured in [R1-after-fixes.txt](../../verification/captured/R1-after-fixes.txt)). The `level 2 metric 100` line on `ge-0/0/0.0` is explained in [lab 05](../05-sr-te/README.md).

## Verify

After stage 1: `ping 10.10.2.2 count 3` from R1 (and the other link neighbours).
After stage 2:

```
show isis adjacency
show route protocol isis
```

Captured on R3 (`show isis adjacency`):

```
Interface             System         L State         Hold (secs) SNPA
ge-0/0/0.0            Router4        2  Up                    25
ge-0/0/1.0            Router5        2  Up                    26
ge-0/0/2.0            Router1        2  Up                    22
```

Expected everywhere: all core neighbours `L 2`, `Up`; loopbacks 10.0.0.1 to 10.0.0.6 in `inet.0`.

## Troubleshoot

| Symptom | Check |
|---|---|
| No adjacency | `family iso` on the interface, interface listed under `protocols isis`, both ends `level 1 disable` and `point-to-point` |
| Adjacency up, loopback missing | `lo0.0` under IS-IS; NET configured on `lo0` |

More: [troubleshooting matrix](../../docs/troubleshooting.md).
