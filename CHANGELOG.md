# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/). Versioning is described in [docs/project-metadata.md](docs/project-metadata.md).

## [Unreleased]

## [1.1.0-junos25.2R1.9] - 2026-10-02

### Fixed
- R1 IS-IS NET corrected to `49.0001.0100.0000.0001.00` (C1). Verified: adjacencies Up, all LSPs in area 49.0001.

### Changed
- R1 `ge-0/0/0.0` IS-IS Level 2 metric set to 100 (I2): the IGP now prefers R3 while the SR-TE primary still goes via R2, so the engineered path is a genuine detour.
- `configs/as-captured/R1.set` and `configs/stages/02-isis/R1.set` updated; the original is kept in `configs/history/1.0.0-junos25.2R1.9/`.

### Added
- `verification/captured/R1-after-fixes.txt`, including a VRF traceroute from R1 to 10.10.9.1 through R2 and R4 with label stacks.
- Audit checks for SR-TE path versus IGP shortest paths.
- Host-to-host VPCS traces in both directions (`verification/captured/hosts.txt`): the L3VPN is proven end to end.

## [1.0.0-junos25.2R1.9] - initial release

### Added
- Sanitised as-captured configurations for R1 to R6, CE_01 and CE_02, and stage files derived from them.
- Documentation for IS-IS, MPLS, SR-MPLS, L3VPN and SR-TE, with Mermaid diagrams.
- Raw verification captures from R1 to R6.
- Consistency audit script, link checker and CI workflow.
- Corrections and recommended improvements, kept separate from the captured configurations.
