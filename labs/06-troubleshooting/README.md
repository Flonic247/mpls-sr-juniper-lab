# Lab 06: Troubleshooting drills

Four break-and-fix exercises. The commands only change or delete lines that exist in the captured configurations. **Outputs were not captured**; the expectations follow from how the features work, so confirm them in your lab. Always use `commit confirmed 5` and restore the original line afterwards.

| # | Break (device) | Observe | Restore |
|---|---|---|---|
| 1 | Wrong SID in the segment list (R1): `set protocols source-packet-routing segment-list SRTE_R1_R2_R4_R6 hope2 label 800044` | `show spring-traffic-engineering lsp`; `show route table inet.3 10.0.0.6`; the weights in `show route 203.0.113.0/24 detail`. Label 800044 is not a router's Node-SID (index 44 is unused) | `... hope2 label 800004` |
| 2 | Route-target mismatch (R6): `set policy-options community RT_CE02 members target:65000:2` | `show route table CUSTOMER_A.inet.0` on R1 and R6. R6 now exports and imports `65000:2` while R1 uses `65000:1`, so neither side should import the other's routes | `... members target:65000:1` |
| 3 | `as-override` removed (R6): `delete routing-instances CUSTOMER_A protocols bgp group Customer_A as-override` | On CE_02: `show route 10.64.99.0/24 hidden`. The path now contains CE_02's own AS 65100, so CE_02 should reject it as a loop | `set routing-instances CUSTOMER_A protocols bgp group Customer_A as-override` |
| 4 | `icmp-tunneling` removed (R2): `delete protocols mpls icmp-tunneling` | `traceroute 10.10.9.1 routing-instance CUSTOMER_A no-resolve` from R1. The author's notes say transit routers need it to return ICMP errors for labelled packets, so R2's hop may disappear | `set protocols mpls icmp-tunneling` |

For each drill write down: symptom, the command that exposed it, the cause, the fix. Compare with the [troubleshooting matrix](../../docs/troubleshooting.md).
