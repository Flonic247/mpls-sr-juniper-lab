# Lab 02: MPLS (stage 3)

**Objective:** enable label switching on every core-facing interface. No LDP or RSVP is used; labels come from IS-IS in lab 03.

**Stage files:** [03-mpls](../../configs/stages/03-mpls/).

## Configuration (R1; the CE-facing interface ge-0/0/2 is intentionally absent)

```
set interfaces ge-0/0/0 unit 0 family mpls
set interfaces ge-0/0/1 unit 0 family mpls
set protocols mpls interface ge-0/0/0.0
set protocols mpls interface ge-0/0/1.0
```

Note: `family mpls` lines sit next to the interface addresses in the full configuration; the stage file groups them here. R2, R3 and R4 also carry `set protocols mpls icmp-tunneling`; R5 does not ([C6](../../configs/corrections.md)).

## Explanation

- `family mpls` allows the interface to carry labelled packets; `protocols mpls interface` includes it in MPLS processing. Both are needed.
- The PE-CE links (R1 ge-0/0/2, R6 ge-0/0/1) must stay IP-only.
- `icmp-tunneling` lets transit routers return ICMP errors for labelled packets, which makes traceroute through the core work.

## Verify

```
show mpls interface
```

Captured on R3:

```
Interface        State       Administrative groups (x: extended)
ge-0/0/0.0       Up         <none>
ge-0/0/1.0       Up         <none>
ge-0/0/2.0       Up         <none>
```

Expected: every core interface listed and `Up`. Note: `show mpls forwarding-table` is rejected on this platform.

## Troubleshoot

| Symptom | Check |
|---|---|
| Interface missing from `show mpls interface` | `family mpls` **and** `protocols mpls interface` on both ends |
| Labelled routes avoid a link | The link lacks MPLS on one side |
