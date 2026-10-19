# Lab 03: Segment Routing (stage 4) and fast protection (stage 7)

**Objective:** advertise an SRGB and one Node-SID per router in IS-IS so every router can label-switch to every loopback.

**Stage files:** [04-segment-routing](../../configs/stages/04-segment-routing/) and, optionally, [07-protection](../../configs/stages/07-protection/) (BFD and post-convergence LFA).

## Configuration (R1)

```
set protocols isis source-packet-routing srgb start-label 800000
set protocols isis source-packet-routing srgb index-range 20000
set protocols isis source-packet-routing node-segment ipv4-index 1
set protocols isis source-packet-routing explicit-null
```

Only `ipv4-index` changes per router (1 to 6). Optional protection stage on R1:

```
set protocols isis interface ge-0/0/0.0 level 2 post-convergence-lfa
set protocols isis interface ge-0/0/0.0 bfd-liveness-detection minimum-interval 1000
set protocols isis interface ge-0/0/0.0 bfd-liveness-detection multiplier 3
set protocols isis interface ge-0/0/1.0 level 2 post-convergence-lfa
set protocols isis interface ge-0/0/1.0 bfd-liveness-detection minimum-interval 1000
set protocols isis interface ge-0/0/1.0 bfd-liveness-detection multiplier 3
set protocols isis backup-spf-options use-post-convergence-lfa
```

## Explanation

- Label = SRGB start (800000) plus index, so R4's Node-SID is 800004. The full table is in [sr-mpls.md](../../docs/sr-mpls.md).
- `explicit-null` makes the penultimate router swap to label 0 instead of popping.
- BFD and `post-convergence-lfa` need to be on both ends of a link to work; the audit checks this.

## Verify

```
show isis database extensive | match SID
show route table inet.3
show route table mpls.0
show bfd session
```

Captured on R5, `inet.3` entry for R6 (adjacent, so `Push 0`; the backup path pushes two labels):

```
10.0.0.6/32        *[L-ISIS/14] 1d 00:32:33, metric 10
                    >  to 10.10.7.2 via ge-0/0/0.0, Push 0
                       to 10.10.5.1 via ge-0/0/2.0, Push 800006, Push 800004(top)
```

Captured on R2, `mpls.0` entry for R4's Node-SID (`Swap 0` toward R4):

```
800004             *[L-ISIS/14] 23:40:16, metric 10
                    >  to 10.10.4.2 via ge-0/0/1.0, Swap 0
                       to 10.10.2.1 via ge-0/0/0.0, Swap 800004, Push 800003(top)
```

Captured on R5, `show bfd session`:

```
                                                  Detect   Transmit
Address                  State     Interface      Time     Interval  Multiplier
10.10.5.1                Up        ge-0/0/2.0     3.000     1.000        3
10.10.7.2                Up        ge-0/0/0.0     3.000     1.000        3

2 sessions, 2 clients
Cumulative transmit rate 2.0 pps, cumulative receive rate 2.0 pps
```

## Troubleshoot

| Symptom | Check |
|---|---|
| No label route to a loopback | That router's `node-segment ipv4-index`; `show isis database extensive \| match SID` |
| Labels differ from the table | SRGB `start-label` and `index-range` identical everywhere |
| BFD not `Up` | BFD configured on both ends with matching timers |
