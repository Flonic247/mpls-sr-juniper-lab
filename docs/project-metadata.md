# Project metadata and release plan

## Name

**`mpls-sr-juniper-lab`** (used throughout). Alternative if you prefer a longer, searchable name: `junos-sr-mpls-l3vpn-srte-lab`.

## GitHub repository description (one line)

Reproducible Juniper Junos lab: IS-IS, MPLS, SR-MPLS, L3VPN (MP-BGP) and SR-TE on 6 routers + 2 CEs, with real configs, captures, diagrams and a troubleshooting guide.

## Topics

`junos` `juniper` `segment-routing` `sr-mpls` `sr-te` `mpls` `l3vpn` `mp-bgp` `is-is` `network-automation` `networking-lab` `eve-ng` `vmx` `jncie` `ccnp` `network-engineering`

## LinkedIn announcement (draft)

> I turned my Juniper Segment Routing lab into an open-source learning project.
>
> It covers IS-IS, MPLS, SR-MPLS, an L3VPN over MP-BGP, and SR-TE with an explicit segment list that pins R1 to R6 over R1-R2-R4-R6. Six Junos routers, two CEs, real configurations, real show-command captures, Mermaid diagrams and a troubleshooting matrix.
>
> What I like most: it documents its own flaws. A consistency audit script found a malformed IS-IS NET, a redundant VRF target, and the fact that my "engineered" SR-TE path was one of three equal-cost IGP paths. I fixed the NET, added an IS-IS metric so the path became a real detour, and kept the original configs in a history folder.
>
> Clone it, deploy it, break it, fix it: <repository link>
>
> Feedback and extra captures welcome. #Junos #SegmentRouting #MPLS #NetworkEngineering #JNCIE

## Release and versioning strategy

Current release: `1.1.0-junos25.2R1.9`.

- **Scheme:** `MAJOR.MINOR.PATCH-junos<version>`, for example `1.0.0-junos25.2R1.9`. The suffix says which Junos release the captures belong to.
- **MAJOR:** topology or addressing changes. **MINOR:** new labs, new captures, new documentation. **PATCH:** typo and diagram fixes.
- **Never edit** `configs/as-captured/` for a given release. If the lab changes, add a new capture set in a new release and describe it in [CHANGELOG.md](../CHANGELOG.md).
- Tag releases on `main`; attach a zip of the tag. Keep one branch per Junos major release only if the configurations diverge.
- Before every release: `python3 tools/audit.py`, `python3 tools/check_links.py`, review the audit's WARNING and ERROR lists.

## Placeholders to complete before publishing

Copyright holder in [LICENSE](../LICENSE), security contact in [SECURITY.md](../SECURITY.md), repository link in the LinkedIn text.
